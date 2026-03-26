"""Панель настроек сетки"""
import tkinter as tk
from tkinter import messagebox

_GRID_HELP_TEXT = (
    "Блок «Настройки сетки» — задание сетки линий (клеток) на изображении.\n\n"
    "• Метод построения (выберите один подходящий):\n"
    "  — «Анализ градиентов» — автоматический поиск линий по границам и контрасту.\n"
    "  — «Разметка слева направо» — пошаговая разметка по изображению.\n"
    "  — «Ручная настройка» — задайте число линий по X/Y и шаг в пикселях.\n\n"
    "• Кнопки «−» и «+» удаляют или добавляют линию в выбранном направлении "
    "(пока сетка не заблокирована после получения палитры).\n\n"
    "• «Построить сетку» — строит сетку по выбранному методу.\n\n"
    "После «Получить палитру» сетка обычно блокируется; для правок используйте "
    "«Разблокировать» (если доступно).\n\n"
    "Удобный порядок: загрузить картинку → настроить и построить сетку → "
    "затем фрагментация и палитра."
)


class GridPanel:
    """Инкапсулирует элементы управления настройками сетки."""
    
    def __init__(self, editor, parent_frame):
        """
        Args:
            editor: Экземпляр GridEditor
            parent_frame: Родительский фрейм для размещения панели
        """
        self.editor = editor
        
        # Внешний блок с рамкой, заголовок и ссылка (?)
        self.frame = tk.Frame(parent_frame, relief=tk.GROOVE, borderwidth=2)
        self.frame.pack(fill=tk.X, padx=5, pady=5)
        header_row = tk.Frame(self.frame)
        tk.Label(header_row, text="Настройки сетки", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 0))
        _help_font = ('Arial', 8)
        _help_font_u = ('Arial', 8, 'underline')
        help_link = tk.Label(
            header_row,
            text="(?)",
            fg='blue',
            cursor='hand2',
            font=_help_font,
        )
        help_link.pack(side=tk.LEFT, padx=(1, 0))
        help_link.bind('<Button-1>', lambda e: self._show_grid_help())
        help_link.bind('<Enter>', lambda e: help_link.config(font=_help_font_u))
        help_link.bind('<Leave>', lambda e: help_link.config(font=_help_font))
        header_row.pack(fill=tk.X, padx=5, pady=(8, 4))

        self.inner = tk.Frame(self.frame)
        self.inner.pack(fill=tk.X, padx=5, pady=(0, 8))
        
        # Метка (скрывается при построенной сетке, показывается при разблокировке)
        self.methods_label = tk.Label(
            self.inner,
            text="Выберите метод построения сетки:",
            font=('Arial', 8),
            anchor='w'
        )
        self.methods_label.pack(fill=tk.X, padx=5, pady=(5, 5))
        
        # Фрейм для чекбоксов методов (Анализ градиентов, Разметка слева направо, Ручная настройка)
        self.methods_frame = tk.Frame(self.inner)
        self.methods_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # Инициализируем переменные для полей ввода (даже если чекбокс выключен)
        if not hasattr(self.editor, 'num_vertical'):
            self.editor.num_vertical = tk.IntVar(value=150)
        if not hasattr(self.editor, 'num_horizontal'):
            self.editor.num_horizontal = tk.IntVar(value=150)
        if not hasattr(self.editor, 'step_vertical'):
            self.editor.step_vertical = tk.IntVar(value=7)
        if not hasattr(self.editor, 'step_horizontal'):
            self.editor.step_horizontal = tk.IntVar(value=7)
        
        # Чекбокс 1: Анализ градиентов
        self.editor.adaptive_method_gradients = tk.BooleanVar(value=False)
        tk.Checkbutton(
            self.methods_frame,
            text="Анализ градиентов",
            variable=self.editor.adaptive_method_gradients,
            font=('Arial', 9),
            anchor='w',
            command=self._on_gradients_changed
        ).pack(fill=tk.X, pady=0)
        
        # Чекбокс: Разметка слева направо
        self.editor.manual_marking_enabled = tk.BooleanVar(value=False)
        tk.Checkbutton(
            self.methods_frame,
            text="Разметка слева направо",
            variable=self.editor.manual_marking_enabled,
            font=('Arial', 9),
            anchor='w',
            command=self._on_marking_changed
        ).pack(fill=tk.X, pady=0)
        
        # Чекбокс 2: Ручная настройка (в конце)
        self.editor.manual_grid_enabled = tk.BooleanVar(value=False)
        manual_checkbox = tk.Checkbutton(
            self.methods_frame,
            text="Ручная настройка",
            variable=self.editor.manual_grid_enabled,
            font=('Arial', 9),
            anchor='w',
            command=self._on_manual_grid_changed
        )
        manual_checkbox.pack(fill=tk.X, pady=0)
        
        # Фрейм для полей ручной настройки (скрыт по умолчанию)
        # Размещаем его сразу после чекбокса "Ручная настройка" внутри methods_frame
        self.manual_settings_frame = tk.Frame(self.methods_frame)
        
        def _create_manual_settings():
            # Первая строка: количество вертикальных и горизонтальных линий
            row1_frame = tk.Frame(self.manual_settings_frame)
            row1_frame.pack(fill=tk.X, padx=(5, 5), pady=2)
            
            # Количество вертикальных линий
            vertical_label_frame = tk.Frame(row1_frame)
            vertical_label_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
            tk.Label(vertical_label_frame, text="Линий X:", font=('Arial', 8)).pack(anchor=tk.W)
            num_vertical_spinbox = tk.Spinbox(vertical_label_frame, from_=1, to=500, 
                                              textvariable=self.editor.num_vertical,
                                              width=10, command=self.editor.on_grid_params_changed,
                                              font=('Arial', 8))
            num_vertical_spinbox.pack(anchor=tk.W, pady=2)
            self.editor.num_vertical.trace('w', lambda *args: self.editor.on_grid_params_changed())
            
            # Количество горизонтальных линий
            horizontal_label_frame = tk.Frame(row1_frame)
            horizontal_label_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
            tk.Label(horizontal_label_frame, text="Линий Y:", font=('Arial', 8)).pack(anchor=tk.W)
            num_horizontal_spinbox = tk.Spinbox(horizontal_label_frame, from_=1, to=500, 
                                                textvariable=self.editor.num_horizontal,
                                                width=10, command=self.editor.on_grid_params_changed,
                                                font=('Arial', 8))
            num_horizontal_spinbox.pack(anchor=tk.W, pady=2)
            self.editor.num_horizontal.trace('w', lambda *args: self.editor.on_grid_params_changed())
            
            # Вторая строка: шаги для вертикальных и горизонтальных линий
            row2_frame = tk.Frame(self.manual_settings_frame)
            row2_frame.pack(fill=tk.X, padx=(5, 5), pady=2)
            
            # Шаг для вертикальных линий
            step_vertical_frame = tk.Frame(row2_frame)
            step_vertical_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
            tk.Label(step_vertical_frame, text="Шаг (px) X:", font=('Arial', 8)).pack(anchor=tk.W)
            step_vertical_spinbox = tk.Spinbox(step_vertical_frame, from_=1, to=1000, 
                                               textvariable=self.editor.step_vertical,
                                               width=10, command=self.editor.on_grid_params_changed,
                                               font=('Arial', 8))
            step_vertical_spinbox.pack(anchor=tk.W, pady=2)
            self.editor.step_vertical.trace('w', lambda *args: self.editor.on_grid_params_changed())
            
            # Шаг для горизонтальных линий
            step_horizontal_frame = tk.Frame(row2_frame)
            step_horizontal_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
            tk.Label(step_horizontal_frame, text="Шаг (px) Y:", font=('Arial', 8)).pack(anchor=tk.W)
            step_horizontal_spinbox = tk.Spinbox(step_horizontal_frame, from_=1, to=1000, 
                                                 textvariable=self.editor.step_horizontal,
                                                 width=10, command=self.editor.on_grid_params_changed,
                                                 font=('Arial', 8))
            step_horizontal_spinbox.pack(anchor=tk.W, pady=2)
            self.editor.step_horizontal.trace('w', lambda *args: self.editor.on_grid_params_changed())
        
        _create_manual_settings()
        
        # Фрейм для кнопок управления линиями сетки (нужен для восстановления порядка при разблокировке)
        self.lines_control_frame = tk.Frame(self.inner)
        self.lines_control_frame.pack(padx=5, pady=(5, 5))
        
        # Метка для кнопок управления линиями
        tk.Label(
            self.lines_control_frame,
            text="Управление линиями:",
            font=('Arial', 8),
            anchor='w'
        ).pack(fill=tk.X, pady=(0, 3))
        
        # Фрейм для кнопок - и +
        buttons_frame = tk.Frame(self.lines_control_frame)
        buttons_frame.pack(fill=tk.X)
        
        # Кнопка удаления линии (-)
        self.remove_line_btn = tk.Button(
            buttons_frame,
            text="−",
            command=lambda: self.editor.remove_line(None),
            font=('Arial', 9, 'bold'),
            bg='#808080',
            fg='white',
            activebackground='#6B6B6B',
            activeforeground='white',
            relief=tk.FLAT,
            bd=0,
            cursor='hand2',
            width=2,
            padx=1,
            pady=1
        )
        self.remove_line_btn.pack(side=tk.LEFT, padx=(0, 2), expand=True, fill=tk.X)
        
        # Кнопка добавления линии (+)
        self.add_line_btn = tk.Button(
            buttons_frame,
            text="+",
            command=lambda: self.editor.add_line(None),
            font=('Arial', 9, 'bold'),
            bg='#808080',
            fg='white',
            activebackground='#6B6B6B',
            activeforeground='white',
            relief=tk.FLAT,
            bd=0,
            cursor='hand2',
            width=2,
            padx=1,
            pady=1
        )
        self.add_line_btn.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        # Кнопка построения сетки
        self.build_grid_btn = tk.Button(
            self.inner, 
            text="Построить сетку", 
            command=self.editor.build_grid,
            font=('Arial', 10, 'bold'), 
            bg='#FF6B35', 
            fg='white', 
            activebackground='#E55A2B', 
            activeforeground='white',
            relief=tk.FLAT, 
            bd=0, 
            cursor='hand2', 
            width=18,
            padx=5, 
            pady=4
        )
        self.build_grid_btn.pack(pady=5, padx=5)
        
        # Выравниваем ширину фрейма с кнопками + и - по ширине кнопки «Построить сетку»
        self.inner.update_idletasks()
        btn_width = self.build_grid_btn.winfo_reqwidth()
        self.lines_control_frame.config(width=btn_width)
        
        # Кнопка разблокировки сетки (скрыта по умолчанию)
        self.unlock_grid_btn = tk.Button(
            self.inner, 
            text="🔓 Разблокировать", 
            command=self.unlock_grid,
            font=('Arial', 10, 'bold'), 
            bg='#808080', 
            fg='white', 
            activebackground='#6B6B6B', 
            activeforeground='white',
            relief=tk.FLAT, 
            bd=0, 
            cursor='hand2', 
            width=18,
            padx=5, 
            pady=4
        )
        # Кнопка изначально скрыта
        self.unlock_grid_btn.pack_forget()
        
        # Инициализируем переменную для шага сдвига, если её нет (для совместимости)
        if not hasattr(self.editor, 'grid_shift_step'):
            self.editor.grid_shift_step = tk.IntVar(value=1)

    def _show_grid_help(self):
        """Справка по блоку настроек сетки."""
        messagebox.showinfo(
            "Настройки сетки — справка",
            _GRID_HELP_TEXT,
            parent=self.editor.root,
        )
    
    def _on_gradients_changed(self):
        """Обработчик изменения чекбокса 'Анализ градиентов'"""
        if self.editor.adaptive_method_gradients.get():
            # Снимаем выбор с других чекбоксов
            self.editor.manual_marking_enabled.set(False)
            self.editor.manual_grid_enabled.set(False)
            self.manual_settings_frame.pack_forget()
    
    def _on_marking_changed(self):
        """Обработчик изменения чекбокса 'Разметка слева направо'"""
        if self.editor.manual_marking_enabled.get():
            # Снимаем выбор с других чекбоксов
            self.editor.adaptive_method_gradients.set(False)
            self.editor.manual_grid_enabled.set(False)
            self.manual_settings_frame.pack_forget()
    
    def _on_manual_grid_changed(self):
        """Обработчик изменения чекбокса 'Ручная настройка'"""
        if self.editor.manual_grid_enabled.get():
            # Снимаем выбор с других чекбоксов
            self.editor.adaptive_method_gradients.set(False)
            self.editor.manual_marking_enabled.set(False)
        # Переключаем видимость полей ручной настройки
        self._toggle_manual_settings()
    
    def _toggle_manual_settings(self):
        """Переключает видимость полей ручной настройки"""
        if self.editor.manual_grid_enabled.get():
            self.manual_settings_frame.pack(fill=tk.X, padx=(0, 5), pady=2)
        else:
            self.manual_settings_frame.pack_forget()
    
    def disable_grid_controls(self):
        """Отключает кнопки управления сеткой после получения палитры (сетка построена)"""
        if hasattr(self, 'add_line_btn'):
            self.add_line_btn.config(state='disabled')
        if hasattr(self, 'remove_line_btn'):
            self.remove_line_btn.config(state='disabled')
        if hasattr(self, 'build_grid_btn'):
            self.build_grid_btn.config(state='disabled')
        # Скрываем чекбоксы: Анализ градиентов, Разметка слева направо, Ручная настройка
        if hasattr(self, 'methods_label'):
            self.methods_label.pack_forget()
        if hasattr(self, 'methods_frame'):
            self.methods_frame.pack_forget()
        # Показываем кнопку разблокировки
        if hasattr(self, 'unlock_grid_btn'):
            self.unlock_grid_btn.pack(pady=5, padx=5)
    
    def enable_grid_controls(self):
        """Включает кнопки управления сеткой и снова показывает чекбоксы (после «Разблокировать»)"""
        if hasattr(self, 'add_line_btn'):
            self.add_line_btn.config(state='normal')
        if hasattr(self, 'remove_line_btn'):
            self.remove_line_btn.config(state='normal')
        if hasattr(self, 'build_grid_btn'):
            self.build_grid_btn.config(state='normal')
        # Показываем надпись и чекбоксы над «Управление линиями»: сначала чекбоксы, затем надпись сверху
        if hasattr(self, 'methods_frame') and hasattr(self, 'lines_control_frame'):
            self.methods_frame.pack(fill=tk.X, padx=5, pady=2, before=self.lines_control_frame)
        if hasattr(self, 'methods_label') and hasattr(self, 'methods_frame'):
            self.methods_label.pack(fill=tk.X, padx=5, pady=(5, 5), before=self.methods_frame)
        # Скрываем кнопку разблокировки
        if hasattr(self, 'unlock_grid_btn'):
            self.unlock_grid_btn.pack_forget()
    
    def unlock_grid(self):
        """Разблокирует сетку, позволяя её редактировать"""
        if hasattr(self.editor, 'grid_locked'):
            self.editor.grid_locked = False
            # Включаем кнопки управления сеткой
            self.enable_grid_controls()
            # Показываем сообщение
            from tkinter import messagebox
            from utils.version_utils import get_app_name_with_version
            app_name = get_app_name_with_version()
            messagebox.showinfo(f"Информация - {app_name}", "Сетка разблокирована. Теперь можно редактировать сетку.")

