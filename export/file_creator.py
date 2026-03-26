"""
Модуль для создания файлов из фрагментированного изображения
(схема символьная, органайзер, главная страница, Excel)
"""
import os
import sys
import math
import json
import shutil
import time
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import tkinter as tk
from tkinter import messagebox
from utils.version_utils import get_version
try:
    from utils.path_utils import get_static_path
except ImportError:
    get_static_path = None

# Импортируем функции из slicer_utils
# Сначала пробуем абсолютный импорт (для скомпилированного приложения)
try:
    from export.slicer_utils.color_layout_25 import (
        create_pdf_table,
        create_pdf_symbols_only,
        create_organizer_image,
        save_gamma_legend_to_excel,
        load_gamma_legend_from_excel,
        create_palette_pdf,
        create_palette_image,
        pdf_to_jpg,
        add_table_page_to_pdf,
        calculate_color_counts,
        SPECIAL_CHARS,
        get_font,
        merge_pdf_pages,
        create_a4_pages,
        save_jpg_with_metadata
    )
    from export.slicer_utils.create_a5_main_from_image import create_a5_main_page_from_image
    from export.slicer_utils.create_a5_with_crosses import create_a5_main_with_crosses_for_organizer
    from export.slicer_utils import config
    HAS_SLICER_182 = True
except ImportError:
    # Если не получилось, пробуем относительный импорт (для разработки)
    try:
        from utils.path_utils import get_base_path
        base_path = get_base_path()
        slicer_utils_path = os.path.join(base_path, 'export', 'slicer_utils')
        if slicer_utils_path not in sys.path:
            sys.path.insert(0, slicer_utils_path)
        
        from color_layout_25 import (
            create_pdf_table,
            create_pdf_symbols_only,
            create_organizer_image,
            save_gamma_legend_to_excel,
            load_gamma_legend_from_excel,
            create_palette_pdf,
            create_palette_image,
            pdf_to_jpg,
            add_table_page_to_pdf,
            calculate_color_counts,
            SPECIAL_CHARS,
            get_font,
            merge_pdf_pages,
            create_a4_pages,
            save_jpg_with_metadata
        )
        from create_a5_main_from_image import create_a5_main_page_from_image
        from create_a5_with_crosses import create_a5_main_with_crosses_for_organizer
        import config
        HAS_SLICER_182 = True
    except ImportError as e:
        print(f"[WARNING] Не удалось импортировать функции из slicer_utils: {e}")
        import traceback
        traceback.print_exc()
        HAS_SLICER_182 = False

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    print("[WARNING] pandas не установлен. Работа с Excel будет недоступна.")

try:
    from PyPDF2 import PdfMerger
except ImportError:
    try:
        from pypdf import PdfMerger
    except ImportError:
        PdfMerger = None

try:
    from PyPDF2 import PdfReader, PdfWriter
except ImportError:
    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError:
        PdfReader = None
        PdfWriter = None


def _format_pdf_datetime(dt):
    """Форматирует дату/время в формат PDF: D:YYYYMMDDHHmmSS."""
    return dt.strftime("D:%Y%m%d%H%M%S")


def _set_pdf_creation_metadata(pdf_path, created_dt=None, dmc_author_only=False):
    """Обновляет метаданные PDF файла.

    Args:
        pdf_path: путь к PDF файлу.
        created_dt: дата/время создания (используется в обычном режиме).
        dmc_author_only: если True, очищает все теги и оставляет только Author=Lilu&Stitch.
    """
    if PdfReader is None or PdfWriter is None:
        return False, "Библиотека для изменения PDF-метаданных недоступна"

    if not os.path.exists(pdf_path):
        return False, "PDF файл не найден"

    if created_dt is None:
        created_dt = datetime.now()

    tmp_path = f"{pdf_path}.tmp"

    try:
        reader = PdfReader(pdf_path)
        writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        if dmc_author_only:
            writer.add_metadata({"/Author": "Lilu&Stitch"})
        else:
            pdf_dt = _format_pdf_datetime(created_dt)
            human_dt = created_dt.strftime("%Y-%m-%d %H:%M:%S")
            existing_metadata = {}
            if reader.metadata:
                for key, value in reader.metadata.items():
                    if key and isinstance(key, str) and key.startswith("/") and value is not None:
                        existing_metadata[key] = str(value)

            existing_metadata["/CreationDate"] = pdf_dt
            existing_metadata["/ModDate"] = pdf_dt
            existing_metadata["/Creator"] = "NexelSoftware"
            existing_metadata["/Дата создания"] = human_dt
            writer.add_metadata(existing_metadata)

        with open(tmp_path, "wb") as temp_file:
            writer.write(temp_file)

        os.replace(tmp_path, pdf_path)
        if dmc_author_only:
            return True, "Author = Lilu&Stitch"
        return True, human_dt
    except Exception as e:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        return False, str(e)


class ProgressDialog:
    """Диалоговое окно для отображения прогресса создания файлов"""
    
    def __init__(self, parent):
        self.parent = parent
        self.window = None
        self.status_label = None
        self.details_text = None
        self.stop_flag = False
        self.start_time = None
        self.path_label = None  # Метка для пути проекта
        
    def show(self, title="Создание файлов"):
        """Показывает диалоговое окно прогресса"""
        # Засекаем время начала
        self.start_time = time.time()
        
        self.window = tk.Toplevel(self.parent)
        self.window.title(title)
        self.window.geometry("600x400")
        self.window.resizable(True, True)
        
        # Центрируем окно
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (self.window.winfo_width() // 2)
        y = (self.window.winfo_screenheight() // 2) - (self.window.winfo_height() // 2)
        self.window.geometry(f"+{x}+{y}")
        
        # Заголовок
        header_label = tk.Label(self.window, text="Создание файлов проекта", 
                               font=('Arial', 12, 'bold'))
        header_label.pack(pady=10)
        
        # Статус
        self.status_label = tk.Label(self.window, text="Инициализация...", 
                                     font=('Arial', 10), wraplength=550)
        self.status_label.pack(pady=5, padx=10)
        
        # Область детальной информации
        details_frame = tk.Frame(self.window)
        details_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = tk.Scrollbar(details_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.details_text = tk.Text(details_frame, wrap=tk.WORD, 
                                    yscrollcommand=scrollbar.set,
                                    font=('Courier', 9), height=11)
        self.details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.details_text.yview)
        
        # Фрейм для пути проекта (будет создан в finish)
        self.path_frame = None
        
        # Кнопка закрытия (изначально неактивна)
        self.close_button = tk.Button(self.window, text="Закрыть", 
                                      command=self.close, state=tk.DISABLED,
                                      width=15)
        self.close_button.pack(pady=10)
        
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        self.window.transient(self.parent)
        self.window.grab_set()
        
    def update_status(self, message):
        """Обновляет статусное сообщение (только в статусе, без дублирования в деталях)"""
        if self.status_label:
            self.status_label.config(text=message)
        self.window.update_idletasks()
        self.window.update()  # Принудительное обновление интерфейса
        
    def add_detail(self, message):
        """Добавляет детальное сообщение в текстовую область"""
        if self.details_text:
            self.details_text.insert(tk.END, message + "\n")
            self.details_text.see(tk.END)
        self.window.update_idletasks()
        self.window.update()  # Принудительное обновление интерфейса
    
    def finish(self, success=True, message="", output_path=None):
        """Завершает диалог и активирует кнопку закрытия
        
        Args:
            success: True если успешно, False при ошибке
            message: Сообщение для отображения
            output_path: Путь к папке проекта (будет показан как кликабельная ссылка)
        """
        # Вычисляем время выполнения
        elapsed_time = 0
        if self.start_time:
            elapsed_time = time.time() - self.start_time
            minutes = int(elapsed_time // 60)
            seconds = int(elapsed_time % 60)
            time_str = f"{minutes} мин {seconds} сек" if minutes > 0 else f"{seconds} сек"
        else:
            time_str = "неизвестно"
        
        # Формируем финальное сообщение с временем
        if success:
            base_message = message or "Все файлы успешно созданы!"
            final_message = f"{base_message}\n\nВремя выполнения: {time_str}"
            self.update_status("✓ " + final_message)
            # Также добавляем в детали
            self.add_detail(f"\n{'='*60}")
            self.add_detail(f"Время выполнения: {time_str}")
        else:
            base_message = message or "Произошла ошибка при создании файлов"
            final_message = f"{base_message}\n\nВремя выполнения: {time_str}"
            self.update_status("✗ " + final_message)
            self.add_detail(f"\n{'='*60}")
            self.add_detail(f"Время выполнения: {time_str}")
        
        # Добавляем кликабельную ссылку на путь проекта, если он передан и успешно
        if success and output_path and os.path.exists(output_path):
            # Создаем фрейм для пути, если его еще нет
            if self.path_frame is None:
                self.path_frame = tk.Frame(self.window)
                self.path_frame.pack(pady=5, padx=10, before=self.close_button)
            
            # Удаляем старую метку, если она есть
            if self.path_label:
                self.path_label.destroy()
            
            # Создаем метку с кликабельной ссылкой
            path_text = f"Путь к проекту: {output_path}"
            self.path_label = tk.Label(
                self.path_frame,
                text=path_text,
                font=('Arial', 9),
                fg='blue',
                cursor='hand2',
                wraplength=550,
                justify=tk.LEFT
            )
            self.path_label.pack()
            
            # Привязываем обработчик клика для открытия проводника
            def open_explorer(event):
                try:
                    # Нормализуем путь для Windows
                    normalized_path = os.path.normpath(output_path)
                    # Открываем проводник Windows
                    if sys.platform == 'win32':
                        os.startfile(normalized_path)
                    else:
                        # Для других ОС используем subprocess
                        import subprocess
                        if sys.platform == 'darwin':  # macOS
                            subprocess.Popen(['open', normalized_path])
                        else:  # Linux
                            subprocess.Popen(['xdg-open', normalized_path])
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось открыть папку:\n{str(e)}")
            
            self.path_label.bind('<Button-1>', open_explorer)
            # Добавляем подчеркивание при наведении
            def on_enter(event):
                self.path_label.config(font=('Arial', 9, 'underline'))
            def on_leave(event):
                self.path_label.config(font=('Arial', 9))
            self.path_label.bind('<Enter>', on_enter)
            self.path_label.bind('<Leave>', on_leave)
        
        if self.close_button:
            self.close_button.config(state=tk.NORMAL)
        self.window.grab_release()
        
    def close(self):
        """Закрывает диалог"""
        if self.window:
            self.window.destroy()
    
    def on_close(self):
        """Обработчик закрытия окна"""
        if self.close_button['state'] == tk.NORMAL:
            self.close()


def _create_image_from_painted_cells_only(painted_cells, vertical_lines, horizontal_lines, fragmented_image):
    """
    Создает изображение только из закрашенных ячеек (без fragmented_image).
    Использует реальные размеры изображения на основе координат сетки.
    
    Args:
        painted_cells: dict - словарь {(col, row): color} с закрашенными ячейками
        vertical_lines: list - вертикальные линии сетки
        horizontal_lines: list - горизонтальные линии сетки
        fragmented_image: PIL Image - используется только для определения нормализованных размеров ячеек
    
    Returns:
        PIL Image - изображение только с закрашенными ячейками на белом фоне
    """
    from PIL import ImageDraw
    
    if not painted_cells or len(painted_cells) == 0:
        return None
    
    if not vertical_lines or not horizontal_lines or len(vertical_lines) < 2 or len(horizontal_lines) < 2:
        return None
    
    if fragmented_image is None:
        return None
    
    # Вычисляем реальные размеры изображения на основе координат сетки
    # Используем последние координаты линий сетки как границы изображения
    width = vertical_lines[-1] if vertical_lines else fragmented_image.width
    height = horizontal_lines[-1] if horizontal_lines else fragmented_image.height
    
    # Вычисляем количество ячеек
    num_cols = len(vertical_lines) - 1
    num_rows = len(horizontal_lines) - 1
    
    if num_cols == 0 or num_rows == 0:
        return None
    
    
    # Создаем новое изображение с белым фоном (используем реальные размеры)
    result_image = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(result_image)
    
    # Рисуем только закрашенные ячейки
    for (col, row), color in painted_cells.items():
        if 0 <= col < num_cols and 0 <= row < num_rows:
            # Вычисляем координаты ячейки в реальных координатах изображения
            # Используем реальные координаты сетки
            x1 = vertical_lines[col]
            x2 = vertical_lines[col + 1]
            y1 = horizontal_lines[row]
            y2 = horizontal_lines[row + 1]
            
            # Убеждаемся, что координаты в пределах изображения
            x1 = max(0, min(int(x1), width))
            x2 = max(0, min(int(x2), width))
            y1 = max(0, min(int(y1), height))
            y2 = max(0, min(int(y2), height))
            
            if x2 > x1 and y2 > y1:
                # Нормализуем цвет до кортежа
                if isinstance(color, (list, np.ndarray)):
                    color_tuple = tuple(int(c) for c in color[:3])
                elif isinstance(color, tuple):
                    color_tuple = tuple(int(c) for c in color[:3])
                else:
                    color_tuple = color
                
                # Закрашиваем ячейку в реальных координатах
                draw.rectangle([x1, y1, x2-1, y2-1], fill=color_tuple, outline=None)
    
    return result_image


def create_files_from_fragmented_image(
    fragmented_image,
    palette,
    vertical_lines,
    horizontal_lines,
    image_path=None,
    output_folder=None,
    project_name=None,
    parent_window=None,
    config_settings=None,
    article_name=None,
    painted_cells=None
):
    """
    Создает все файлы из уже фрагментированного изображения.
    Пропускает этап фрагментации - использует уже готовое изображение и палитру.
    
    Args:
        fragmented_image: PIL Image - уже фрагментированное изображение
        palette: numpy.ndarray или list - палитра цветов
        vertical_lines: list - вертикальные линии сетки
        horizontal_lines: list - горизонтальные линии сетки
        image_path: str - путь к исходному изображению (для главной страницы)
        output_folder: str - папка для сохранения файлов (по умолчанию "task/<article_name>")
        project_name: str - название проекта (если None, берется из image_path) - используется для имен файлов
        parent_window: tk.Toplevel - родительское окно для диалога прогресса
        config_settings: dict - настройки конфигурации из диалога (если None, используются значения по умолчанию)
        article_name: str - артикул для формирования пути к папке проекта (если None, используется project_name)
    
    Returns:
        bool: True если успешно, False при ошибке
    """
    if not HAS_SLICER_182:
        messagebox.showerror("Ошибка", "Не удалось загрузить функции из slicer_utils")
        return False
    
    if fragmented_image is None or palette is None:
        messagebox.showwarning("Предупреждение", 
                             "Фрагментированное изображение и палитра необходимы!")
        return False
    
    # Определяем название проекта (для имен файлов)
    if project_name is None:
        if image_path:
            project_name = os.path.splitext(os.path.basename(image_path))[0]
        else:
            project_name = "project"
    
        # Определяем артикул для формирования пути к папке проекта и имен файлов
    if article_name is None:
        # Если артикул не передан, пытаемся взять из config_settings
        if config_settings and config_settings.get('article'):
            article_name = config_settings['article'].strip()
        # Если артикул все еще не определен, используем project_name
        if not article_name:
            article_name = project_name
    
    # Определяем папку для сохранения (используем артикул)
    if output_folder is None:
        output_folder = os.path.join("task", article_name)
    
    # Определяем название проекта для баров и A5 страницы
    project_name_text = project_name  # По умолчанию
    if config_settings and config_settings.get('project_name_text'):
        project_name_text = config_settings['project_name_text'].strip()
    
    # Получаем корневую директорию проекта (где находится static/)
    from utils.path_utils import get_base_path
    project_root = get_base_path()  # корень проекта
    
    # Создаем диалог прогресса, если передан parent_window
    progress_dialog = None
    if parent_window:
        progress_dialog = ProgressDialog(parent_window)
        progress_dialog.show()
    
    def update_progress(message, show_in_details=False):
        """Вспомогательная функция для обновления прогресса"""
        if progress_dialog:
            progress_dialog.update_status(message)
            if show_in_details:
                progress_dialog.add_detail(message)
        # Обновляем главное окно, чтобы интерфейс не зависал
        if parent_window:
            try:
                parent_window.update_idletasks()
            except:
                pass
    
    # Применяем настройки конфигурации, если они переданы
    saved_config = {}
    if config_settings and HAS_SLICER_182:
        # Сохраняем текущие значения config
        if hasattr(config, 'EMBROIDERY_SETTINGS'):
            saved_config['EMBROIDERY_SETTINGS'] = config.EMBROIDERY_SETTINGS.copy()
        if hasattr(config, 'TEXTS'):
            saved_config['TEXTS'] = config.TEXTS.copy()
        if hasattr(config, 'DPI'):
            saved_config['DPI'] = config.DPI
        if hasattr(config, 'JPEG_QUALITY'):
            saved_config['JPEG_QUALITY'] = config.JPEG_QUALITY
        if hasattr(config, 'BLOCKS_PER_PAGE_WIDTH'):
            saved_config['BLOCKS_PER_PAGE_WIDTH'] = config.BLOCKS_PER_PAGE_WIDTH
        if hasattr(config, 'BLOCKS_PER_PAGE_HEIGHT'):
            saved_config['BLOCKS_PER_PAGE_HEIGHT'] = config.BLOCKS_PER_PAGE_HEIGHT
        
        # Применяем новые настройки
        if not hasattr(config, 'EMBROIDERY_SETTINGS'):
            config.EMBROIDERY_SETTINGS = {}
        config.EMBROIDERY_SETTINGS['size'] = config_settings.get('size', '23 х 23 см')
        config.EMBROIDERY_SETTINGS['project_name_text'] = config_settings.get('project_name_text', '')
        config.EMBROIDERY_SETTINGS['article'] = config_settings.get('article', '')
        
        if not hasattr(config, 'TEXTS'):
            config.TEXTS = {}
        config.TEXTS['top_text'] = config_settings.get('top_text', 'Набор для вышивания крестом')
        
        config.DPI = config_settings.get('dpi', 300)
        config.JPEG_QUALITY = config_settings.get('jpeg_quality', 95)
        config.BLOCKS_PER_PAGE_WIDTH = config_settings.get('blocks_per_page_width', 56)
        config.BLOCKS_PER_PAGE_HEIGHT = config_settings.get('blocks_per_page_height', 85)
    
    # Сохраняем текущую рабочую директорию
    original_cwd = os.getcwd()
    
    # Меняем рабочую директорию на корень проекта, чтобы функции находили файлы в static/
    try:
        os.chdir(project_root)
        
        update_progress("Инициализация...")
        
        # Создаем структуру папок
        task_dir = output_folder
        task_a4_dir = os.path.join(task_dir, "A4-pdf")  # Папка для PDF
        task_A4_dir = os.path.join(task_dir, "A4")  # Папка для JPG (с большой буквы)
        os.makedirs(task_dir, exist_ok=True)
        os.makedirs(task_a4_dir, exist_ok=True)
        os.makedirs(task_A4_dir, exist_ok=True)
        
        # Вычисляем количество блоков
        num_blocks_width = len(vertical_lines) - 1 if vertical_lines else 150
        num_blocks_height = len(horizontal_lines) - 1 if horizontal_lines else 150
        
        # Добавляем начальную информацию в детали
        if progress_dialog:
            progress_dialog.add_detail(f"Артикул: {article_name}")
            progress_dialog.add_detail(f"Название проекта: {project_name_text}")
            progress_dialog.add_detail(f"Выходная папка: {task_dir}")
            progress_dialog.add_detail(f"Количество блоков: {num_blocks_width}x{num_blocks_height}")
            progress_dialog.add_detail(f"Количество цветов: {len(palette)}")
            # Получаем размер вышивки из config_settings или config
            embroidery_size = "Не указан"
            if config_settings and config_settings.get('size'):
                embroidery_size = config_settings['size']
            elif HAS_SLICER_182 and hasattr(config, 'EMBROIDERY_SETTINGS'):
                embroidery_size = config.EMBROIDERY_SETTINGS.get('size', 'Не указан')
            progress_dialog.add_detail(f"Размер: {embroidery_size}")
            progress_dialog.add_detail("")
        
        # Сохраняем layout изображение
        update_progress("Сохранение layout изображения...")
        layout_image_path = os.path.join(task_dir, f"{article_name}_layout.jpg")
        
        # Если есть закрашенные ячейки, создаем изображение только из них (без fragmented_image)
        # Иначе используем fragmented_image
        if painted_cells and len(painted_cells) > 0:
            layout_rgb = _create_image_from_painted_cells_only(
                painted_cells,
                vertical_lines,
                horizontal_lines,
                fragmented_image
            )
            # Если не удалось создать из painted_cells, используем fragmented_image как fallback
            if layout_rgb is None:
                layout_rgb = fragmented_image.convert("RGB")
        else:
            # Если нет закрашенных ячеек, используем fragmented_image
            layout_rgb = fragmented_image.convert("RGB")
        
        if HAS_SLICER_182:
            title = f"{article_name} - Схема для вышивания"
            save_jpg_with_metadata(layout_rgb, layout_image_path, quality=95, title=title)
        else:
            layout_rgb.save(layout_image_path, 'JPEG', quality=95)
        
        # Нормализуем палитру до кортежей
        normalized_palette = []
        for color in palette:
            if isinstance(color, (list, np.ndarray)):
                normalized_color = tuple(int(c) for c in color[:3])
            elif isinstance(color, tuple):
                normalized_color = tuple(int(c) for c in color[:3])
            else:
                normalized_color = color
            normalized_palette.append(normalized_color)
        palette = normalized_palette
        
        # Обновляем палитру на основе painted_cells, если есть закрашенные ячейки
        # Это необходимо, чтобы учитывались только реально используемые цвета после ручных правок
        if painted_cells and len(painted_cells) > 0:
            # Собираем уникальные цвета из painted_cells
            unique_colors_from_cells = set()
            for cell_color in painted_cells.values():
                if isinstance(cell_color, (list, np.ndarray)):
                    color_tuple = tuple(int(c) for c in cell_color[:3])
                elif isinstance(cell_color, tuple):
                    color_tuple = tuple(int(c) for c in cell_color[:3])
                else:
                    color_tuple = cell_color
                unique_colors_from_cells.add(color_tuple)
            
            # Если есть уникальные цвета из painted_cells, обновляем палитру
            if unique_colors_from_cells:
                # Сохраняем порядок цветов из исходной палитры, оставляя только те, что есть в painted_cells
                updated_palette = []
                for color in palette:
                    if color in unique_colors_from_cells:
                        updated_palette.append(color)
                        unique_colors_from_cells.discard(color)
                
                # Добавляем оставшиеся цвета из painted_cells, которых нет в исходной палитре
                for color in unique_colors_from_cells:
                    updated_palette.append(color)
                
                # Обновляем палитру только если она изменилась
                if len(updated_palette) != len(palette):
                    palette = updated_palette
                    print(f"[INFO] Палитра обновлена на основе painted_cells: {len(palette)} цветов (было {len(normalized_palette)})")
        
        # Создаем соответствие между цветами и символами
        char_list = SPECIAL_CHARS * ((len(palette) // len(SPECIAL_CHARS)) + 1)
        color_to_char = {color: char_list[i] for i, color in enumerate(palette)}
        
        # Путь к Excel файлу Gamma в static/
        gamma_excel_path = os.path.join(project_root, "static", "DMCtoGamma_with_Gamma_OFF_formattedColor.xlsx")
        if not os.path.exists(gamma_excel_path):
            print(f"[WARNING] Excel файл Gamma не найден: {gamma_excel_path}")
        
        # Рассчитываем количество кубиков для каждого цвета (для столбца Длина)
        color_counts = calculate_color_counts(
            layout_image_path, 
            palette, 
            num_blocks_width, 
            num_blocks_height, 
            painted_cells
        )
        
        # Получаем настройку use_dmc и бренд из config_settings
        use_dmc = config_settings.get('use_dmc', False) if config_settings else False
        brand = config_settings.get('brand', 'marfa') if config_settings else 'marfa'
        
        # Сохраняем данные в Excel файл <артикул>.xlsx
        update_progress("Создание Excel файла с палитрой...")
        gamma_legend_path = os.path.join(task_dir, f"{article_name}.xlsx")
        save_gamma_legend_to_excel(
            palette, 
            color_to_char, 
            gamma_excel_path if os.path.exists(gamma_excel_path) else None, 
            gamma_legend_path,
            color_counts,
            use_dmc=use_dmc
        )
        
        # При DMC PDF создаются с другими именами (_table_symbols_DMC.pdf и т.д.)
        pdf_suffix = "_DMC" if use_dmc else ""
        # Создаем PDF таблицы
        update_progress("Создание PDF таблиц...")
        pdf_output = os.path.join(task_dir, f"{article_name}_table.pdf")
        create_pdf_table(layout_image_path, pdf_output, num_blocks_width, num_blocks_height, 
                        include_symbols=False, palette=palette, 
                        painted_cells=painted_cells, vertical_lines=vertical_lines, horizontal_lines=horizontal_lines,
                        brand=brand)
        
        pdf_symbols_output = os.path.join(task_dir, f"{article_name}_table_symbols{pdf_suffix}.pdf")
        create_pdf_table(layout_image_path, pdf_symbols_output, num_blocks_width, num_blocks_height, 
                        include_symbols=True, palette=palette,
                        painted_cells=painted_cells, vertical_lines=vertical_lines, horizontal_lines=horizontal_lines,
                        brand=brand)
        
        pdf_symbols_only_output = os.path.join(task_dir, f"{article_name}_table_symbols_only{pdf_suffix}.pdf")
        create_pdf_symbols_only(layout_image_path, pdf_symbols_only_output, num_blocks_width, 
                               num_blocks_height, palette=palette,
                               painted_cells=painted_cells, vertical_lines=vertical_lines, horizontal_lines=horizontal_lines,
                               brand=brand)
        
        # Загружаем color_to_char из Excel для правильного порядка
        palette_numbers = None
        dmc_numbers = {}
        if os.path.exists(gamma_legend_path):
            loaded_color_to_char, loaded_palette, loaded_numbers, loaded_dmc_numbers = load_gamma_legend_from_excel(gamma_legend_path)
            if loaded_color_to_char and loaded_palette:
                color_to_char = loaded_color_to_char
                palette = loaded_palette
                palette_numbers = loaded_numbers
                if loaded_dmc_numbers:
                    dmc_numbers = loaded_dmc_numbers
        
        # Создаем PDF палитры
        update_progress("Создание палитры...")
        palette_pdf_path = os.path.join(task_dir, f"{article_name}_layout_palette.pdf")
        create_palette_pdf(palette, color_to_char, palette_pdf_path, numbers=palette_numbers)
        if parent_window:
            parent_window.update()
        
        palette_image_path = os.path.join(task_dir, f"{article_name}_layout_palette.jpg")
        if not pdf_to_jpg(palette_pdf_path, palette_image_path, dpi=300):
            create_palette_image(palette, color_to_char, palette_image_path, numbers=palette_numbers)
        if parent_window:
            parent_window.update()
        
        # Добавляем таблицу из Excel в PDF файлы
        if os.path.exists(gamma_legend_path):
            add_table_page_to_pdf(pdf_symbols_output, gamma_legend_path, use_dmc=use_dmc, colorize_symbols=True, brand=brand)
            add_table_page_to_pdf(pdf_symbols_only_output, gamma_legend_path, use_dmc=use_dmc, colorize_symbols=False, brand=brand)
        if parent_window:
            parent_window.update()
        
        # Создаем органайзер
        update_progress("Создание органайзера...")
        organizer_path = os.path.join(task_dir, f"{article_name}_Органайзер.jpg")
        qr_url = config_settings.get('qr_url', '').strip() if config_settings else ''
        create_organizer_image(
            palette, 
            color_to_char, 
            organizer_path, 
            project_name=article_name,  # Артикул для заголовка сверху
            project_name_text=project_name_text,  # Название проекта для текста внизу
            gamma_excel_path=gamma_excel_path if os.path.exists(gamma_excel_path) else None,
            layout_image_path=layout_image_path,
            num_blocks_width=num_blocks_width,
            num_blocks_height=num_blocks_height,
            qr_url=qr_url if qr_url else None,
            painted_cells=painted_cells,  # Передаем painted_cells для точного подсчета кубиков
            use_dmc=use_dmc  # Использовать DMC вместо Gamma
        )
        if parent_window:
            parent_window.update()
        
        # Создаем страницы A4 (при DMC — другие имена и бренд Lilu&Stitch, без QR на легенде)
        update_progress("Создание страниц A4...")
        # Используем артикул для имени файла
        qr_url = config_settings.get('qr_url', '').strip() if config_settings else ''
        auto_blocks = config_settings.get('auto_blocks_per_page', False) if config_settings else False
        base_name_symbols = f"{article_name}_table_symbols{pdf_suffix}"
        total_pages_colored = create_a4_pages(
            layout_image_path, 
            base_name_symbols, 
            num_blocks_width, 
            num_blocks_height,
            include_colors=True, 
            include_symbols=True, 
            blocks_per_page_width=None, 
            blocks_per_page_height=None, 
            output_dir=task_a4_dir, 
            palette=palette, 
            palette_image_path=palette_image_path, 
            project_name=project_name_text,  # Используем название проекта для правого бара
            qr_url=qr_url if qr_url else None,
            painted_cells=painted_cells, 
            vertical_lines=vertical_lines, 
            horizontal_lines=horizontal_lines,
            auto_blocks_per_page=auto_blocks,
            use_dmc=use_dmc,
            brand=brand
        )
        
        base_name_symbols_only = f"{article_name}_table_symbols_only{pdf_suffix}"
        total_pages_bw = create_a4_pages(
            layout_image_path, 
            base_name_symbols_only, 
            num_blocks_width, 
            num_blocks_height,
            include_colors=False, 
            include_symbols=True, 
            blocks_per_page_width=None, 
            blocks_per_page_height=None, 
            output_dir=task_a4_dir, 
            palette=palette, 
            palette_image_path=palette_image_path, 
            project_name=project_name_text,  # Используем название проекта для правого бара
            qr_url=qr_url if qr_url else None,
            painted_cells=painted_cells, 
            vertical_lines=vertical_lines, 
            horizontal_lines=horizontal_lines,
            auto_blocks_per_page=auto_blocks,
            use_dmc=use_dmc,
            brand=brand
        )
        if parent_window:
            parent_window.update()
        
        # Объединяем страницы A4 (base_name уже содержит _DMC при use_dmc)
        merged_colored_path = os.path.join(task_a4_dir, f"{base_name_symbols}_merged.pdf")
        merge_pdf_pages(task_a4_dir, base_name_symbols, total_pages_colored, merged_colored_path)
        
        merged_bw_path = os.path.join(task_a4_dir, f"{base_name_symbols_only}_merged.pdf")
        merge_pdf_pages(task_a4_dir, base_name_symbols_only, total_pages_bw, merged_bw_path)
        
        # Создаем JPG изображения из PDF файлов с барами (base_name для поиска PDF: table_symbols или table_symbols_DMC)
        try:
            update_progress("Создание JPG изображений из PDF...")
            # Используем артикул для левого бара и название проекта для правого бара
            # Импортируем функцию для создания JPG
            try:
                from export.slicer_utils.create_a4_jpg_from_pdf import create_a4_jpg_pages_from_pdfs
            except ImportError:
                # Если не получилось, пробуем через путь
                from utils.path_utils import get_base_path
                base_path = get_base_path()
                slicer_utils_path = os.path.join(base_path, 'export', 'slicer_utils')
                if slicer_utils_path not in sys.path:
                    sys.path.insert(0, slicer_utils_path)
                from create_a4_jpg_from_pdf import create_a4_jpg_pages_from_pdfs
            
            # Создаем JPG из PDF с символами и цветами (при DMC — base_name table_symbols_DMC)
            qr_url = config_settings.get('qr_url', '').strip() if config_settings else ''
            create_a4_jpg_pages_from_pdfs(task_dir, article_name, project_name_text, base_name=f"table_symbols{pdf_suffix}", qr_url=qr_url if qr_url else None)
            
            # Создаем JPG из PDF только с символами
            create_a4_jpg_pages_from_pdfs(task_dir, article_name, project_name_text, base_name=f"table_symbols_only{pdf_suffix}", qr_url=qr_url if qr_url else None)
            
        except Exception as e:
            update_progress(f"⚠ Ошибка при создании JPG из PDF: {e}")
            import traceback
            traceback.print_exc()
        
        # Создаем главную страницу
        try:
            update_progress("Создание главной страницы...")
            # Получаем размер вышивки из config_settings или config
            embroidery_size_value = None
            if config_settings and config_settings.get('size'):
                embroidery_size_value = config_settings.get('size')
            elif HAS_SLICER_182 and hasattr(config, 'EMBROIDERY_SETTINGS'):
                embroidery_size_value = config.EMBROIDERY_SETTINGS.get('size', None)
            
            # Проверяем, нужно ли использовать _layout.jpg
            use_layout_image = config_settings and config_settings.get('use_layout_image', False)
            
            if use_layout_image:
                # Используем старую логику с _layout.jpg
                main_page_image_path = None
                
                # Вариант 1: Изображение, выбранное вручную в диалоге конфигурации (наивысший приоритет)
                if config_settings and config_settings.get('main_page_image'):
                    manual_image_path = config_settings['main_page_image'].strip()
                    if manual_image_path and os.path.exists(manual_image_path):
                        main_page_image_path = manual_image_path
                        update_progress(f"Используется выбранное вручную изображение для главной страницы: {manual_image_path}")
                
                # Вариант 2: Исходное изображение проекта (если не выбрано вручную)
                if not main_page_image_path:
                    if image_path and os.path.exists(image_path):
                        main_page_image_path = image_path
                        update_progress(f"Используется исходное изображение для главной страницы: {image_path}")
                
                # Вариант 3: Layout изображение (если ничего не найдено)
                if not main_page_image_path:
                    if os.path.exists(layout_image_path):
                        main_page_image_path = layout_image_path
                        update_progress(f"Используется layout изображение для главной страницы: {layout_image_path}")
                
                if main_page_image_path:
                    # Получаем размер канвы из конфигурации
                    canvas_size = config_settings.get('canvas_size', 16) if config_settings else 16
                    # Шаблон главной страницы для бренда «Мулен стиль»
                    main_template_path = None
                    if brand == 'mulen' and get_static_path and callable(get_static_path):
                        main_template_path = get_static_path("pic/main_template_mulen.png")
                        if not os.path.exists(main_template_path):
                            main_template_path = None
                    
                    # Используем артикул для артикула и project_name_text уже установлен в config
                    create_a5_main_page_from_image(
                        image_path=main_page_image_path,
                        pdf_name=article_name,  # Используем артикул для имени PDF
                        article_text=article_name,  # Используем артикул для артикула
                        output_folder=task_dir,
                        template_path=main_template_path,
                        num_colors=len(palette),
                        project_name_text=project_name_text,  # Передаем название проекта из конфигурации
                        embroidery_size=embroidery_size_value,  # Передаем размер вышивки из конфигурации
                        canvas_size=canvas_size  # Передаем размер канвы из конфигурации
                    )
                else:
                    update_progress("⚠ Не найдено изображение для главной страницы")
            else:
                # Новая логика: создаем главную страницу с крестиками по умолчанию
                update_progress("Создание главной страницы с крестиками...")
                # Получаем размер канвы из конфигурации
                canvas_size = config_settings.get('canvas_size', 16) if config_settings else 16
                # Получаем флаг использования saga/paradise из конфигурации
                use_saga_paradise = config_settings.get('use_saga_paradise', False) if config_settings else False
                # Шаблон главной страницы для бренда «Мулен стиль»
                main_template_path = None
                if brand == 'mulen' and get_static_path and callable(get_static_path):
                    main_template_path = get_static_path("pic/main_template_mulen.png")
                    if not os.path.exists(main_template_path):
                        main_template_path = None
                
                create_a5_main_with_crosses_for_organizer(
                    fragmented_image=fragmented_image,
                    vertical_lines=vertical_lines,
                    horizontal_lines=horizontal_lines,
                    painted_cells=painted_cells,
                    palette=palette,
                    pdf_name=article_name,  # Используем артикул для имени PDF
                    article_text=article_name,  # Используем артикул для артикула
                    output_folder=task_dir,
                    project_name_text=project_name_text,  # Передаем название проекта из конфигурации
                    embroidery_size=embroidery_size_value,  # Передаем размер вышивки из конфигурации
                    cross_opacity=1.0,  # Используем оригинальную прозрачность крестика
                    blend_mode="multiply",  # Режим смешивания
                    canvas_size=canvas_size,  # Передаем размер канвы из конфигурации
                    use_saga_paradise=use_saga_paradise,  # Передаем флаг saga/paradise из конфигурации
                    template_path=main_template_path  # Шаблон для Мулен стиль
                )
        except Exception as e:
            update_progress(f"⚠ Ошибка при создании главной страницы: {e}")
            import traceback
            traceback.print_exc()
        
        # Создаем файл data.json с общей информацией о проекте
        update_progress("Создание файла data.json...")
        try:
            data_file_path = os.path.join(task_dir, f"{article_name}_data.json")
            # Получаем размер вышивки из config_settings или config
            embroidery_size = "Не указан"
            if config_settings and config_settings.get('size'):
                embroidery_size = config_settings['size']
            elif HAS_SLICER_182 and hasattr(config, 'EMBROIDERY_SETTINGS'):
                embroidery_size = config.EMBROIDERY_SETTINGS.get('size', 'Не указан')
            
            # Получаем размер канвы из конфигурации
            canvas_size = config_settings.get('canvas_size', 16) if config_settings else 16
            
            # Определяем тип цвета (Gamma или DMC)
            color_type = "DMC" if use_dmc else "Gamma"
            
            # Формируем данные в виде словаря (ключи на английском, значения могут быть на любом языке)
            data = {
                "project_name": project_name_text,
                "article": article_name,
                "num_colors": len(palette),
                "embroidery_size": embroidery_size,
                "cell_count": {
                    "width": num_blocks_width,
                    "height": num_blocks_height
                },
                "canvas_type": f"{canvas_size} ct",
                "color_type": color_type,
                "metadata": {
                    "created_date": datetime.now().isoformat(),
                    "version": get_version()
                }
            }
            
            # Записываем данные в JSON файл
            with open(data_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            update_progress(f"Файл {article_name}_data.json создан: {data_file_path}")
        except Exception as e:
            update_progress(f"⚠ Ошибка при создании {article_name}_data.json: {e}")
            import traceback
            traceback.print_exc()
        
        # Создаем OXS файл, если галочка установлена
        if config_settings and config_settings.get('create_oxs', False):
            try:
                update_progress("Создание OXS файла...")
                from export.oxs_exporter import export_to_oxs_to_path
                
                oxs_path = os.path.join(task_dir, f"{article_name}.oxs")
                result = export_to_oxs_to_path(
                    fragmented_image=fragmented_image,
                    palette=palette,
                    painted_cells=painted_cells,
                    vertical_lines=vertical_lines,
                    horizontal_lines=horizontal_lines,
                    image_path=image_path,
                    output_path=oxs_path
                )
                
                if result:
                    update_progress(f"OXS файл создан: {oxs_path}")
                else:
                    update_progress(f"⚠ Ошибка при создании OXS файла")
            except Exception as e:
                update_progress(f"⚠ Ошибка при создании OXS файла: {e}")
                import traceback
                traceback.print_exc()
        
        # Создаем папку "Инструкции" и перемещаем туда PDF файлы
        try:
            update_progress("Создание папки 'Инструкции'...")
            instruction_dir = os.path.join(task_dir, "Инструкции")
            os.makedirs(instruction_dir, exist_ok=True)
            instruction_pdf_paths = []
            
            # Перемещаем файлы (при DMC — имена с суффиксом _DMC)
            pdf_symbols_file = os.path.join(task_dir, f"{article_name}_table_symbols{pdf_suffix}.pdf")
            pdf_symbols_only_file = os.path.join(task_dir, f"{article_name}_table_symbols_only{pdf_suffix}.pdf")
            
            if os.path.exists(pdf_symbols_file):
                dest_symbols = os.path.join(instruction_dir, f"{article_name}_table_symbols{pdf_suffix}.pdf")
                shutil.move(pdf_symbols_file, dest_symbols)
                instruction_pdf_paths.append(dest_symbols)
                update_progress(f"Файл перемещен: {dest_symbols}")
            
            if os.path.exists(pdf_symbols_only_file):
                dest_symbols_only = os.path.join(instruction_dir, f"{article_name}_table_symbols_only{pdf_suffix}.pdf")
                shutil.move(pdf_symbols_only_file, dest_symbols_only)
                instruction_pdf_paths.append(dest_symbols_only)
                update_progress(f"Файл перемещен: {dest_symbols_only}")
            
            # Перемещаем merged PDF файлы из папки A4-pdf
            merged_symbols_file = os.path.join(task_a4_dir, f"{article_name}_table_symbols{pdf_suffix}_merged.pdf")
            merged_symbols_only_file = os.path.join(task_a4_dir, f"{article_name}_table_symbols_only{pdf_suffix}_merged.pdf")
            
            if os.path.exists(merged_symbols_file):
                dest_merged_symbols = os.path.join(instruction_dir, f"{article_name}_table_symbols{pdf_suffix}_merged.pdf")
                shutil.move(merged_symbols_file, dest_merged_symbols)
                instruction_pdf_paths.append(dest_merged_symbols)
                update_progress(f"Файл перемещен: {dest_merged_symbols}")
            
            if os.path.exists(merged_symbols_only_file):
                dest_merged_symbols_only = os.path.join(instruction_dir, f"{article_name}_table_symbols_only{pdf_suffix}_merged.pdf")
                shutil.move(merged_symbols_only_file, dest_merged_symbols_only)
                instruction_pdf_paths.append(dest_merged_symbols_only)
                update_progress(f"Файл перемещен: {dest_merged_symbols_only}")

            # Добавляем метатег "Дата создания" для PDF файлов в папке "Инструкции"
            metadata_dt = datetime.now()
            for pdf_path in instruction_pdf_paths:
                ok, info = _set_pdf_creation_metadata(
                    pdf_path,
                    metadata_dt,
                    dmc_author_only=use_dmc,
                )
                if ok:
                    if use_dmc:
                        update_progress(
                            f"Метаданные PDF обновлены ({os.path.basename(pdf_path)}): оставлен только Author = Lilu&Stitch"
                        )
                    else:
                        update_progress(
                            f"Метаданные PDF обновлены ({os.path.basename(pdf_path)}): Дата создания = {info}"
                        )
                else:
                    update_progress(f"⚠ Не удалось обновить метаданные PDF ({os.path.basename(pdf_path)}): {info}")
        except Exception as e:
            update_progress(f"⚠ Ошибка при создании папки 'Инструкции' или перемещении файлов: {e}")
            import traceback
            traceback.print_exc()
        
        update_progress("Завершение...")
        
        if progress_dialog:
            # Получаем абсолютный путь для отображения
            abs_task_dir = os.path.abspath(task_dir)
            progress_dialog.finish(True, f"Все файлы успешно созданы!", output_path=abs_task_dir)
        
        return True
        
    except Exception as e:
        error_msg = f"Ошибка при создании файлов: {e}"
        print(f"[ERROR] {error_msg}")
        import traceback
        traceback.print_exc()
        if progress_dialog:
            progress_dialog.finish(False, error_msg)
        else:
            messagebox.showerror("Ошибка", error_msg)
        return False
    finally:
        # Восстанавливаем исходную рабочую директорию
        os.chdir(original_cwd)
        
        # Восстанавливаем настройки конфигурации, если они были изменены
        if saved_config and HAS_SLICER_182:
            if 'EMBROIDERY_SETTINGS' in saved_config:
                config.EMBROIDERY_SETTINGS = saved_config['EMBROIDERY_SETTINGS']
            if 'TEXTS' in saved_config:
                config.TEXTS = saved_config['TEXTS']
            if 'DPI' in saved_config:
                config.DPI = saved_config['DPI']
            if 'JPEG_QUALITY' in saved_config:
                config.JPEG_QUALITY = saved_config['JPEG_QUALITY']
            if 'BLOCKS_PER_PAGE_WIDTH' in saved_config:
                config.BLOCKS_PER_PAGE_WIDTH = saved_config['BLOCKS_PER_PAGE_WIDTH']
            if 'BLOCKS_PER_PAGE_HEIGHT' in saved_config:
                config.BLOCKS_PER_PAGE_HEIGHT = saved_config['BLOCKS_PER_PAGE_HEIGHT']
