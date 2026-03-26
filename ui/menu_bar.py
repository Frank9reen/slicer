"""Меню-бар приложения"""
import tkinter as tk


class MenuBar:
    """Инкапсулирует создание и управление меню-баром."""
    
    def __init__(self, editor, root):
        """
        Args:
            editor: Экземпляр GridEditor
            root: Корневое окно Tkinter
        """
        self.editor = editor
        self.root = root
        
        # Создаем меню-бар
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)
        
        self._create_file_menu()
        self._create_grid_menu()
        self._create_palette_menu()
        self._create_about_menu()
    
    def _create_file_menu(self):
        """Создает меню 'Файл'."""
        file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Открыть изображение", command=self.editor.open_image)
        file_menu.add_command(label="Сохранить изображение с сеткой", command=self.editor.save_image)
        file_menu.add_command(label="Сохранить изображение без сетки", command=self.editor.save_image_without_grid)
        file_menu.add_separator()
        file_menu.add_command(label="Сохранить проект как...", command=self.editor.save_project)
        file_menu.add_command(label="Загрузить проект...", command=self.editor.load_project)
        file_menu.add_separator()
        file_menu.add_command(label="Дополнительные настройки...", command=self.editor.show_project_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Создать OXS-файл", command=self.editor.export_to_oxs)
        file_menu.add_command(label="Создать главную страницу через загрузку", command=self.editor.create_main_page_only)
        file_menu.add_command(label="Создать А5 главную картинку с крестиками", command=self.editor.create_main_page_with_crosses)
        file_menu.add_separator()
        file_menu.add_command(label="Создать файлы (схема, органайзер, главная страница, Excel)", command=self.editor.create_all_files)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.root.quit)
    
    def _create_grid_menu(self):
        """Создает меню 'Сетка'."""
        self.editor.grid_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Сетка", menu=self.editor.grid_menu)
        
        self.editor.grid_menu.add_command(label="Показывать сетку", command=self.editor.toggle_grid_visibility_menu)
        self.editor.grid_menu.add_command(label="Толщина сетки", command=self.editor.set_grid_line_width)
        self.editor.grid_menu.add_command(label="Цвет сетки", command=self.editor.set_grid_color)
        self.editor.grid_menu.add_separator()
        self.editor.grid_menu.add_command(label="Удалить всю сетку", command=self.editor.delete_all_grid)
        self.editor.grid_menu.add_separator()
        self.editor.grid_menu.add_command(label="Выбрать цвет подложки", command=self.editor.choose_background_color)
        self.editor.grid_menu.add_separator()
        self.editor.grid_menu.add_command(label="Кадрировать изображение", command=self.editor.crop_image)
        # Добавляем пункт меню для нормализации размеров ячеек
        normalize_status = "ВКЛ" if getattr(self.editor, 'normalize_cell_sizes', True) else "ВЫКЛ"
        self.editor.grid_menu.add_command(
            label=f"Нормализация размеров ячеек: {normalize_status}",
            command=self.editor.toggle_normalize_cell_sizes
        )
    
    def _create_palette_menu(self):
        """Создает меню 'Палитра'."""
        palette_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Палитра", menu=palette_menu)
        
        palette_menu.add_command(label="Получить палитру (фрагментация)", command=self.editor.fragment_image)
        palette_menu.add_command(label="Удалить палитру", command=self.editor.delete_palette)
        palette_menu.add_separator()
        palette_menu.add_command(label="Таблица палитры Гамма (Gamma)", command=self.editor.show_gamma_palette_table)
        palette_menu.add_separator()
        palette_menu.add_command(label="Автозакрашивание ячеек", command=self.editor.auto_paint_cells)
        palette_menu.add_command(label="Укрупнение ячеек (x4)", command=self.editor.upscale_cells)
        palette_menu.add_separator()
        palette_menu.add_command(label="Выделить одиночные пиксели", command=self.editor.select_single_pixels_all)
        palette_menu.add_command(label="Удалить одиночные пиксели со всего изображения", command=self.editor.remove_single_pixels_all)
        palette_menu.add_command(label="Удалить одиночные пиксели из выделенной области", command=self.editor.remove_single_pixels_selection)
    
    def _create_about_menu(self):
        """Создает меню 'О программе'."""
        self.editor.about_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="О программе", menu=self.editor.about_menu)
        
        # Пункты из меню "Лицензия"
        self.editor.about_menu.add_command(label="Лицензия", command=self.editor.show_license_status)
        self.editor.about_menu.add_separator()
        
        # Пункты из меню "Справка"
        self.editor.about_menu.add_command(label="Помощь", command=self.editor.show_instructions)
        self.editor.about_menu.add_command(label="Разработчики", command=self.editor.show_about)
        self.editor.activate_menu_item_id = None  # ID пункта меню "Активировать лицензию"

