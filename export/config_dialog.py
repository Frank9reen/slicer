"""
Диалог настроек конфигурации для создания файлов
"""
import tkinter as tk
from tkinter import ttk, filedialog
import os

# Импортируем конфигурацию для получения значений по умолчанию
try:
    from export.slicer_utils import config
    HAS_CONFIG = True
except ImportError:
    # Пробуем относительный импорт для разработки
    try:
        from utils.path_utils import get_base_path
        base_path = get_base_path()
        slicer_utils_path = os.path.join(base_path, 'export', 'slicer_utils')
        import sys
        if slicer_utils_path not in sys.path:
            sys.path.insert(0, slicer_utils_path)
        import config
        HAS_CONFIG = True
    except ImportError:
        HAS_CONFIG = False


class ConfigDialog:
    """Диалоговое окно настроек конфигурации"""
    
    def __init__(self, parent, project_name=None, project_article=None, qr_url=None, vertical_lines=None, horizontal_lines=None):
        """
        Args:
            parent: Родительское окно
            project_name: Название проекта (для подстановки по умолчанию)
            project_article: Артикул проекта (для подстановки по умолчанию)
            vertical_lines: Список вертикальных линий сетки (для расчета размера)
            horizontal_lines: Список горизонтальных линий сетки (для расчета размера)
        """
        self.parent = parent
        self.result = None
        self.project_name = project_name
        self.project_article = project_article
        self.qr_url = qr_url
        self.vertical_lines = vertical_lines
        self.horizontal_lines = horizontal_lines
        
        # Рассчитываем размер из сетки, если есть
        calculated_size = self._calculate_embroidery_size()
        
        # Значения по умолчанию из конфига или запасные
        # Приоритет: project_name/project_article из проекта > имя файла > конфиг
        if HAS_CONFIG:
            config_size = getattr(config, 'EMBROIDERY_SETTINGS', {}).get('size', '23 х 23 см')
            # Используем рассчитанный размер, если есть, иначе из конфига
            self.default_size = calculated_size if calculated_size else config_size
            # Приоритет: project_name из проекта > project_name (имя файла) > конфиг
            if project_name:
                self.default_project_text = project_name
            else:
                self.default_project_text = getattr(config, 'EMBROIDERY_SETTINGS', {}).get('project_name_text', '')
            # Приоритет: project_article из проекта > project_name (имя файла) > конфиг
            if project_article:
                self.default_article = project_article
            elif project_name:
                self.default_article = project_name
            else:
                self.default_article = getattr(config, 'EMBROIDERY_SETTINGS', {}).get('article', '')
            self.default_top_text = getattr(config, 'TEXTS', {}).get('top_text', 'Набор для вышивания крестом')
            self.default_dpi = getattr(config, 'DPI', 300)
            self.default_jpeg_quality = getattr(config, 'JPEG_QUALITY', 95)
            self.default_blocks_per_page_w = getattr(config, 'BLOCKS_PER_PAGE_WIDTH', 56)
            self.default_blocks_per_page_h = getattr(config, 'BLOCKS_PER_PAGE_HEIGHT', 85)
        else:
            # Используем рассчитанный размер, если есть, иначе значение по умолчанию
            self.default_size = calculated_size if calculated_size else '23 х 23 см'
            self.default_project_text = project_name or ''
            # Приоритет: project_article > project_name
            self.default_article = project_article if project_article else (project_name or '')
            self.default_top_text = 'Набор для вышивания крестом'
            self.default_dpi = 300
            self.default_jpeg_quality = 95
            self.default_blocks_per_page_w = 56
            self.default_blocks_per_page_h = 85
        
        self.dialog = None
        self.values = {}
    
    def _calculate_embroidery_size(self):
        """
        Рассчитывает размер вышивки в см для канвы Aida 16 на основе сетки.
        Возвращает строку формата "ширина x высота см" или None, если сетка не задана.
        """
        if not self.vertical_lines or not self.horizontal_lines:
            return None
        
        if len(self.vertical_lines) < 2 or len(self.horizontal_lines) < 2:
            return None
        
        # Рассчитываем размер в см для канвы Aida 16 (16 клеток на дюйм)
        # 1 дюйм = 2.54 см, значит 1 клетка = 2.54 / 16 = 0.15875 см
        cells_per_cm = 16 / 2.54  # Клеток на см
        
        # Количество ячеек = количество линий - 1
        num_cells_width = len(self.vertical_lines) - 1
        num_cells_height = len(self.horizontal_lines) - 1
        
        width_cm = num_cells_width / cells_per_cm
        height_cm = num_cells_height / cells_per_cm
        
        return f"{width_cm:.1f} х {height_cm:.1f} см"
    
    def show(self):
        """Показывает диалог и возвращает словарь с настройками или None при отмене"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Настройки создания файлов")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Основной фрейм с прокруткой
        main_frame = ttk.Frame(self.dialog, padding=8)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Заголовок
        header_label = tk.Label(main_frame, text="Настройки конфигурации", 
                               font=('Arial', 12, 'bold'))
        header_label.pack(pady=(0, 10))
        
        # Создаем переменные для значений
        self.size_var = tk.StringVar(value=self.default_size)
        self.project_text_var = tk.StringVar(value=self.default_project_text)
        self.article_var = tk.StringVar(value=self.default_article)
        self.top_text_var = tk.StringVar(value=self.default_top_text)
        self.qr_url_var = tk.StringVar(value=self.qr_url if self.qr_url else '')  # URL для QR-кода
        self.dpi_var = tk.IntVar(value=self.default_dpi)
        self.quality_var = tk.IntVar(value=self.default_jpeg_quality)
        self.blocks_w_var = tk.IntVar(value=self.default_blocks_per_page_w)
        self.blocks_h_var = tk.IntVar(value=self.default_blocks_per_page_h)
        self.create_oxs_var = tk.BooleanVar(value=True)  # По умолчанию создавать OXS
        self.main_page_image_path = tk.StringVar(value='')  # Путь к изображению для главной страницы
        self.use_layout_image_var = tk.BooleanVar(value=False)  # По умолчанию НЕ использовать _layout.jpg
        self.canvas_size_var = tk.IntVar(value=16)  # Размер канвы (ct), по умолчанию Aida 16
        self.use_saga_paradise_var = tk.BooleanVar(value=True)  # По умолчанию использовать saga/paradise
        self.auto_blocks_per_page_var = tk.BooleanVar(value=True)  # По умолчанию включен автоматический расчет
        # Режим сборки: marfa / mulen / lilu_dmc
        self.brand_var = tk.StringVar(value='marfa')
        
        # Секция: Настройки главной страницы A5
        a5_frame = ttk.LabelFrame(main_frame, text="Настройки главной страницы A5", padding=7)
        a5_frame.pack(fill=tk.X, pady=3)
        
        # Размер вышивки
        ttk.Label(a5_frame, text="Размер вышивки:").grid(row=0, column=0, sticky=tk.W, pady=3, padx=5)
        size_entry = ttk.Entry(a5_frame, textvariable=self.size_var, width=30)
        size_entry.grid(row=0, column=1, sticky=tk.EW, pady=3, padx=5)
        ttk.Label(a5_frame, text="(напр.: 23 х 23 см)", font=('Arial', 8)).grid(row=0, column=2, sticky=tk.W, pady=3, padx=5)
        
        # Название проекта
        ttk.Label(a5_frame, text="Название проекта:").grid(row=1, column=0, sticky=tk.W, pady=3, padx=5)
        project_entry = ttk.Entry(a5_frame, textvariable=self.project_text_var, width=30)
        project_entry.grid(row=1, column=1, sticky=tk.EW, pady=3, padx=5)
        ttk.Label(a5_frame, text="(напр.: Капибара в душе)", font=('Arial', 8)).grid(row=1, column=2, sticky=tk.W, pady=3, padx=5)
        
        # Артикул
        ttk.Label(a5_frame, text="Артикул:").grid(row=2, column=0, sticky=tk.W, pady=3, padx=5)
        article_entry = ttk.Entry(a5_frame, textvariable=self.article_var, width=30)
        article_entry.grid(row=2, column=1, sticky=tk.EW, pady=3, padx=5)
        ttk.Label(a5_frame, text="(напр.: emb-capybara_shower)", font=('Arial', 8)).grid(row=2, column=2, sticky=tk.W, pady=3, padx=5)
        
        # Верхний текст
        ttk.Label(a5_frame, text="Верхний текст:").grid(row=3, column=0, sticky=tk.W, pady=3, padx=5)
        top_text_entry = ttk.Entry(a5_frame, textvariable=self.top_text_var, width=60)
        top_text_entry.grid(row=3, column=1, columnspan=2, sticky=tk.EW, pady=3, padx=5)
        
        # URL для QR-кода
        ttk.Label(a5_frame, text="URL для QR-кода:").grid(row=4, column=0, sticky=tk.W, pady=3, padx=5)
        qr_url_entry = ttk.Entry(a5_frame, textvariable=self.qr_url_var, width=30)
        qr_url_entry.grid(row=4, column=1, sticky=tk.EW, pady=3, padx=5)
        ttk.Label(a5_frame, text="(для схемы и органайзера)", font=('Arial', 8)).grid(row=4, column=2, sticky=tk.W, pady=3, padx=5)
        
        # Изображение для главной страницы
        ttk.Label(a5_frame, text="Изображение для главной страницы:").grid(row=5, column=0, sticky=tk.W, pady=3, padx=5)
        ttk.Label(a5_frame, text="(по умолчанию создается картинка с крестиками)", font=('Arial', 8)).grid(row=5, column=1, columnspan=2, sticky=tk.W, pady=3, padx=5)
        
        image_path_frame = ttk.Frame(a5_frame)
        image_path_frame.grid(row=6, column=1, columnspan=2, sticky=tk.EW, pady=3, padx=5)
        image_path_entry = ttk.Entry(image_path_frame, textvariable=self.main_page_image_path, width=25)
        image_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(image_path_frame, text="Выбрать...", command=self.browse_main_page_image, width=12).pack(side=tk.LEFT, padx=(5, 0))
        
        # Чекбокс для использования _layout.jpg
        use_layout_checkbox = ttk.Checkbutton(a5_frame, text="Использовать картинку _layout.jpg", variable=self.use_layout_image_var)
        use_layout_checkbox.grid(row=7, column=1, columnspan=2, sticky=tk.W, pady=3, padx=5)
        
        # Чекбокс для saga/paradise
        saga_paradise_checkbox = ttk.Checkbutton(a5_frame, text="Добавить плашку saga/paradise", variable=self.use_saga_paradise_var)
        saga_paradise_checkbox.grid(row=8, column=1, columnspan=2, sticky=tk.W, pady=3, padx=5)
        
        a5_frame.columnconfigure(1, weight=1)
        
        # Секция: Настройки канвы
        canvas_frame = ttk.LabelFrame(main_frame, text="Канва", padding=7)
        canvas_frame.pack(fill=tk.X, pady=3)
        
        # Размер канвы
        ttk.Label(canvas_frame, text="Размер канвы:").grid(row=0, column=0, sticky=tk.W, pady=3, padx=5)
        canvas_size_spin = ttk.Spinbox(canvas_frame, from_=8, to=32, increment=1, textvariable=self.canvas_size_var, width=10)
        canvas_size_spin.grid(row=0, column=1, sticky=tk.W, pady=3, padx=5)
        ttk.Label(canvas_frame, text="ct (напр.: 14, 16, 18)", font=('Arial', 8)).grid(row=0, column=2, sticky=tk.W, pady=3, padx=5)
        
        # Секция: Настройки страниц A4
        a4_frame = ttk.LabelFrame(main_frame, text="Настройки страниц A4", padding=7)
        a4_frame.pack(fill=tk.X, pady=3)
        
        # Количество блоков по ширине на странице
        ttk.Label(a4_frame, text="Блоков по ширине:").grid(row=0, column=0, sticky=tk.W, pady=3, padx=5)
        blocks_w_spin = ttk.Spinbox(a4_frame, from_=1, to=200, increment=1, textvariable=self.blocks_w_var, width=10)
        blocks_w_spin.grid(row=0, column=1, sticky=tk.W, pady=3, padx=5)
        ttk.Label(a4_frame, text="(по умолчанию: 56)", font=('Arial', 8)).grid(row=0, column=2, sticky=tk.W, pady=3, padx=5)
        
        # Количество блоков по высоте на странице
        ttk.Label(a4_frame, text="Блоков по высоте:").grid(row=1, column=0, sticky=tk.W, pady=3, padx=5)
        blocks_h_spin = ttk.Spinbox(a4_frame, from_=1, to=200, increment=1, textvariable=self.blocks_h_var, width=10)
        blocks_h_spin.grid(row=1, column=1, sticky=tk.W, pady=3, padx=5)
        ttk.Label(a4_frame, text="(по умолчанию: 85)", font=('Arial', 8)).grid(row=1, column=2, sticky=tk.W, pady=3, padx=5)
        
        # Чекбокс для автоматического расчета
        auto_blocks_checkbox = ttk.Checkbutton(a4_frame, text="Автоматически рассчитывать количество блоков на странице", variable=self.auto_blocks_per_page_var)
        auto_blocks_checkbox.grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=3, padx=5)
        ttk.Label(a4_frame, text="(чтобы страницы были заполнены более чем на 1/3)", font=('Arial', 8)).grid(row=3, column=0, columnspan=3, sticky=tk.W, pady=(0, 3), padx=5)
        
        # Секция: Дополнительные опции
        options_frame = ttk.LabelFrame(main_frame, text="Дополнительные опции", padding=7)
        options_frame.pack(fill=tk.X, pady=3)
        
        # Чекбокс для создания OXS файла
        oxs_checkbox = ttk.Checkbutton(options_frame, text="Создать OXS-файл", variable=self.create_oxs_var)
        oxs_checkbox.grid(row=0, column=0, sticky=tk.W, pady=3, padx=5)
        
        # Выбор режима/бренда (в одну строку)
        brand_row = ttk.Frame(options_frame)
        brand_row.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=3, padx=5)
        ttk.Label(brand_row, text="Сборка для бренда:").pack(side=tk.LEFT)
        ttk.Radiobutton(brand_row, text="Марфа Иголкина", variable=self.brand_var, value='marfa').pack(side=tk.LEFT, padx=(8, 15))
        ttk.Radiobutton(brand_row, text="Мулен стиль", variable=self.brand_var, value='mulen').pack(side=tk.LEFT, padx=(0, 15))
        ttk.Radiobutton(brand_row, text="Lilu&Stitch (DMC)", variable=self.brand_var, value='lilu_dmc').pack(side=tk.LEFT)
        
        # Кнопки
        button_frame = tk.Frame(main_frame)
        button_frame.pack(pady=(10, 5), anchor=tk.E)
        
        ok_button = tk.Button(button_frame, text="ОК", command=self.ok, width=12, height=1, relief=tk.RAISED)
        ok_button.pack(side=tk.RIGHT, padx=5)
        cancel_button = tk.Button(button_frame, text="Отмена", command=self.cancel, width=12, height=1, relief=tk.RAISED)
        cancel_button.pack(side=tk.RIGHT, padx=5)
        
        # Центрируем окно по фактическому размеру содержимого
        self.dialog.update_idletasks()
        w = self.dialog.winfo_reqwidth()
        h = self.dialog.winfo_reqheight()
        x = (self.dialog.winfo_screenwidth() // 2) - (w // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (h // 2)
        self.dialog.geometry(f"{w}x{h}+{x}+{y}")
        
        # Устанавливаем фокус на первое поле
        size_entry.focus()
        
        # Ждем закрытия диалога
        self.dialog.wait_window()
        
        return self.result
    
    def browse_main_page_image(self):
        """Открывает диалог выбора изображения для главной страницы"""
        file_path = filedialog.askopenfilename(
            title="Выберите изображение для главной страницы",
            filetypes=[
                ("Изображения", "*.jpg *.jpeg *.png *.bmp *.gif"),
                ("JPEG", "*.jpg *.jpeg"),
                ("PNG", "*.png"),
                ("Все файлы", "*.*")
            ]
        )
        if file_path:
            self.main_page_image_path.set(file_path)
    
    def ok(self):
        """Сохраняет настройки и закрывает диалог"""
        main_page_image = self.main_page_image_path.get().strip()
        # Проверяем, что файл существует, если указан
        if main_page_image and not os.path.exists(main_page_image):
            from tkinter import messagebox
            messagebox.showwarning("Предупреждение", 
                                 f"Файл изображения не найден:\n{main_page_image}\n\n"
                                 "Главная страница будет создана из layout изображения.")
            main_page_image = ''
        
        selected_mode = self.brand_var.get()
        use_dmc = selected_mode == 'lilu_dmc'
        # Для совместимости со старой логикой brand оставляем marfa/mulen
        brand = 'mulen' if selected_mode == 'mulen' else 'marfa'

        self.result = {
            'size': self.size_var.get(),
            'project_name_text': self.project_text_var.get(),
            'article': self.article_var.get(),
            'top_text': self.top_text_var.get(),
            'qr_url': self.qr_url_var.get(),
            'create_oxs': self.create_oxs_var.get(),
            'use_dmc': use_dmc,  # Использовать DMC вместо Gamma
            'main_page_image': main_page_image,  # Путь к изображению для главной страницы
            'use_layout_image': self.use_layout_image_var.get(),  # Использовать ли _layout.jpg
            'canvas_size': self.canvas_size_var.get(),  # Размер канвы (ct)
            'use_saga_paradise': self.use_saga_paradise_var.get(),  # Использовать ли saga/paradise
            'blocks_per_page_width': self.blocks_w_var.get(),  # Количество блоков по ширине на странице A4
            'blocks_per_page_height': self.blocks_h_var.get(),  # Количество блоков по высоте на странице A4
            'auto_blocks_per_page': self.auto_blocks_per_page_var.get(),  # Автоматический расчет блоков на странице
            'brand': brand,  # Бренд: 'marfa' (Марфа Иголкина) или 'mulen' (Мулен стиль)
        }
        self.dialog.destroy()
    
    def cancel(self):
        """Закрывает диалог без сохранения"""
        self.result = None
        self.dialog.destroy()

