"""Панель настроек фрагментации"""
import tkinter as tk
from tkinter import messagebox

_FRAGMENT_HELP_TEXT = (
    "Блок «Настройки фрагментации» — разбиение изображения на ограниченное число цветов "
    "(палитру ниток для вышивки).\n\n"
    "• Выберите один метод кластеризации цветов: KMeans, улучшенный KMeans, взвешенный, "
    "иерархический + KMeans, Octree и др. Алгоритмы по-разному группируют похожие оттенки.\n\n"
    "• «Количество цветов в палитре» — сколько различных цветов будет в наборе.\n\n"
    "• «Фокусировка на центре» — при расчёте палитры больший вес у центра изображения.\n\n"
    "• «Получить палитру» запускает фрагментацию: появляется палитра внизу и "
    "фрагментированное изображение для схемы.\n\n"
    "• «Автозакрашивание» закрашивает ячейки сетки цветами из палитры по сходству.\n\n"
    "Рекомендуемый порядок: построить сетку → задать метод и число цветов → "
    "«Получить палитру» → при необходимости автозакрашивание и правки кистью."
)


class FragmentPanel:
    """Инкапсулирует элементы управления настройками фрагментации."""
    
    def __init__(self, editor, parent_frame):
        """
        Args:
            editor: Экземпляр GridEditor
            parent_frame: Родительский фрейм для размещения панели
        """
        self.editor = editor
        
        self.frame = tk.Frame(parent_frame, relief=tk.GROOVE, borderwidth=2)
        self.frame.pack(fill=tk.X, padx=5, pady=5)
        header_row = tk.Frame(self.frame)
        tk.Label(header_row, text="Настройки фрагментации", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 0))
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
        help_link.bind('<Button-1>', lambda e: self._show_fragment_help())
        help_link.bind('<Enter>', lambda e: help_link.config(font=_help_font_u))
        help_link.bind('<Leave>', lambda e: help_link.config(font=_help_font))
        header_row.pack(fill=tk.X, padx=5, pady=(8, 4))

        self.inner = tk.Frame(self.frame)
        self.inner.pack(fill=tk.X, padx=5, pady=(0, 8))
        
        # Метка
        tk.Label(
            self.inner,
            text="Выберите метод создания палитры:",
            font=('Arial', 8),
            anchor='w'
        ).pack(fill=tk.X, padx=5, pady=(5, 5))
        
        # Фрейм для чекбоксов методов
        methods_frame = tk.Frame(self.inner)
        methods_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # Список всех методов для взаимного исключения
        self.method_vars = []
        self.method_checkboxes = []
        
        # Функция для обработки выбора метода
        def on_method_selected(selected_var):
            """Отключает другие методы при выборе одного"""
            if selected_var.get():  # Только если чекбокс включен
                for var in self.method_vars:
                    if var != selected_var:
                        var.set(False)
        
        # Чекбокс 1: KMeans
        self.editor.palette_method_kmeans = tk.BooleanVar(value=False)
        cb1 = tk.Checkbutton(
            methods_frame,
            text="KMeans",
            variable=self.editor.palette_method_kmeans,
            font=('Arial', 9),
            anchor='w',
            command=lambda: on_method_selected(self.editor.palette_method_kmeans)
        )
        cb1.pack(fill=tk.X, pady=0)
        self.method_vars.append(self.editor.palette_method_kmeans)
        self.method_checkboxes.append(cb1)
        
        # Чекбокс 1.1: KMeans улучшенный
        self.editor.palette_method_kmeans_improved = tk.BooleanVar(value=False)
        cb2 = tk.Checkbutton(
            methods_frame,
            text="KMeans (улучшенный)",
            variable=self.editor.palette_method_kmeans_improved,
            font=('Arial', 9),
            anchor='w',
            command=lambda: on_method_selected(self.editor.palette_method_kmeans_improved)
        )
        cb2.pack(fill=tk.X, pady=0)
        self.method_vars.append(self.editor.palette_method_kmeans_improved)
        self.method_checkboxes.append(cb2)
        
        # Чекбокс 1.2: KMeans взвешенный
        self.editor.palette_method_kmeans_weighted = tk.BooleanVar(value=False)
        cb3 = tk.Checkbutton(
            methods_frame,
            text="KMeans (взвешенный)",
            variable=self.editor.palette_method_kmeans_weighted,
            font=('Arial', 9),
            anchor='w',
            command=lambda: on_method_selected(self.editor.palette_method_kmeans_weighted)
        )
        cb3.pack(fill=tk.X, pady=0)
        self.method_vars.append(self.editor.palette_method_kmeans_weighted)
        self.method_checkboxes.append(cb3)
        
        # Чекбокс 1.3: Иерархическая + KMeans
        self.editor.palette_method_hierarchical_kmeans = tk.BooleanVar(value=False)
        cb4 = tk.Checkbutton(
            methods_frame,
            text="Иерархическая + KMeans",
            variable=self.editor.palette_method_hierarchical_kmeans,
            font=('Arial', 9),
            anchor='w',
            command=lambda: on_method_selected(self.editor.palette_method_hierarchical_kmeans)
        )
        cb4.pack(fill=tk.X, pady=0)
        self.method_vars.append(self.editor.palette_method_hierarchical_kmeans)
        self.method_checkboxes.append(cb4)
        
        # Чекбокс 2: Median Cut
        # self.editor.palette_method_median_cut = tk.BooleanVar(value=False)
        # cb5 = tk.Checkbutton(
        #     methods_frame,
        #     text="Median Cut",
        #     variable=self.editor.palette_method_median_cut,
        #     font=('Arial', 9),
        #     anchor='w',
        #     command=lambda: on_method_selected(self.editor.palette_method_median_cut)
        # )
        # cb5.pack(fill=tk.X, pady=0)
        # self.method_vars.append(self.editor.palette_method_median_cut)
        # self.method_checkboxes.append(cb5)
        
        # Чекбокс 3: Octree
        self.editor.palette_method_octree = tk.BooleanVar(value=False)
        cb6 = tk.Checkbutton(
            methods_frame,
            text="Octree",
            variable=self.editor.palette_method_octree,
            font=('Arial', 9),
            anchor='w',
            command=lambda: on_method_selected(self.editor.palette_method_octree)
        )
        cb6.pack(fill=tk.X, pady=0)
        self.method_vars.append(self.editor.palette_method_octree)
        self.method_checkboxes.append(cb6)
        
        # Блок ввода количества цветов в палитре
        colors_label_frame = tk.Frame(self.inner)
        colors_label_frame.pack(fill=tk.X, padx=5, pady=(5, 2))
        tk.Label(colors_label_frame, text="Количество цветов в палитре:", font=('Arial', 9)).pack(anchor=tk.W)
        
        # Строка с полем ввода и кнопкой
        colors_row_frame = tk.Frame(self.inner)
        colors_row_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # Поле ввода количества цветов
        if not hasattr(self.editor, 'num_colors'):
            self.editor.num_colors = tk.IntVar(value=24)
        colors_spinbox = tk.Spinbox(colors_row_frame, from_=0, to=256, 
                                    textvariable=self.editor.num_colors,
                                    width=10, font=('Arial', 9))
        colors_spinbox.pack(side=tk.LEFT, padx=(0, 10))
        
        # Чекбокс для фокусировки на центре изображения (всегда включен)
        if not hasattr(self.editor, 'focus_on_center_var'):
            self.editor.focus_on_center_var = tk.BooleanVar(value=True)
        else:
            # Убеждаемся, что значение всегда True
            self.editor.focus_on_center_var.set(True)
        
        focus_center_checkbox = tk.Checkbutton(
            self.inner, 
            text="Фокусировка на центре",
            variable=self.editor.focus_on_center_var,
            font=('Arial', 9)
        )
        focus_center_checkbox.pack(anchor=tk.W, padx=5, pady=(0, 5))
        
        # Кнопка получения палитры
        tk.Button(self.inner, text="Получить палитру", command=self.editor.fragment_image,
                 font=('Arial', 10, 'bold'), bg='#9B59B6', fg='white',
                 activebackground='#8E44AD', activeforeground='white',
                 relief=tk.FLAT, bd=0, cursor='hand2', width=18,
                 padx=5, pady=4).pack(pady=5, padx=5)
        
        # Кнопка автозакрашивания (под кнопкой "Получить палитру")
        tk.Button(self.inner, text="Автозакрашивание", command=self.editor.auto_paint_cells,
                 font=('Arial', 10, 'bold'), bg='#3498DB', fg='white',
                 activebackground='#2980B9', activeforeground='white',
                 relief=tk.FLAT, bd=0, cursor='hand2', width=18,
                 padx=5, pady=4).pack(pady=5, padx=5)

    def _show_fragment_help(self):
        """Справка по блоку настроек фрагментации."""
        messagebox.showinfo(
            "Настройки фрагментации — справка",
            _FRAGMENT_HELP_TEXT,
            parent=self.editor.root,
        )

