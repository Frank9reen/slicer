"""
Диалог выбора цвета из палитры Гаммы
"""
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import numpy as np
import colorsys
from color.gamma_palette import get_gamma_palette

# Режимы отображения списка цветов
DISPLAY_MODE_GAMMA = "По номеру Gamma (по возрастанию)"
DISPLAY_MODE_HUE = "По оттенку (близкие цвета рядом)"
DISPLAY_MODE_BRIGHTNESS = "По яркости (тёмное → светлое)"
DISPLAY_MODE_NAME = "По названию"
DISPLAY_MODES = [DISPLAY_MODE_GAMMA, DISPLAY_MODE_HUE, DISPLAY_MODE_BRIGHTNESS, DISPLAY_MODE_NAME]


class GammaColorPicker:
    """Диалог выбора цвета из палитры Гаммы"""
    
    def __init__(self, parent, target_color_rgb=None, target_gamma_code=None):
        """
        Args:
            parent: Родительское окно
            target_color_rgb: Целевой RGB цвет (R, G, B) для поиска ближайшего
            target_gamma_code: Номер Гаммы для исходного цвета (как в палитре редактора), если известен
        """
        self.parent = parent
        self.target_color_rgb = target_color_rgb
        self.target_gamma_code = target_gamma_code  # из палитры редактора (Excel), чтобы отображать верно
        self.selected_color = None
        self.applied = False  # Флаг, что была нажата кнопка "Применить"
        
        # Загружаем палитру Гаммы
        self.gamma_palette = get_gamma_palette()
        
        self.dialog = None
        self.tree = None
        self.overlay_canvas = None
        self.item_colors = {}  # Связь item_id -> (r, g, b)
        self.item_to_color_info = {}  # Связь item_id -> color_info
        self.all_colors = []
        self.rgb_canvas = None  # Canvas только для колонки RGB
    
    @staticmethod
    def _gamma_sort_key(color_info):
        """Ключ для сортировки по номеру Гаммы по возрастанию (числовой порядок)."""
        gamma = color_info.get('gamma') or ''
        s = str(gamma).strip().upper()
        if s.startswith('G'):
            s = s[1:]
        try:
            return (0, int(s)) if s.isdigit() else (1, s)
        except (ValueError, TypeError):
            return (1, s)
    
    @staticmethod
    def _hue_sort_key(color_info):
        """Ключ для сортировки по оттенку (HSV) — близкие по цвету рядом."""
        rgb = color_info.get('rgb')
        if rgb is None:
            return (1, 0.0, 0.0, 0.0)
        r, g, b = [x / 255.0 for x in rgb]
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        return (0, h, s, v)
    
    @staticmethod
    def _brightness_sort_key(color_info):
        """Ключ для сортировки по яркости (тёмное → светлое)."""
        rgb = color_info.get('rgb')
        if rgb is None:
            return 0.0
        r, g, b = rgb
        return (r * 299 + g * 587 + b * 114) / 1000.0
    
    @staticmethod
    def _name_sort_key(color_info):
        """Ключ для сортировки по названию."""
        name = color_info.get('name') or ''
        return str(name).lower()
    
    def _sort_colors_by_mode(self, colors, mode):
        """Возвращает копию списка цветов, отсортированную по выбранному режиму."""
        if mode == DISPLAY_MODE_GAMMA:
            return sorted(colors, key=self._gamma_sort_key)
        if mode == DISPLAY_MODE_HUE:
            return sorted(colors, key=self._hue_sort_key)
        if mode == DISPLAY_MODE_BRIGHTNESS:
            return sorted(colors, key=self._brightness_sort_key)
        if mode == DISPLAY_MODE_NAME:
            return sorted(colors, key=self._name_sort_key)
        return list(colors)
    
    def _get_current_filtered_colors(self):
        """Возвращает текущий список цветов с учётом поиска и режима отображения."""
        query = (self.search_var.get() or "").strip().lower()
        if query:
            results = [
                c for c in self.all_colors
                if query in str(c.get('gamma', '')).lower()
            ]
        else:
            results = list(self.all_colors)
        mode = self.display_mode_var.get() if hasattr(self, 'display_mode_var') else DISPLAY_MODE_GAMMA
        return self._sort_colors_by_mode(results, mode)
    
    def _on_display_mode_change(self, *args):
        """При смене режима отображения перестраиваем список."""
        if hasattr(self, 'tree') and self.tree is not None:
            colors = self._get_current_filtered_colors()
            self.display_colors(colors)
    
    def show(self) -> tuple:
        """
        Показывает диалог и возвращает выбранный цвет
        
        Returns:
            (rgb_tuple, color_info_dict) или (None, None) при отмене
        """
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Выбор цвета из палитры Гаммы")
        self.dialog.geometry("900x700")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Обрабатываем закрытие окна через крестик
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel)
        
        # Центрируем окно
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        # Основной контейнер
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Поиск и режим отображения в одну строку
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="Поиск по номеру Gamma:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search_change)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(search_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=2)
        
        ttk.Label(search_frame, text="Режим отображения:").pack(side=tk.LEFT, padx=(0, 5))
        self.display_mode_var = tk.StringVar(value=DISPLAY_MODE_GAMMA)
        mode_combo = ttk.Combobox(
            search_frame,
            textvariable=self.display_mode_var,
            values=DISPLAY_MODES,
            state="readonly",
            width=38
        )
        mode_combo.pack(side=tk.LEFT, padx=2)
        self.display_mode_var.trace('w', self._on_display_mode_change)
        
        info_label = ttk.Label(search_frame, text="")
        info_label.pack(side=tk.RIGHT, padx=5)
        self.info_label = info_label
        
        # Показываем исходный цвет (из палитры) и выбранный цвет (из таблицы гаммы)
        colors_frame = ttk.Frame(main_frame)
        colors_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Исходный цвет из палитры
        if self.target_color_rgb:
            source_frame = ttk.Frame(colors_frame)
            source_frame.pack(side=tk.LEFT, padx=10)
            
            ttk.Label(source_frame, text="Исходный цвет:").pack(side=tk.LEFT, padx=5)
            r, g, b = self.target_color_rgb
            source_canvas = tk.Canvas(source_frame, width=40, height=30)
            source_canvas.pack(side=tk.LEFT, padx=5)
            source_canvas.create_rectangle(0, 0, 40, 30, fill=f"#{r:02x}{g:02x}{b:02x}", outline='black')
            
            # Номер Гаммы для исходного цвета: используем переданный (как в палитре редактора) или ищем в палитре диалога
            if getattr(self, 'target_gamma_code', None):
                gamma_code_str = f"Гамма: {self.target_gamma_code}"
            else:
                closest_gamma = self.gamma_palette.find_closest_color(self.target_color_rgb)
                gamma_code = closest_gamma.get('gamma', 'N/A') if closest_gamma else 'N/A'
                if gamma_code and gamma_code != 'N/A':
                    gamma_code_str = f"Гамма: {gamma_code}"
                else:
                    gamma_code_str = "Гамма: N/A"
            
            ttk.Label(source_frame, text=f"RGB: ({r}, {g}, {b}) | {gamma_code_str}").pack(side=tk.LEFT, padx=5)
        
        # Стрелочка между исходным и заменяемым цветом
        if self.target_color_rgb:
            arrow_label = ttk.Label(colors_frame, text="→", font=('Arial', 16, 'bold'))
            arrow_label.pack(side=tk.LEFT, padx=5)
        
        # Выбранный цвет из таблицы гаммы
        selected_frame = ttk.Frame(colors_frame)
        selected_frame.pack(side=tk.LEFT, padx=10)
        
        ttk.Label(selected_frame, text="Цвет замены:").pack(side=tk.LEFT, padx=5)
        self.selected_color_canvas = tk.Canvas(selected_frame, width=40, height=30, bg='lightgray')
        self.selected_color_canvas.pack(side=tk.LEFT, padx=5)
        self.selected_color_label = ttk.Label(selected_frame, text="Не выбран")
        self.selected_color_label.pack(side=tk.LEFT, padx=5)
        
        # Контейнер для Treeview
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Вертикальная прокрутка
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Горизонтальная прокрутка
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Таблица
        columns = ('№', 'Gamma', 'RGB', 'DMC', 'Название', 'HEX')
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings', 
                           yscrollcommand=lambda *args: (vsb.set(*args), self._update_colors()),
                           xscrollcommand=lambda *args: (hsb.set(*args), self._update_colors()),
                           height=25,
                           selectmode='browse')
        
        vsb.config(command=lambda *args: (tree.yview(*args), self._update_colors()))
        hsb.config(command=tree.xview)
        
        # Настройка колонок
        tree.heading('№', text='№')
        tree.heading('Gamma', text='Gamma')
        tree.heading('RGB', text='RGB')
        tree.heading('DMC', text='DMC')
        tree.heading('Название', text='Название')
        tree.heading('HEX', text='HEX')
        
        tree.column('№', width=60, anchor=tk.CENTER)
        tree.column('Gamma', width=100, anchor=tk.CENTER)
        tree.column('RGB', width=120, anchor=tk.CENTER)
        tree.column('DMC', width=80, anchor=tk.CENTER)
        tree.column('Название', width=300, anchor=tk.W)
        tree.column('HEX', width=100, anchor=tk.CENTER)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree = tree
        
        # Привязываем выбор строки
        tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        
        # Canvas будет создан динамически только для колонки RGB
        self.rgb_canvas = None
        self.overlay_canvas = None
        
        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Отмена", command=self.cancel).pack(side=tk.RIGHT, padx=5)
        self.apply_button = ttk.Button(button_frame, text="Применить", command=self.ok, state='disabled')
        self.apply_button.pack(side=tk.RIGHT, padx=5)
        
        # Загружаем данные и сортируем по номеру Гаммы по возрастанию
        self.all_colors = sorted(
            self.gamma_palette.get_all_colors(),
            key=self._gamma_sort_key
        )
        self.display_colors(self.all_colors)
        
        # Если указан целевой цвет, выделяем ближайший
        if self.target_color_rgb:
            closest = self.gamma_palette.find_closest_color(self.target_color_rgb)
            if closest:
                self.selected_color = closest
                # Находим и выделяем строку с ближайшим цветом
                self.scroll_to_color(closest)
                # Обновляем отображение выбранного цвета
                self.update_selected_color_display()
        
        # Принудительно вызываем закрашивание после загрузки
        # Используем несколько попыток с задержками, чтобы дождаться полной отрисовки tree
        def force_draw():
            self.dialog.update_idletasks()
            self.tree.update_idletasks()
            self._draw_color_cells_rgb_only()
        
        self.dialog.update_idletasks()
        self.tree.update_idletasks()
        # Вызываем сразу и с задержками
        force_draw()
        self.dialog.after(50, force_draw)
        self.dialog.after(150, force_draw)
        self.dialog.after(300, force_draw)
        self.dialog.after(500, force_draw)
        
        # Устанавливаем фокус на поиск
        search_entry.focus()
        
        # Ждем закрытия диалога
        self.dialog.wait_window()
        
        # Возвращаем цвет только если была нажата кнопка "Применить"
        if self.applied and self.selected_color:
            return (self.selected_color['rgb'], self.selected_color)
        return (None, None)
    
    def on_search_change(self, *args):
        """Обработчик изменения поискового запроса — поиск по номеру Гаммы, порядок по выбранному режиму."""
        colors = self._get_current_filtered_colors()
        self.display_colors(colors)
    
    def _update_colors(self):
        """Обновляет отображение закрашенных ячеек"""
        if self.dialog and self.dialog.winfo_exists():
            self.dialog.after(50, self._draw_color_cells_rgb_only)
    
    def _draw_color_cells_rgb_only(self):
        """Закрашивает только ячейки колонки RGB цветом, не скрывая текст"""
        if not hasattr(self, 'tree') or self.tree is None:
            return
        
        # Получаем координаты колонки RGB для размещения canvas
        children = self.tree.get_children()
        if not children:
            # Если элементов нет, пробуем еще раз через некоторое время
            if self.dialog and self.dialog.winfo_exists():
                self.dialog.after(200, self._draw_color_cells_rgb_only)
            return
        
        try:
            # Вычисляем позицию колонки RGB на основе ширины предыдущих колонок
            # Колонки: №, Gamma, RGB
            num_width = self.tree.column('№', 'width')
            gamma_width = self.tree.column('Gamma', 'width')
            rgb_width = self.tree.column('RGB', 'width')
            rgb_x = num_width + gamma_width
            
            # Пробуем получить bbox для проверки, но если не получается, используем вычисленные координаты
            bbox = None
            for item in children[:10]:  # Пробуем первые 10 элементов
                bbox = self.tree.bbox(item, 'RGB')
                if bbox:
                    # Используем реальные координаты если доступны
                    rgb_x, rgb_y, rgb_width, rgb_height = bbox
                    break
            
            # Если bbox не доступен, используем вычисленные координаты
            if not bbox:
                rgb_x = num_width + gamma_width
                rgb_width = self.tree.column('RGB', 'width')
            
            # Создаем canvas только для колонки RGB, если его еще нет
            if self.rgb_canvas is None:
                self.rgb_canvas = tk.Canvas(self.tree.master, highlightthickness=0)
                self.overlay_canvas = self.rgb_canvas
                
                # Делаем Canvas прозрачным для событий мыши
                def pass_through(event):
                    # Пересчитываем координаты относительно tree
                    self.tree.event_generate('<Button-1>', x=event.x + rgb_x, y=event.y)
                    return "break"
                
                self.rgb_canvas.bind('<Button-1>', pass_through)
                self.rgb_canvas.configure(cursor='')
                
                # Привязываем обновление при прокрутке и изменении размеров
                def on_tree_configure(event):
                    self._update_colors()
                
                self.tree.bind('<Configure>', on_tree_configure)
                self.rgb_canvas.bind('<Configure>', lambda e: self._update_colors())
            
            # Размещаем canvas только в области колонки RGB
            # Заголовок Treeview находится в отдельной области, canvas не должен его перекрывать
            # Но для надежности размещаем canvas начиная с y=0, заголовок все равно будет виден
            # так как он находится в отдельной области Treeview
            self.rgb_canvas.place(in_=self.tree, x=rgb_x, y=0, width=rgb_width, relheight=1)
            
            # Убеждаемся, что заголовок установлен (он уже установлен выше, но проверим)
            if hasattr(self.tree, 'heading'):
                try:
                    # Заголовок уже установлен, просто убеждаемся что он виден
                    pass
                except:
                    pass
            
            # Удаляем предыдущие заливки
            self.rgb_canvas.delete('color_cell')
            
            # Закрашиваем ячейки RGB
            for item_id in children:
                if item_id in self.item_colors:
                    r, g, b = self.item_colors[item_id]
                    
                    try:
                        # Получаем bounding box колонки "RGB" для этого элемента
                        bbox = self.tree.bbox(item_id, 'RGB')
                        if bbox:
                            x, y, width, height = bbox
                            
                            # Координаты относительно canvas (x уже учтен в place)
                            canvas_x = x - rgb_x
                            
                            # Закрашиваем только ячейку RGB цветом
                            # Используем stipple для полупрозрачности, чтобы текст был виден
                            rect_id = self.rgb_canvas.create_rectangle(
                                canvas_x, y,
                                canvas_x + width, y + height,
                                fill=f"#{r:02x}{g:02x}{b:02x}",
                                outline='black',
                                width=1,
                                tags='color_cell'
                            )
                            
                            # Добавляем текст поверх цвета для видимости
                            # Вычисляем яркость для выбора цвета текста
                            brightness = (r * 299 + g * 587 + b * 114) / 1000
                            text_color = 'white' if brightness < 128 else 'black'
                            
                            # Рисуем текст поверх цвета
                            self.rgb_canvas.create_text(
                                canvas_x + width / 2, y + height / 2,
                                text=f"({r}, {g}, {b})",
                                fill=text_color,
                                font=('Arial', 9),
                                tags='color_cell'
                            )
                    except (ValueError, TypeError, KeyError):
                        # Пропускаем цвета с None или некорректными значениями
                        pass
        except Exception:
            pass
    
    def display_colors(self, colors):
        """Отображает цвета в таблице"""
        # Очищаем таблицу
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.item_colors = {}
        self.item_to_color_info = {}
        
        # Заполняем таблицу
        for idx, color_info in enumerate(colors):
            rgb = color_info.get('rgb')
            
            # Обрабатываем случай, когда RGB пустой (None)
            if rgb is None:
                r, g, b = None, None, None
                hex_color = color_info.get('hex') or 'N/A'
            else:
                r, g, b = rgb
                hex_color = color_info.get('hex', f"#{r:02x}{g:02x}{b:02x}")
                
                # Валидация HEX цвета
                if not hex_color.startswith('#') or len(hex_color) != 7:
                    hex_color = f"#{r:02x}{g:02x}{b:02x}"
                else:
                    try:
                        int(hex_color[1:], 16)
                    except ValueError:
                        hex_color = f"#{r:02x}{g:02x}{b:02x}"
            
            name = color_info.get('name', 'N/A') or 'N/A'
            dmc = color_info.get('dmc', 'N/A') or 'N/A'
            gamma = color_info.get('gamma', 'N/A') or 'N/A'
            
            # Номер цвета (индекс + 1)
            color_number = color_info.get('index', idx) + 1
            
            # Вставляем данные
            # Для колонки RGB оставляем пустую строку - текст будет нарисован на canvas
            item_id = self.tree.insert('', tk.END, values=(
                color_number,
                gamma,  # Колонка "Gamma"
                '',  # Колонка "RGB" - будет закрашена цветом, текст на canvas
                dmc,
                name,
                hex_color
            ))
            
            # Сохраняем цвет для отрисовки (только если RGB не None)
            if rgb is not None:
                self.item_colors[item_id] = (r, g, b)
            self.item_to_color_info[item_id] = color_info
            
            # Сохраняем текст RGB для отрисовки на canvas
            # Текст будет нарисован поверх цвета на canvas
            
            # Выделяем выбранный цвет
            if self.selected_color and color_info.get('index') == self.selected_color.get('index'):
                self.tree.selection_set(item_id)
                self.tree.see(item_id)
        
        # Обновляем информацию о количестве
        self.info_label.config(text=f"Найдено: {len(colors)} из {len(self.all_colors)}")
        
        # Применяем цвета через canvas только для колонки RGB
        if self.dialog and self.dialog.winfo_exists():
            self.tree.update_idletasks()
            # Вызываем закрашивание с несколькими задержками для гарантии отрисовки
            self.dialog.after(50, self._draw_color_cells_rgb_only)
            self.dialog.after(150, self._draw_color_cells_rgb_only)
            self.dialog.after(300, self._draw_color_cells_rgb_only)
    
    def on_tree_select(self, event):
        """Обработчик выбора строки в таблице"""
        selection = self.tree.selection()
        if selection:
            item_id = selection[0]
            if item_id in self.item_to_color_info:
                self.selected_color = self.item_to_color_info[item_id]
                # Обновляем отображение выбранного цвета
                self.update_selected_color_display()
    
    def scroll_to_color(self, color_info):
        """Прокручивает к указанному цвету"""
        if not color_info:
            return
        
        # Находим item_id с этим цветом
        target_rgb = color_info['rgb']
        for item_id, rgb in self.item_colors.items():
            if rgb == target_rgb:
                self.tree.selection_set(item_id)
                self.tree.see(item_id)
                break
    
    def update_selected_color_display(self):
        """Обновляет отображение выбранного цвета"""
        if self.selected_color and hasattr(self, 'selected_color_canvas'):
            r, g, b = self.selected_color['rgb']
            # Очищаем canvas
            self.selected_color_canvas.delete('all')
            # Рисуем цвет
            self.selected_color_canvas.create_rectangle(0, 0, 40, 30, 
                                                       fill=f"#{r:02x}{g:02x}{b:02x}", 
                                                       outline='black')
            # Обновляем текст с кодом Гаммы
            name = self.selected_color.get('name', 'N/A') or 'N/A'
            if len(name) > 30:
                name = name[:27] + "..."
            gamma_code = self.selected_color.get('gamma', 'N/A') or 'N/A'
            if gamma_code and gamma_code != 'N/A':
                gamma_code_str = f"Гамма: {gamma_code}"
            else:
                gamma_code_str = "Гамма: N/A"
            self.selected_color_label.config(text=f"{name} RGB: ({r}, {g}, {b}) | {gamma_code_str}")
            # Активируем кнопку "Применить"
            self.apply_button.config(state='normal')
        else:
            # Сбрасываем отображение
            if hasattr(self, 'selected_color_canvas'):
                self.selected_color_canvas.delete('all')
                self.selected_color_label.config(text="Не выбран")
                self.apply_button.config(state='disabled')
    
    def ok(self):
        """Применяет выбранный цвет и закрывает диалог"""
        if self.selected_color is None:
            messagebox.showwarning("Предупреждение", "Выберите цвет из палитры Гаммы")
            return
        # Устанавливаем флаг, что была нажата кнопка "Применить"
        self.applied = True
        self.dialog.destroy()
    
    def cancel(self):
        """Закрывает диалог без выбора"""
        self.selected_color = None
        self.applied = False
        self.dialog.destroy()

