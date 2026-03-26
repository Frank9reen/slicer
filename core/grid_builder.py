"""Построение и сдвиг сетки"""
from tkinter import messagebox
from core.adaptive_grid import AdaptiveGrid


class GridBuilder:
    """Управляет построением и сдвигом сетки."""
    
    def __init__(self, editor):
        """
        Args:
            editor: Экземпляр GridEditor
        """
        self.editor = editor
        self.adaptive_grid = AdaptiveGrid()
    
    def build_grid(self):
        # Убираем фокус с полей ввода
        self.editor.canvas.focus_set()
        
        # Проверяем, заблокирована ли сетка
        if hasattr(self.editor, 'grid_locked') and self.editor.grid_locked:
            messagebox.showinfo("Информация", "Сетка заблокирована после получения палитры")
            return
        
        if self.editor.image is None:
            messagebox.showwarning("Предупреждение", "Сначала откройте изображение")
            return
        
        try:
            # Проверяем, включена ли ручная разметка (только рамка)
            manual_marking_enabled = (hasattr(self.editor, 'manual_marking_enabled') and 
                                     self.editor.manual_marking_enabled.get())
            
            # Проверяем, включена ли ручная настройка
            manual_enabled = (hasattr(self.editor, 'manual_grid_enabled') and 
                             self.editor.manual_grid_enabled.get())
            
            # Определяем, какие методы адаптивной сетки выбраны
            selected_methods = []
            
            if hasattr(self.editor, 'adaptive_method_gradients') and self.editor.adaptive_method_gradients.get():
                selected_methods.append('gradients')
            
            # Проверяем, что выбран хотя бы один метод
            if not manual_marking_enabled and not manual_enabled and not selected_methods:
                messagebox.showwarning("Предупреждение", "Выберите метод построения сетки:\n"
                                                         "- Разметка слева направо\n"
                                                         "- Ручная настройка\n"
                                                         "- или один из методов адаптивной сетки")
                return
            
            # Если включена разметка слева направо, строим рамку и начальные линии
            if manual_marking_enabled:
                # Строим рамку (границы изображения) и добавляем по одной линии по X и Y
                # Первая линия по X ставится на 1/4 от левого края
                first_x = self.editor.image.width // 4
                # Первая линия по Y ставится на 1/4 от верхнего края
                first_y = self.editor.image.height // 4
                
                vertical_lines = [0, first_x, self.editor.image.width - 1]
                horizontal_lines = [0, first_y, self.editor.image.height - 1]
                
                # Устанавливаем линии
                self.editor.grid_manager.vertical_lines = vertical_lines
                self.editor.grid_manager.horizontal_lines = horizontal_lines
                self.editor.vertical_lines = self.editor.grid_manager.vertical_lines
                self.editor.horizontal_lines = self.editor.grid_manager.horizontal_lines
            # Если включена ручная настройка, используем обычную сетку
            elif manual_enabled:
                # Используем обычную сетку
                num_vertical = int(self.editor.num_vertical.get())
                num_horizontal = int(self.editor.num_horizontal.get())
                step_vertical = int(self.editor.step_vertical.get())
                step_horizontal = int(self.editor.step_horizontal.get())
                
                self.editor.grid_manager.build_grid(
                    self.editor.image.width,
                    self.editor.image.height,
                    num_vertical,
                    num_horizontal,
                    step_vertical,
                    step_horizontal
                )
                
                # Синхронизируем линии
                self.editor.vertical_lines = self.editor.grid_manager.vertical_lines
                self.editor.horizontal_lines = self.editor.grid_manager.horizontal_lines
            # Если выбран хотя бы один адаптивный метод, используем адаптивную сетку
            elif selected_methods:
                # Используем адаптивную сетку
                try:
                    
                    self.editor.info_label.config(
                        text=f"Анализ изображения ({len(selected_methods)} метод(ов))..."
                    )
                    self.editor.root.update()
                    
                    # Собираем результаты от всех выбранных методов
                    all_vertical_lines = []
                    all_horizontal_lines = []
                    
                    for method in selected_methods:
                        try:
                            if method == 'gradients':
                                v_lines, h_lines = self.adaptive_grid.detect_by_gradients(
                                    self.editor.image, min_cell_size=3, max_cell_size=50
                                )
                            else:
                                continue
                            
                            all_vertical_lines.extend(v_lines)
                            all_horizontal_lines.extend(h_lines)
                        except Exception as e:
                            # Пропускаем методы, которые не сработали
                            print(f"Метод {method} не сработал: {str(e)}")
                            continue
                    
                    # Объединяем и фильтруем результаты
                    if all_vertical_lines and all_horizontal_lines:
                        # Удаляем дубликаты и сортируем
                        vertical_lines = sorted(list(set(all_vertical_lines)))
                        horizontal_lines = sorted(list(set(all_horizontal_lines)))
                        
                        # Фильтруем слишком близкие линии (минимум 3 пикселя между линиями)
                        vertical_lines = self._filter_close_lines(vertical_lines, min_distance=3)
                        horizontal_lines = self._filter_close_lines(horizontal_lines, min_distance=3)
                        
                        # Добавляем граничные линии, если их нет
                        if not vertical_lines or vertical_lines[0] > 0:
                            vertical_lines.insert(0, 0)
                        if not vertical_lines or vertical_lines[-1] < self.editor.image.width - 1:
                            vertical_lines.append(self.editor.image.width - 1)
                        
                        if not horizontal_lines or horizontal_lines[0] > 0:
                            horizontal_lines.insert(0, 0)
                        if not horizontal_lines or horizontal_lines[-1] < self.editor.image.height - 1:
                            horizontal_lines.append(self.editor.image.height - 1)
                        
                        # Устанавливаем линии
                        self.editor.grid_manager.vertical_lines = vertical_lines
                        self.editor.grid_manager.horizontal_lines = horizontal_lines
                        self.editor.vertical_lines = self.editor.grid_manager.vertical_lines
                        self.editor.horizontal_lines = self.editor.grid_manager.horizontal_lines
                    else:
                        raise Exception("Не удалось построить сетку ни одним из выбранных методов")
                        
                except ImportError as e:
                    messagebox.showerror("Ошибка", f"Для адаптивной сетки требуются библиотеки:\n"
                                                   f"opencv-python и scipy\n\n"
                                                   f"Установите их командой:\n"
                                                   f"pip install opencv-python scipy")
                    return
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось построить адаптивную сетку:\n{str(e)}")
                    return
            
            # Сбрасываем фрагментированное изображение и палитру при изменении сетки
            self.editor.fragmented_image = None
            self.editor.palette = None
            self.editor.selected_color = None
            for widget in self.editor.palette_frame.winfo_children():
                widget.destroy()
            self.editor.palette_canvas = None
            
            # Разблокируем сетку при построении новой сетки
            if hasattr(self.editor, 'grid_locked'):
                self.editor.grid_locked = False
                # Включаем кнопки управления сеткой обратно
                if hasattr(self.editor, 'grid_panel'):
                    self.editor.grid_panel.enable_grid_controls()
            
            # Обновляем отображение
            self.editor.update_display()
            self.editor.info_label.config(
                text=f"Сетка построена\nВертикальных линий: {len(self.editor.vertical_lines)}\n"
                     f"Горизонтальных линий: {len(self.editor.horizontal_lines)}"
            )
            # Обновляем информацию в футере
            self.editor.update_footer_info()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось построить сетку:\n{str(e)}")
    
    def shift_grid_left(self):
        """Сдвигает всю сетку влево"""
        # Проверяем, заблокирована ли сетка
        if hasattr(self.editor, 'grid_locked') and self.editor.grid_locked:
            messagebox.showinfo("Информация", "Сетка заблокирована после получения палитры")
            return
        
        if not self.editor.vertical_lines or self.editor.image is None:
            messagebox.showwarning("Предупреждение", "Сначала постройте сетку")
            return
        
        # Убираем фокус с полей ввода
        self.editor.canvas.focus_set()
        
        shift = self.editor.grid_shift_step.get()
        if self.editor.grid_manager.shift_grid_left(self.editor.image.width, shift):
            self.editor.vertical_lines = self.editor.grid_manager.vertical_lines
            self.editor.update_display()
            self.editor.update_footer_info()
        else:
            messagebox.showwarning("Предупреждение", "Нельзя сдвинуть сетку влево: линии выйдут за границы изображения")
    
    def shift_grid_right(self):
        """Сдвигает всю сетку вправо"""
        # Проверяем, заблокирована ли сетка
        if hasattr(self.editor, 'grid_locked') and self.editor.grid_locked:
            messagebox.showinfo("Информация", "Сетка заблокирована после получения палитры")
            return
        
        if not self.editor.vertical_lines or self.editor.image is None:
            messagebox.showwarning("Предупреждение", "Сначала постройте сетку")
            return
        
        # Убираем фокус с полей ввода
        self.editor.canvas.focus_set()
        
        shift = self.editor.grid_shift_step.get()
        if self.editor.grid_manager.shift_grid_right(self.editor.image.width, shift):
            self.editor.vertical_lines = self.editor.grid_manager.vertical_lines
            self.editor.update_display()
            self.editor.update_footer_info()
        else:
            messagebox.showwarning("Предупреждение", "Нельзя сдвинуть сетку вправо: линии выйдут за границы изображения")
    
    def shift_grid_up(self):
        """Сдвигает всю сетку вверх"""
        # Проверяем, заблокирована ли сетка
        if hasattr(self.editor, 'grid_locked') and self.editor.grid_locked:
            messagebox.showinfo("Информация", "Сетка заблокирована после получения палитры")
            return
        
        if not self.editor.horizontal_lines or self.editor.image is None:
            messagebox.showwarning("Предупреждение", "Сначала постройте сетку")
            return
        
        # Убираем фокус с полей ввода
        self.editor.canvas.focus_set()
        
        shift = self.editor.grid_shift_step.get()
        if self.editor.grid_manager.shift_grid_up(self.editor.image.height, shift):
            self.editor.horizontal_lines = self.editor.grid_manager.horizontal_lines
            self.editor.update_display()
            self.editor.update_footer_info()
        else:
            messagebox.showwarning("Предупреждение", "Нельзя сдвинуть сетку вверх: линии выйдут за границы изображения")
    
    def shift_grid_down(self):
        """Сдвигает всю сетку вниз"""
        # Проверяем, заблокирована ли сетка
        if hasattr(self.editor, 'grid_locked') and self.editor.grid_locked:
            messagebox.showinfo("Информация", "Сетка заблокирована после получения палитры")
            return
        
        if not self.editor.horizontal_lines or self.editor.image is None:
            messagebox.showwarning("Предупреждение", "Сначала постройте сетку")
            return
        
        # Убираем фокус с полей ввода
        self.editor.canvas.focus_set()
        
        shift = self.editor.grid_shift_step.get()
        if self.editor.grid_manager.shift_grid_down(self.editor.image.height, shift):
            self.editor.horizontal_lines = self.editor.grid_manager.horizontal_lines
            self.editor.update_display()
            self.editor.update_footer_info()
        else:
            messagebox.showwarning("Предупреждение", "Нельзя сдвинуть сетку вниз: линии выйдут за границы изображения")
    
    def _filter_close_lines(self, lines, min_distance=3):
        """
        Фильтрует слишком близкие линии, оставляя только одну из группы близких линий.
        
        Args:
            lines: Список позиций линий
            min_distance: Минимальное расстояние между линиями
        
        Returns:
            list: Отфильтрованный список линий
        """
        if not lines:
            return []
        
        lines = sorted(lines)
        filtered = [lines[0]]
        
        for line in lines[1:]:
            if line - filtered[-1] >= min_distance:
                filtered.append(line)
        
        return filtered

