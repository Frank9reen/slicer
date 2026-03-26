"""Обработчик событий canvas"""
import tkinter as tk


class CanvasHandler:
    """Обрабатывает события canvas: клики, движение мыши, зум, панорамирование."""
    
    def __init__(self, editor):
        """
        Args:
            editor: Экземпляр GridEditor
        """
        self.editor = editor
        self.dragging_line = False
        self.dragged_line_index = None
        self.dragged_line_type = None
    
    def canvas_to_image_coords(self, canvas_x, canvas_y):
        """Преобразует координаты canvas в координаты изображения"""
        if not hasattr(self.editor, 'scale'):
            return None, None
        
        img_x = int((canvas_x - self.editor.offset_x) / self.editor.scale)
        img_y = int((canvas_y - self.editor.offset_y) / self.editor.scale)
        
        # Проверяем, что координаты в пределах изображения
        if self.editor.image is not None:
            if 0 <= img_x < self.editor.image.width and 0 <= img_y < self.editor.image.height:
                return img_x, img_y
        
        return None, None
    
    def on_canvas_click(self, event):
        """Обрабатывает клик на canvas"""
        if self.editor.image is None:
            return

        # Режим лупы: зум по левому клику после выбора "Приблизить/Отдалить"
        zoom_click_mode = getattr(self.editor, 'zoom_click_mode', None)
        if zoom_click_mode in ('in', 'out'):
            zoom_in = (zoom_click_mode == 'in')
            # Временная инверсия направления зума при зажатом Alt
            if self._is_alt_pressed(event):
                zoom_in = not zoom_in
            self._zoom_at_canvas_point(event.x, event.y, zoom_in=zoom_in)
            return
        
        canvas_x, canvas_y = event.x, event.y
        img_x, img_y = self.canvas_to_image_coords(canvas_x, canvas_y)
        
        if img_x is None or img_y is None:
            return
        
        # Режим выделения области
        if self.editor.selection_mode:
            self.editor.handle_selection_click(img_x, img_y)
            return
        
        # Инструмент обрабатывает клик
        if self.editor.active_tool and self.editor.active_tool.on_mouse_down(img_x, img_y):
            return
        
        # Обычный режим выбора линий (только если не активны режимы закрашивания, пипетки или курсора)
        # Если активен инструмент курсор, он сам обрабатывает клики
        if self.editor.active_tool and hasattr(self.editor.active_tool, 'name') and self.editor.active_tool.name == 'cursor':
            return
        
        # Проверяем клик по вертикальным линиям (погрешность 5 пикселей)
        threshold = 5 / self.editor.scale if hasattr(self.editor, 'scale') else 5
        self.editor.selected_line = None
        self.editor.selected_line_type = None
        self.editor.grid_manager.selected_line = None
        self.editor.grid_manager.selected_line_type = None
        self.dragging_line = False
        self.dragged_line_index = None
        self.dragged_line_type = None
        
        # Проверяем, заблокирована ли сетка (не позволяем выбирать линии для перемещения)
        if hasattr(self.editor, 'grid_locked') and self.editor.grid_locked:
            # Если сетка заблокирована, не обрабатываем клики по линиям
            pass
        else:
            for i, x in enumerate(self.editor.vertical_lines):
                if abs(img_x - x) < threshold:
                    self.editor.selected_line = x
                    self.editor.selected_line_type = 'v'
                    self.editor.grid_manager.selected_line = x
                    self.editor.grid_manager.selected_line_type = 'v'
                    # Начинаем перетаскивание
                    self.dragging_line = True
                    self.dragged_line_index = i
                    self.dragged_line_type = 'v'
                    # Сохраняем состояние перед перемещением
                    if not self.editor.state_saved_for_action:
                        self.editor.save_state()
                        self.editor.state_saved_for_action = True
                    break
            
            # Если не выбрана вертикальная, проверяем горизонтальные
            if self.editor.selected_line is None:
                for i, y in enumerate(self.editor.horizontal_lines):
                    if abs(img_y - y) < threshold:
                        self.editor.selected_line = y
                        self.editor.selected_line_type = 'h'
                        self.editor.grid_manager.selected_line = y
                        self.editor.grid_manager.selected_line_type = 'h'
                        # Начинаем перетаскивание
                        self.dragging_line = True
                        self.dragged_line_index = i
                        self.dragged_line_type = 'h'
                        # Сохраняем состояние перед перемещением
                        if not self.editor.state_saved_for_action:
                            self.editor.save_state()
                            self.editor.state_saved_for_action = True
                        break
        
        self.editor.update_display()
        
        if self.editor.selected_line is not None:
            line_type = "вертикальная" if self.editor.selected_line_type == 'v' else "горизонтальная"
            self.editor.info_label.config(text=f"Выбрана {line_type} линия\n"
                                               f"Позиция: {self.editor.selected_line}\n"
                                               f"Перетащите для перемещения")

    def set_zoom_click_mode(self, zoom_in: bool):
        """Включает режим лупы: масштаб по клику ЛКМ на canvas."""
        self.editor.zoom_click_mode = 'in' if zoom_in else 'out'
        action_text = "Приблизить" if zoom_in else "Отдалить"
        if hasattr(self.editor, 'info_label'):
            self.editor.info_label.config(
                text=f"Режим: Лупа ({action_text})\nЛКМ - зум, Alt+ЛКМ - обратный зум"
            )
        # Ставим фокус на canvas, чтобы не терять горячие клавиши и управление мышью
        if hasattr(self.editor, 'canvas'):
            self.editor.canvas.focus_set()
    
    def on_canvas_configure(self, event):
        """Обрабатывает изменение размера canvas"""
        if self.editor.image is not None:
            self.editor.update_display()
    
    def on_canvas_motion(self, event):
        """Изменяет курсор при наведении на линию или рисует карандашом"""
        if self.editor.image is None:
            return
        
        canvas_x, canvas_y = event.x, event.y
        img_x, img_y = self.canvas_to_image_coords(canvas_x, canvas_y)
        
        if img_x is None or img_y is None:
            return
        
        # Если идет перетаскивание линии в обычном режиме (без активного инструмента)
        # Проверяем, заблокирована ли сетка
        if self.dragging_line and self.dragged_line_index is not None and self.dragged_line_type:
            if hasattr(self.editor, 'grid_locked') and self.editor.grid_locked:
                # Если сетка заблокирована, прекращаем перетаскивание
                self.dragging_line = False
                self.dragged_line_index = None
                self.dragged_line_type = None
                return
            if not self.editor.active_tool or self.editor.active_tool.name != 'cursor':
                if self.dragged_line_type == 'v':
                    # Перемещаем вертикальную линию
                    max_pos = self.editor.image.width
                    success, new_pos = self.editor.grid_manager.move_line_to_position(
                        self.dragged_line_index, 'v', img_x, max_pos, min_distance=1
                    )
                    if success:
                        self.editor.vertical_lines = self.editor.grid_manager.vertical_lines
                        self.editor.selected_line = new_pos
                        self.editor.grid_manager.selected_line = new_pos
                        # Обновляем индекс после сортировки
                        self.dragged_line_index = self.editor.vertical_lines.index(new_pos)
                        # Сбрасываем фрагментированное изображение и палитру при изменении сетки
                        self.editor.fragmented_image = None
                        self.editor.palette = None
                        self.editor.selected_color = None
                        for widget in self.editor.palette_frame.winfo_children():
                            widget.destroy()
                        self.editor.palette_canvas = None
                        self.editor.update_display()
                        self.editor.update_footer_info()
                        self.editor.info_label.config(
                            text=f"Вертикальная линия\nПозиция: {new_pos}\nСтолбец: {self.dragged_line_index}"
                        )
                else:  # 'h'
                    # Перемещаем горизонтальную линию
                    max_pos = self.editor.image.height
                    success, new_pos = self.editor.grid_manager.move_line_to_position(
                        self.dragged_line_index, 'h', img_y, max_pos, min_distance=1
                    )
                    if success:
                        self.editor.horizontal_lines = self.editor.grid_manager.horizontal_lines
                        self.editor.selected_line = new_pos
                        self.editor.grid_manager.selected_line = new_pos
                        # Обновляем индекс после сортировки
                        self.dragged_line_index = self.editor.horizontal_lines.index(new_pos)
                        # Сбрасываем фрагментированное изображение и палитру при изменении сетки
                        self.editor.fragmented_image = None
                        self.editor.palette = None
                        self.editor.selected_color = None
                        for widget in self.editor.palette_frame.winfo_children():
                            widget.destroy()
                        self.editor.palette_canvas = None
                        self.editor.update_display()
                        self.editor.update_footer_info()
                        self.editor.info_label.config(
                            text=f"Горизонтальная линия\nПозиция: {new_pos}\nСтрока: {self.dragged_line_index}"
                        )
                return
        
        # Инструмент обрабатывает движение
        if self.editor.active_tool and self.editor.active_tool.on_mouse_move(img_x, img_y):
            return
        
        threshold = 5 / self.editor.scale if hasattr(self.editor, 'scale') else 5
        
        # Проверяем наведение на вертикальные линии (только если не в режиме закрашивания, пипетки или выделения)
        # Если активен инструмент курсор, он сам обрабатывает наведение
        if (not self.editor.paint_mode and not self.editor.eyedropper_mode and not self.editor.selection_mode and
            (not self.editor.active_tool or not hasattr(self.editor.active_tool, 'name') or self.editor.active_tool.name != 'cursor')):
            for x in self.editor.vertical_lines:
                if abs(img_x - x) < threshold:
                    self.editor.canvas.config(cursor='sb_h_double_arrow')
                    return
        
        # Проверяем наведение на горизонтальные линии (только если не в режиме закрашивания, пипетки или выделения)
        # Если активен инструмент курсор, он сам обрабатывает наведение
        if (not self.editor.paint_mode and not self.editor.eyedropper_mode and not self.editor.selection_mode and
            (not self.editor.active_tool or not hasattr(self.editor.active_tool, 'name') or self.editor.active_tool.name != 'cursor')):
            for y in self.editor.horizontal_lines:
                if abs(img_y - y) < threshold:
                    self.editor.canvas.config(cursor='sb_v_double_arrow')
                    return
        
        # Обновляем курсор в зависимости от режима
        if self.editor.eyedropper_mode:
            self.editor.canvas.config(cursor='cross')
        elif self.editor.selection_mode:
            self.editor.canvas.config(cursor='tcross')
        elif self.editor.paint_mode:
            if self.editor.paint_tool == 'pencil':
                self.editor.canvas.config(cursor='dotbox')
            elif self.editor.paint_tool == 'eraser':
                self.editor.canvas.config(cursor='circle')  # Курсор резинки
            else:
                self.editor.canvas.config(cursor='spraycan')
        else:
            self.editor.canvas.config(cursor='crosshair')
    
    def on_canvas_release(self, event):
        """Обрабатывает отпускание кнопки мыши"""
        canvas_x, canvas_y = event.x, event.y
        img_x, img_y = self.canvas_to_image_coords(canvas_x, canvas_y)
        
        # Завершаем перетаскивание линии в обычном режиме
        if self.dragging_line:
            self.dragging_line = False
            self.dragged_line_index = None
            self.dragged_line_type = None
            # Сбрасываем флаг сохранения состояния после завершения действия
            if hasattr(self.editor, 'state_saved_for_action'):
                self.editor.state_saved_for_action = False
        
        if self.editor.active_tool:
            self.editor.active_tool.on_mouse_up(img_x, img_y)
    
    def on_mousewheel(self, event):
        """Обрабатывает прокрутку колеса мыши для зума"""
        if self.editor.image is None:
            return
        
        # Определяем направление прокрутки
        if event.num == 4 or event.delta > 0:  # Прокрутка вверх
            zoom_factor = 1.1
        elif event.num == 5 or event.delta < 0:  # Прокрутка вниз
            zoom_factor = 0.9
        else:
            return
        
        # Получаем позицию мыши на canvas
        canvas_x = self.editor.canvas.winfo_pointerx() - self.editor.canvas.winfo_rootx()
        canvas_y = self.editor.canvas.winfo_pointery() - self.editor.canvas.winfo_rooty()
        
        # Преобразуем в координаты изображения до зума
        img_x, img_y = self.canvas_to_image_coords(canvas_x, canvas_y)
        
        if img_x is None or img_y is None:
            return
        
        # Применяем зум
        old_zoom = self.editor.zoom
        self.editor.zoom *= zoom_factor
        self.editor.zoom = max(0.1, min(10.0, self.editor.zoom))  # Ограничиваем зум
        
        # Вычисляем новую позицию мыши после зума
        # Корректируем панорамирование, чтобы точка под курсором осталась на месте
        zoom_change = self.editor.zoom / old_zoom
        self.editor.pan_x = canvas_x - (canvas_x - self.editor.pan_x) * zoom_change
        self.editor.pan_y = canvas_y - (canvas_y - self.editor.pan_y) * zoom_change
        
        self.editor.update_display()
    
    def _zoom_at_canvas_point(self, canvas_x, canvas_y, zoom_in: bool):
        """Применяет зум в точке canvas, сохраняя точку под курсором."""
        img_x, img_y = self.canvas_to_image_coords(canvas_x, canvas_y)
        if img_x is None or img_y is None:
            return

        zoom_factor = 1.1 if zoom_in else 0.9
        old_zoom = self.editor.zoom
        self.editor.zoom *= zoom_factor
        self.editor.zoom = max(0.1, min(10.0, self.editor.zoom))

        zoom_change = self.editor.zoom / old_zoom
        self.editor.pan_x = canvas_x - (canvas_x - self.editor.pan_x) * zoom_change
        self.editor.pan_y = canvas_y - (canvas_y - self.editor.pan_y) * zoom_change
        self.editor.update_display()

    @staticmethod
    def _is_alt_pressed(event):
        """Определяет, зажат ли Alt/Mod1 в момент события."""
        return bool(getattr(event, 'state', 0) & 0x0008)

    def zoom_from_ui(self, zoom_in: bool):
        """Приближение/отдаление от центра холста (кнопка лупы). Логика как у колеса мыши."""
        if self.editor.image is None:
            return
        zoom_factor = 1.1 if zoom_in else 0.9
        canvas = self.editor.canvas
        canvas.update_idletasks()
        w = max(canvas.winfo_width(), 1)
        h = max(canvas.winfo_height(), 1)
        canvas_x = w / 2.0
        canvas_y = h / 2.0
        img_x, img_y = self.canvas_to_image_coords(canvas_x, canvas_y)
        if img_x is None or img_y is None:
            return
        old_zoom = self.editor.zoom
        self.editor.zoom *= zoom_factor
        self.editor.zoom = max(0.1, min(10.0, self.editor.zoom))
        zoom_change = self.editor.zoom / old_zoom
        self.editor.pan_x = canvas_x - (canvas_x - self.editor.pan_x) * zoom_change
        self.editor.pan_y = canvas_y - (canvas_y - self.editor.pan_y) * zoom_change
        self.editor.update_display()
    
    def on_pan_start(self, event):
        """Обрабатывает начало панорамирования (нажатие правой кнопки мыши)"""
        if self.editor.image is not None:
            # Сохраняем начальную позицию для определения, был ли клик или перетаскивание
            self.editor.pan_start_x = event.x
            self.editor.pan_start_y = event.y
            self.editor.pan_active = True
            self.editor.last_pan_x = event.x
            self.editor.last_pan_y = event.y
            
            # Проверяем, можно ли показать контекстное меню (только при клике без движения)
            canvas_x, canvas_y = event.x, event.y
            img_x, img_y = self.canvas_to_image_coords(canvas_x, canvas_y)
            
            if img_x is not None and img_y is not None:
                # Сохраняем координаты для возможного контекстного меню
                self.editor.right_click_pos = (img_x, img_y)
                self.editor.right_click_time = event.time
            
            self.editor.canvas.config(cursor='fleur')
    
    def on_pan_motion(self, event):
        """Обрабатывает движение мыши при зажатой правой кнопке для панорамирования"""
        if not self.editor.pan_active or self.editor.image is None:
            return
        
        # Вычисляем смещение
        dx = event.x - self.editor.last_pan_x
        dy = event.y - self.editor.last_pan_y
        
        # Применяем смещение
        self.editor.pan_x += dx
        self.editor.pan_y += dy
        
        # Обновляем последнюю позицию
        self.editor.last_pan_x = event.x
        self.editor.last_pan_y = event.y
        
        self.editor.update_display()
    
    def on_pan_release(self, event):
        """Обрабатывает отпускание правой кнопки мыши"""
        self.editor.pan_active = False
        if hasattr(self.editor, 'right_click_pos'):
            delattr(self.editor, 'right_click_pos')
        if hasattr(self.editor, 'pan_start_x'):
            delattr(self.editor, 'pan_start_x')
        if hasattr(self.editor, 'pan_start_y'):
            delattr(self.editor, 'pan_start_y')
        self.editor.canvas.config(cursor='crosshair')

