"""
Диалог таблицы палитры Гаммы
Показывает все цвета с названиями, RGB и номерами
Только для просмотра (редактирование отключено)
Использует подход из gamma_color_picker.py
"""
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from color.gamma_palette import get_gamma_palette


class GammaPaletteTable:
    """Диалог таблицы палитры Гаммы"""
    
    def __init__(self, parent):
        """
        Args:
            parent: Родительское окно
        """
        self.parent = parent
        self.gamma_palette = get_gamma_palette()
        self.dialog = None
        self.item_colors = {}  # Связь item_id -> (r, g, b)
        self.item_to_color_info = {}  # Связь item_id -> color_info
        self.all_colors = []
    
    def show(self):
        """Показывает таблицу палитры Гаммы"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Таблица палитры Гамма (Gamma)")
        self.dialog.geometry("800x533")
        self.dialog.transient(self.parent)
        
        # Центрируем окно
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        # Основной контейнер
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Поиск
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="Поиск:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search_change)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40)
        search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Информация о количестве цветов
        info_label = ttk.Label(search_frame, text="")
        info_label.pack(side=tk.RIGHT, padx=5)
        self.info_label = info_label
        
        # Контейнер для Treeview
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Вертикальная прокрутка
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Горизонтальная прокрутка
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Таблица - добавляем отдельную колонку "Цвет"
        columns = ('№', 'Цвет', 'Gamma', 'RGB', 'DMC', 'Название', 'HEX')
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings', 
                           yscrollcommand=lambda *args: (vsb.set(*args), self._update_colors()),
                           xscrollcommand=lambda *args: (hsb.set(*args), self._update_colors()),
                           height=20,
                           selectmode='browse')
        
        vsb.config(command=lambda *args: (tree.yview(*args), self._update_colors()))
        hsb.config(command=tree.xview)
        
        # Настройка колонок
        tree.heading('№', text='№')
        tree.heading('Цвет', text='Цвет')
        tree.heading('Gamma', text='Gamma')
        tree.heading('RGB', text='RGB')
        tree.heading('DMC', text='DMC')
        tree.heading('Название', text='Название')
        tree.heading('HEX', text='HEX')
        
        tree.column('№', width=60, anchor=tk.CENTER)
        tree.column('Цвет', width=120, anchor=tk.CENTER)
        tree.column('Gamma', width=100, anchor=tk.CENTER)
        tree.column('RGB', width=120, anchor=tk.CENTER)
        tree.column('DMC', width=100, anchor=tk.CENTER)
        tree.column('Название', width=300, anchor=tk.W)
        tree.column('HEX', width=120, anchor=tk.CENTER)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree = tree
        
        # Редактирование отключено - двойной клик не привязан
        
        # Canvas будет создан динамически для колонки "Цвет"
        self.color_canvas = None
        
        # Загружаем данные с обработкой ошибок
        try:
            self.all_colors = self.gamma_palette.get_all_colors()
            if not self.all_colors:
                messagebox.showwarning("Предупреждение", 
                    f"Палитра Гаммы не загружена или пуста.\nФайл: {self.gamma_palette.excel_path}")
                self.all_colors = []
            else:
                self.display_colors(self.all_colors)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить палитру Гаммы:\n{str(e)}")
            try:
                from utils.logger import setup_logger
                import traceback
                logger = setup_logger(__name__)
                logger.error(f"Не удалось загрузить палитру Гаммы: {str(e)}\n{traceback.format_exc()}")
            except:
                pass
            self.all_colors = []
        
        # Принудительно вызываем закрашивание после загрузки
        def force_draw():
            if self.dialog and self.dialog.winfo_exists():
                self.dialog.update_idletasks()
                if self.tree:
                    self.tree.update_idletasks()
                    self._draw_color_cells_rgb_only()
        
        if self.dialog and self.tree:
            self.dialog.update_idletasks()
            self.tree.update_idletasks()
            force_draw()
            self.dialog.after(50, force_draw)
            self.dialog.after(150, force_draw)
            self.dialog.after(300, force_draw)
        
        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Обновить", 
                  command=self.reload_palette).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Закрыть", 
                  command=self.on_close).pack(side=tk.RIGHT, padx=5)
        
        # Устанавливаем фокус на поиск
        search_entry.focus()
        
        # Обработчик закрытия окна
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def on_close(self):
        """Обработчик закрытия окна"""
        self.dialog.destroy()
    
    def reload_palette(self):
        """Перезагружает палитру из файла"""
        try:
            # Перезагружаем палитру
            self.gamma_palette.load_palette()
            self.all_colors = self.gamma_palette.get_all_colors()
            if not self.all_colors:
                messagebox.showwarning("Предупреждение", "Палитра не загружена или пуста.")
            else:
                self.display_colors(self.all_colors)
                messagebox.showinfo("Успех", "Палитра перезагружена из файла.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при перезагрузке палитры:\n{str(e)}")
    
    def on_search_change(self, *args):
        """Обработчик изменения поискового запроса"""
        query = self.search_var.get()
        if query:
            results = self.gamma_palette.search_colors(query)
        else:
            results = self.all_colors
        
        self.display_colors(results)
    
    def _update_colors(self):
        """Обновляет отображение закрашенных ячеек"""
        if self.dialog and self.dialog.winfo_exists():
            self.dialog.after(50, self._draw_color_cells_rgb_only)
    
    def _draw_color_cells_rgb_only(self):
        """Закрашивает ячейки колонки 'Цвет' RGB цветом"""
        if not hasattr(self, 'tree') or self.tree is None:
            return
        
        children = self.tree.get_children()
        if not children:
            if self.dialog and self.dialog.winfo_exists():
                self.dialog.after(200, self._draw_color_cells_rgb_only)
            return
        
        try:
            # Вычисляем позицию колонки "Цвет"
            num_width = self.tree.column('№', 'width')
            color_width = self.tree.column('Цвет', 'width')
            color_x = num_width
            
            # Создаем canvas для колонки "Цвет", если его еще нет
            if self.color_canvas is None:
                self.color_canvas = tk.Canvas(self.tree.master, highlightthickness=0)
                
                # Делаем Canvas прозрачным для событий мыши
                def pass_through(event):
                    self.tree.event_generate('<Button-1>', x=event.x + color_x, y=event.y)
                    return "break"
                
                self.color_canvas.bind('<Button-1>', pass_through)
                self.color_canvas.bind('<Double-1>', pass_through)
                self.color_canvas.configure(cursor='')
                
                # Привязываем обновление
                def on_tree_configure(event):
                    self._update_colors()
                
                self.tree.bind('<Configure>', on_tree_configure)
                self.color_canvas.bind('<Configure>', lambda e: self._update_colors())
            
            # Получаем высоту заголовков
            header_height = 25
            try:
                if children:
                    first_item = children[0]
                    bbox_first = self.tree.bbox(first_item)
                    if bbox_first:
                        header_height = bbox_first[1]
            except:
                pass
            
            # Размещаем canvas в области колонки "Цвет", начиная после заголовков
            tree_height = self.tree.winfo_height()
            if tree_height > 1:
                self.color_canvas.place(in_=self.tree, x=color_x, y=header_height, width=color_width, 
                                       height=tree_height - header_height)
            
            # Удаляем предыдущие заливки
            self.color_canvas.delete('color_cell')
            
            # Закрашиваем ячейки "Цвет"
            for item_id in children:
                if item_id in self.item_colors:
                    r, g, b = self.item_colors[item_id]
                    
                    try:
                        bbox = self.tree.bbox(item_id, 'Цвет')
                        if bbox:
                            x, y, width, height = bbox
                            # Координаты относительно canvas
                            canvas_x = x - color_x
                            if canvas_x < 0:
                                canvas_x = 0
                            
                            # Y координата относительно canvas (вычитаем высоту заголовков)
                            canvas_y = y - header_height
                            if canvas_y < 0:
                                continue  # Пропускаем, если ячейка в области заголовков
                            
                            # Рисуем цветной прямоугольник, занимающий большую часть ячейки
                            margin = 3
                            rect_width = width - (margin * 2)
                            rect_height = height - (margin * 2)
                            
                            self.color_canvas.create_rectangle(
                                canvas_x + margin, canvas_y + margin,
                                canvas_x + margin + rect_width, canvas_y + margin + rect_height,
                                fill=f"#{r:02x}{g:02x}{b:02x}",
                                outline='black',
                                width=1,
                                tags='color_cell'
                            )
                    except (ValueError, TypeError, KeyError):
                        # Пропускаем цвета с None или некорректными значениями
                        pass
        
        except Exception as e:
            print(f"Ошибка при отрисовке цветов: {e}")
    
    def display_colors(self, colors):
        """Отображает цвета в таблице"""
        if not self.tree:
            return
        
        # Очищаем таблицу
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.item_colors = {}
        self.item_to_color_info = {}
        
        # Заполняем таблицу
        for idx, color_info in enumerate(colors):
            try:
                rgb = color_info.get('rgb')
                
                # Обрабатываем случай, когда RGB пустой (None)
                if rgb is None:
                    r, g, b = None, None, None
                    rgb_text = 'N/A'
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
                    rgb_text = f"({r}, {g}, {b})"
                
                name = color_info.get('name', 'N/A') or 'N/A'
                dmc = color_info.get('dmc', 'N/A') or 'N/A'
                gamma = color_info.get('gamma', 'N/A') or 'N/A'
                
                # Номер цвета (индекс + 1)
                original_index = color_info.get('index', idx)
                color_number = original_index + 1
                
                # Вставляем данные
                item_id = self.tree.insert('', tk.END, values=(
                    color_number,
                    '',  # Колонка "Цвет" - будет закрашена на Canvas
                    gamma,
                    rgb_text,  # RGB - только текст
                    dmc,
                    name,
                    hex_color
                ))
                
                # Сохраняем цвет для отрисовки (только если RGB не None)
                if rgb is not None:
                    self.item_colors[item_id] = (r, g, b)
                self.item_to_color_info[item_id] = color_info
            except Exception as e:
                print(f"Ошибка при отображении цвета {idx}: {e}")
                continue
        
        # Обновляем информацию о количестве
        self.info_label.config(text=f"Найдено: {len(colors)} из {len(self.all_colors)}")
        
        # Обновляем Canvas и закрашиваем ячейки цветом
        if self.tree and self.dialog:
            self.tree.update_idletasks()
            self.dialog.after(100, self._draw_color_cells_rgb_only)
            self.dialog.after(200, self._draw_color_cells_rgb_only)
    