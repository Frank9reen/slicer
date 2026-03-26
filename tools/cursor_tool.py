"""Инструмент курсор для выделения строк и столбцов"""
from tkinter import messagebox

from .base_tool import BaseTool


class CursorTool(BaseTool):
    """Инструмент для выделения строк и столбцов сетки."""

    name = "cursor"
    cursor = "arrow"

    def __init__(self, editor):
        super().__init__(editor)
        self.dragging = False
        self.dragged_line_index = None
        self.dragged_line_type = None

    def activate(self):
        editor = self.editor
        editor.selection_mode = False
        if hasattr(editor, "selection_mode_var"):
            editor.selection_mode_var.set(False)
        editor.paint_mode = False
        editor.eyedropper_mode = False
        editor.paint_tool = None
        editor.info_label.config(
            text="Режим: Курсор\nКликните на линию сетки для выделения строки или столбца\nЗажмите и перетащите для перемещения линии"
        )
        editor.update_tool_buttons()
        editor.update_paint_cursor()

    def deactivate(self):
        editor = self.editor
        # Сбрасываем выделение линий при деактивации
        editor.selected_line = None
        editor.selected_line_type = None
        editor.grid_manager.selected_line = None
        editor.grid_manager.selected_line_type = None
        self.dragging = False
        self.dragged_line_index = None
        self.dragged_line_type = None
        editor.update_display()

    def on_mouse_down(self, img_x, img_y):
        """Обрабатывает клик для выбора линии сетки и начало перетаскивания"""
        editor = self.editor
        
        if editor.image is None:
            return False
        
        # Проверяем, заблокирована ли сетка
        if hasattr(editor, 'grid_locked') and editor.grid_locked:
            messagebox.showinfo("Информация", "Сетка заблокирована после получения палитры")
            return True
        
        if len(editor.vertical_lines) < 2 or len(editor.horizontal_lines) < 2:
            messagebox.showwarning("Предупреждение", "Сначала постройте сетку!")
            return True
        
        # Определяем порог для клика по линии (с учетом зума)
        # Используем scale из view_manager, если доступен, иначе zoom
        if hasattr(editor, 'scale') and editor.scale > 0:
            threshold = 5 / editor.scale
        elif hasattr(editor, 'zoom') and editor.zoom > 0:
            threshold = 5 / editor.zoom
        else:
            threshold = 5
        
        # Сбрасываем предыдущее выделение
        editor.selected_line = None
        editor.selected_line_type = None
        editor.grid_manager.selected_line = None
        editor.grid_manager.selected_line_type = None
        self.dragging = False
        self.dragged_line_index = None
        self.dragged_line_type = None
        
        # Проверяем клик по вертикальным линиям
        for i, x in enumerate(editor.vertical_lines):
            if abs(img_x - x) < threshold:
                editor.selected_line = x
                editor.selected_line_type = 'v'
                editor.grid_manager.selected_line = x
                editor.grid_manager.selected_line_type = 'v'
                # Начинаем перетаскивание
                self.dragging = True
                self.dragged_line_index = i
                self.dragged_line_type = 'v'
                # Сохраняем состояние перед перемещением
                if not editor.state_saved_for_action:
                    editor.save_state()
                    editor.state_saved_for_action = True
                editor.update_display()
                editor.info_label.config(
                    text=f"Выбрана вертикальная линия\nПозиция: {x}\nСтолбец: {i}\nПеретащите для перемещения"
                )
                return True
        
        # Проверяем клик по горизонтальным линиям
        for i, y in enumerate(editor.horizontal_lines):
            if abs(img_y - y) < threshold:
                editor.selected_line = y
                editor.selected_line_type = 'h'
                editor.grid_manager.selected_line = y
                editor.grid_manager.selected_line_type = 'h'
                # Начинаем перетаскивание
                self.dragging = True
                self.dragged_line_index = i
                self.dragged_line_type = 'h'
                # Сохраняем состояние перед перемещением
                if not editor.state_saved_for_action:
                    editor.save_state()
                    editor.state_saved_for_action = True
                editor.update_display()
                editor.info_label.config(
                    text=f"Выбрана горизонтальная линия\nПозиция: {y}\nСтрока: {i}\nПеретащите для перемещения"
                )
                return True
        
        # Если клик не попал на линию, сбрасываем выделение
        editor.update_display()
        editor.info_label.config(text="Клик вне линии сетки")
        return True

    def on_mouse_move(self, img_x, img_y):
        """Изменяет курсор при наведении на линию или перемещает линию при перетаскивании"""
        editor = self.editor
        
        if editor.image is None:
            return False
        
        if len(editor.vertical_lines) < 2 or len(editor.horizontal_lines) < 2:
            return False
        
        # Если идет перетаскивание, перемещаем линию
        # Проверяем, заблокирована ли сетка
        if self.dragging and self.dragged_line_index is not None and self.dragged_line_type:
            if hasattr(editor, 'grid_locked') and editor.grid_locked:
                # Если сетка заблокирована, прекращаем перетаскивание
                self.dragging = False
                self.dragged_line_index = None
                self.dragged_line_type = None
                editor.selected_line = None
                editor.selected_line_type = None
                editor.grid_manager.selected_line = None
                editor.grid_manager.selected_line_type = None
                editor.update_display()
                return True
            
            if self.dragged_line_type == 'v':
                # Перемещаем вертикальную линию
                max_pos = editor.image.width
                success, new_pos = editor.grid_manager.move_line_to_position(
                    self.dragged_line_index, 'v', img_x, max_pos, min_distance=1
                )
                if success:
                    editor.vertical_lines = editor.grid_manager.vertical_lines
                    editor.selected_line = new_pos
                    editor.grid_manager.selected_line = new_pos
                    # Обновляем индекс после сортировки
                    self.dragged_line_index = editor.vertical_lines.index(new_pos)
                    # Сбрасываем фрагментированное изображение и палитру при изменении сетки
                    editor.fragmented_image = None
                    editor.palette = None
                    editor.selected_color = None
                    for widget in editor.palette_frame.winfo_children():
                        widget.destroy()
                    editor.palette_canvas = None
                    editor.update_display()
                    editor.update_footer_info()
                    editor.info_label.config(
                        text=f"Вертикальная линия\nПозиция: {new_pos}\nСтолбец: {self.dragged_line_index}"
                    )
            else:  # 'h'
                # Перемещаем горизонтальную линию
                max_pos = editor.image.height
                success, new_pos = editor.grid_manager.move_line_to_position(
                    self.dragged_line_index, 'h', img_y, max_pos, min_distance=1
                )
                if success:
                    editor.horizontal_lines = editor.grid_manager.horizontal_lines
                    editor.selected_line = new_pos
                    editor.grid_manager.selected_line = new_pos
                    # Обновляем индекс после сортировки
                    self.dragged_line_index = editor.horizontal_lines.index(new_pos)
                    # Сбрасываем фрагментированное изображение и палитру при изменении сетки
                    editor.fragmented_image = None
                    editor.palette = None
                    editor.selected_color = None
                    for widget in editor.palette_frame.winfo_children():
                        widget.destroy()
                    editor.palette_canvas = None
                    editor.update_display()
                    editor.update_footer_info()
                    editor.info_label.config(
                        text=f"Горизонтальная линия\nПозиция: {new_pos}\nСтрока: {self.dragged_line_index}"
                    )
            return True
        
        # Определяем порог для наведения на линию
        # Используем scale из view_manager, если доступен, иначе zoom
        if hasattr(editor, 'scale') and editor.scale > 0:
            threshold = 5 / editor.scale
        elif hasattr(editor, 'zoom') and editor.zoom > 0:
            threshold = 5 / editor.zoom
        else:
            threshold = 5
        
        # Проверяем наведение на вертикальные линии
        for x in editor.vertical_lines:
            if abs(img_x - x) < threshold:
                editor.canvas.config(cursor='sb_h_double_arrow')
                return True
        
        # Проверяем наведение на горизонтальные линии
        for y in editor.horizontal_lines:
            if abs(img_y - y) < threshold:
                editor.canvas.config(cursor='sb_v_double_arrow')
                return True
        
        # Если не на линии, возвращаем обычный курсор
        editor.canvas.config(cursor='arrow')
        return False

    def on_mouse_up(self, img_x, img_y):
        """Обрабатывает отпускание кнопки мыши и завершает перетаскивание"""
        if self.dragging:
            self.dragging = False
            # Сбрасываем флаг сохранения состояния после завершения действия
            if hasattr(self.editor, 'state_saved_for_action'):
                self.editor.state_saved_for_action = False
            return True
        return False

