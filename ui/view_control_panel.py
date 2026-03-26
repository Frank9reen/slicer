"""Панель управления просмотром"""
import tkinter as tk


class ViewControlPanel:
    """Инкапсулирует элементы управления просмотром (сетка, кадрирование, режимы просмотра)."""
    
    def __init__(self, editor, parent_frame):
        """
        Args:
            editor: Экземпляр GridEditor
            parent_frame: Родительский фрейм для размещения панели
        """
        self.editor = editor
        
        # Создаем основной фрейм
        self.frame = tk.Frame(parent_frame)
        self.frame.pack(fill=tk.X, padx=5, pady=(0, 2))
        
        # Кнопки управления изображением (открытие и сохранение)
        # Иконка папки для открытия изображения
        folder_button = tk.Button(self.frame, text="📁", command=self.editor.open_image,
                                 font=('Arial', 16), bg='lightgray', width=3, height=1,
                                 relief=tk.RAISED, bd=2, cursor='hand2',
                                 padx=0, pady=0, anchor='center')
        folder_button.pack(side=tk.LEFT, padx=2)
        self.editor.create_tooltip(folder_button, "Открыть изображение")
        
        # Иконка сохранения изображения (с сеткой)
        save_button = tk.Button(self.frame, text="💾", command=self.editor.save_image,
                               font=('Arial', 16), bg='lightgray', width=3, height=1,
                               relief=tk.RAISED, bd=2, cursor='hand2',
                               padx=0, pady=0, anchor='center')
        save_button.pack(side=tk.LEFT, padx=2)
        self.editor.create_tooltip(save_button, "Сохранить изображение с сеткой")
        
        # Иконка сохранения изображения без сетки
        save_no_grid_button = tk.Button(self.frame, text="📷", command=self.editor.save_image_without_grid,
                                       font=('Arial', 16), bg='lightgray', width=3, height=1,
                                       relief=tk.RAISED, bd=2, cursor='hand2',
                                       padx=0, pady=0, anchor='center')
        save_no_grid_button.pack(side=tk.LEFT, padx=2)
        self.editor.create_tooltip(save_no_grid_button, "Сохранить изображение без сетки")
        
        # Вертикальная черта перед кнопками отмены/возврата
        separator_before_undo = tk.Frame(self.frame, width=2, bg='gray', relief=tk.SUNKEN)
        separator_before_undo.pack(side=tk.LEFT, padx=5, pady=3, fill=tk.Y)
        
        # Кнопка отмены (назад)
        self.editor.undo_button = tk.Button(self.frame, text="↶", command=self.editor.undo_last_action,
                                           font=('Arial', 16), bg='lightgray', width=3, height=1,
                                           relief=tk.RAISED, bd=2, cursor='hand2',
                                           padx=0, pady=0, anchor='center')
        self.editor.undo_button.pack(side=tk.LEFT, padx=2)
        self.editor.create_tooltip(self.editor.undo_button, "Отмена (Ctrl+Z)")
        
        # Кнопка возврата (вперед)
        self.editor.redo_button = tk.Button(self.frame, text="↷", command=self.editor.redo_last_action,
                                           font=('Arial', 16), bg='lightgray', width=3, height=1,
                                           relief=tk.RAISED, bd=2, cursor='hand2',
                                           padx=0, pady=0, anchor='center')
        self.editor.redo_button.pack(side=tk.LEFT, padx=2)
        self.editor.create_tooltip(self.editor.redo_button, "Возврат (Ctrl+Y)")
        
        # Вертикальная черта для разграничения групп кнопок
        # separator_before_shift = tk.Frame(self.frame, width=2, bg='gray', relief=tk.SUNKEN)
        # separator_before_shift.pack(side=tk.LEFT, padx=5, pady=3, fill=tk.Y)
        
        # Кнопки сдвига сетки (закомментировано)
        # Инициализируем переменную для шага сдвига, если её нет
        if not hasattr(self.editor, 'grid_shift_step'):
            self.editor.grid_shift_step = tk.IntVar(value=1)
        
        # Фрейм для кнопок сдвига
        # shift_frame = tk.Frame(self.frame)
        # shift_frame.pack(side=tk.LEFT, padx=2)
        
        # Кнопка сдвига влево
        # shift_left_button = tk.Button(
        #     shift_frame,
        #     text="←",
        #     command=self.editor.shift_grid_left,
        #     font=('Arial', 14),
        #     bg='lightblue',
        #     width=2,
        #     height=1,
        #     relief=tk.RAISED,
        #     bd=2,
        #     cursor='hand2',
        #     padx=0,
        #     pady=0,
        #     anchor='center',
        # )
        # shift_left_button.pack(side=tk.LEFT, padx=1)
        # self.editor.create_tooltip(shift_left_button, "Сдвинуть сетку влево")
        
        # Кнопка сдвига вправо
        # shift_right_button = tk.Button(
        #     shift_frame,
        #     text="→",
        #     command=self.editor.shift_grid_right,
        #     font=('Arial', 14),
        #     bg='lightblue',
        #     width=2,
        #     height=1,
        #     relief=tk.RAISED,
        #     bd=2,
        #     cursor='hand2',
        #     padx=0,
        #     pady=0,
        #     anchor='center',
        # )
        # shift_right_button.pack(side=tk.LEFT, padx=1)
        # self.editor.create_tooltip(shift_right_button, "Сдвинуть сетку вправо")
        
        # Кнопка сдвига вверх
        # shift_up_button = tk.Button(
        #     shift_frame,
        #     text="↑",
        #     command=self.editor.shift_grid_up,
        #     font=('Arial', 14),
        #     bg='lightblue',
        #     width=2,
        #     height=1,
        #     relief=tk.RAISED,
        #     bd=2,
        #     cursor='hand2',
        #     padx=0,
        #     pady=0,
        #     anchor='center',
        # )
        # shift_up_button.pack(side=tk.LEFT, padx=1)
        # self.editor.create_tooltip(shift_up_button, "Сдвинуть сетку вверх")
        
        # Кнопка сдвига вниз
        # shift_down_button = tk.Button(
        #     shift_frame,
        #     text="↓",
        #     command=self.editor.shift_grid_down,
        #     font=('Arial', 14),
        #     bg='lightblue',
        #     width=2,
        #     height=1,
        #     relief=tk.RAISED,
        #     bd=2,
        #     cursor='hand2',
        #     padx=0,
        #     pady=0,
        #     anchor='center',
        # )
        # shift_down_button.pack(side=tk.LEFT, padx=1)
        # self.editor.create_tooltip(shift_down_button, "Сдвинуть сетку вниз")
        
        # Вертикальная черта для разграничения групп кнопок
        separator_before_tools = tk.Frame(self.frame, width=2, bg='gray', relief=tk.SUNKEN)
        separator_before_tools.pack(side=tk.LEFT, padx=5, pady=3, fill=tk.Y)
        
        # Блок выделения: Выделение области, Залить выделенную область, Очистить выделенную область
        if not hasattr(self.editor, 'selection_mode_var'):
            self.editor.selection_mode_var = tk.BooleanVar(value=False)
        self.editor.selection_button = tk.Button(
            self.frame,
            text="📐",
            command=self._toggle_selection_button,
            font=('Arial', 16),
            bg='lightgray',
            width=3,
            height=1,
            relief=tk.RAISED,
            bd=2,
            cursor='hand2',
            padx=0,
            pady=0,
            anchor='center',
        )
        self.editor.selection_button.pack(side=tk.LEFT, padx=2)
        self.editor.create_tooltip(self.editor.selection_button, "Выделение области")
        
        fill_selection_button = tk.Button(
            self.frame,
            text="🎨",
            command=self.editor.fill_selected_area,
            font=('Arial', 16),
            bg='lightgray',
            width=3,
            height=1,
            relief=tk.RAISED,
            bd=2,
            cursor='hand2',
            padx=0,
            pady=0,
            anchor='center',
        )
        fill_selection_button.pack(side=tk.LEFT, padx=2)
        self.editor.create_tooltip(fill_selection_button, "Залить выделенную область")
        
        clear_selection_button = tk.Button(
            self.frame,
            text="❌",
            command=self.editor.clear_selected_area,
            font=('Arial', 16),
            bg='lightgray',
            width=3,
            height=1,
            relief=tk.RAISED,
            bd=2,
            cursor='hand2',
            padx=0,
            pady=0,
            anchor='center',
            overrelief=tk.RAISED,
        )
        clear_selection_button.pack(side=tk.LEFT, padx=2)
        self.editor.create_tooltip(clear_selection_button, "Очистить выделенную область")
        
        separator_after_selection = tk.Frame(self.frame, width=2, bg='gray', relief=tk.SUNKEN)
        separator_after_selection.pack(side=tk.LEFT, padx=5, pady=3, fill=tk.Y)
        
        # Кнопки инструментов (курсор, карандаш, ластик, пипетка)
        self.editor.cursor_button = tk.Button(
            self.frame,
            text="➕",
            command=lambda: self.editor.activate_tool('cursor'),
            font=('Arial', 16),
            bg='lightgray',
            width=3,
            height=1,
            relief=tk.RAISED,
            bd=2,
            cursor='hand2',
            padx=0,
            pady=0,
            anchor='center',
        )
        self.editor.cursor_button.pack(side=tk.LEFT, padx=2)
        self.editor.create_tooltip(self.editor.cursor_button, "Выделение строк и столбцов сетки")
        
        self.editor.ruler_button = tk.Button(
            self.frame,
            text="📏",
            command=lambda: self.editor.activate_tool('ruler'),
            font=('Arial', 16),
            bg='lightgray',
            width=3,
            height=1,
            relief=tk.RAISED,
            bd=2,
            cursor='hand2',
            padx=0,
            pady=0,
            anchor='center',
        )
        self.editor.ruler_button.pack(side=tk.LEFT, padx=2)
        self.editor.create_tooltip(self.editor.ruler_button, "Линейка")
        
        # Лупа: меню приблизить / отдалить (дополнительно к колесу мыши)
        self.editor.zoom_view_button = tk.Button(
            self.frame,
            text="🔍",
            command=lambda: self.editor.show_zoom_menu(),
            font=('Arial', 16),
            bg='lightgray',
            width=3,
            height=1,
            relief=tk.RAISED,
            bd=2,
            cursor='hand2',
            padx=0,
            pady=0,
            anchor='center',
        )
        self.editor.zoom_view_button.pack(side=tk.LEFT, padx=2)
        self.editor.create_tooltip(
            self.editor.zoom_view_button,
            "Масштаб изображения: приблизить или отдалить (также колёсико мыши на холсте)",
        )
        
        # Вертикальный сепаратор после кнопки выделения
        separator_after_cursor = tk.Frame(self.frame, width=2, bg='gray', relief=tk.SUNKEN)
        separator_after_cursor.pack(side=tk.LEFT, padx=5, pady=3, fill=tk.Y)
        
        self.editor.pencil_button = tk.Button(
            self.frame,
            text="✏️",
            command=lambda: self.editor.show_pencil_size_menu(),
            font=('Arial', 16),
            bg='lightgray',
            width=3,
            height=1,
            relief=tk.RAISED,
            bd=2,
            cursor='hand2',
            padx=0,
            pady=0,
            anchor='center',
            overrelief=tk.RAISED,
        )
        self.editor.pencil_button.pack(side=tk.LEFT, padx=2)
        self.editor.create_tooltip(self.editor.pencil_button, "Карандаш (x1) (B) - клик для выбора размера")
        
        self.editor.eraser_button = tk.Button(
            self.frame,
            text="🧹",
            command=lambda: self.editor.show_eraser_size_menu(),
            font=('Arial', 16),
            bg='lightgray',
            width=3,
            height=1,
            relief=tk.RAISED,
            bd=2,
            cursor='hand2',
            padx=0,
            pady=0,
            anchor='center',
        )
        self.editor.eraser_button.pack(side=tk.LEFT, padx=2)
        self.editor.create_tooltip(self.editor.eraser_button, "Резинка (x1) (E) - клик для выбора размера")
        
        self.editor.eyedropper_button = tk.Button(
            self.frame,
            text="🧪",
            command=lambda: self.editor.activate_tool('eyedropper'),
            font=('Arial', 16),
            bg='lightgray',
            width=3,
            height=1,
            relief=tk.RAISED,
            bd=2,
            cursor='hand2',
            padx=0,
            pady=0,
            anchor='center',
        )
        self.editor.eyedropper_button.pack(side=tk.LEFT, padx=2)
        self.editor.create_tooltip(self.editor.eyedropper_button, "Пипетка (I)")
        
        self.editor.line_paint_button = tk.Button(
            self.frame,
            text="📏",
            command=lambda: self.editor.activate_tool('line_paint'),
            font=('Arial', 16),
            bg='lightgray',
            width=3,
            height=1,
            relief=tk.RAISED,
            bd=2,
            cursor='hand2',
            padx=0,
            pady=0,
            anchor='center',
        )
        self.editor.line_paint_button.pack(side=tk.LEFT, padx=2)
        self.editor.create_tooltip(self.editor.line_paint_button, "Закрашивание по линии")
        
        # Вертикальная черта для разграничения групп кнопок (после инструментов)
        separator = tk.Frame(self.frame, width=2, bg='gray', relief=tk.SUNKEN)
        separator.pack(side=tk.LEFT, padx=5, pady=3, fill=tk.Y)
        
        # Кнопка удаления одиночных пикселей со всего изображения (удалена с панели, перенесена в меню Палитра)
        # remove_all_button = tk.Button(
        #     self.frame,
        #     text="🎯",
        #     command=self.editor.remove_single_pixels_all,
        #     font=('Arial', 16),
        #     bg='lightgray',
        #     width=3,
        #     height=1,
        #     relief=tk.RAISED,
        #     bd=2,
        #     cursor='hand2',
        #     padx=0,
        #     pady=0,
        #     anchor='center',
        # )
        # remove_all_button.pack(side=tk.LEFT, padx=2)
        # self.editor.create_tooltip(remove_all_button, "Удалить одиночные пиксели со всего изображения")
        
        # Создаем или обновляем словарь кнопок инструментов
        if not hasattr(self.editor, 'tool_buttons'):
            self.editor.tool_buttons = {}
        self.editor.tool_buttons['cursor'] = self.editor.cursor_button
        self.editor.tool_buttons['pencil'] = self.editor.pencil_button
        self.editor.tool_buttons['eraser'] = self.editor.eraser_button
        self.editor.tool_buttons['eyedropper'] = self.editor.eyedropper_button
        self.editor.tool_buttons['ruler'] = self.editor.ruler_button
        self.editor.tool_buttons['line_paint'] = self.editor.line_paint_button
        
        # Блок прозрачности изображения (слева от режимов просмотра)
        opacity_frame = tk.Frame(self.frame)
        opacity_frame.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Инициализируем переменную для прозрачности, если её нет
        if not hasattr(self.editor, 'image_opacity'):
            self.editor.image_opacity = 1.0
        
        # Слайдер прозрачности
        self.editor.opacity_var = tk.DoubleVar(value=self.editor.image_opacity * 100)  # В процентах для слайдера
        opacity_slider = tk.Scale(opacity_frame, from_=0, to=100, 
                                 variable=self.editor.opacity_var,
                                 orient=tk.HORIZONTAL, length=120,
                                 command=self.on_opacity_changed)
        opacity_slider.pack(side=tk.LEFT)
        
        # Метка с текущим значением
        initial_opacity_percent = int(self.editor.image_opacity * 100)
        self.opacity_label = tk.Label(opacity_frame, text=f"{initial_opacity_percent}%", font=('Arial', 8), width=4)
        self.opacity_label.pack(side=tk.LEFT, padx=(5, 0))
        
        self.editor.create_tooltip(opacity_slider, "Изменение прозрачности первой загруженной картинки")
        
        # Кнопка выбора цвета подложки рядом с кнопкой сетки (#)
        self.editor.background_color_button = tk.Button(
            self.frame,
            text="",
            command=self.editor.choose_background_color,
            font=('Arial', 16),
            bg=self.editor.background_color,
            width=3,
            height=1,
            relief=tk.RAISED,
            bd=2,
            cursor='hand2',
            padx=0,
            pady=0,
            anchor='center'
        )
        self.editor.background_color_button.pack(side=tk.RIGHT, padx=(2, 2))
        self.editor.create_tooltip(self.editor.background_color_button, "Цвет задней подложки")
        self.editor.update_background_color_button()

        # Кнопка переключения сетки перед режимами просмотра
        self.editor.grid_toggle_button = tk.Button(self.frame, text="#", command=self.editor.toggle_grid_with_button,
                                                 font=('Arial', 16), bg='lightgreen', width=3, height=1,
                                                 relief=tk.SUNKEN, bd=2, cursor='hand2', padx=0, pady=0,
                                                 anchor='center')
        self.editor.grid_toggle_button.pack(side=tk.RIGHT, padx=(10, 2))
        self.editor.create_tooltip(self.editor.grid_toggle_button, "Показать/скрыть сетку")
        self.editor.update_grid_button_appearance()
        
        # Режимы просмотра справа
        view_label_frame = tk.Frame(self.frame)
        view_label_frame.pack(side=tk.RIGHT)
        
        view_buttons_frame = tk.Frame(view_label_frame)
        view_buttons_frame.pack(side=tk.LEFT)
        
        self.editor.view_mode_buttons = []
        self.editor.view_mode_button_1 = tk.Button(view_buttons_frame, text="1", command=lambda: self.editor.set_view_mode(1),
                                                   font=('Arial', 16, 'bold'), width=3, height=1, bg='lightblue', 
                                                   relief=tk.SUNKEN, bd=2, cursor='hand2', padx=0, pady=0,
                                                   anchor='center')
        self.editor.view_mode_button_1.pack(side=tk.LEFT, padx=1)
        self.editor.view_mode_buttons.append(self.editor.view_mode_button_1)
        self.editor.create_tooltip(self.editor.view_mode_button_1, "Исходное изображение")
        
        self.editor.view_mode_button_2 = tk.Button(view_buttons_frame, text="2", command=lambda: self.editor.set_view_mode(2),
                                                   font=('Arial', 16, 'bold'), width=3, height=1, bg='lightgray', 
                                                   relief=tk.RAISED, bd=2, cursor='hand2', padx=0, pady=0,
                                                   anchor='center')
        self.editor.view_mode_button_2.pack(side=tk.LEFT, padx=1)
        self.editor.view_mode_buttons.append(self.editor.view_mode_button_2)
        self.editor.create_tooltip(self.editor.view_mode_button_2, "Закрашенное и исходное изображение")
        
        self.editor.view_mode_button_3 = tk.Button(view_buttons_frame, text="3", command=lambda: self.editor.set_view_mode(3),
                                                   font=('Arial', 16, 'bold'), width=3, height=1, bg='lightgray', 
                                                   relief=tk.RAISED, bd=2, cursor='hand2', padx=0, pady=0,
                                                   anchor='center')
        self.editor.view_mode_button_3.pack(side=tk.LEFT, padx=1)
        self.editor.view_mode_buttons.append(self.editor.view_mode_button_3)
        self.editor.create_tooltip(self.editor.view_mode_button_3, "Режим просмотра: Только закрашенные ячейки")
        
        self.editor.view_mode_button_4 = tk.Button(view_buttons_frame, text="D", command=lambda: self.editor.set_view_mode(4),
                                                   font=('Arial', 16, 'bold'), width=3, height=1, bg='lightgray', 
                                                   relief=tk.RAISED, bd=2, cursor='hand2', padx=0, pady=0,
                                                   anchor='center')
        self.editor.view_mode_button_4.pack(side=tk.LEFT, padx=1)
        self.editor.view_mode_buttons.append(self.editor.view_mode_button_4)
        self.editor.create_tooltip(self.editor.view_mode_button_4, "Фрагментированно и исходное изображение")
    
    def on_opacity_changed(self, value):
        """Обработчик изменения прозрачности"""
        opacity_percent = float(value)
        self.editor.image_opacity = opacity_percent / 100.0  # Преобразуем в диапазон 0.0-1.0
        self.opacity_label.config(text=f"{int(opacity_percent)}%")
        # Обновляем отображение
        if self.editor.image is not None:
            self.editor.update_display()
    
    def _toggle_selection_button(self):
        """Переключает режим выделения области через кнопку"""
        # Убираем фокус с полей ввода
        self.editor.canvas.focus_set()
        
        # Переключаем состояние
        current_state = self.editor.selection_mode_var.get()
        self.editor.selection_mode_var.set(not current_state)
        
        # Вызываем переключение режима
        self.editor.toggle_selection_mode()
    
    def update_selection_button_appearance(self):
        """Обновляет внешний вид кнопки выделения области"""
        if hasattr(self.editor, 'selection_button'):
            if self.editor.selection_mode_var.get():
                self.editor.selection_button.config(bg='lightblue', relief=tk.SUNKEN)
            else:
                self.editor.selection_button.config(bg='lightgray', relief=tk.RAISED)

