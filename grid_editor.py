import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser, ttk
from PIL import Image, ImageTk
import numpy as np
import os
from utils.license_manager import LicenseManager, LicenseDialog
from utils.help_text import get_help_text
# Новые модули
from color.palette_manager import PaletteManager
from color.palette_ui import PaletteUI
from export.oxs_exporter import export_to_oxs as export_oxs
from core.image_processor import ImageProcessor
from core.grid_manager import GridManager
from core.state_manager import StateManager
from core.selection_manager import SelectionManager
from core.display_manager import DisplayManager
from core.image_file_manager import ImageFileManager
from core.paint_operations import PaintOperations
from core.cell_upscaling import CellUpscaling
from ui.canvas_handler import CanvasHandler
from ui.paint_panel import PaintPanel
from ui.grid_panel import GridPanel
from ui.fragment_panel import FragmentPanel
from ui.view_control_panel import ViewControlPanel
from ui.menu_bar import MenuBar
from ui.footer_panel import FooterPanel
from tools.pencil_tool import PencilTool
from tools.eraser_tool import EraserTool
from tools.eyedropper_tool import EyedropperTool
from tools.selection_tool import SelectionTool
from tools.cursor_tool import CursorTool
from tools.ruler_tool import RulerTool
from tools.line_paint_tool import LinePaintTool
from project.project_manager import ProjectManager
from utils.license_utils import LicenseUtils
from utils.help_dialog import HelpDialog
from utils.grid_settings import GridSettings
from utils.ui_utils import UIUtils
from utils.tool_manager import ToolManager
from utils.version_utils import get_app_name_with_version
from core.view_manager import ViewManager
from core.undo_redo_manager import UndoRedoManager
from core.grid_operations import GridOperations
from core.grid_builder import GridBuilder
from ui.dialogs import ImageDialogs
from ui.project_dialogs import ProjectDialogs

class GridEditor:
    def __init__(self, root):
        self.root = root
        self.root.title(get_app_name_with_version())
        self.root.geometry("1200x800")
        
        # Устанавливаем иконку приложения
        try:
            from utils.path_utils import get_resource_path
            icon_path = get_resource_path("static/pixel_17431878.png")
            if os.path.exists(icon_path):
                # Загружаем изображение и устанавливаем как иконку
                icon_image = Image.open(icon_path)
                icon_photo = ImageTk.PhotoImage(icon_image)
                self.root.iconphoto(False, icon_photo)
                # Сохраняем ссылку, чтобы изображение не удалялось сборщиком мусора
                self.root.icon_image = icon_photo
        except Exception as e:
            # Если не удалось установить иконку, продолжаем без неё
            print(f"Не удалось установить иконку: {e}")
        
        # Устанавливаем минимальный размер, максимальный размер не ограничиваем
        self.root.minsize(800, 600)
        # Разворачиваем окно на весь экран при запуске
        try:
            self.root.state('zoomed')  # Для Windows
        except:
            # Для Linux/Mac используем альтернативный способ
            self.root.attributes('-zoomed', True)
        
        # Переменные
        self.image = None
        self.image_path = None
        self.display_image = None
        self.photo = None
        self.original_image = None  # Оригинальное изображение без закрашивания
        # Линии сетки будут инициализированы через grid_manager
        self.selected_line = None
        self.selected_line_type = None  # 'v' для вертикальных, 'h' для горизонтальных
        self.fragmented_image = None  # Фрагментированное изображение
        self.palette = None  # Палитра цветов
        self.selected_color = None  # Выбранный цвет из палитры
        self.current_project_path = None  # Путь к текущему проекту (для быстрого сохранения)
        self.project_name = None  # Название проекта (для создания файлов)
        self.project_article = None  # Артикул проекта (для создания файлов)
        self.qr_url = None  # Ссылка для QR-кода (для создания файлов)
        self.paint_mode = False  # Режим закрашивания
        self.paint_tool = 'pencil'  # Инструмент закрашивания: 'pencil' (карандаш) или 'eraser' (резинка)
        self.eraser_size = 1  # Размер резинки: 1 (1x1), 4 (4x4), 8 (8x8), 16 (16x16)
        self.pencil_size = 1  # Размер карандаша: 1 (1x1), 4 (4x4), 8 (8x8)
        self.tool_buttons = {}  # Словарь кнопок инструментов
        self.last_painted_cell = None  # Последняя закрашенная ячейка (для карандаша)
        self.pencil_drawing = False  # Флаг активного рисования карандашом
        self.eyedropper_mode = False  # Режим пипетки
        self.view_mode = 1  # Режим просмотра: 1 - базовый, 2 - без исходного, 3 - только закрашенные
        self.painted_cells = {}  # Словарь закрашенных ячеек: {(col, row): color}
        self.undo_history = []  # История для отмены действий: список состояний (image, painted_cells)
        self.redo_history = []  # История для повтора действий
        self.state_saved_for_action = False  # Флаг, что состояние сохранено для текущего действия
        self.selection_mode = False  # Режим выделения области
        self.selection_start = None  # Начальная ячейка выделения (col, row)
        self.selection_end = None  # Конечная ячейка выделения (col, row)
        self.selected_regions = []  # Список выделенных связанных областей (каждая область - set ячеек)
        self.show_grid = True  # Показывать ли сетку
        self.grid_line_width = 1  # Толщина линий сетки
        self.grid_color = (180, 80, 80)  # Цвет линий сетки (приглушенный красный для обычных линий)
        self.grid_color_horizontal = (180, 80, 80)  # Цвет горизонтальных линий сетки (приглушенный красный для обычных линий)
        self.background_color = '#FEFEFE'  # Цвет задней подложки (почти белый, чтобы белый можно было закрашивать)
        self.normalize_cell_sizes = True  # Нормализация размеров ячеек (включено по умолчанию, но замедляет отрисовку)
        self.image_opacity = 1.0  # Прозрачность первой загруженной картинки (0.0 - полностью прозрачная, 1.0 - непрозрачная)
        self.grid_locked = False  # Флаг блокировки сетки после получения палитры
        
        # Переменные для зума и панорамирования
        self.zoom = 1.0
        self.zoom_click_mode = None  # Режим клика лупой: None / 'in' / 'out'
        self.pan_x = 0
        self.pan_y = 0
        self.pan_active = False
        self.last_pan_x = 0
        self.last_pan_y = 0
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.right_click_pos = None
        
        # Инициализируем переменную шага сдвига сетки (будет переопределена в UI, если UI уже создан)
        if not hasattr(self, 'grid_shift_step'):
            self.grid_shift_step = tk.IntVar(value=1)
        
        # Переменная для упорядочивания палитры по Гамме (по умолчанию включено)
        if not hasattr(self, 'sort_palette_by_gamma_var'):
            self.sort_palette_by_gamma_var = tk.BooleanVar(value=True)
        
        # Менеджер лицензий
        self.license_manager = LicenseManager()
        
        # Менеджер палитры
        self.palette_manager = PaletteManager()
        
        # Обработчик изображений
        self.image_processor = ImageProcessor()
        
        # Менеджер сетки
        self.grid_manager = GridManager()
        # Синхронизируем линии сетки с менеджером (используем ссылки на списки)
        self.vertical_lines = self.grid_manager.vertical_lines
        self.horizontal_lines = self.grid_manager.horizontal_lines
        
        # Менеджер состояний (undo/redo)
        self.state_manager = StateManager()
        # Синхронизируем историю с менеджером (используем ссылки на списки)
        self.undo_history = self.state_manager.undo_history
        self.redo_history = self.state_manager.redo_history

        # Инструменты рисования
        self.palette_ui = PaletteUI(self)
        self.tools = {
            'cursor': CursorTool(self),
            'pencil': PencilTool(self),
            'eraser': EraserTool(self),
            'eyedropper': EyedropperTool(self),
            'selection': SelectionTool(self),
            'ruler': RulerTool(self),
            'line_paint': LinePaintTool(self),
        }
        self.active_tool = None
        
        # Менеджер проектов
        self.project_manager = ProjectManager()
        
        # Менеджер выделения
        self.selection_manager = SelectionManager(self)
        
        # Менеджер отображения
        self.display_manager = DisplayManager(self)
        
        # Менеджер файлов изображений
        self.image_file_manager = ImageFileManager(self)
        
        # Обработчик событий canvas
        self.canvas_handler = CanvasHandler(self)
        
        # Операции закрашивания
        self.paint_operations = PaintOperations(self)
        
        # Операции укрупнения ячеек
        self.cell_upscaling = CellUpscaling(self)
        
        # Утилиты
        self.license_utils = LicenseUtils(self)
        self.help_dialog = HelpDialog(self)
        self.grid_settings = GridSettings(self)
        self.ui_utils = UIUtils(self)
        self.tool_manager = ToolManager(self)
        
        # Менеджеры
        self.view_manager = ViewManager(self)
        self.undo_redo_manager = UndoRedoManager(self)
        self.grid_operations = GridOperations(self)
        self.grid_builder = GridBuilder(self)
        
        # UI-диалоги
        self.image_dialogs = ImageDialogs(self)
        self.project_dialogs = ProjectDialogs(self)
        
        # Создаем интерфейс
        self.create_ui()
        
        # Обновляем состояние кнопок отмены/возврата при запуске
        self.root.after(100, self.update_undo_redo_buttons)
        
        # Проверяем лицензию при запуске
        self.check_license_on_startup()
        
        # Обновляем меню лицензии в зависимости от состояния
        self.update_license_menu()
        
        # Привязываем клавиши
        self.root.bind('<Left>', self.move_line_left)
        self.root.bind('<Right>', self.move_line_right)
        self.root.bind('<Up>', self.move_line_up)
        self.root.bind('<Down>', self.move_line_down)
        self.root.bind('<plus>', self.add_line)
        self.root.bind('<equal>', self.add_line)  # + без Shift
        self.root.bind('<minus>', self.remove_line)
        self.root.bind('<KP_Add>', self.add_line)  # + на цифровой клавиатуре
        self.root.bind('<KP_Subtract>', self.remove_line)  # - на цифровой клавиатуре
        self.root.bind('<KeyPress-i>', self.toggle_eyedropper)  # I для пипетки
        self.root.bind('<KeyPress-I>', self.toggle_eyedropper)  # I для пипетки (с Shift)
        self.root.bind('<KeyPress-b>', self.activate_pencil)  # B для карандаша
        self.root.bind('<KeyPress-B>', self.activate_pencil)  # B для карандаша (с Shift)
        self.root.bind('<KeyPress-e>', self.activate_eraser)  # E для резинки
        self.root.bind('<KeyPress-E>', self.activate_eraser)  # E для резинки (с Shift)
        self.root.bind('<Control-1>', lambda e: self.set_view_mode(1))  # Ctrl+1 - базовый режим
        self.root.bind('<Control-2>', lambda e: self.set_view_mode(2))  # Ctrl+2 - без исходного
        self.root.bind('<Control-3>', lambda e: self.set_view_mode(3))  # Ctrl+3 - только закрашенные
        self.root.bind('<Control-4>', lambda e: self.set_view_mode(4))  # Ctrl+4 - два окна
        self.root.bind('<Control-d>', lambda e: self.set_view_mode(4))  # Ctrl+D - два окна
        self.root.bind('<Control-D>', lambda e: self.set_view_mode(4))  # Ctrl+D - два окна (с Shift)
        self.root.bind('<Control-s>', lambda e: self.save_project_quick())  # Ctrl+S - быстрое сохранение
        self.root.bind('<Control-S>', lambda e: self.save_project_quick())  # Ctrl+S - быстрое сохранение (с Shift)
        self.root.bind('<Control-z>', lambda e: self.undo_last_action())  # Ctrl+Z - отмена
        self.root.bind('<Control-Z>', lambda e: self.undo_last_action())  # Ctrl+Z - отмена (с Shift)
        self.root.bind('<Control-y>', lambda e: self.redo_last_action())  # Ctrl+Y - повтор
        
        # Универсальная обработка Ctrl+C, Ctrl+X, Ctrl+V, Ctrl+A для полей ввода (любая раскладка — по keycode)
        _text_widgets = (tk.Entry, tk.Text, ttk.Entry, ttk.Spinbox, ttk.Combobox)

        def handle_copy(event):
            """Копирование (Ctrl+C), физическая клавиша C на любой раскладке"""
            widget = event.widget
            if isinstance(widget, _text_widgets):
                try:
                    widget.event_generate('<<Copy>>')
                except Exception:
                    pass
            return "break"

        def handle_cut(event):
            """Вырезание (Ctrl+X), физическая клавиша X на любой раскладке"""
            widget = event.widget
            if isinstance(widget, _text_widgets):
                try:
                    widget.event_generate('<<Cut>>')
                except Exception:
                    pass
            return "break"

        def handle_paste(event):
            """Вставка (Ctrl+V), работает с любой раскладкой клавиатуры"""
            widget = event.widget
            if isinstance(widget, _text_widgets):
                try:
                    widget.event_generate('<<Paste>>')
                except Exception:
                    pass
            return "break"
        
        def handle_select_all(event):
            """Выделить всё (Ctrl+A)"""
            widget = event.widget
            if isinstance(widget, _text_widgets):
                try:
                    if isinstance(widget, tk.Text):
                        widget.tag_add(tk.SEL, '1.0', tk.END)
                        widget.mark_set(tk.INSERT, '1.0')
                        widget.see(tk.INSERT)
                    else:
                        widget.select_range(0, tk.END)
                        widget.icursor(tk.END)
                except Exception:
                    pass
            return "break"
        
        def handle_control_key(event):
            """Универсальный обработчик Ctrl+клавиша в полях ввода (keycode = физическая клавиша Windows)"""
            # 67=C, 88=X, 86=V, 65=A — одинаковы при EN и RU
            if event.keycode == 67:
                return handle_copy(event)
            if event.keycode == 88:
                return handle_cut(event)
            if event.keycode == 86:
                return handle_paste(event)
            if event.keycode == 65:
                return handle_select_all(event)
            return None
        
        # Привязываем обработчик для Ctrl+клавиша
        self.root.bind_class('Entry', '<Control-KeyPress>', handle_control_key)
        self.root.bind_class('TEntry', '<Control-KeyPress>', handle_control_key)
        self.root.bind_class('Text', '<Control-KeyPress>', handle_control_key)
        self.root.bind_class('TSpinbox', '<Control-KeyPress>', handle_control_key)
        self.root.bind_class('TCombobox', '<Control-KeyPress>', handle_control_key)
        self.root.bind('<Control-Y>', lambda e: self.redo_last_action())  # Ctrl+Y - повтор (с Shift)
        
        # Дополнительные привязки для русской раскладки (по keycode)
        # Эти привязки работают параллельно с существующими
        def _hotkey_focus_uses_delete_backspace():
            """True, если фокус в поле ввода/списке — Delete/Backspace не трогаем сетку."""
            w = self.root.focus_get()
            if w is None:
                return False
            cls = w.winfo_class()
            return cls in (
                'Entry', 'Text', 'TEntry', 'TSpinbox', 'TCombobox', 'Spinbox',
                'Treeview', 'Listbox',
            )

        def handle_universal_hotkeys(event):
            """Универсальный обработчик горячих клавиш по keycode (работает с любой раскладкой)"""
            keycode = event.keycode
            state = getattr(event, 'state', 0)
            ctrl_pressed = (state & 0x4) != 0
            
            # Обработка комбинаций с Control
            if ctrl_pressed:
                if keycode == 68:  # D/В - два окна
                    self.set_view_mode(4)
                    return "break"
                elif keycode == 83:  # S/Ы - сохранение
                    self.save_project_quick()
                    return "break"
                elif keycode == 90:  # Z/Я - отмена
                    self.undo_last_action()
                    return "break"
                elif keycode == 89:  # Y/Н - повтор
                    self.redo_last_action()
                    return "break"
            else:
                # Delete / Backspace — удалить выбранную линию сетки (как кнопка «−»), любая раскладка
                # Windows: VK_BACK=8, VK_DELETE=46
                if keycode in (8, 46):
                    if not _hotkey_focus_uses_delete_backspace():
                        self.remove_line(None)
                        return "break"
                    return None
                # Обработка одиночных клавиш
                if keycode == 73:  # I/Ш - пипетка
                    self.toggle_eyedropper()
                    return "break"
                elif keycode == 66:  # B/И - карандаш
                    self.activate_pencil()
                    return "break"
                elif keycode == 69:  # E/У - резинка
                    self.activate_eraser()
                    return "break"
        
        # Привязываем универсальный обработчик (срабатывает после существующих)
        self.root.bind('<KeyPress>', handle_universal_hotkeys, add='+')
        
        # Сохраняем обработчик для последующей привязки к canvas
        self._universal_hotkeys_handler = handle_universal_hotkeys
        
        self.root.focus_set()
    
    def create_ui(self):
        # Создаем меню-бар
        self.menu_bar = MenuBar(self, self.root)
        
        # Панель управления просмотром (кнопки) - под меню, на всю ширину
        self.view_control_panel = ViewControlPanel(self, self.root)
        
        # Контейнер для левой и правой панелей
        content_frame = tk.Frame(self.root)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 0))
        
        # Левая панель с настройками (не расширяется до футера)
        left_frame = tk.Frame(content_frame, width=248, bg='lightgray')
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        left_frame.pack_propagate(False)
        
        # Настройки сетки
        self.grid_panel = GridPanel(self, left_frame)
        
        # Настройки фрагментации
        self.fragment_panel = FragmentPanel(self, left_frame)
        
        # Настройки закрашивания / инструменты
        self.paint_panel = PaintPanel(self, left_frame)
        
        # Создаем info_label скрытым (используется в коде, но панель не показываем)
        self.info_label = tk.Label(left_frame, text="")
        # Не показываем label, но он нужен для совместимости с кодом
        
        # Правая панель с изображением (не расширяется до футера)
        right_frame = tk.Frame(content_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Фрейм для палитры цветов (увеличена высота для отображения количества и номера Гаммы)
        self.palette_frame = tk.Frame(right_frame, bg='lightgray', height=80)
        self.palette_frame.pack(fill=tk.X, pady=(0, 5))
        self.palette_frame.pack_propagate(False)
        self.palette_canvas = None  # Canvas для палитры
        
        # Фрейм для canvas(ов) - может содержать один или два canvas
        self.canvas_container = tk.Frame(right_frame)
        self.canvas_container.pack(fill=tk.BOTH, expand=True)
        
        # Фрейм с кнопками для пустого состояния (когда изображение не загружено)
        self.empty_state_frame = tk.Frame(self.canvas_container, bg='lightgray')
        self.empty_state_frame.pack(fill=tk.BOTH, expand=True)
        
        # Центрируем кнопки
        button_container = tk.Frame(self.empty_state_frame, bg='lightgray')
        button_container.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Кнопка "Загрузить картинку"
        load_image_btn = tk.Button(
            button_container, 
            text="Загрузить картинку", 
            command=self.open_image,
            font=('Arial', 14),
            bg='#4CAF50',
            fg='white',
            width=20,
            height=2,
            relief=tk.RAISED,
            bd=3,
            cursor='hand2'
        )
        load_image_btn.pack(pady=10)
        
        # Кнопка "Загрузить проект"
        load_project_btn = tk.Button(
            button_container, 
            text="Загрузить проект", 
            command=self.load_project,
            font=('Arial', 14),
            bg='#2196F3',
            fg='white',
            width=20,
            height=2,
            relief=tk.RAISED,
            bd=3,
            cursor='hand2'
        )
        load_project_btn.pack(pady=10)
        
        # Canvas для изображения (основной) - изначально скрыт
        self.canvas = tk.Canvas(self.canvas_container, bg=self.background_color, cursor='crosshair')
        
        # Canvas для исходного изображения (для режима 4)
        self.original_canvas = None
        self.original_photo = None
        
        # Привязываем клики на canvas
        self.canvas.bind('<Button-1>', self.canvas_handler.on_canvas_click)
        self.canvas.bind('<ButtonRelease-1>', self.canvas_handler.on_canvas_release)
        self.canvas.bind('<Motion>', self.canvas_handler.on_canvas_motion)
        
        # Привязываем Ctrl+Z и Ctrl+Y на canvas для отмены/повтора
        self.canvas.bind('<Control-z>', lambda e: self.undo_last_action())
        self.canvas.bind('<Control-Z>', lambda e: self.undo_last_action())
        self.canvas.bind('<Control-y>', lambda e: self.redo_last_action())
        self.canvas.bind('<Control-Y>', lambda e: self.redo_last_action())
        
        # Привязываем универсальные горячие клавиши для canvas (для русской раскладки)
        if hasattr(self, '_universal_hotkeys_handler'):
            self.canvas.bind('<KeyPress>', self._universal_hotkeys_handler, add='+')
            self.canvas.bind('<Control-KeyPress>', self._universal_hotkeys_handler, add='+')
        
        # Создаем футер (в самом конце)
        self.footer_panel = FooterPanel(self, self.root)
        self.canvas.bind('<Configure>', self.canvas_handler.on_canvas_configure)
        
        # При первом запуске показываем фрейм с кнопками, если изображение не загружено
        if self.image is None:
            self.update_display()
        
        # Привязываем зум колесом мыши
        self.canvas.bind('<MouseWheel>', self.canvas_handler.on_mousewheel)  # Windows
        self.canvas.bind('<Button-4>', self.canvas_handler.on_mousewheel)    # Linux
        self.canvas.bind('<Button-5>', self.canvas_handler.on_mousewheel)    # Linux
        
        # Привязываем панорамирование правой кнопкой мыши
        self.canvas.bind('<Button-3>', self.canvas_handler.on_pan_start)  # Правая кнопка мыши
        self.canvas.bind('<B3-Motion>', self.canvas_handler.on_pan_motion)
        self.canvas.bind('<ButtonRelease-3>', self.canvas_handler.on_pan_release)
        
        # Обновляем информацию в футере
        self.update_footer_info()
        
        # Инициализируем выделение кнопки режима 1
        if hasattr(self, 'view_mode_buttons') and len(self.view_mode_buttons) > 0:
            self.view_mode_buttons[0].config(bg='lightblue', relief=tk.SUNKEN)
    
    def create_tooltip(self, widget, text):
        """Прокси к UIUtils для совместимости."""
        return self.ui_utils.create_tooltip(widget, text)
    
    def update_footer_info(self):
        """Прокси к UIUtils для совместимости."""
        return self.ui_utils.update_footer_info()
    
    def check_license_on_startup(self):
        """Прокси к LicenseUtils для совместимости."""
        return self.license_utils.check_license_on_startup()
    
    def update_license_menu(self):
        """Прокси к LicenseUtils для совместимости."""
        return self.license_utils.update_license_menu()
    
    def show_license_status(self):
        """Прокси к LicenseUtils для совместимости."""
        return self.license_utils.show_license_status()
    
    def show_license_dialog(self):
        """Прокси к LicenseUtils для совместимости."""
        return self.license_utils.show_license_dialog()
    
    def show_language_menu(self):
        """Заглушка для меню выбора языка"""
        from tkinter import messagebox
        messagebox.showinfo("Язык", "Выбор языка будет доступен в будущих версиях")
    
    def show_about(self):
        """Показывает информацию о программе"""
        from tkinter import messagebox
        from utils.version_utils import get_app_name_with_version, get_version
        
        app_name = get_app_name_with_version()
        version = get_version()
        about_text = f"{app_name}\n\n"
        about_text += f"Версия: {version}\n\n"
        about_text += f"Разработчики:\nZhdanov V.Y., Zhdanov I.Y.\n\n"
        about_text += f"© 2026"
        messagebox.showinfo("О программе", about_text)
    
    def show_instructions(self):
        """Прокси к HelpDialog для совместимости."""
        return self.help_dialog.show_instructions()
    
    def open_image(self):
        """Прокси к ImageFileManager для совместимости."""
        return self.image_file_manager.open_image()
    
    def on_grid_params_changed(self):
        """Вызывается при изменении параметров сетки (шаг, количество линий)"""
        # Сбрасываем фрагментированное изображение и палитру при изменении сетки
        if self.fragmented_image is not None:
            self.fragmented_image = None
        if self.palette is not None and len(self.palette) > 0:
            self.palette = None
        if self.painted_cells:
            self.painted_cells = {}
        # Очищаем палитру в UI
        if self.palette_canvas is not None:
            for widget in self.palette_frame.winfo_children():
                widget.destroy()
            self.palette_canvas = None
        # Разблокируем сетку при изменении параметров
        if hasattr(self, 'grid_locked'):
            self.grid_locked = False
            # Включаем кнопки управления сеткой обратно
            if hasattr(self, 'grid_panel'):
                self.grid_panel.enable_grid_controls()
        # Обновляем отображение
        if self.image is not None:
            self.update_display()
    
    def build_grid(self):
        """Прокси к GridBuilder для совместимости."""
        return self.grid_builder.build_grid()
    
    def shift_grid_left(self):
        """Прокси к GridBuilder для совместимости."""
        return self.grid_builder.shift_grid_left()
    
    def shift_grid_right(self):
        """Прокси к GridBuilder для совместимости."""
        return self.grid_builder.shift_grid_right()
    
    def shift_grid_up(self):
        """Прокси к GridBuilder для совместимости."""
        return self.grid_builder.shift_grid_up()
    
    def shift_grid_down(self):
        """Прокси к GridBuilder для совместимости."""
        return self.grid_builder.shift_grid_down()
    
    def shift_grid_left_keyboard(self):
        """Сдвигает сетку влево с клавиатуры (без предупреждений)"""
        # Проверяем, заблокирована ли сетка
        if hasattr(self, 'grid_locked') and self.grid_locked:
            return
        
        if not self.vertical_lines or self.image is None:
            return
        
        shift = self.grid_shift_step.get() if hasattr(self, 'grid_shift_step') else 1
        if self.grid_manager.shift_grid_left(self.image.width, shift):
            self.vertical_lines = self.grid_manager.vertical_lines
            self.update_display()
            self.update_footer_info()
    
    def shift_grid_right_keyboard(self):
        """Сдвигает сетку вправо с клавиатуры (без предупреждений)"""
        # Проверяем, заблокирована ли сетка
        if hasattr(self, 'grid_locked') and self.grid_locked:
            return
        
        if not self.vertical_lines or self.image is None:
            return
        
        shift = self.grid_shift_step.get() if hasattr(self, 'grid_shift_step') else 1
        if self.grid_manager.shift_grid_right(self.image.width, shift):
            self.vertical_lines = self.grid_manager.vertical_lines
            self.update_display()
            self.update_footer_info()
    
    def shift_grid_up_keyboard(self):
        """Сдвигает сетку вверх с клавиатуры (без предупреждений)"""
        # Проверяем, заблокирована ли сетка
        if hasattr(self, 'grid_locked') and self.grid_locked:
            return
        
        if not self.horizontal_lines or self.image is None:
            return
        
        shift = self.grid_shift_step.get() if hasattr(self, 'grid_shift_step') else 1
        if self.grid_manager.shift_grid_up(self.image.height, shift):
            self.horizontal_lines = self.grid_manager.horizontal_lines
            self.update_display()
            self.update_footer_info()
    
    def shift_grid_down_keyboard(self):
        """Сдвигает сетку вниз с клавиатуры (без предупреждений)"""
        # Проверяем, заблокирована ли сетка
        if hasattr(self, 'grid_locked') and self.grid_locked:
            return
        
        if not self.horizontal_lines or self.image is None:
            return
        
        shift = self.grid_shift_step.get() if hasattr(self, 'grid_shift_step') else 1
        if self.grid_manager.shift_grid_down(self.image.height, shift):
            self.horizontal_lines = self.grid_manager.horizontal_lines
            self.update_display()
            self.update_footer_info()
    
    
    def update_display(self):
        """Прокси к DisplayManager для совместимости."""
        return self.display_manager.update_display()
    
    def canvas_to_image_coords(self, canvas_x, canvas_y):
        """Прокси к CanvasHandler для совместимости."""
        return self.canvas_handler.canvas_to_image_coords(canvas_x, canvas_y)
    
    def display_palette(self):
        """Прокси к PaletteUI для совместимости."""
        return self.palette_ui.display_palette()

    def on_palette_click(self, event):
        """Прокси к PaletteUI для совместимости."""
        return self.palette_ui.on_palette_click(event)

    def on_palette_double_click(self, event):
        """Прокси к PaletteUI для совместимости."""
        return self.palette_ui.on_palette_double_click(event)

    def on_palette_right_click(self, event):
        """Прокси к PaletteUI для совместимости."""
        return self.palette_ui.on_palette_right_click(event)

    def select_all_cells_with_color(self, color_idx):
        """Прокси к PaletteUI для совместимости."""
        return self.palette_ui.select_all_cells_with_color(color_idx)

    def clear_selected_cells(self):
        """Прокси к PaletteUI для совместимости."""
        return self.palette_ui.clear_selected_cells()

    def find_connected_regions(self, cells_set):
        """Прокси к PaletteUI для совместимости."""
        return self.palette_ui._find_connected_regions(cells_set)

    def delete_color_from_palette(self, color_idx):
        """Прокси к PaletteUI для совместимости."""
        return self.palette_ui.delete_color_from_palette(color_idx)

    def replace_with_closest_color(self, color_idx):
        """Прокси к PaletteUI для совместимости."""
        return self.palette_ui.replace_with_closest_color(color_idx)

    def toggle_grid_visibility_menu(self):
        """Прокси к GridSettings для совместимости."""
        return self.grid_settings.toggle_grid_visibility_menu()
    
    def choose_background_color(self):
        """Прокси к GridSettings для совместимости."""
        return self.grid_settings.choose_background_color()
    
    def get_background_color_rgb(self):
        """Прокси к GridSettings для совместимости."""
        return self.grid_settings.get_background_color_rgb()
    
    def set_grid_line_width(self):
        """Прокси к GridSettings для совместимости."""
        return self.grid_settings.set_grid_line_width()
    
    def set_grid_color(self):
        """Открывает диалог выбора цвета сетки."""
        if self.image is None:
            messagebox.showwarning("Предупреждение", "Сначала откройте изображение!")
            return
        
        # Показываем диалог выбора цвета
        color = colorchooser.askcolor(
            title="Выбор цвета сетки",
            color=self.grid_color
        )
        
        if color[1] is not None:  # color[1] - это hex строка, color[0] - это RGB tuple
            # Преобразуем hex в RGB
            hex_color = color[1].lstrip('#')
            rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            self.grid_color = rgb
            self.grid_color_horizontal = rgb  # Используем тот же цвет для горизонтальных линий
            
            # Обновляем отображение
            self.update_display()
            
            app_name = get_app_name_with_version()
            messagebox.showinfo(f"Успех - {app_name}", f"Цвет сетки изменен на RGB: {rgb}")
    
    def delete_all_grid(self):
        """Удаляет всю сетку (все линии)"""
        if self.image is None:
            messagebox.showwarning("Предупреждение", "Сначала откройте изображение!")
            return
        
        # Сохраняем состояние перед удалением
        self.save_state()
        
        # Сбрасываем сетку
        self.grid_manager.reset()
        
        # Синхронизируем линии
        self.vertical_lines = self.grid_manager.vertical_lines
        self.horizontal_lines = self.grid_manager.horizontal_lines
        
        # Сбрасываем выделение
        self.selected_line = None
        self.selected_line_type = None
        
        # Сбрасываем фрагментированное изображение и палитру при изменении сетки
        self.fragmented_image = None
        self.palette = None
        self.selected_color = None
        for widget in self.palette_frame.winfo_children():
            widget.destroy()
        self.palette_canvas = None
        
        # Разблокируем сетку при удалении
        if hasattr(self, 'grid_locked'):
            self.grid_locked = False
            # Включаем кнопки управления сеткой обратно
            if hasattr(self, 'grid_panel'):
                self.grid_panel.enable_grid_controls()
        
        # Обновляем отображение
        self.update_display()
        self.update_footer_info()
        
        app_name = get_app_name_with_version()
        messagebox.showinfo(f"Успех - {app_name}", "Вся сетка удалена")
    
    def toggle_normalize_cell_sizes(self):
        """Переключает нормализацию размеров ячеек"""
        self.normalize_cell_sizes = not self.normalize_cell_sizes
        self.update_display()
        # Обновляем пункт меню
        if hasattr(self, 'grid_menu'):
            menu_index = None
            for i in range(self.grid_menu.index('end') + 1):
                try:
                    label = self.grid_menu.entryconfig(i, 'label')[4]
                    if 'Нормализация размеров ячеек' in label:
                        menu_index = i
                        break
                except:
                    continue
            if menu_index is not None:
                status = "ВКЛ" if self.normalize_cell_sizes else "ВЫКЛ"
                self.grid_menu.entryconfig(menu_index, label=f"Нормализация размеров ячеек: {status}")
    
    def update_background_color_button(self):
        """Прокси к GridSettings для совместимости."""
        return self.grid_settings.update_background_color_button()
    
    def toggle_grid_visibility(self):
        """Прокси к GridSettings для совместимости."""
        return self.grid_settings.toggle_grid_visibility()
    
    def toggle_grid_with_button(self):
        """Прокси к GridSettings для совместимости."""
        return self.grid_settings.toggle_grid_with_button()
    
    def update_grid_button_appearance(self):
        """Прокси к GridSettings для совместимости."""
        return self.grid_settings.update_grid_button_appearance()
    
    def deactivate_active_tool(self):
        """Прокси к ToolManager для совместимости."""
        return self.tool_manager.deactivate_active_tool()

    def activate_tool(self, tool):
        """Прокси к ToolManager для совместимости."""
        return self.tool_manager.activate_tool(tool)
    
    def update_tool_buttons(self):
        """Прокси к ToolManager для совместимости."""
        return self.tool_manager.update_tool_buttons()
    
    def toggle_selection_mode(self):
        """Прокси к ToolManager для совместимости."""
        return self.tool_manager.toggle_selection_mode()
    
    def update_selection_button_appearance(self):
        """Обновляет внешний вид кнопки выделения области"""
        if hasattr(self, 'view_control_panel'):
            self.view_control_panel.update_selection_button_appearance()
    
    def handle_selection_click(self, img_x, img_y):
        """Обрабатывает клик в режиме выделения области"""
        if 'selection' in self.tools:
            self.tools['selection'].on_mouse_down(img_x, img_y)
    
    def fill_selected_area(self):
        """Прокси к SelectionManager для совместимости."""
        return self.selection_manager.fill_selected_area()
    
    def clear_selected_area(self):
        """Прокси к SelectionManager для совместимости."""
        return self.selection_manager.clear_selected_area()
    
    def is_single_pixel(self, col, row, color):
        """Проверяет, является ли пиксель одиночным (не имеет соседей того же цвета)"""
        # Проверяем 8 соседей
        neighbors = [
            (col - 1, row - 1), (col, row - 1), (col + 1, row - 1),
            (col - 1, row),                     (col + 1, row),
            (col - 1, row + 1), (col, row + 1), (col + 1, row + 1)
        ]
        
        for neighbor_col, neighbor_row in neighbors:
            if (neighbor_col, neighbor_row) in self.painted_cells:
                neighbor_color = self.painted_cells[(neighbor_col, neighbor_row)]
                # Сравниваем цвета (RGB кортежи)
                if neighbor_color == color:
                    return False  # Найден сосед с тем же цветом
        return True  # Нет соседей с тем же цветом - одиночный пиксель
    
    def get_neighbor_color(self, col, row):
        """Получает цвет соседних ячеек для заполнения удаляемого пикселя из палитры"""
        # Проверяем наличие палитры
        if self.palette is None or len(self.palette) == 0:
            # Если палитры нет, возвращаем белый цвет
            return (255, 255, 255)
        
        # Проверяем 8 соседей
        neighbors = [
            (col - 1, row - 1), (col, row - 1), (col + 1, row - 1),
            (col - 1, row),                     (col + 1, row),
            (col - 1, row + 1), (col, row + 1), (col + 1, row + 1)
        ]
        
        neighbor_colors = []
        for neighbor_col, neighbor_row in neighbors:
            # Проверяем, что сосед в пределах сетки
            if (neighbor_row >= 0 and neighbor_row < len(self.horizontal_lines) - 1 and
                neighbor_col >= 0 and neighbor_col < len(self.vertical_lines) - 1):
                # Сначала проверяем закрашенные ячейки
                if (neighbor_col, neighbor_row) in self.painted_cells:
                    neighbor_color = self.painted_cells[(neighbor_col, neighbor_row)]
                    # Нормализуем цвет в tuple
                    if isinstance(neighbor_color, np.ndarray):
                        neighbor_colors.append(tuple(neighbor_color[:3]))
                    elif isinstance(neighbor_color, (list, tuple)):
                        neighbor_colors.append(tuple(neighbor_color[:3]))
                    else:
                        neighbor_colors.append(tuple(neighbor_color[:3]))
                else:
                    # Если ячейка не закрашена, берем цвет из текущего изображения
                    if self.image is not None:
                        n_x1 = self.vertical_lines[neighbor_col]
                        n_x2 = self.vertical_lines[neighbor_col + 1]
                        n_y1 = self.horizontal_lines[neighbor_row]
                        n_y2 = self.horizontal_lines[neighbor_row + 1]
                        
                        # Получаем средний цвет ячейки из текущего изображения
                        img_array = np.array(self.image)
                        cell_region = img_array[n_y1:n_y2, n_x1:n_x2]
                        if cell_region.size > 0:
                            # Берем медиану цветов в ячейке
                            if len(cell_region.shape) == 3:
                                median_color = np.median(cell_region.reshape(-1, cell_region.shape[2]), axis=0)
                                neighbor_colors.append(tuple(median_color[:3].astype(int)))
        
        # Определяем цвет для поиска в палитре
        if neighbor_colors:
            # Используем медиану цветов соседей для более стабильного результата
            neighbor_colors_array = np.array(neighbor_colors)
            median_color = np.median(neighbor_colors_array, axis=0).astype(np.float32)
        else:
            # Если соседей нет, берем цвет из текущего изображения в этой ячейке
            if self.image is not None:
                x1 = self.vertical_lines[col]
                x2 = self.vertical_lines[col + 1]
                y1 = self.horizontal_lines[row]
                y2 = self.horizontal_lines[row + 1]
                
                img_array = np.array(self.image)
                cell_region = img_array[y1:y2, x1:x2]
                if cell_region.size > 0:
                    if len(cell_region.shape) == 3:
                        median_color = np.median(cell_region.reshape(-1, cell_region.shape[2]), axis=0).astype(np.float32)
                    else:
                        # Если ничего не найдено, возвращаем первый цвет из палитры
                        return tuple(self.palette[0][:3])
                else:
                    # Если ничего не найдено, возвращаем первый цвет из палитры
                    return tuple(self.palette[0][:3])
            else:
                # Если изображения нет, возвращаем первый цвет из палитры
                return tuple(self.palette[0][:3])
        
        # Находим ближайший цвет в палитре
        palette_colors = self.palette.astype(np.float32)
        
        # Вычисляем расстояния от медианного цвета до каждого цвета палитры
        distances = np.sqrt(np.sum((median_color - palette_colors) ** 2, axis=1))
        closest_idx = np.argmin(distances)
        
        # Возвращаем ближайший цвет из палитры
        closest_color = self.palette[closest_idx]
        if isinstance(closest_color, np.ndarray):
            return tuple(closest_color[:3])
        elif isinstance(closest_color, (list, tuple)):
            return tuple(closest_color[:3])
        else:
            return tuple(closest_color[:3])
    
    def remove_single_pixels_all(self):
        """Прокси к SelectionManager для совместимости."""
        return self.selection_manager.remove_single_pixels_all()
    
    def select_single_pixels_all(self):
        """Прокси к SelectionManager для выделения одиночных пикселей."""
        return self.selection_manager.select_single_pixels_all()
    
    def remove_single_pixels_selection(self):
        """Прокси к SelectionManager для совместимости."""
        return self.selection_manager.remove_single_pixels_selection()
    
    def mirror_selection_2x_horizontal(self):
        """Зеркалирует выделенную область по горизонтали (2-х симметрия)"""
        return self.selection_manager.mirror_selection_2x_horizontal()
    
    def mirror_selection_2x_vertical(self):
        """Зеркалирует выделенную область по вертикали (2-х симметрия)"""
        return self.selection_manager.mirror_selection_2x_vertical()
    
    def mirror_selection_4x(self):
        """Зеркалирует выделенную область в 4 стороны (4-х симметрия)"""
        return self.selection_manager.mirror_selection_4x()
    
    def update_paint_cursor(self):
        """Обновляет курсор в зависимости от инструмента"""
        if self.eyedropper_mode:
            self.canvas.config(cursor='cross')
        elif self.selection_mode:
            self.canvas.config(cursor='tcross')
        elif self.paint_mode:
            if self.paint_tool == 'pencil':
                self.canvas.config(cursor='dotbox')
            elif self.paint_tool == 'eraser':
                self.canvas.config(cursor='circle')  # Курсор резинки
            else:
                self.canvas.config(cursor='spraycan')
        else:
            self.canvas.config(cursor='crosshair')
    
    def set_view_mode(self, mode):
        """Прокси к ViewManager для совместимости."""
        return self.view_manager.set_view_mode(mode)
    
    def _setup_dual_view(self):
        """Настраивает два фрейма для режима 4 (текущее + исходное)"""
        if self.original_canvas is None:
            # Создаем второй canvas для исходного изображения
            self.original_canvas = tk.Canvas(self.canvas_container, bg=self.background_color, cursor='arrow')
            self.original_canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
            
            # Привязываем зум и панорамирование для второго canvas
            self.original_canvas.bind('<MouseWheel>', self._on_original_canvas_wheel)
            self.original_canvas.bind('<Button-4>', self._on_original_canvas_wheel)
            self.original_canvas.bind('<Button-5>', self._on_original_canvas_wheel)
            self.original_canvas.bind('<Button-3>', self._on_original_pan_start)
            self.original_canvas.bind('<B3-Motion>', self._on_original_pan_motion)
            self.original_canvas.bind('<ButtonRelease-3>', self._on_original_pan_release)
            
            # Инициализируем переменные для зума и панорамирования второго canvas
            if not hasattr(self, 'original_zoom'):
                self.original_zoom = 1.0
            if not hasattr(self, 'original_pan_x'):
                self.original_pan_x = 0
            if not hasattr(self, 'original_pan_y'):
                self.original_pan_y = 0
            if not hasattr(self, 'original_pan_active'):
                self.original_pan_active = False
        
        # Показываем оба canvas
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.original_canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
    
    def _setup_single_view(self):
        """Настраивает один фрейм для режимов 1-3"""
        if self.original_canvas is not None:
            # Скрываем второй canvas
            self.original_canvas.pack_forget()
        
        # Основной canvas занимает все пространство
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    def _on_original_canvas_wheel(self, event):
        """Обработчик зума для второго canvas"""
        if self.original_image is None:
            return
        
        # Определяем направление зума
        if event.delta > 0 or event.num == 4:
            self.original_zoom *= 1.1
        else:
            self.original_zoom /= 1.1
        
        # Ограничиваем зум
        self.original_zoom = max(0.1, min(10.0, self.original_zoom))
        
        self._update_original_canvas()
    
    def _on_original_pan_start(self, event):
        """Начало панорамирования для второго canvas"""
        self.original_pan_active = True
        if not hasattr(self, 'original_last_pan_x'):
            self.original_last_pan_x = event.x
            self.original_last_pan_y = event.y
        else:
            self.original_last_pan_x = event.x
            self.original_last_pan_y = event.y
    
    def _on_original_pan_motion(self, event):
        """Движение при панорамировании для второго canvas"""
        if not self.original_pan_active:
            return
        
        dx = event.x - self.original_last_pan_x
        dy = event.y - self.original_last_pan_y
        
        self.original_pan_x += dx
        self.original_pan_y += dy
        
        self.original_last_pan_x = event.x
        self.original_last_pan_y = event.y
        
        self._update_original_canvas()
    
    def _on_original_pan_release(self, event):
        """Окончание панорамирования для второго canvas"""
        self.original_pan_active = False
    
    def _update_original_canvas(self):
        """Обновляет отображение исходного изображения на втором canvas"""
        if self.original_canvas is None or self.original_image is None:
            return
        
        canvas_width = self.original_canvas.winfo_width()
        canvas_height = self.original_canvas.winfo_height()
        
        if canvas_width > 1 and canvas_height > 1:
            # Базовый масштаб для вписывания в canvas
            base_scale_w = canvas_width / self.original_image.width
            base_scale_h = canvas_height / self.original_image.height
            base_scale = min(base_scale_w, base_scale_h)
            
            # Применяем зум
            scale = base_scale * self.original_zoom
            scale = max(0.1, min(10.0, scale))
            
            new_width = int(self.original_image.width * scale)
            new_height = int(self.original_image.height * scale)
            
            display_copy = self.original_image.resize((new_width, new_height), Image.Resampling.NEAREST)
            self.original_photo = ImageTk.PhotoImage(display_copy)
            
            # Очищаем canvas
            self.original_canvas.delete("all")
            
            # Вычисляем позицию с учетом панорамирования
            img_x = canvas_width // 2 + self.original_pan_x
            img_y = canvas_height // 2 + self.original_pan_y
            
            self.original_canvas.create_image(img_x, img_y, image=self.original_photo, anchor=tk.CENTER)
    
    def save_state(self):
        """Прокси к UndoRedoManager для совместимости."""
        return self.undo_redo_manager.save_state()
    
    def undo_last_action(self, event=None):
        """Прокси к UndoRedoManager для совместимости."""
        result = self.undo_redo_manager.undo_last_action(event)
        self.update_undo_redo_buttons()
        return result
    
    def redo_last_action(self, event=None):
        """Прокси к UndoRedoManager для совместимости."""
        result = self.undo_redo_manager.redo_last_action(event)
        self.update_undo_redo_buttons()
        return result
    
    def update_undo_redo_buttons(self):
        """Обновляет состояние кнопок отмены и возврата"""
        if hasattr(self, 'undo_button') and hasattr(self, 'redo_button'):
            # Проверяем доступность отмены и возврата
            can_undo = self.state_manager.can_undo()
            can_redo = self.state_manager.can_redo()
            
            # Обновляем состояние кнопок
            self.undo_button.config(state='normal' if can_undo else 'disabled')
            self.redo_button.config(state='normal' if can_redo else 'disabled')
    
    def toggle_eyedropper(self, event=None):
        """Переключает режим пипетки (горячая клавиша I)"""
        if self.eyedropper_mode:
            # Выключаем пипетку
            self.deactivate_active_tool()
            self.paint_mode = False
            self.paint_tool = None
            self.update_tool_buttons()
            self.update_paint_cursor()
            self.info_label.config(text="Режим выбора линий")
        else:
            # Включаем пипетку через activate_tool
            self.activate_tool('eyedropper')
    
    def activate_pencil(self, event=None):
        """Активирует режим карандаша (горячая клавиша B)"""
        # Активируем карандаш через activate_tool (он уже выключает выделение и пипетку)
        self.activate_tool('pencil')
    
    def activate_eraser(self, event=None):
        """Активирует режим резинки (горячая клавиша E)"""
        # Активируем резинку через activate_tool (он уже выключает выделение и пипетку)
        self.activate_tool('eraser')
    
    def show_eraser_size_menu(self, event=None):
        """Показывает меню выбора размера резинки"""
        menu = tk.Menu(self.root, tearoff=0)
        
        # Добавляем пункты меню для каждого размера
        sizes = [1, 4, 8, 16]
        for size in sizes:
            label = f"x{size}"
            # Помечаем текущий выбранный размер
            checkmark = "✓ " if self.eraser_size == size else ""
            menu.add_command(
                label=f"{checkmark}{label}",
                command=lambda s=size: self.set_eraser_size(s)
            )
        
        # Показываем меню рядом с кнопкой
        if event:
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()
        else:
            # Если событие не передано, показываем меню под кнопкой
            button = self.tool_buttons.get('eraser')
            if button:
                x = button.winfo_rootx()
                y = button.winfo_rooty() + button.winfo_height()
                try:
                    menu.tk_popup(x, y)
                finally:
                    menu.grab_release()
    
    def set_eraser_size(self, size):
        """Устанавливает размер резинки и активирует инструмент"""
        self.eraser_size = size
        self.activate_tool('eraser')
        # Обновляем подсказку кнопки
        if 'eraser' in self.tool_buttons:
            size_text = f"x{size}"
            self.create_tooltip(self.tool_buttons['eraser'], f"Резинка ({size_text}) (E)")
    
    def show_pencil_size_menu(self, event=None):
        """Показывает меню выбора размера карандаша"""
        menu = tk.Menu(self.root, tearoff=0)
        
        # Добавляем пункты меню для каждого размера
        sizes = [1, 4, 8]
        for size in sizes:
            label = f"x{size}"
            # Помечаем текущий выбранный размер
            checkmark = "✓ " if self.pencil_size == size else ""
            menu.add_command(
                label=f"{checkmark}{label}",
                command=lambda s=size: self.set_pencil_size(s)
            )
        
        # Показываем меню рядом с кнопкой
        if event:
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()
        else:
            # Если событие не передано, показываем меню под кнопкой
            button = self.tool_buttons.get('pencil')
            if button:
                x = button.winfo_rootx()
                y = button.winfo_rooty() + button.winfo_height()
                try:
                    menu.tk_popup(x, y)
                finally:
                    menu.grab_release()
    
    def show_zoom_menu(self, event=None):
        """Меню масштаба: приблизить / отдалить (кнопка лупы на панели)."""
        if self.image is None:
            messagebox.showinfo("Масштаб", "Сначала откройте изображение.")
            return
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(
            label="Приблизить",
            command=lambda: self.canvas_handler.set_zoom_click_mode(True),
        )
        menu.add_command(
            label="Отдалить",
            command=lambda: self.canvas_handler.set_zoom_click_mode(False),
        )
        button = getattr(self, 'zoom_view_button', None)
        if button:
            x = button.winfo_rootx()
            y = button.winfo_rooty() + button.winfo_height()
        elif event:
            x, y = event.x_root, event.y_root
        else:
            x = self.root.winfo_rootx() + 50
            y = self.root.winfo_rooty() + 50
        try:
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()
    
    def set_pencil_size(self, size):
        """Устанавливает размер карандаша и активирует инструмент"""
        self.pencil_size = size
        self.activate_tool('pencil')
        # Обновляем подсказку кнопки
        if 'pencil' in self.tool_buttons:
            size_text = f"x{size}"
            self.create_tooltip(self.tool_buttons['pencil'], f"Карандаш ({size_text}) (B)")
    
    def get_cell_indices(self, img_x, img_y):
        """Возвращает индексы ячейки (col, row) для заданных координат изображения"""
        # Используем grid_manager для определения ячейки
        return self.grid_manager.get_cell_from_position(img_x, img_y)
    
    def pick_color_from_cell(self, img_x, img_y):
        """Выбирает цвет из ячейки и выделяет его в палитре"""
        if len(self.vertical_lines) < 2 or len(self.horizontal_lines) < 2:
            messagebox.showwarning("Предупреждение", "Сначала постройте сетку!")
            return
        
        # Находим индексы ячейки
        col, row = self.get_cell_indices(img_x, img_y)
        
        if col is None or row is None:
            messagebox.showwarning("Предупреждение", "Клик вне ячейки сетки!")
            return
        
        if col < 0 or row < 0:
            messagebox.showwarning("Предупреждение", "Клик вне ячейки сетки!")
            return
        
        # Проверяем, закрашена ли ячейка - если да, берем цвет из палитры
        cell_key = (col, row)
        if cell_key in self.painted_cells:
            # Ячейка закрашена - берем цвет из палитры
            cell_color = self.painted_cells[cell_key]
            
            # Нормализуем цвет
            normalized_color = self.palette_ui._normalize_color(cell_color)
            if normalized_color is None:
                # Если не удалось нормализовать, используем логику из изображения
                pass
            else:
                # Ищем этот цвет в палитре
                if self.palette is not None and len(self.palette) > 0:
                    palette_colors = self.palette.astype(np.float32)
                    cell_color_array = np.array(normalized_color, dtype=np.float32)
                    
                    # Вычисляем расстояния до всех цветов палитры
                    distances = np.sqrt(np.sum((palette_colors - cell_color_array) ** 2, axis=1))
                    closest_idx = np.argmin(distances)
                    
                    # Выбираем этот цвет из палитры
                    self.selected_color = self.palette[closest_idx]
                    
                    # Выделяем цвет в палитре
                    self.highlight_color_in_palette(closest_idx)
                    
                    self.info_label.config(text=f"Выбран цвет из ячейки [{col}, {row}]\nRGB: {tuple(self.selected_color)}")
                    return
                else:
                    # Если палитры нет, используем нормализованный цвет
                    self.selected_color = normalized_color
                    self.info_label.config(text=f"Выбран цвет из ячейки [{col}, {row}]\nRGB: {tuple(self.selected_color)}\n(Палитра не создана)")
                    return
        
        # Если ячейка не закрашена, берем цвет из изображения (старая логика)
        x1 = self.vertical_lines[col]
        x2 = self.vertical_lines[col + 1]
        y1 = self.horizontal_lines[row]
        y2 = self.horizontal_lines[row + 1]
        
        img_array = np.array(self.image)
        if img_array.shape[2] == 4:
            cell = img_array[y1:y2, x1:x2, :3]
        else:
            cell = img_array[y1:y2, x1:x2]
        
        if cell.size == 0:
            return
        
        # Вычисляем средний цвет ячейки
        cell_flat = cell.reshape(-1, 3)
        picked_color = np.mean(cell_flat, axis=0).astype(np.uint8)
        
        # Ищем ближайший цвет в палитре
        if self.palette is not None and len(self.palette) > 0:
            palette_colors = self.palette.astype(np.float32)
            picked_color_float = picked_color.astype(np.float32)
            
            # Вычисляем расстояния до всех цветов палитры
            distances = np.sqrt(np.sum((palette_colors - picked_color_float) ** 2, axis=1))
            closest_idx = np.argmin(distances)
            
            # Выбираем этот цвет
            self.selected_color = self.palette[closest_idx]
            
            # Выделяем цвет в палитре
            self.highlight_color_in_palette(closest_idx)
            
            self.info_label.config(text=f"Выбран цвет из ячейки [{col}, {row}]\nRGB: {tuple(self.selected_color)}")
        else:
            # Если палитры нет, просто сохраняем цвет
            self.selected_color = picked_color
            self.info_label.config(text=f"Выбран цвет из ячейки [{col}, {row}]\nRGB: {tuple(self.selected_color)}\n(Палитра не создана)")
    
    def highlight_color_in_palette(self, color_idx):
        """Прокси к PaletteUI для совместимости."""
        return self.palette_ui.highlight_color_in_palette(color_idx)

    def paint_cell_at_position(self, img_x, img_y):
        """Закрашивает ячейки в области размером pencil_size x pencil_size выбранным цветом"""
        if self.selected_color is None:
            return
        
        # Проверяем, что цвет не почти белый (почти белый - это цвет подложки)
        if isinstance(self.selected_color, (list, tuple, np.ndarray)):
            color_rgb = tuple(self.selected_color[:3]) if len(self.selected_color) >= 3 else tuple(self.selected_color)
        else:
            color_rgb = (self.selected_color, self.selected_color, self.selected_color) if isinstance(self.selected_color, (int, np.integer)) else (255, 255, 255)
        
        # Проверяем, что цвет не почти белый (254, 254, 254) - цвет подложки
        # Теперь белый (255, 255, 255) можно закрашивать
        if len(color_rgb) >= 3 and color_rgb[:3] == (254, 254, 254):
            return  # Не закрашиваем почти белый цвет (цвет подложки)
        
        # Определяем в какую ячейку попал клик
        if len(self.vertical_lines) < 2 or len(self.horizontal_lines) < 2:
            messagebox.showwarning("Предупреждение", "Сначала постройте сетку!")
            return
        
        # Находим индексы центральной ячейки
        center_col, center_row = self.get_cell_indices(img_x, img_y)
        
        if center_col is None or center_row is None:
            return
        
        # Определяем диапазон ячеек для закрашивания на основе pencil_size
        size = self.pencil_size if self.paint_tool == 'pencil' else 1
        num_cols = len(self.vertical_lines) - 1
        num_rows = len(self.horizontal_lines) - 1
        
        # Вычисляем смещение (половина размера)
        # Для нечетных размеров центр точно в центре, для четных - немного смещен влево/вверх
        offset = size // 2
        
        # Определяем диапазон столбцов и строк для закрашивания
        # Для размера size нужно size ячеек, центрированных вокруг center
        start_col = max(0, center_col - offset)
        end_col = min(num_cols, start_col + size)
        start_row = max(0, center_row - offset)
        end_row = min(num_rows, start_row + size)
        
        # Проверяем, не закрашена ли уже центральная ячейка (для карандаша)
        current_cell = (center_col, center_row)
        if self.paint_tool == 'pencil' and self.last_painted_cell == current_cell:
            return  # Пропускаем, если уже закрасили
        
        # Сохраняем состояние перед закрашиванием
        # Для карандаша - только перед первой ячейкой
        if self.paint_tool == 'pencil' and not self.state_saved_for_action:
            # Для карандаша сохраняем состояние только перед первой ячейкой
            self.save_state()
            self.state_saved_for_action = True
        
        # Закрашиваем все ячейки в области
        img_array = np.array(self.image)
        cells_painted = []
        for col in range(start_col, end_col):
            for row in range(start_row, end_row):
                # Координаты ячейки
                x1 = self.vertical_lines[col]
                x2 = self.vertical_lines[col + 1]
                y1 = self.horizontal_lines[row]
                y2 = self.horizontal_lines[row + 1]
                
                # Обновляем изображение
                if img_array.shape[2] == 4:
                    # Если есть альфа-канал, обновляем только RGB
                    img_array[y1:y2, x1:x2, 0] = self.selected_color[0]
                    img_array[y1:y2, x1:x2, 1] = self.selected_color[1]
                    img_array[y1:y2, x1:x2, 2] = self.selected_color[2]
                else:
                    img_array[y1:y2, x1:x2] = self.selected_color
                
                # Сохраняем информацию о закрашенной ячейке
                cell = (col, row)
                self.painted_cells[cell] = tuple(self.selected_color)
                cells_painted.append(cell)
        
        self.image = Image.fromarray(img_array)
        
        # Автоматически переключаемся на режим 2 при закрашивании
        if self.view_mode == 1:
            self.set_view_mode(2)
        else:
            # Обновляем отображение всегда (как в slicer_2.5)
            self.update_display()
        
        # Сбрасываем фрагментированное изображение, так как исходное изменилось
        self.fragmented_image = None
        
        # Сохраняем последнюю закрашенную ячейку (для карандаша)
        self.last_painted_cell = current_cell
        
        # Обновляем палитру только если не в режиме рисования (чтобы не тормозить при перетаскивании)
        # При перетаскивании палитра будет обновлена после отпускания мыши
        if self.palette is not None and len(self.palette) > 0 and not self.pencil_drawing:
            self.display_palette()
        
        # Обновляем информацию только если не в режиме рисования (чтобы не тормозить)
        if not self.pencil_drawing:
            if size > 1:
                self.info_label.config(text=f"Область [{start_col}-{end_col-1}, {start_row}-{end_row-1}] закрашена ({len(cells_painted)} ячеек)")
            else:
                self.info_label.config(text=f"Ячейка [{center_col}, {center_row}] закрашена")
    
    def erase_cell_at_position(self, img_x, img_y):
        """Стирает закрашенные ячейки в области размером eraser_size x eraser_size, восстанавливая оригинальный цвет"""
        # Определяем в какую ячейку попал клик
        if len(self.vertical_lines) < 2 or len(self.horizontal_lines) < 2:
            messagebox.showwarning("Предупреждение", "Сначала постройте сетку!")
            return
        
        # Находим индексы центральной ячейки
        center_col, center_row = self.get_cell_indices(img_x, img_y)
        
        if center_col is None or center_row is None:
            return
        
        # Определяем диапазон ячеек для стирания на основе eraser_size
        size = self.eraser_size
        num_cols = len(self.vertical_lines) - 1
        num_rows = len(self.horizontal_lines) - 1
        
        # Вычисляем смещение (половина размера)
        # Для нечетных размеров центр точно в центре, для четных - немного смещен влево/вверх
        offset = size // 2
        
        # Определяем диапазон столбцов и строк для стирания
        # Для размера size нужно size ячеек, центрированных вокруг center
        start_col = max(0, center_col - offset)
        end_col = min(num_cols, start_col + size)
        start_row = max(0, center_row - offset)
        end_row = min(num_rows, start_row + size)
        
        # Проверяем, есть ли закрашенные ячейки в области
        cells_to_erase = []
        for col in range(start_col, end_col):
            for row in range(start_row, end_row):
                cell = (col, row)
                if cell in self.painted_cells:
                    cells_to_erase.append(cell)
        
        if not cells_to_erase:
            # Нет закрашенных ячеек в области
            return
        
        # Проверяем, не стираем ли уже эти ячейки (для карандаша-резинки)
        current_cell = (center_col, center_row)
        if self.pencil_drawing and self.last_painted_cell == current_cell:
            return  # Пропускаем, если уже стерли
        
        # Сохраняем состояние перед стиранием
        if not self.pencil_drawing:
            # Для одиночного клика сохраняем состояние перед каждым кликом
            self.save_state()
        elif not self.state_saved_for_action:
            # Для карандаша-резинки сохраняем состояние только перед первой ячейкой
            self.save_state()
            self.state_saved_for_action = True
        
        # Стираем все ячейки в области
        img_array = np.array(self.image)
        for col, row in cells_to_erase:
            # Координаты ячейки
            x1 = self.vertical_lines[col]
            x2 = self.vertical_lines[col + 1]
            y1 = self.horizontal_lines[row]
            y2 = self.horizontal_lines[row + 1]
            
            # Получаем оригинальный цвет из original_image
            if self.original_image is not None:
                original_array = np.array(self.original_image)
                if original_array.shape[2] == 4:
                    original_color = original_array[y1:y2, x1:x2, :3]
                else:
                    original_color = original_array[y1:y2, x1:x2]
            else:
                # Если нет original_image, используем средний цвет из текущего изображения
                if img_array.shape[2] == 4:
                    block = img_array[y1:y2, x1:x2, :3]
                else:
                    block = img_array[y1:y2, x1:x2]
                if block.size > 0:
                    block_flat = block.reshape(-1, 3)
                    original_color = np.median(block_flat, axis=0).astype(np.uint8)
                    original_color = np.tile(original_color, (y2-y1, x2-x1, 1))
                else:
                    original_color = np.zeros((y2-y1, x2-x1, 3), dtype=np.uint8)
            
            # Обновляем изображение
            if img_array.shape[2] == 4:
                # Если есть альфа-канал, обновляем только RGB
                if len(original_color.shape) == 3:
                    img_array[y1:y2, x1:x2, 0] = original_color[:, :, 0]
                    img_array[y1:y2, x1:x2, 1] = original_color[:, :, 1]
                    img_array[y1:y2, x1:x2, 2] = original_color[:, :, 2]
            else:
                img_array[y1:y2, x1:x2] = original_color
            
            # Удаляем информацию о закрашенной ячейке
            del self.painted_cells[(col, row)]
        
        self.image = Image.fromarray(img_array)
        
        # Сохраняем последнюю стертую ячейку (для карандаша-резинки)
        self.last_painted_cell = current_cell
        
        # Обновляем отображение всегда (как в slicer_2.5)
        self.update_display()
        
        # Обновляем палитру только если не в режиме рисования (чтобы не тормозить при перетаскивании)
        # При перетаскивании палитра будет обновлена после отпускания мыши
        if self.palette is not None and len(self.palette) > 0 and not self.pencil_drawing:
            self.display_palette()
        
        # Сохраняем последнюю стертую ячейку (для карандаша-резинки)
        self.last_painted_cell = current_cell
        
        # Обновляем информацию только если не в режиме рисования (чтобы не тормозить)
        if not self.pencil_drawing:
            self.info_label.config(text=f"Ячейка [{col}, {row}] стерта")
    
    def on_canvas_click(self, event):
        """Прокси к CanvasHandler для совместимости."""
        return self.canvas_handler.on_canvas_click(event)
    
    def on_canvas_configure(self, event):
        """Прокси к CanvasHandler для совместимости."""
        return self.canvas_handler.on_canvas_configure(event)
    
    def on_canvas_motion(self, event):
        """Прокси к CanvasHandler для совместимости."""
        return self.canvas_handler.on_canvas_motion(event)
    
    def on_canvas_release(self, event):
        """Прокси к CanvasHandler для совместимости."""
        return self.canvas_handler.on_canvas_release(event)
    
    def on_mousewheel(self, event):
        """Прокси к CanvasHandler для совместимости."""
        return self.canvas_handler.on_mousewheel(event)
    
    def on_pan_start(self, event):
        """Прокси к CanvasHandler для совместимости."""
        return self.canvas_handler.on_pan_start(event)
    
    def on_pan_motion(self, event):
        """Прокси к CanvasHandler для совместимости."""
        return self.canvas_handler.on_pan_motion(event)
    
    def on_pan_release(self, event):
        """Прокси к CanvasHandler для совместимости."""
        return self.canvas_handler.on_pan_release(event)
    
    def move_line_left(self, event):
        """Обрабатывает стрелку влево - перемещает выбранную линию или сдвигает сетку"""
        # Проверяем, заблокирована ли сетка
        if hasattr(self, 'grid_locked') and self.grid_locked:
            return
        
        # Проверяем, не находится ли фокус в поле ввода
        focused_widget = self.root.focus_get()
        if focused_widget and isinstance(focused_widget, (tk.Entry, tk.Spinbox, tk.Text)):
            return  # Игнорируем, если фокус в поле ввода
        
        # Если выбрана линия, перемещаем её, иначе сдвигаем всю сетку
        if self.selected_line is not None and self.selected_line_type:
            return self.grid_operations.move_line_left(event)
        else:
            return self.shift_grid_left_keyboard()
    
    def move_line_right(self, event):
        """Обрабатывает стрелку вправо - перемещает выбранную линию или сдвигает сетку"""
        # Проверяем, заблокирована ли сетка
        if hasattr(self, 'grid_locked') and self.grid_locked:
            return
        
        # Проверяем, не находится ли фокус в поле ввода
        focused_widget = self.root.focus_get()
        if focused_widget and isinstance(focused_widget, (tk.Entry, tk.Spinbox, tk.Text)):
            return  # Игнорируем, если фокус в поле ввода
        
        # Если выбрана линия, перемещаем её, иначе сдвигаем всю сетку
        if self.selected_line is not None and self.selected_line_type:
            return self.grid_operations.move_line_right(event)
        else:
            return self.shift_grid_right_keyboard()
    
    def move_line_up(self, event):
        """Обрабатывает стрелку вверх - перемещает выбранную линию или сдвигает сетку"""
        # Проверяем, заблокирована ли сетка
        if hasattr(self, 'grid_locked') and self.grid_locked:
            return
        
        # Проверяем, не находится ли фокус в поле ввода
        focused_widget = self.root.focus_get()
        if focused_widget and isinstance(focused_widget, (tk.Entry, tk.Spinbox, tk.Text)):
            return  # Игнорируем, если фокус в поле ввода
        
        # Если выбрана линия, перемещаем её, иначе сдвигаем всю сетку
        if self.selected_line is not None and self.selected_line_type:
            return self.grid_operations.move_line_up(event)
        else:
            return self.shift_grid_up_keyboard()
    
    def move_line_down(self, event):
        """Обрабатывает стрелку вниз - перемещает выбранную линию или сдвигает сетку"""
        # Проверяем, заблокирована ли сетка
        if hasattr(self, 'grid_locked') and self.grid_locked:
            return
        
        # Проверяем, не находится ли фокус в поле ввода
        focused_widget = self.root.focus_get()
        if focused_widget and isinstance(focused_widget, (tk.Entry, tk.Spinbox, tk.Text)):
            return  # Игнорируем, если фокус в поле ввода
        
        # Если выбрана линия, перемещаем её, иначе сдвигаем всю сетку
        if self.selected_line is not None and self.selected_line_type:
            return self.grid_operations.move_line_down(event)
        else:
            return self.shift_grid_down_keyboard()
    
    def add_line(self, event):
        """Прокси к GridOperations для совместимости."""
        return self.grid_operations.add_line(event)
    
    def remove_line(self, event):
        """Прокси к GridOperations для совместимости."""
        return self.grid_operations.remove_line(event)
    
    def delete_palette(self):
        """Удаляет палитру и сбрасывает закрашенные ячейки."""
        if self.palette is None and not self.painted_cells:
            from tkinter import messagebox
            messagebox.showinfo("Информация", "Палитра уже пуста")
            return
        from tkinter import messagebox
        if not messagebox.askokcancel("Удалить палитру", "Удалить палитру и сбросить все закрашенные ячейки?\nСетка останется на месте."):
            return
        self.fragmented_image = None
        self.palette = None
        self.painted_cells = {}
        self.selected_color = None
        if hasattr(self, 'palette_manager') and self.palette_manager is not None:
            self.palette_manager.set_palette(None)
        for widget in self.palette_frame.winfo_children():
            widget.destroy()
        self.palette_canvas = None
        if self.original_image is not None:
            self.image = self.original_image.copy()
        if hasattr(self, 'grid_locked') and self.grid_locked:
            self.grid_locked = False
            if hasattr(self, 'grid_panel'):
                self.grid_panel.enable_grid_controls()
        self.update_display()
        self.update_footer_info()
        from utils.version_utils import get_app_name_with_version
        messagebox.showinfo(f"Успех - {get_app_name_with_version()}", "Палитра удалена")
    
    def fragment_image(self):
        """Прокси к PaintOperations для совместимости."""
        # Убираем фокус с полей ввода
        self.canvas.focus_set()
        return self.paint_operations.fragment_image()
    
    def auto_paint_cells(self, palette=None, rgb_array=None):
        """Прокси к PaintOperations для совместимости."""
        # Убираем фокус с полей ввода
        self.canvas.focus_set()
        return self.paint_operations.auto_paint_cells(palette, rgb_array)
    
    def upscale_cells(self, method='mean'):
        """Показывает диалог выбора метода и выполняет укрупнение ячеек"""
        # Показываем диалог выбора метода
        self.image_dialogs.show_upscale_method_dialog()
    
    def export_to_oxs(self):
        """Экспортирует схему в формат OXS (Ursa Software MacStitch/WinStitch)"""
        # Используем новый модуль экспорта
        export_oxs(
            self.fragmented_image,
            self.palette,
            self.painted_cells,
            self.vertical_lines,
            self.horizontal_lines,
            self.image_path,
            self.root
        )
    
    def save_image(self):
        """Прокси к ImageFileManager для совместимости."""
        return self.image_file_manager.save_image()
    
    def save_image_without_grid(self):
        """Прокси к ImageFileManager для совместимости."""
        return self.image_file_manager.save_image_without_grid()
    
    def crop_image(self):
        """Прокси к ImageDialogs для совместимости."""
        return self.image_dialogs.crop_image()
    
    def save_project(self):
        """Прокси к ProjectDialogs для совместимости."""
        return self.project_dialogs.save_project()
    
    def save_project_quick(self, event=None):
        """Быстрое сохранение проекта (Ctrl+S). Сохраняет в текущий файл или вызывает диалог, если проект не сохранен."""
        if self.image is None:
            messagebox.showwarning("Предупреждение", "Нет изображения для сохранения проекта")
            return
        
        # Если проект уже сохранен, сохраняем в тот же файл
        if self.current_project_path:
            try:
                self.project_dialogs.save_project_to_path(self.current_project_path)
                return
            except Exception as e:
                # Если сохранение не удалось, вызываем диалог
                pass
        
        # Если проект не сохранен, вызываем диалог сохранения
        return self.project_dialogs.save_project()
    
    def load_project(self):
        """Прокси к ProjectDialogs для совместимости."""
        return self.project_dialogs.load_project()
    
    def create_all_files(self):
        """Создает все файлы из фрагментированного изображения (схема, органайзер, главная страница, Excel)"""
        from export.file_creator import create_files_from_fragmented_image
        from export.config_dialog import ConfigDialog
        from tkinter import messagebox
        
        # Проверяем наличие изображения
        if self.image is None:
            messagebox.showwarning("Предупреждение", 
                                 "Сначала откройте изображение!")
            return
        
        # Проверяем наличие сетки
        if len(self.vertical_lines) < 2 or len(self.horizontal_lines) < 2:
            messagebox.showwarning("Предупреждение", 
                                 "Сначала постройте сетку!")
            return
        
        # Проверяем наличие палитры
        if self.palette is None or len(self.palette) == 0:
            messagebox.showwarning("Предупреждение", 
                                 "Палитра не создана!\n"
                                 "Нажмите 'Получить палитру' после построения сетки.")
            return
        
        # Определяем название проекта из сохраненных настроек проекта или имени файла
        if self.project_name:
            saved_project_name = self.project_name
        elif self.image_path:
            saved_project_name = os.path.splitext(os.path.basename(self.image_path))[0]
        else:
            saved_project_name = "project"
        
        # Показываем диалог настроек (передаем информацию о сетке для автоматического расчета размера)
        # Передаем сохраненные значения из проекта, если они есть
        config_dialog = ConfigDialog(
            self.root, 
            project_name=saved_project_name,
            project_article=self.project_article,
            qr_url=self.qr_url,
            vertical_lines=self.vertical_lines,
            horizontal_lines=self.horizontal_lines
        )
        config_settings = config_dialog.show()
        
        # Если пользователь отменил, выходим
        if config_settings is None:
            return
        
        # Обновляем палитру с актуальным количеством закрашенных ячеек
        # Это необходимо, чтобы учитывались все изменения (удаленные ячейки и т.д.)
        if self.palette is not None and len(self.palette) > 0:
            self.display_palette()
        
        # Используем артикул из настроек для формирования пути к папке проекта
        # Если артикул не указан, используем saved_project_name (название файла)
        article_name = config_settings.get('article', '').strip()
        if not article_name:
            article_name = saved_project_name
        
        # Используем fragmented_image если есть, иначе используем текущее изображение
        # (которое уже обработано - закрашено или фрагментировано)
        image_to_use = self.fragmented_image if self.fragmented_image is not None else self.image
        
        # Создаем файлы (передаем root окно для отображения прогресса и настройки)
        success = create_files_from_fragmented_image(
            fragmented_image=image_to_use,
            palette=self.palette,
            vertical_lines=self.vertical_lines,
            horizontal_lines=self.horizontal_lines,
            image_path=self.image_path,
            output_folder=None,  # Будет использована папка task/<article_name>
            project_name=saved_project_name,  # Используем saved_project_name для имен файлов
            parent_window=self.root,  # Передаем root для отображения прогресса
            config_settings=config_settings,  # Передаем настройки конфигурации
            article_name=article_name,  # Передаем артикул для формирования пути к папке
            painted_cells=self.painted_cells  # Передаем закрашенные ячейки для OXS
        )
        
        # Сообщение об успехе уже показывается в диалоге прогресса
        if not success:
            # Ошибка также показывается в диалоге прогресса
            pass
    
    def show_gamma_palette_table(self):
        """Показывает таблицу палитры Гаммы"""
        from ui.gamma_palette_table import GammaPaletteTable
        table = GammaPaletteTable(self.root)
        table.show()
    
    def show_project_settings(self):
        """Показывает диалог дополнительных настроек проекта"""
        from ui.project_settings_dialog import ProjectSettingsDialog
        dialog = ProjectSettingsDialog(self.root, self.project_name, self.project_article, self.qr_url)
        result = dialog.show()
        if result:
            self.project_name = result.get('project_name', '')
            self.project_article = result.get('project_article', '')
            self.qr_url = result.get('qr_url', '')
            # Обновляем футер после изменения артикула и названия проекта
            self.update_footer_info()
    
    def create_main_page_only(self):
        """Создает только главную страницу из выбранного изображения"""
        import os
        import sys
        from tkinter import filedialog, messagebox, ttk
        
        try:
            from export.slicer_utils.create_a5_main_from_image import create_a5_main_page_from_image
        except ImportError:
            from utils.path_utils import get_base_path
            base_path = get_base_path()
            slicer_utils_path = os.path.join(base_path, 'export', 'slicer_utils')
            if slicer_utils_path not in sys.path:
                sys.path.insert(0, slicer_utils_path)
            from create_a5_main_from_image import create_a5_main_page_from_image
        
        # Создаем диалог для ввода артикула с чекбоксом saga/paradise
        dialog = tk.Toplevel(self.root)
        dialog.title("Артикул")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Переменные
        article_var = tk.StringVar(value=self.project_article if self.project_article else "")
        use_saga_paradise_var = tk.BooleanVar(value=True)  # По умолчанию включено
        
        # Фрейм для полей
        main_frame = ttk.Frame(dialog, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Поле артикула
        ttk.Label(main_frame, text="Артикул:").grid(row=0, column=0, sticky=tk.W, pady=5)
        article_entry = ttk.Entry(main_frame, textvariable=article_var, width=30)
        article_entry.grid(row=0, column=1, sticky=tk.EW, pady=5, padx=5)
        main_frame.columnconfigure(1, weight=1)
        
        # Чекбокс saga/paradise
        saga_checkbox = ttk.Checkbutton(main_frame, text="saga/paradise", variable=use_saga_paradise_var)
        saga_checkbox.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Кнопки
        button_frame = tk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0))
        
        result = {"article": None, "use_saga_paradise": False}
        
        def ok_clicked():
            article = article_var.get().strip()
            if not article:
                messagebox.showwarning("Предупреждение", "Артикул не указан!", parent=dialog)
                return
            result["article"] = article
            result["use_saga_paradise"] = use_saga_paradise_var.get()
            dialog.destroy()
        
        def cancel_clicked():
            dialog.destroy()
        
        ok_button = tk.Button(button_frame, text="ОК", command=ok_clicked, width=10)
        ok_button.pack(side=tk.LEFT, padx=5)
        cancel_button = tk.Button(button_frame, text="Отмена", command=cancel_clicked, width=10)
        cancel_button.pack(side=tk.LEFT, padx=5)
        
        # Фокус на поле ввода
        article_entry.focus()
        article_entry.select_range(0, tk.END)
        
        # Обработка Enter
        article_entry.bind('<Return>', lambda e: ok_clicked())
        
        # Размер по содержимому и центрирование
        dialog.update_idletasks()
        w = dialog.winfo_reqwidth()
        h = dialog.winfo_reqheight()
        x = (dialog.winfo_screenwidth() // 2) - (w // 2)
        y = (dialog.winfo_screenheight() // 2) - (h // 2)
        dialog.geometry(f"{w}x{h}+{x}+{y}")
        
        # Ждем закрытия диалога
        dialog.wait_window()
        
        if not result["article"]:
            return
        
        article = result["article"]
        use_saga_paradise = result["use_saga_paradise"]
        
        # Выбираем изображение для главной страницы
        image_path = filedialog.askopenfilename(
            title="Выберите изображение для главной страницы",
            filetypes=[
                ("Изображения", "*.jpg *.jpeg *.png *.bmp"),
                ("JPEG", "*.jpg *.jpeg"),
                ("PNG", "*.png"),
                ("Все файлы", "*.*")
            ]
        )
        
        if not image_path or not os.path.exists(image_path):
            messagebox.showwarning("Предупреждение", "Изображение не выбрано!")
            return
        
        # Создаем папку task/<артикул>/
        from utils.path_utils import get_base_path
        base_path = get_base_path()
        task_dir = os.path.join(base_path, "task", article)
        os.makedirs(task_dir, exist_ok=True)
        
        # Обновляем config.EMBROIDERY_SETTINGS с названием проекта из дополнительных настроек
        # Это нужно, чтобы get_bottom_text мог получить правильное значение
        try:
            from export.slicer_utils import config as slicer_config
            if hasattr(slicer_config, 'EMBROIDERY_SETTINGS'):
                if self.project_name:
                    slicer_config.EMBROIDERY_SETTINGS['project_name_text'] = self.project_name
        except (ImportError, AttributeError):
            pass  # Если config не найден, просто пропускаем
        
        # Рассчитываем размер вышивки из сетки проекта (такая же логика, как в ConfigDialog)
        # Используем ту же функцию расчета, что и в функции "Создать файл..органайзер"
        calculated_size = None
        if self.vertical_lines and self.horizontal_lines and len(self.vertical_lines) >= 2 and len(self.horizontal_lines) >= 2:
            # Рассчитываем размер в см для канвы Aida 16 (16 клеток на дюйм)
            # 1 дюйм = 2.54 см, значит 1 клетка = 2.54 / 16 = 0.15875 см
            # Эта же логика используется в ConfigDialog._calculate_embroidery_size()
            cells_per_cm = 16 / 2.54  # Клеток на см
            
            # Количество ячеек = количество линий - 1
            num_cells_width = len(self.vertical_lines) - 1
            num_cells_height = len(self.horizontal_lines) - 1
            
            width_cm = num_cells_width / cells_per_cm
            height_cm = num_cells_height / cells_per_cm
            
            calculated_size = f"{width_cm:.1f} х {height_cm:.1f} см"
        
        try:
            # Определяем количество цветов
            # Если есть палитра в текущем проекте, используем её
            num_colors = None
            if self.palette is not None:
                try:
                    palette_len = len(self.palette)
                    if palette_len > 0:
                        num_colors = palette_len
                except (TypeError, ValueError):
                    # Если палитра не может быть преобразована в длину, пропускаем
                    pass
            
            # Если количество цветов не определено, запрашиваем у пользователя
            if num_colors is None:
                num_colors_str = simpledialog.askstring(
                    "Количество цветов",
                    "Введите количество цветов в наборе:",
                    initialvalue="10"
                )
                if num_colors_str:
                    try:
                        num_colors = int(num_colors_str)
                    except ValueError:
                        messagebox.showwarning("Предупреждение", "Некорректное значение количества цветов! Будет использовано значение по умолчанию (10).")
                        num_colors = 10
                else:
                    num_colors = 10  # Значение по умолчанию
            
            # Создаем главную страницу
            # Используем артикул для pdf_name и article_text
            # Название проекта берем из дополнительных настроек (self.project_name)
            # Размер берем из расчета сетки проекта (как в футере)
            project_name_text = self.project_name if self.project_name else None
            output_path = create_a5_main_page_from_image(
                image_path=image_path,
                pdf_name=article,  # Используем артикул для имени
                article_text=article,  # Используем артикул для артикула
                output_folder=task_dir,  # Сохраняем в task/<артикул>/
                num_colors=num_colors,  # Передаем количество цветов
                project_name_text=project_name_text,  # Передаем название проекта из дополнительных настроек
                embroidery_size=calculated_size,  # Передаем рассчитанный размер из сетки проекта
                use_saga_paradise=use_saga_paradise  # Вставить картинку saga/paradise
            )
            
            messagebox.showinfo("Успех", f"Главная страница успешно создана!\n\n{output_path}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при создании главной страницы:\n{e}")
            import traceback
            traceback.print_exc()
    
    def create_main_page_with_crosses(self):
        """Создает А5 главную страницу с наложением крестиков на каждую ячейку"""
        from tkinter import messagebox, ttk
        from utils.path_utils import get_static_path
        
        try:
            from export.slicer_utils.create_a5_with_crosses import create_a5_main_with_crosses
        except ImportError:
            messagebox.showerror("Ошибка", "Модуль создания A5 с крестиками не найден!")
            return
        
        # Проверяем наличие изображения
        if self.image is None:
            messagebox.showwarning("Предупреждение", 
                                 "Сначала откройте изображение!")
            return
        
        # Проверяем наличие сетки
        if len(self.vertical_lines) < 2 or len(self.horizontal_lines) < 2:
            messagebox.showwarning("Предупреждение", 
                                 "Сначала постройте сетку!")
            return
        
        # Проверяем наличие фрагментированного изображения или закрашенных ячеек
        if self.fragmented_image is None and (not self.painted_cells or len(self.painted_cells) == 0):
            messagebox.showwarning("Предупреждение", 
                                 "Сначала выполните фрагментацию изображения или закрасьте ячейки!\n"
                                 "Используйте 'Палитра' → 'Получить палитру (фрагментация)' или закрасьте ячейки вручную")
            return
        
        # Проверяем наличие палитры
        if self.palette is None or len(self.palette) == 0:
            messagebox.showwarning("Предупреждение", 
                                 "Палитра не создана!\n"
                                 "Нажмите 'Получить палитру' после построения сетки.")
            return
        
        # Создаем диалог для ввода артикула с чекбоксом saga/paradise
        dialog = tk.Toplevel(self.root)
        dialog.title("Артикул")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Переменные
        article_var = tk.StringVar(value=self.project_article if self.project_article else "")
        use_saga_paradise_var = tk.BooleanVar(value=True)  # По умолчанию включено
        
        # Фрейм для полей
        main_frame = ttk.Frame(dialog, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Поле артикула
        ttk.Label(main_frame, text="Артикул:").grid(row=0, column=0, sticky=tk.W, pady=5)
        article_entry = ttk.Entry(main_frame, textvariable=article_var, width=30)
        article_entry.grid(row=0, column=1, sticky=tk.EW, pady=5, padx=5)
        main_frame.columnconfigure(1, weight=1)
        
        # Чекбокс saga/paradise
        saga_checkbox = ttk.Checkbutton(main_frame, text="saga/paradise", variable=use_saga_paradise_var)
        saga_checkbox.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Кнопки
        button_frame = tk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0))
        
        result = {"article": None, "use_saga_paradise": False}
        
        def ok_clicked():
            article = article_var.get().strip()
            if not article:
                messagebox.showwarning("Предупреждение", "Артикул не указан!", parent=dialog)
                return
            result["article"] = article
            result["use_saga_paradise"] = use_saga_paradise_var.get()
            dialog.destroy()
        
        def cancel_clicked():
            dialog.destroy()
        
        ok_button = tk.Button(button_frame, text="ОК", command=ok_clicked, width=10)
        ok_button.pack(side=tk.LEFT, padx=5)
        cancel_button = tk.Button(button_frame, text="Отмена", command=cancel_clicked, width=10)
        cancel_button.pack(side=tk.LEFT, padx=5)
        
        # Фокус на поле ввода
        article_entry.focus()
        article_entry.select_range(0, tk.END)
        
        # Обработка Enter
        article_entry.bind('<Return>', lambda e: ok_clicked())
        
        # Размер по содержимому и центрирование
        dialog.update_idletasks()
        w = dialog.winfo_reqwidth()
        h = dialog.winfo_reqheight()
        x = (dialog.winfo_screenwidth() // 2) - (w // 2)
        y = (dialog.winfo_screenheight() // 2) - (h // 2)
        dialog.geometry(f"{w}x{h}+{x}+{y}")
        
        # Ждем закрытия диалога
        dialog.wait_window()
        
        if not result["article"]:
            return
        
        article = result["article"]
        use_saga_paradise = result["use_saga_paradise"]
        
        # Используем режим Multiply по умолчанию
        blend_mode = "multiply"
        
        try:
            # Получаем путь к изображению крестика
            cross_image_path = get_static_path("cross.png")
            
            if not os.path.exists(cross_image_path):
                messagebox.showerror("Ошибка", f"Изображение крестика не найдено: {cross_image_path}")
                return
            
            # Создаем папку для сохранения
            from utils.path_utils import get_base_path
            base_path = get_base_path()
            task_dir = os.path.join(base_path, "task", article)
            os.makedirs(task_dir, exist_ok=True)
            
            # Рассчитываем размер вышивки из сетки проекта
            num_cols = len(self.vertical_lines) - 1
            num_rows = len(self.horizontal_lines) - 1
            
            # Размер для канвы Aida 16 (16 крестиков на дюйм = 6.3 крестика на см)
            width_cm = round(num_cols / 6.3, 1)
            height_cm = round(num_rows / 6.3, 1)
            calculated_size = f"{width_cm} х {height_cm} см"
            
            # Определяем количество цветов из палитры
            if self.palette is not None:
                try:
                    # Проверяем, является ли палитра numpy массивом
                    if hasattr(self.palette, 'shape'):
                        num_colors = self.palette.shape[0]
                    else:
                        num_colors = len(self.palette)
                except:
                    num_colors = 10
            else:
                num_colors = 10
            
            project_name_text = self.project_name if self.project_name else None
            
            # Создаем A5 главную страницу с крестиками
            output_path = create_a5_main_with_crosses(
                fragmented_image=self.fragmented_image,
                vertical_lines=self.vertical_lines,
                horizontal_lines=self.horizontal_lines,
                painted_cells=self.painted_cells,
                palette=self.palette,
                cross_image_path=cross_image_path,
                pdf_name=article,
                article_text=article,
                output_folder=task_dir,
                project_name_text=project_name_text,
                embroidery_size=calculated_size,
                cross_opacity=1.0,  # Используем оригинальную прозрачность крестика
                blend_mode=blend_mode,  # Выбранный режим смешивания
                use_saga_paradise=use_saga_paradise  # Вставить картинку saga/paradise
            )
            
            messagebox.showinfo("Успех", f"А5 главная страница с крестиками успешно создана!\n\n{output_path}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при создании А5 с крестиками:\n{e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    root = tk.Tk()
    app = GridEditor(root)
    root.mainloop()

