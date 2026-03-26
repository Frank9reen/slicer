"""Инструмент для закрашивания ячеек по линии"""
from .base_tool import BaseTool
from core.image_processor import ImageProcessor
import numpy as np
from PIL import Image


class LinePaintTool(BaseTool):
    """Инструмент для закрашивания ячеек вдоль нарисованной линии."""

    name = "line_paint"
    cursor = "pencil"

    def __init__(self, editor):
        super().__init__(editor)
        self.drawing = False
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        self.preview_line_id = None
        self.cells_to_paint = set()  # Множество ячеек для закрашивания

    def activate(self):
        """Включает инструмент закрашивания по линии."""
        editor = self.editor
        editor.selection_mode = False
        if hasattr(editor, "selection_mode_var"):
            editor.selection_mode_var.set(False)
        editor.paint_mode = False
        editor.eyedropper_mode = False
        editor.paint_tool = None
        editor.info_label.config(
            text="Режим: Закрашивание по линии\nЗажмите ЛКМ и ведите линию.\nВсе ячейки вдоль линии будут закрашены выбранным цветом"
        )
        editor.update_tool_buttons()
        editor.update_paint_cursor()
        self.drawing = False
        self._clear_preview()

    def deactivate(self):
        """Выключает инструмент."""
        self.drawing = False
        self._clear_preview()

    def _clear_preview(self):
        """Удаляет линию предпросмотра с canvas."""
        if self.preview_line_id is not None:
            try:
                self.editor.canvas.delete(self.preview_line_id)
            except:
                pass
            self.preview_line_id = None
        
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        self.cells_to_paint.clear()

    def _image_to_canvas_coords(self, img_x, img_y):
        """Преобразует координаты изображения в координаты canvas."""
        if not hasattr(self.editor, 'scale'):
            return None, None
        
        canvas_x = int(img_x * self.editor.scale + self.editor.offset_x)
        canvas_y = int(img_y * self.editor.scale + self.editor.offset_y)
        
        return canvas_x, canvas_y

    def _get_line_cells(self, x1, y1, x2, y2):
        """
        Получает все ячейки вдоль линии используя алгоритм Брезенхема.
        
        Args:
            x1, y1: Начальная точка (координаты изображения)
            x2, y2: Конечная точка (координаты изображения)
        
        Returns:
            set: Множество кортежей (col, row) - ячеек для закрашивания
        """
        cells = set()
        
        # Алгоритм Брезенхема для получения всех точек линии
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        
        x, y = x1, y1
        
        # Проходим по всем точкам линии
        max_iterations = dx + dy + 1000  # Защита от бесконечного цикла
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # Определяем ячейку для текущей точки
            cell = ImageProcessor.get_cell_from_position(
                x, y,
                self.editor.vertical_lines,
                self.editor.horizontal_lines
            )
            
            if cell[0] is not None and cell[1] is not None:
                cells.add(cell)
            
            # Проверяем, достигли ли конечной точки
            if x == x2 and y == y2:
                break
            
            # Следующий шаг по алгоритму Брезенхема
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
        
        return cells

    def _draw_preview(self, canvas_x1, canvas_y1, canvas_x2, canvas_y2):
        """Рисует линию предпросмотра на canvas."""
        # Удаляем предыдущую линию
        if self.preview_line_id is not None:
            try:
                self.editor.canvas.delete(self.preview_line_id)
            except:
                pass
        
        # Рисуем линию предпросмотра
        self.preview_line_id = self.editor.canvas.create_line(
            canvas_x1, canvas_y1, canvas_x2, canvas_y2,
            fill='red', width=3, tags='line_paint_preview'
        )

    def on_mouse_down(self, img_x, img_y):
        """Обрабатывает нажатие кнопки мыши."""
        if self.editor.image is None:
            return False
        
        # Проверяем, выбран ли цвет
        if self.editor.selected_color is None:
            self.editor.info_label.config(
                text="Сначала выберите цвет для закрашивания!"
            )
            return False
        
        # Сохраняем состояние перед закрашиванием
        self.editor.save_state()
        
        self.drawing = True
        self.start_x = img_x
        self.start_y = img_y
        self.end_x = img_x
        self.end_y = img_y
        
        # Получаем координаты canvas для начальной точки
        canvas_x, canvas_y = self._image_to_canvas_coords(img_x, img_y)
        if canvas_x is not None and canvas_y is not None:
            self._draw_preview(canvas_x, canvas_y, canvas_x, canvas_y)
        
        return True

    def on_mouse_move(self, img_x, img_y):
        """Обрабатывает движение мыши при нажатой кнопке."""
        if not self.drawing or self.start_x is None or self.start_y is None:
            return False
        
        self.end_x = img_x
        self.end_y = img_y
        
        # Получаем ячейки вдоль линии
        self.cells_to_paint = self._get_line_cells(
            self.start_x, self.start_y,
            self.end_x, self.end_y
        )
        
        # Обновляем превью линии
        canvas_x1, canvas_y1 = self._image_to_canvas_coords(self.start_x, self.start_y)
        canvas_x2, canvas_y2 = self._image_to_canvas_coords(self.end_x, self.end_y)
        
        if canvas_x1 is not None and canvas_y1 is not None and canvas_x2 is not None and canvas_y2 is not None:
            self._draw_preview(canvas_x1, canvas_y1, canvas_x2, canvas_y2)
        
        # Обновляем информацию о количестве ячеек
        self.editor.info_label.config(
            text=f"Закрашивание по линии\nЯчеек для закрашивания: {len(self.cells_to_paint)}"
        )
        
        return True

    def on_mouse_up(self, img_x, img_y):
        """Обрабатывает отпускание кнопки мыши - закрашивает ячейки."""
        if not self.drawing:
            return False
        
        self.drawing = False
        
        # Обновляем финальную позицию
        if img_x is not None and img_y is not None:
            self.end_x = img_x
            self.end_y = img_y
            
            # Получаем финальный список ячеек
            self.cells_to_paint = self._get_line_cells(
                self.start_x, self.start_y,
                self.end_x, self.end_y
            )
            
            # Закрашиваем все ячейки вдоль линии
            if len(self.cells_to_paint) > 0:
                self._paint_cells()
        
        # Очищаем превью
        self._clear_preview()
        
        return True

    def _paint_cells(self):
        """Закрашивает все ячейки из списка."""
        if not self.cells_to_paint:
            return
        
        # Получаем массив изображения
        img_array = np.array(self.editor.image)
        
        # Закрашиваем каждую ячейку
        for col, row in self.cells_to_paint:
            if col < 0 or col >= len(self.editor.vertical_lines) - 1:
                continue
            if row < 0 or row >= len(self.editor.horizontal_lines) - 1:
                continue
            
            x1 = self.editor.vertical_lines[col]
            x2 = self.editor.vertical_lines[col + 1]
            y1 = self.editor.horizontal_lines[row]
            y2 = self.editor.horizontal_lines[row + 1]
            
            # Закрашиваем ячейку
            if img_array.shape[2] == 4:
                # Если есть альфа-канал, обновляем только RGB
                img_array[y1:y2, x1:x2, 0] = self.editor.selected_color[0]
                img_array[y1:y2, x1:x2, 1] = self.editor.selected_color[1]
                img_array[y1:y2, x1:x2, 2] = self.editor.selected_color[2]
            else:
                img_array[y1:y2, x1:x2] = self.editor.selected_color
            
            # Сохраняем информацию о закрашенной ячейке
            self.editor.painted_cells[(col, row)] = tuple(self.editor.selected_color)
        
        # Обновляем изображение
        self.editor.image = Image.fromarray(img_array)
        
        # Автоматически переключаемся на режим 2 при закрашивании
        if self.editor.view_mode == 1:
            self.editor.set_view_mode(2)
        else:
            self.editor.update_display()
        
        # Обновляем палитру для отображения новых счетчиков
        if self.editor.palette is not None:
            self.editor.display_palette()
        
        self.editor.info_label.config(
            text=f"Закрашено ячеек: {len(self.cells_to_paint)}"
        )

