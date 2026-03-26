"""Инструмент линейка"""
import math
from .base_tool import BaseTool


class RulerTool(BaseTool):
    """Инструмент для измерения расстояний на изображении."""

    name = "ruler"
    cursor = "crosshair"

    def __init__(self, editor):
        super().__init__(editor)
        self.measuring = False
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        self.ruler_line_id = None
        self.ruler_text_id = None

    def activate(self):
        """Включает инструмент линейка."""
        editor = self.editor
        editor.selection_mode = False
        if hasattr(editor, "selection_mode_var"):
            editor.selection_mode_var.set(False)
        editor.paint_mode = False
        editor.eyedropper_mode = False
        editor.paint_tool = None
        editor.info_label.config(
            text="Режим: Линейка\nЗажмите ЛКМ и двигайте мышь для измерения"
        )
        editor.update_tool_buttons()
        editor.update_paint_cursor()
        self.measuring = False
        self._clear_ruler()

    def deactivate(self):
        """Выключает инструмент линейка."""
        self.measuring = False
        self._clear_ruler()

    def _clear_ruler(self):
        """Удаляет линию линейки с canvas."""
        if self.ruler_line_id is not None:
            try:
                self.editor.canvas.delete(self.ruler_line_id)
            except:
                pass
            self.ruler_line_id = None
        
        if self.ruler_text_id is not None:
            try:
                self.editor.canvas.delete(self.ruler_text_id)
            except:
                pass
            self.ruler_text_id = None
        
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None

    def _canvas_to_image_coords(self, canvas_x, canvas_y):
        """Преобразует координаты canvas в координаты изображения."""
        if not hasattr(self.editor, 'scale'):
            return None, None
        
        img_x = int((canvas_x - self.editor.offset_x) / self.editor.scale)
        img_y = int((canvas_y - self.editor.offset_y) / self.editor.scale)
        
        if self.editor.image is not None:
            if 0 <= img_x < self.editor.image.width and 0 <= img_y < self.editor.image.height:
                return img_x, img_y
        
        return None, None

    def _image_to_canvas_coords(self, img_x, img_y):
        """Преобразует координаты изображения в координаты canvas."""
        if not hasattr(self.editor, 'scale'):
            return None, None
        
        canvas_x = int(img_x * self.editor.scale + self.editor.offset_x)
        canvas_y = int(img_y * self.editor.scale + self.editor.offset_y)
        
        return canvas_x, canvas_y

    def _calculate_distance(self, x1, y1, x2, y2):
        """Вычисляет расстояние между двумя точками в пикселях."""
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    
    def _calculate_distance_cm(self, x1, y1, x2, y2):
        """
        Вычисляет расстояние между двумя точками в см на основе сетки.
        Использует канву Aida 16 (16 клеток на дюйм).
        """
        if (not hasattr(self.editor, 'vertical_lines') or 
            not hasattr(self.editor, 'horizontal_lines') or
            len(self.editor.vertical_lines) < 2 or 
            len(self.editor.horizontal_lines) < 2):
            return None
        
        # Рассчитываем размер в см для канвы Aida 16 (16 клеток на дюйм)
        # 1 дюйм = 2.54 см, значит 1 клетка = 2.54 / 16 = 0.15875 см
        cells_per_cm = 16 / 2.54  # Клеток на см
        
        # Вычисляем общий размер изображения в см
        num_cells_width = len(self.editor.vertical_lines) - 1
        num_cells_height = len(self.editor.horizontal_lines) - 1
        total_width_cm = num_cells_width / cells_per_cm
        total_height_cm = num_cells_height / cells_per_cm
        
        # Вычисляем размер изображения в пикселях
        image_width_px = self.editor.image.width
        image_height_px = self.editor.image.height
        
        if image_width_px == 0 or image_height_px == 0:
            return None
        
        # Вычисляем коэффициенты пересчета: см на пиксель
        cm_per_px_width = total_width_cm / image_width_px
        cm_per_px_height = total_height_cm / image_height_px
        
        # Вычисляем расстояние в пикселях
        dx_px = x2 - x1
        dy_px = y2 - y1
        
        # Пересчитываем в см
        dx_cm = dx_px * cm_per_px_width
        dy_cm = dy_px * cm_per_px_height
        
        # Вычисляем общее расстояние в см (теорема Пифагора)
        distance_cm = math.sqrt(dx_cm ** 2 + dy_cm ** 2)
        
        return distance_cm

    def _draw_ruler(self, canvas_x1, canvas_y1, canvas_x2, canvas_y2):
        """Рисует линию линейки на canvas с текстом длины."""
        # Удаляем предыдущую линию и текст
        if self.ruler_line_id is not None:
            try:
                self.editor.canvas.delete(self.ruler_line_id)
            except:
                pass
        
        if self.ruler_text_id is not None:
            try:
                self.editor.canvas.delete(self.ruler_text_id)
            except:
                pass
        
        # Рисуем линию
        self.ruler_line_id = self.editor.canvas.create_line(
            canvas_x1, canvas_y1, canvas_x2, canvas_y2,
            fill='yellow', width=2, tags='ruler'
        )
        
        # Вычисляем расстояние в пикселях изображения
        img_x1, img_y1 = self._canvas_to_image_coords(canvas_x1, canvas_y1)
        img_x2, img_y2 = self._canvas_to_image_coords(canvas_x2, canvas_y2)
        
        if img_x1 is not None and img_y1 is not None and img_x2 is not None and img_y2 is not None:
            # Вычисляем расстояние в см на основе сетки
            distance_cm = self._calculate_distance_cm(img_x1, img_y1, img_x2, img_y2)
            
            if distance_cm is not None:
                distance_text = f"{distance_cm:.2f} см"
            else:
                # Если не удалось вычислить в см, показываем в пикселях
                distance_px = self._calculate_distance(img_x1, img_y1, img_x2, img_y2)
                distance_text = f"{distance_px:.1f} px"
            
            # Позиция текста - середина линии, немного смещена вверх
            text_x = (canvas_x1 + canvas_x2) // 2
            text_y = (canvas_y1 + canvas_y2) // 2 - 10
            
            # Рисуем текст с фоном для лучшей читаемости
            self.ruler_text_id = self.editor.canvas.create_text(
                text_x, text_y,
                text=distance_text,
                fill='yellow',
                font=('Arial', 12, 'bold'),
                tags='ruler'
            )
            
            # Обновляем информацию в info_label
            if distance_cm is not None:
                self.editor.info_label.config(
                    text=f"Линейка: {distance_text}\n"
                         f"Начало: ({int(img_x1)}, {int(img_y1)})\n"
                         f"Конец: ({int(img_x2)}, {int(img_y2)})"
                )
            else:
                distance_px = self._calculate_distance(img_x1, img_y1, img_x2, img_y2)
                self.editor.info_label.config(
                    text=f"Линейка: {distance_text}\n"
                         f"Начало: ({int(img_x1)}, {int(img_y1)})\n"
                         f"Конец: ({int(img_x2)}, {int(img_y2)})\n"
                         f"(Сетка не построена)"
                )

    def update_ruler_display(self):
        """Обновляет отображение линейки при изменении масштаба или панорамирования."""
        if self.start_x is not None and self.start_y is not None and self.end_x is not None and self.end_y is not None:
            canvas_x1, canvas_y1 = self._image_to_canvas_coords(self.start_x, self.start_y)
            canvas_x2, canvas_y2 = self._image_to_canvas_coords(self.end_x, self.end_y)
            
            if canvas_x1 is not None and canvas_y1 is not None and canvas_x2 is not None and canvas_y2 is not None:
                self._draw_ruler(canvas_x1, canvas_y1, canvas_x2, canvas_y2)

    def on_mouse_down(self, img_x, img_y):
        """Обрабатывает нажатие кнопки мыши."""
        if self.editor.image is None:
            return False
        
        self.measuring = True
        self.start_x = img_x
        self.start_y = img_y
        self.end_x = img_x
        self.end_y = img_y
        
        # Получаем координаты canvas для начальной точки
        canvas_x, canvas_y = self._image_to_canvas_coords(img_x, img_y)
        if canvas_x is not None and canvas_y is not None:
            self._draw_ruler(canvas_x, canvas_y, canvas_x, canvas_y)
        
        return True

    def on_mouse_move(self, img_x, img_y):
        """Обрабатывает движение мыши при нажатой кнопке."""
        if not self.measuring or self.start_x is None or self.start_y is None:
            return False
        
        self.end_x = img_x
        self.end_y = img_y
        
        # Получаем координаты canvas для обеих точек
        canvas_x1, canvas_y1 = self._image_to_canvas_coords(self.start_x, self.start_y)
        canvas_x2, canvas_y2 = self._image_to_canvas_coords(self.end_x, self.end_y)
        
        if canvas_x1 is not None and canvas_y1 is not None and canvas_x2 is not None and canvas_y2 is not None:
            self._draw_ruler(canvas_x1, canvas_y1, canvas_x2, canvas_y2)
        
        return True

    def on_mouse_up(self, img_x, img_y):
        """Обрабатывает отпускание кнопки мыши."""
        if not self.measuring:
            return False
        
        self.measuring = False
        
        # Обновляем финальную позицию
        if img_x is not None and img_y is not None:
            self.end_x = img_x
            self.end_y = img_y
            
            # Вычисляем финальное расстояние
            if self.start_x is not None and self.start_y is not None:
                distance_cm = self._calculate_distance_cm(self.start_x, self.start_y, self.end_x, self.end_y)
                
                if distance_cm is not None:
                    distance_text = f"{distance_cm:.2f} см"
                else:
                    distance_px = self._calculate_distance(self.start_x, self.start_y, self.end_x, self.end_y)
                    distance_text = f"{distance_px:.1f} px"
                
                if distance_cm is not None:
                    self.editor.info_label.config(
                        text=f"Линейка: {distance_text}\n"
                             f"Начало: ({int(self.start_x)}, {int(self.start_y)})\n"
                             f"Конец: ({int(self.end_x)}, {int(self.end_y)})"
                    )
                else:
                    self.editor.info_label.config(
                        text=f"Линейка: {distance_text}\n"
                             f"Начало: ({int(self.start_x)}, {int(self.start_y)})\n"
                             f"Конец: ({int(self.end_x)}, {int(self.end_y)})\n"
                             f"(Сетка не построена)"
                    )
        
        return True

