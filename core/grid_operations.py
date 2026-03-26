"""Операции с сеткой (перемещение, добавление, удаление линий)"""
from tkinter import messagebox


class GridOperations:
    """Управляет операциями с сеткой (перемещение, добавление, удаление линий)."""
    
    def __init__(self, editor):
        """
        Args:
            editor: Экземпляр GridEditor
        """
        self.editor = editor
    
    def move_line_left(self, event):
        if self.editor.image is None:
            return
        
        # Проверяем, заблокирована ли сетка
        if hasattr(self.editor, 'grid_locked') and self.editor.grid_locked:
            return
        
        if self.editor.selected_line is not None and self.editor.selected_line_type:
            # Сохраняем состояние перед перемещением линии
            if not self.editor.state_saved_for_action:
                self.editor.save_state()
                self.editor.state_saved_for_action = True
            
            # Используем grid_manager для перемещения линии
            line_idx = self.editor.grid_manager.find_line_index(self.editor.selected_line, self.editor.selected_line_type)
            if line_idx is not None:
                success, new_pos = self.editor.grid_manager.move_line_left(line_idx, self.editor.selected_line_type)
                if success:
                    # Синхронизируем линии
                    if self.editor.selected_line_type == 'v':
                        self.editor.vertical_lines = self.editor.grid_manager.vertical_lines
                    else:
                        self.editor.horizontal_lines = self.editor.grid_manager.horizontal_lines
                    self.editor.selected_line = new_pos
                    
                    # Сбрасываем фрагментированное изображение и палитру при изменении сетки
                    self.editor.fragmented_image = None
                    self.editor.palette = None
                    self.editor.selected_color = None
                    for widget in self.editor.palette_frame.winfo_children():
                        widget.destroy()
                    self.editor.palette_canvas = None
                    
                    self.editor.update_display()
                    self.editor.update_footer_info()
    
    def move_line_right(self, event):
        if self.editor.image is None:
            return
        
        # Проверяем, заблокирована ли сетка
        if hasattr(self.editor, 'grid_locked') and self.editor.grid_locked:
            return
        
        if self.editor.selected_line is not None and self.editor.selected_line_type:
            # Сохраняем состояние перед перемещением линии
            if not self.editor.state_saved_for_action:
                self.editor.save_state()
                self.editor.state_saved_for_action = True
            
            # Используем grid_manager для перемещения линии
            line_idx = self.editor.grid_manager.find_line_index(self.editor.selected_line, self.editor.selected_line_type)
            if line_idx is not None:
                max_pos = self.editor.image.width if self.editor.selected_line_type == 'v' else self.editor.image.height
                success, new_pos = self.editor.grid_manager.move_line_right(line_idx, self.editor.selected_line_type, max_pos)
                if success:
                    # Синхронизируем линии
                    if self.editor.selected_line_type == 'v':
                        self.editor.vertical_lines = self.editor.grid_manager.vertical_lines
                    else:
                        self.editor.horizontal_lines = self.editor.grid_manager.horizontal_lines
                    self.editor.selected_line = new_pos
                    
                    # Сбрасываем фрагментированное изображение и палитру при изменении сетки
                    self.editor.fragmented_image = None
                    self.editor.palette = None
                    self.editor.selected_color = None
                    for widget in self.editor.palette_frame.winfo_children():
                        widget.destroy()
                    self.editor.palette_canvas = None
                    
                    self.editor.update_display()
                    self.editor.update_footer_info()
    
    def move_line_up(self, event):
        if self.editor.image is None:
            return
        
        # Проверяем, заблокирована ли сетка
        if hasattr(self.editor, 'grid_locked') and self.editor.grid_locked:
            return
        
        if self.editor.selected_line is not None and self.editor.selected_line_type == 'h':
            # Сохраняем состояние перед перемещением линии
            if not self.editor.state_saved_for_action:
                self.editor.save_state()
                self.editor.state_saved_for_action = True
            
            # Используем grid_manager для перемещения линии
            line_idx = self.editor.grid_manager.find_line_index(self.editor.selected_line, self.editor.selected_line_type)
            if line_idx is not None:
                success, new_pos = self.editor.grid_manager.move_line_left(line_idx, self.editor.selected_line_type)
                if success:
                    self.editor.horizontal_lines = self.editor.grid_manager.horizontal_lines
                    self.editor.selected_line = new_pos
                    
                    # Сбрасываем фрагментированное изображение и палитру при изменении сетки
                    self.editor.fragmented_image = None
                    self.editor.palette = None
                    self.editor.selected_color = None
                    for widget in self.editor.palette_frame.winfo_children():
                        widget.destroy()
                    self.editor.palette_canvas = None
                    
                    self.editor.update_display()
                    self.editor.update_footer_info()
    
    def move_line_down(self, event):
        if self.editor.image is None:
            return
        
        # Проверяем, заблокирована ли сетка
        if hasattr(self.editor, 'grid_locked') and self.editor.grid_locked:
            return
        
        if self.editor.selected_line is not None and self.editor.selected_line_type == 'h':
            # Сохраняем состояние перед перемещением линии
            if not self.editor.state_saved_for_action:
                self.editor.save_state()
                self.editor.state_saved_for_action = True
            
            # Используем grid_manager для перемещения линии
            line_idx = self.editor.grid_manager.find_line_index(self.editor.selected_line, self.editor.selected_line_type)
            if line_idx is not None:
                success, new_pos = self.editor.grid_manager.move_line_right(line_idx, self.editor.selected_line_type, self.editor.image.height)
                if success:
                    self.editor.horizontal_lines = self.editor.grid_manager.horizontal_lines
                    self.editor.selected_line = new_pos
                    
                    # Сбрасываем фрагментированное изображение и палитру при изменении сетки
                    self.editor.fragmented_image = None
                    self.editor.palette = None
                    self.editor.selected_color = None
                    for widget in self.editor.palette_frame.winfo_children():
                        widget.destroy()
                    self.editor.palette_canvas = None
                    
                    self.editor.update_display()
                    self.editor.update_footer_info()
    
    def add_line(self, event):
        """Добавляет линию того типа, который выделен"""
        if self.editor.image is None:
            return
        
        # Проверяем, заблокирована ли сетка
        if hasattr(self.editor, 'grid_locked') and self.editor.grid_locked:
            messagebox.showinfo("Информация", "Сетка заблокирована после получения палитры")
            return
        
        if self.editor.selected_line is None:
            messagebox.showinfo("Информация", "Сначала выберите линию, чтобы определить тип")
            return
        
        # Проверяем, включен ли режим "Разметка слева направо"
        manual_marking_enabled = (hasattr(self.editor, 'manual_marking_enabled') and 
                                  self.editor.manual_marking_enabled.get())
        
        # Сохраняем состояние перед добавлением линии
        self.editor.save_state()
        
        # Сбрасываем фрагментированное изображение и палитру при изменении сетки
        self.editor.fragmented_image = None
        self.editor.palette = None
        self.editor.selected_color = None
        for widget in self.editor.palette_frame.winfo_children():
            widget.destroy()
        self.editor.palette_canvas = None
        
        if self.editor.selected_line_type == 'v':
            idx = self.editor.vertical_lines.index(self.editor.selected_line)
            
            if manual_marking_enabled:
                # Режим "Разметка слева направо": добавляем линию справа от выбранной
                # Если выбрана первая неграничная линия (индекс 1), ставим на расстоянии от границы до первой линии
                if idx == 1:
                    # Расстояние от границы (0) до первой линии
                    distance = self.editor.selected_line - 0
                    new_pos = self.editor.selected_line + distance
                    # Проверяем, что не выходим за следующую линию или границу
                    if idx + 1 < len(self.editor.vertical_lines):
                        new_pos = min(new_pos, self.editor.vertical_lines[idx + 1] - 1)
                    else:
                        new_pos = min(new_pos, self.editor.image.width - 1)
                elif idx > 1 and idx < len(self.editor.vertical_lines) - 1:
                    # Расстояние между предыдущей и текущей линией
                    prev_line = self.editor.vertical_lines[idx - 1]
                    distance = self.editor.selected_line - prev_line
                    new_pos = self.editor.selected_line + distance
                    # Проверяем, что не выходим за следующую линию
                    next_line = self.editor.vertical_lines[idx + 1]
                    new_pos = min(new_pos, next_line - 1)
                else:
                    # Если это последняя линия, добавляем справа на том же расстоянии
                    if idx > 1:
                        prev_line = self.editor.vertical_lines[idx - 1]
                        distance = self.editor.selected_line - prev_line
                    else:
                        distance = self.editor.selected_line - 0
                    new_pos = min(self.editor.selected_line + distance, self.editor.image.width - 1)
            else:
                # Обычный режим: добавляем линию справа от выбранной (посередине между текущей и следующей)
                if idx < len(self.editor.vertical_lines) - 1:
                    next_line = self.editor.vertical_lines[idx + 1]
                    new_pos = (self.editor.selected_line + next_line) // 2
                    # Проверяем, что новая позиция не слишком близко к границам
                    if new_pos == self.editor.selected_line or new_pos == next_line:
                        new_pos = min(self.editor.selected_line + 10, next_line - 1)
                else:
                    # Если это последняя линия, добавляем справа
                    new_pos = min(self.editor.selected_line + 50, self.editor.image.width - 1)
            
            # Проверяем, что не добавляем граничные линии и что позиция валидна
            if 0 < new_pos < self.editor.image.width:
                if self.editor.grid_manager.add_line(new_pos, 'v'):
                    self.editor.vertical_lines = self.editor.grid_manager.vertical_lines
                    self.editor.selected_line = new_pos
                    self.editor.grid_manager.selected_line = new_pos
                    self.editor.update_display()
                    self.editor.info_label.config(text=f"Добавлена вертикальная линия\nПозиция: {new_pos}")
                    self.editor.update_footer_info()
        
        elif self.editor.selected_line_type == 'h':
            idx = self.editor.horizontal_lines.index(self.editor.selected_line)
            
            if manual_marking_enabled:
                # Режим "Разметка слева направо": добавляем линию снизу от выбранной
                # Если выбрана первая неграничная линия (индекс 1), ставим на расстоянии от границы до первой линии
                if idx == 1:
                    # Расстояние от границы (0) до первой линии
                    distance = self.editor.selected_line - 0
                    new_pos = self.editor.selected_line + distance
                    # Проверяем, что не выходим за следующую линию или границу
                    if idx + 1 < len(self.editor.horizontal_lines):
                        new_pos = min(new_pos, self.editor.horizontal_lines[idx + 1] - 1)
                    else:
                        new_pos = min(new_pos, self.editor.image.height - 1)
                elif idx > 1 and idx < len(self.editor.horizontal_lines) - 1:
                    # Расстояние между предыдущей и текущей линией
                    prev_line = self.editor.horizontal_lines[idx - 1]
                    distance = self.editor.selected_line - prev_line
                    new_pos = self.editor.selected_line + distance
                    # Проверяем, что не выходим за следующую линию
                    next_line = self.editor.horizontal_lines[idx + 1]
                    new_pos = min(new_pos, next_line - 1)
                else:
                    # Если это последняя линия, добавляем снизу на том же расстоянии
                    if idx > 1:
                        prev_line = self.editor.horizontal_lines[idx - 1]
                        distance = self.editor.selected_line - prev_line
                    else:
                        distance = self.editor.selected_line - 0
                    new_pos = min(self.editor.selected_line + distance, self.editor.image.height - 1)
            else:
                # Обычный режим: добавляем линию снизу от выбранной (посередине между текущей и следующей)
                if idx < len(self.editor.horizontal_lines) - 1:
                    next_line = self.editor.horizontal_lines[idx + 1]
                    new_pos = (self.editor.selected_line + next_line) // 2
                    # Проверяем, что новая позиция не слишком близко к границам
                    if new_pos == self.editor.selected_line or new_pos == next_line:
                        new_pos = min(self.editor.selected_line + 10, next_line - 1)
                else:
                    # Если это последняя линия, добавляем снизу
                    new_pos = min(self.editor.selected_line + 50, self.editor.image.height - 1)
            
            # Проверяем, что не добавляем граничные линии и что позиция валидна
            if 0 < new_pos < self.editor.image.height:
                if self.editor.grid_manager.add_line(new_pos, 'h'):
                    self.editor.horizontal_lines = self.editor.grid_manager.horizontal_lines
                    self.editor.selected_line = new_pos
                    self.editor.grid_manager.selected_line = new_pos
                    self.editor.update_display()
                    self.editor.info_label.config(text=f"Добавлена горизонтальная линия\nПозиция: {new_pos}")
                    self.editor.update_footer_info()
    
    def remove_line(self, event):
        """Удаляет текущую выделенную линию"""
        if self.editor.image is None:
            return
        
        # Проверяем, заблокирована ли сетка
        if hasattr(self.editor, 'grid_locked') and self.editor.grid_locked:
            messagebox.showinfo("Информация", "Сетка заблокирована после получения палитры")
            return
        
        if self.editor.selected_line is None:
            messagebox.showinfo("Информация", "Сначала выберите линию для удаления")
            return
        
        # Сохраняем состояние перед удалением линии
        self.editor.save_state()
        
        # Сбрасываем фрагментированное изображение и палитру при изменении сетки
        self.editor.fragmented_image = None
        self.editor.palette = None
        self.editor.selected_color = None
        for widget in self.editor.palette_frame.winfo_children():
            widget.destroy()
        self.editor.palette_canvas = None
        
        if self.editor.selected_line_type == 'v':
            if self.editor.grid_manager.remove_line(self.editor.selected_line, 'v', min_lines=2):
                self.editor.vertical_lines = self.editor.grid_manager.vertical_lines
                self.editor.selected_line = None
                self.editor.selected_line_type = None
                self.editor.grid_manager.selected_line = None
                self.editor.grid_manager.selected_line_type = None
                self.editor.update_display()
                self.editor.info_label.config(text=f"Удалена вертикальная линия")
                self.editor.update_footer_info()
            else:
                messagebox.showwarning("Предупреждение", "Нельзя удалить все вертикальные линии")
        
        elif self.editor.selected_line_type == 'h':
            if self.editor.grid_manager.remove_line(self.editor.selected_line, 'h', min_lines=2):
                self.editor.horizontal_lines = self.editor.grid_manager.horizontal_lines
                self.editor.selected_line = None
                self.editor.selected_line_type = None
                self.editor.grid_manager.selected_line = None
                self.editor.grid_manager.selected_line_type = None
                self.editor.update_display()
                self.editor.info_label.config(text=f"Удалена горизонтальная линия")
                self.editor.update_footer_info()
            else:
                messagebox.showwarning("Предупреждение", "Нельзя удалить все горизонтальные линии")

