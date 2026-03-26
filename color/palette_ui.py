"""UI-логика для работы с палитрой"""
import os
import sys
import tkinter as tk
from tkinter import messagebox, colorchooser
import numpy as np
from PIL import Image, ImageDraw, ImageTk

# Добавляем путь к slicer_utils для импорта функций
try:
    from utils.path_utils import get_base_path
    base_path = get_base_path()
    slicer_utils_path = os.path.join(base_path, 'export', 'slicer_utils')
except ImportError:
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    slicer_utils_path = os.path.join(current_dir, 'export', 'slicer_utils')
if slicer_utils_path not in sys.path:
    sys.path.insert(0, slicer_utils_path)

try:
    from export.slicer_utils.color_layout_25 import find_closest_gamma_color
    HAS_GAMMA_FUNCTION = True
except ImportError:
    HAS_GAMMA_FUNCTION = False
    try:
        from utils.logger import setup_logger
        logger = setup_logger(__name__)
        logger.warning("Не удалось импортировать find_closest_gamma_color")
    except:
        pass

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    pd = None


class PaletteUI:
    """Класс, отвечающий за отображение и взаимодействие с палитрой цветов."""

    def __init__(self, editor):
        """
        Args:
            editor: Экземпляр GridEditor, которому принадлежит эта палитра.
        """
        self.editor = editor
    
    def sort_palette_by_gamma(self):
        """
        Упорядочивает палитру по возрастанию номеров Гаммы.
        Обновляет painted_cells для соответствия новому порядку.
        Всегда выполняется (чек-бокс убран).
        """
        editor = self.editor
        
        if editor.palette is None or len(editor.palette) == 0:
            return
        
        # Получаем путь к Excel файлу Gamma
        from utils.path_utils import get_static_path
        gamma_excel_path = get_static_path("DMCtoGamma_with_Gamma_OFF_formattedColor.xlsx")
        
        if not HAS_GAMMA_FUNCTION or not os.path.exists(gamma_excel_path):
            try:
                from utils.logger import setup_logger
                logger = setup_logger(__name__)
                logger.warning("Не удалось упорядочить палитру по Гамме: файл или функция недоступны")
            except:
                pass
            return
        
        # Создаем список кортежей (цвет, индекс, номер_Гаммы)
        palette_with_gamma = []
        for i, color in enumerate(editor.palette):
            normalized_color = self._normalize_color(color)
            if normalized_color:
                gamma_num, gamma_rgb, distance = find_closest_gamma_color(normalized_color, gamma_excel_path)
                # Преобразуем номер Гаммы в число для сортировки (если это строка типа "3112")
                if gamma_num:
                    try:
                        # Пытаемся извлечь число из строки (может быть "3112" или "G3112")
                        gamma_str = str(gamma_num).strip().upper()
                        if gamma_str.startswith('G'):
                            gamma_str = gamma_str[1:]
                        gamma_number = int(gamma_str) if gamma_str.isdigit() else float('inf')
                    except (ValueError, AttributeError):
                        gamma_number = float('inf')  # Если не удалось преобразовать, ставим в конец
                else:
                    gamma_number = float('inf')  # Если нет номера Гаммы, ставим в конец
            else:
                gamma_number = float('inf')
            
            palette_with_gamma.append((color, i, gamma_number))
        
        # Сортируем по номеру Гаммы (по возрастанию)
        palette_with_gamma.sort(key=lambda x: x[2])
        
        # Сохраняем исходное количество цветов для ограничения после упорядочивания
        original_palette_size = len(editor.palette)
        
        # Создаем новую упорядоченную палитру
        new_palette = np.array([item[0] for item in palette_with_gamma], dtype=np.uint8)
        
        # Ограничиваем до исходного количества цветов
        if len(new_palette) > original_palette_size:
            new_palette = new_palette[:original_palette_size]
        
        # Создаем маппинг старых индексов на новые
        old_to_new_index = {old_idx: new_idx for new_idx, (_, old_idx, _) in enumerate(palette_with_gamma)}
        
        # Обновляем painted_cells: пересчитываем индексы цветов в палитре
        if editor.painted_cells:
            palette_colors = editor.palette.astype(np.float32)
            new_painted_cells = {}
            
            for (col, row), cell_color in editor.painted_cells.items():
                cell_rgb = self._normalize_color(cell_color)
                if cell_rgb is None:
                    continue
                
                # Находим ближайший цвет в старой палитре
                cell_color_array = np.array(cell_rgb, dtype=np.float32)
                distances = np.sqrt(np.sum((cell_color_array - palette_colors) ** 2, axis=1))
                old_closest_idx = int(np.argmin(distances))
                
                # Получаем новый индекс через маппинг
                if old_closest_idx in old_to_new_index:
                    new_closest_idx = old_to_new_index[old_closest_idx]
                    # Используем цвет из новой палитры
                    new_painted_cells[(col, row)] = tuple(new_palette[new_closest_idx].astype(int))
                else:
                    # Если маппинг не найден, используем цвет как есть
                    new_painted_cells[(col, row)] = cell_rgb
        
        # Обновляем палитру
        editor.palette = new_palette
        editor.palette_manager.set_palette(new_palette)
        
        # Обновляем painted_cells
        if editor.painted_cells:
            editor.painted_cells = new_painted_cells
            
            # Обновляем изображение с новыми цветами из упорядоченной палитры
            if editor.image is not None and len(editor.vertical_lines) >= 2 and len(editor.horizontal_lines) >= 2:
                img_array = np.array(editor.image)
                for (col, row), color in editor.painted_cells.items():
                    if 0 <= col < len(editor.vertical_lines) - 1 and 0 <= row < len(editor.horizontal_lines) - 1:
                        x1 = editor.vertical_lines[col]
                        x2 = editor.vertical_lines[col + 1]
                        y1 = editor.horizontal_lines[row]
                        y2 = editor.horizontal_lines[row + 1]
                        
                        color_tuple = self._normalize_color(color)
                        if color_tuple:
                            if len(img_array.shape) == 3:
                                if img_array.shape[2] == 4:
                                    img_array[y1:y2, x1:x2, 0] = color_tuple[0]
                                    img_array[y1:y2, x1:x2, 1] = color_tuple[1]
                                    img_array[y1:y2, x1:x2, 2] = color_tuple[2]
                                else:
                                    img_array[y1:y2, x1:x2] = color_tuple
                
                from PIL import Image
                editor.image = Image.fromarray(img_array.astype(np.uint8))
        
        # Обновляем selected_color, если он был выбран
        if editor.selected_color is not None:
            selected_rgb = self._normalize_color(editor.selected_color)
            if selected_rgb:
                new_palette_colors = new_palette.astype(np.float32)
                selected_array = np.array(selected_rgb, dtype=np.float32)
                distances = np.sqrt(np.sum((selected_array - new_palette_colors) ** 2, axis=1))
                new_selected_idx = int(np.argmin(distances))
                editor.selected_color = new_palette[new_selected_idx]
        
        try:
            from utils.logger import setup_logger
            logger = setup_logger(__name__)
            logger.info(f"Палитра упорядочена по номерам Гаммы ({len(new_palette)} цветов)")
        except:
            pass
        
        # Обновляем отображение
        editor.update_display()

    def display_palette(self):
        """Отображает палитру цветов над изображением."""
        editor = self.editor

        if editor.palette is None or len(editor.palette) == 0:
            # Очищаем палитру, если её нет
            for widget in editor.palette_frame.winfo_children():
                widget.destroy()
            editor.palette_canvas = None
            return

        # Очищаем предыдущую палитру
        for widget in editor.palette_frame.winfo_children():
            widget.destroy()

        # Создаем canvas для палитры (увеличиваем высоту для нумерации под кубиками)
        palette_canvas = tk.Canvas(editor.palette_frame, bg='lightgray', height=80)
        palette_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Получаем номера Гаммы и RGB цвета Гаммы для каждого цвета
        gamma_numbers = {}
        gamma_rgb_colors = {}  # Сохраняем RGB цвета Гаммы для правильного отображения
        from utils.path_utils import get_static_path
        gamma_excel_path = get_static_path("DMCtoGamma_with_Gamma_OFF_formattedColor.xlsx")
        if HAS_GAMMA_FUNCTION and HAS_PANDAS and os.path.exists(gamma_excel_path):
            for i, color in enumerate(editor.palette):
                normalized_color = self._normalize_color(color)
                if normalized_color:
                    gamma_num, gamma_rgb, distance = find_closest_gamma_color(normalized_color, gamma_excel_path)
                    if gamma_num and gamma_rgb:
                        # Нормализуем номер Гаммы (убираем префикс G, если есть)
                        gamma_str = str(gamma_num).strip().upper()
                        if gamma_str.startswith('G'):
                            gamma_str = gamma_str[1:]
                        gamma_numbers[i] = gamma_str
                        # Сохраняем RGB цвет Гаммы для правильного отображения
                        gamma_rgb_colors[i] = gamma_rgb
                    else:
                        gamma_numbers[i] = ""
                else:
                    gamma_numbers[i] = ""
        else:
            # Если нет функции или файла, заполняем пустыми строками
            gamma_numbers = {i: "" for i in range(len(editor.palette))}

        # Подсчитываем количество ячеек для каждого цвета палитры
        # Сначала считаем по индексам, потом суммируем по Гамме
        color_counts_by_index = {i: 0 for i in range(len(editor.palette))}

        if editor.painted_cells:
            palette_colors = editor.palette.astype(np.float32)

            for cell_color in editor.painted_cells.values():
                cell_rgb = self._normalize_color(cell_color)
                if cell_rgb is None:
                    continue

                cell_color_array = np.array(cell_rgb, dtype=np.float32)
                distances = np.sqrt(np.sum((cell_color_array - palette_colors) ** 2, axis=1))
                closest_idx = int(np.argmin(distances))
                color_counts_by_index[closest_idx] = color_counts_by_index.get(closest_idx, 0) + 1

        # Суммируем количество ячеек по номерам Гаммы
        # Создаем маппинг: номер Гаммы -> список индексов с этой Гаммой
        gamma_to_indices = {}
        for i, gamma_num in gamma_numbers.items():
            gamma_key = gamma_num if gamma_num else f"NO_GAMMA_{i}"
            if gamma_key not in gamma_to_indices:
                gamma_to_indices[gamma_key] = []
            gamma_to_indices[gamma_key].append(i)
        
        # Суммируем количество ячеек для цветов с одинаковой Гаммой
        color_counts = {}
        for i in range(len(editor.palette)):
            gamma_key = gamma_numbers[i] if gamma_numbers[i] else f"NO_GAMMA_{i}"
            # Суммируем все цвета с этой Гаммой
            total_count = sum(color_counts_by_index.get(idx, 0) for idx in gamma_to_indices.get(gamma_key, [i]))
            color_counts[i] = total_count

        # Гаммы, которые повторяются у нескольких цветов (для красной подсветки номеров)
        duplicate_gamma_keys = {
            g for g, indices in gamma_to_indices.items()
            if not g.startswith("NO_GAMMA_") and len(indices) > 1
        }

        color_size = 40
        spacing = 5
        start_x = 10

        for i, color in enumerate(editor.palette):
            x1 = start_x + i * (color_size + spacing)
            y1 = 5
            x2 = x1 + color_size
            y2 = y1 + color_size

            gamma_key = gamma_numbers.get(i, "") or f"NO_GAMMA_{i}"
            # Если у нескольких цветов палитры один номер Гаммы — показываем реальный цвет палитры,
            # иначе два разных оттенка выглядят одинаково. Иначе используем RGB Гаммы.
            if gamma_key in duplicate_gamma_keys:
                rgb_color = (int(color[0]), int(color[1]), int(color[2]))
            elif i in gamma_rgb_colors:
                rgb_color = tuple(int(c) for c in gamma_rgb_colors[i])
            else:
                rgb_color = (int(color[0]), int(color[1]), int(color[2]))

            rect_id = palette_canvas.create_rectangle(
                x1,
                y1,
                x2,
                y2,
                fill=f"#{rgb_color[0]:02x}{rgb_color[1]:02x}{rgb_color[2]:02x}",
                outline='black',
                width=1,
                tags=f"color_{i}",
            )

            palette_canvas.itemconfig(
                rect_id,
                tags=(
                    f"color_{i}",
                    f"rgb_{rgb_color[0]}_{rgb_color[1]}_{rgb_color[2]}",
                ),
            )

            # Показываем количество ячеек именно этого цвета палитры, а не сумму по Гамме
            count = color_counts_by_index.get(i, 0)
            text_x = x1 + color_size / 2
            text_y = y1 + color_size / 2 - 8  # Смещаем вверх для количества
            brightness = (rgb_color[0] * 299 + rgb_color[1] * 587 + rgb_color[2] * 114) / 1000
            text_color = 'white' if brightness < 128 else 'black'

            # Отображаем количество ячеек
            palette_canvas.create_text(
                text_x,
                text_y,
                text=str(count),
                fill=text_color,
                font=('Arial', 9, 'bold'),
                tags=f"count_{i}",
            )

            # Отображаем номер Гаммы под количеством
            gamma_num = gamma_numbers.get(i, "")
            if gamma_num:
                palette_canvas.create_text(
                    text_x,
                    text_y + 12,  # Смещаем вниз для номера Гаммы
                    text=f"G{gamma_num}",
                    fill=text_color,
                    font=('Arial', 7),
                    tags=f"gamma_{i}",
                )
            
            # Отображаем нумерацию под кубиком
            number_y = y2 + 10  # Позиция под квадратиком с отступом
            # Красный — у цветов с одинаковой гаммой; оранжевый — если ячеек < 50; иначе чёрный
            if gamma_key in duplicate_gamma_keys:
                number_color = 'red'
            elif count < 50:
                number_color = 'orange'
            else:
                number_color = 'black'
            palette_canvas.create_text(
                text_x,
                number_y,
                text=str(i + 1),  # Нумерация начиная с 1
                fill=number_color,
                font=('Arial', 8, 'bold'),
                tags=f"number_{i}",
            )

        # Добавляем кнопку добавления нового цвета в конце палитры
        add_color_x1 = start_x + len(editor.palette) * (color_size + spacing)
        add_color_y1 = 5
        add_color_x2 = add_color_x1 + color_size
        add_color_y2 = add_color_y1 + color_size
        
        # Рисуем прямоугольник для кнопки добавления
        add_button_rect = palette_canvas.create_rectangle(
            add_color_x1,
            add_color_y1,
            add_color_x2,
            add_color_y2,
            fill='lightgray',
            outline='black',
            width=1,
            tags="add_color_button",
        )
        
        # Рисуем плюсик в центре
        center_x = add_color_x1 + color_size / 2
        center_y = add_color_y1 + color_size / 2
        line_length = color_size / 3
        
        # Горизонтальная линия плюсика
        palette_canvas.create_line(
            center_x - line_length,
            center_y,
            center_x + line_length,
            center_y,
            fill='black',
            width=2,
            tags="add_color_button",
        )
        
        # Вертикальная линия плюсика
        palette_canvas.create_line(
            center_x,
            center_y - line_length,
            center_x,
            center_y + line_length,
            fill='black',
            width=2,
            tags="add_color_button",
        )

        # Добавляем кнопку обновления палитры справа от кнопки "+"
        refresh_button_x1 = add_color_x2 + spacing
        refresh_button_y1 = add_color_y1
        refresh_button_x2 = refresh_button_x1 + color_size * 1.5
        refresh_button_y2 = add_color_y2
        
        # Рисуем прямоугольник для кнопки обновления
        refresh_button_rect = palette_canvas.create_rectangle(
            refresh_button_x1,
            refresh_button_y1,
            refresh_button_x2,
            refresh_button_y2,
            fill='lightgray',
            outline='black',
            width=1,
            tags="refresh_palette_button",
        )
        
        # Текст "Обновить" на кнопке
        refresh_text_x = refresh_button_x1 + (refresh_button_x2 - refresh_button_x1) / 2
        refresh_text_y = refresh_button_y1 + (refresh_button_y2 - refresh_button_y1) / 2
        palette_canvas.create_text(
            refresh_text_x,
            refresh_text_y,
            text="Обновить",
            fill='black',
            font=('Arial', 8, 'bold'),
            tags="refresh_palette_button",
        )

        palette_canvas.bind('<Button-1>', self.on_palette_click)
        palette_canvas.bind('<Double-Button-1>', self.on_palette_double_click)
        palette_canvas.bind('<Button-3>', self.on_palette_right_click)
        
        # Добавляем tooltip для обеих кнопок (добавления и обновления)
        self._add_palette_buttons_tooltips(palette_canvas, 
                                           add_color_x1, add_color_y1, add_color_x2, add_color_y2,
                                           refresh_button_x1, refresh_button_y1, refresh_button_x2, refresh_button_y2)

        editor.palette_canvas = palette_canvas

    def on_palette_click(self, event):
        """Обрабатывает клик по палитре."""
        editor = self.editor

        if editor.palette_canvas is None or editor.palette is None:
            return

        # Параметры палитры (должны совпадать с display_palette)
        color_size = 40
        spacing = 5
        start_x = 10
        y1 = 5
        y2 = y1 + color_size

        # Проверяем, был ли клик по кнопке добавления цвета
        add_color_x1 = start_x + len(editor.palette) * (color_size + spacing)
        add_color_x2 = add_color_x1 + color_size
        if add_color_x1 <= event.x <= add_color_x2 and y1 <= event.y <= y2:
            self._add_color_to_palette()
            return
        
        # Проверяем, был ли клик по кнопке обновления палитры
        refresh_button_x1 = add_color_x2 + spacing
        refresh_button_x2 = refresh_button_x1 + color_size * 1.5
        if refresh_button_x1 <= event.x <= refresh_button_x2 and y1 <= event.y <= y2:
            self.refresh_palette_counts()
            return

        # Проверяем, попадает ли клик в область какого-либо прямоугольника цвета
        for i in range(len(editor.palette)):
            x1 = start_x + i * (color_size + spacing)
            x2 = x1 + color_size
            
            # Проверяем, попадает ли клик в область прямоугольника цвета
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                # Клик попал в область прямоугольника цвета
                editor.selected_color = editor.palette[i]
                self.highlight_color_in_palette(i)
                rgb = tuple(editor.selected_color)
                editor.info_label.config(text=f"Выбран цвет:\nRGB: {rgb}")
                # То же контекстное меню, что и по правой кнопке
                self._show_palette_color_context_menu(i, event.x_root, event.y_root)
                return

    def on_palette_double_click(self, event):
        """Обрабатывает двойной клик по палитре для редактирования цвета."""
        editor = self.editor

        if editor.palette_canvas is None:
            return

        item = editor.palette_canvas.find_closest(event.x, event.y)[0]
        tags = editor.palette_canvas.gettags(item)

        color_idx = None
        for tag in tags:
            if tag.startswith('color_'):
                color_idx = int(tag.split('_')[1])
                break

        if color_idx is None or color_idx >= len(editor.palette):
            return

        old_color = editor.palette[color_idx]
        old_color_rgb = self._normalize_color(old_color)

        color_hex = f"#{old_color_rgb[0]:02x}{old_color_rgb[1]:02x}{old_color_rgb[2]:02x}"
        new_color = colorchooser.askcolor(color=color_hex, title="Выберите новый цвет")

        if new_color[1] is None:
            return

        editor.save_state()

        new_color_rgb = tuple(int(c) for c in new_color[0])
        new_color_array = np.array(new_color_rgb, dtype=np.uint8)
        editor.palette[color_idx] = new_color_array

        cells_updated = 0
        for (col, row), cell_color in list(editor.painted_cells.items()):
            cell_color_normalized = self._normalize_color(cell_color)
            if cell_color_normalized is None:
                continue

            if cell_color_normalized == tuple(old_color_rgb):
                editor.painted_cells[(col, row)] = new_color_rgb
                cells_updated += 1

        if cells_updated > 0 and editor.image is not None:
            if editor.original_image is not None:
                img_copy = editor.original_image.copy()
            else:
                img_copy = editor.image.copy()

            draw = ImageDraw.Draw(img_copy)
            for (col, row), color in editor.painted_cells.items():
                if 0 <= col < len(editor.vertical_lines) - 1 and 0 <= row < len(editor.horizontal_lines) - 1:
                    x1 = editor.vertical_lines[col]
                    x2 = editor.vertical_lines[col + 1]
                    y1 = editor.horizontal_lines[row]
                    y2 = editor.horizontal_lines[row + 1]
                    draw.rectangle([x1, y1, x2 - 1, y2 - 1], fill=color, outline=None)

            editor.image = img_copy

        if editor.selected_color is not None and np.array_equal(editor.selected_color, old_color):
            editor.selected_color = new_color_array

        # Упорядочиваем палитру по номерам Гаммы после изменения цвета
        self.sort_palette_by_gamma()
        
        self.display_palette()
        editor.update_display()

        editor.info_label.config(
            text=(
                f"Цвет изменен:\n"
                f"Старый: {old_color_rgb}\n"
                f"Новый: {new_color_rgb}\n"
                f"Обновлено ячеек: {cells_updated}\n"
                f"(Отмена: Ctrl+Z)"
            )
        )

    def _show_palette_color_context_menu(self, color_idx, x_root, y_root):
        """Показывает контекстное меню для цвета палитры по индексу (ЛКМ и ПКМ)."""
        editor = self.editor
        if color_idx is None or color_idx < 0 or color_idx >= len(editor.palette):
            return

        context_menu = tk.Menu(editor.root, tearoff=0)
        context_menu.add_command(
            label="Выбрать все ячейки",
            command=lambda: self.select_all_cells_with_color(color_idx),
        )
        context_menu.add_command(
            label="Убрать выделение ячеек",
            command=self.clear_selected_cells,
        )
        context_menu.add_separator()
        context_menu.add_command(
            label="Удалить цвет",
            command=lambda: self.delete_color_from_palette(color_idx),
        )
        context_menu.add_command(
            label="Заменить цвет на близкий в текущей палитре",
            command=lambda: self.replace_with_closest_color(color_idx),
        )
        context_menu.add_command(
            label="Заменить цвет из палитры Гаммы",
            command=lambda: self.replace_with_gamma_color(color_idx),
        )

        try:
            context_menu.tk_popup(x_root, y_root)
        finally:
            context_menu.grab_release()

    def on_palette_right_click(self, event):
        """Обрабатывает правый клик по палитре для вызова контекстного меню."""
        editor = self.editor

        if editor.palette_canvas is None:
            return

        item = editor.palette_canvas.find_closest(event.x, event.y)[0]
        tags = editor.palette_canvas.gettags(item)

        color_idx = None
        for tag in tags:
            if tag.startswith('color_'):
                color_idx = int(tag.split('_')[1])
                break

        if color_idx is None or color_idx >= len(editor.palette):
            return

        self._show_palette_color_context_menu(color_idx, event.x_root, event.y_root)

    def select_all_cells_with_color(self, color_idx):
        """Выбирает все ячейки с указанным цветом из палитры и обводит связанные области."""
        editor = self.editor

        if color_idx < 0 or color_idx >= len(editor.palette):
            return

        palette_color = editor.palette[color_idx]
        palette_rgb = self._normalize_color(palette_color)

        matching_cells_set = set()
        if editor.painted_cells:
            palette_colors = editor.palette.astype(np.float32)

            for (col, row), cell_color in editor.painted_cells.items():
                cell_rgb = self._normalize_color(cell_color)
                if cell_rgb is None:
                    continue

                cell_color_array = np.array(cell_rgb, dtype=np.float32)
                distances = np.sqrt(np.sum((cell_color_array - palette_colors) ** 2, axis=1))
                closest_idx = int(np.argmin(distances))

                if closest_idx == color_idx:
                    matching_cells_set.add((col, row))

        if not matching_cells_set:
            messagebox.showinfo("Информация", "Нет ячеек с выбранным цветом")
            return

        regions = self._find_connected_regions(matching_cells_set)

        if not regions:
            messagebox.showinfo("Информация", "Нет ячеек с выбранным цветом")
            return

        editor.selected_regions = regions
        editor.update_display()

        total_cells = sum(len(region) for region in regions)
        messagebox.showinfo(
            "Информация",
            f"Найдено {len(regions)} областей с выбранным цветом\nВсего ячеек: {total_cells}",
        )

    def clear_selected_cells(self):
        """Убирает выделение со всех ячеек."""
        editor = self.editor
        
        if not editor.selected_regions:
            messagebox.showinfo("Информация", "Нет выделенных ячеек")
            return
        
        editor.selected_regions = []
        editor.update_display()
        messagebox.showinfo("Информация", "Выделение убрано")

    def _show_delete_color_dialog(self, color_rgb):
        """
        Показывает диалог выбора действия при удалении цвета.
        
        Returns:
            str: 'replace' - удалить с заменой ячеек на ближайший цвет из палитры,
                 'delete' - просто удалить, None - отмена
        """
        dialog = tk.Toplevel(self.editor.root)
        dialog.title("Удаление цвета из палитры")
        dialog.resizable(False, False)
        dialog.transient(self.editor.root)
        dialog.grab_set()
        
        result = {'action': None}
        
        # Основной фрейм с отступами
        main_frame = tk.Frame(dialog, padx=15, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Текст вопроса
        question_label = tk.Label(
            main_frame,
            text="Что сделать с этим цветом?",
            font=('Arial', 10, 'bold')
        )
        question_label.pack(pady=(0, 10))
        
        # Фрейм для кнопок
        buttons_frame = tk.Frame(main_frame)
        buttons_frame.pack()
        
        # Центрируем диалог после создания содержимого
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Кнопка "Удалить с заменой на цвет из палитры"
        replace_button = tk.Button(
            buttons_frame,
            text="Удалить с заменой на цвет из палитры",
            command=lambda: self._set_result_and_close(dialog, result, 'replace'),
            font=('Arial', 9),
            width=36,
            bg='lightblue'
        )
        replace_button.pack(side=tk.LEFT, padx=5)
        
        # Кнопка "Просто удалить"
        delete_button = tk.Button(
            buttons_frame,
            text="Просто удалить",
            command=lambda: self._set_result_and_close(dialog, result, 'delete'),
            font=('Arial', 9),
            width=20,
            bg='lightcoral'
        )
        delete_button.pack(side=tk.LEFT, padx=5)
        
        # Кнопка "Отмена"
        cancel_button = tk.Button(
            buttons_frame,
            text="Отмена",
            command=lambda: self._set_result_and_close(dialog, result, None),
            font=('Arial', 9),
            width=15
        )
        cancel_button.pack(side=tk.LEFT, padx=5)
        
        # Ждем закрытия диалога
        dialog.wait_window()
        
        return result['action']
    
    def _set_result_and_close(self, dialog, result, action):
        """Устанавливает результат и закрывает диалог"""
        result['action'] = action
        dialog.destroy()
    
    def delete_color_from_palette(self, color_idx):
        """Удаляет цвет из палитры и очищает все ячейки с этим цветом."""
        editor = self.editor

        if color_idx < 0 or color_idx >= len(editor.palette):
            return

        palette_color = editor.palette[color_idx]
        palette_rgb = self._normalize_color(palette_color)
        
        if palette_rgb is None:
            messagebox.showerror("Ошибка", "Не удалось определить цвет")
            return

        # Показываем диалог выбора действия
        action = self._show_delete_color_dialog(palette_rgb)
        
        if action is None:
            return  # Пользователь отменил
        
        # Замена на ближайший цвет из текущей палитры (та же логика, что в контекстном меню)
        if action == 'replace':
            self.replace_with_closest_color(color_idx)
            return
        
        editor.save_state()
        
        # Просто удаление
        cells_to_remove = []
        if editor.painted_cells:
            palette_colors = editor.palette.astype(np.float32)

            for (col, row), cell_color in editor.painted_cells.items():
                cell_rgb = self._normalize_color(cell_color)
                if cell_rgb is None:
                    continue

                cell_color_array = np.array(cell_rgb, dtype=np.float32)
                distances = np.sqrt(np.sum((cell_color_array - palette_colors) ** 2, axis=1))
                closest_idx = int(np.argmin(distances))

                if closest_idx == color_idx:
                    cells_to_remove.append((col, row))

        for cell in cells_to_remove:
            editor.painted_cells.pop(cell, None)

        editor.palette = np.delete(editor.palette, color_idx, axis=0)

        if editor.selected_color is not None:
            selected_rgb = self._normalize_color(editor.selected_color)
            if selected_rgb == palette_rgb:
                editor.selected_color = None

        if editor.original_image is not None and cells_to_remove:
            img_array = np.array(editor.image)
            original_array = np.array(editor.original_image)

            for (col, row) in cells_to_remove:
                if 0 <= col < len(editor.vertical_lines) - 1 and 0 <= row < len(editor.horizontal_lines) - 1:
                    x1 = editor.vertical_lines[col]
                    x2 = editor.vertical_lines[col + 1]
                    y1 = editor.horizontal_lines[row]
                    y2 = editor.horizontal_lines[row + 1]

                    if original_array.shape[2] == 4:
                        img_array[y1:y2, x1:x2, :3] = original_array[y1:y2, x1:x2, :3]
                    else:
                        img_array[y1:y2, x1:x2] = original_array[y1:y2, x1:x2]

            editor.image = Image.fromarray(img_array.astype(np.uint8))

        editor.update_display()
        self.display_palette()
        
        # Обновляем информацию в футере
        editor.update_footer_info()

        messagebox.showinfo(
            "Успех",
            f"Удалено {len(cells_to_remove)} ячеек и цвет из палитры",
        )

    def replace_with_closest_color(self, color_idx):
        """Заменяет все ячейки с указанным цветом на наиболее близкий цвет из палитры."""
        editor = self.editor

        if color_idx < 0 or color_idx >= len(editor.palette):
            return

        if len(editor.palette) <= 1:
            messagebox.showwarning("Предупреждение", "В палитре недостаточно цветов для замены")
            return

        editor.save_state()

        palette_color = editor.palette[color_idx]
        palette_rgb = self._normalize_color(palette_color)

        palette_colors = editor.palette.astype(np.float32)
        palette_color_array = np.array(palette_rgb, dtype=np.float32)
        distances = np.sqrt(np.sum((palette_color_array - palette_colors) ** 2, axis=1))
        distances[color_idx] = float('inf')

        closest_idx = int(np.argmin(distances))
        closest_color = editor.palette[closest_idx]
        # Используем точный цвет из палитры для правильного подсчета
        closest_rgb = tuple(int(c) for c in closest_color[:3])

        cells_replaced = 0
        if editor.painted_cells:
            for (col, row), cell_color in list(editor.painted_cells.items()):
                cell_rgb = self._normalize_color(cell_color)
                if cell_rgb is None:
                    continue

                cell_color_array = np.array(cell_rgb, dtype=np.float32)
                cell_distances = np.sqrt(np.sum((cell_color_array - palette_colors) ** 2, axis=1))
                cell_closest_idx = int(np.argmin(cell_distances))

                if cell_closest_idx == color_idx:
                    # Используем точный цвет из палитры
                    editor.painted_cells[(col, row)] = closest_rgb
                    cells_replaced += 1

        if cells_replaced > 0:
            img_array = np.array(editor.image)
            for (col, row), color in editor.painted_cells.items():
                if 0 <= col < len(editor.vertical_lines) - 1 and 0 <= row < len(editor.horizontal_lines) - 1:
                    x1 = editor.vertical_lines[col]
                    x2 = editor.vertical_lines[col + 1]
                    y1 = editor.horizontal_lines[row]
                    y2 = editor.horizontal_lines[row + 1]

                    color_tuple = self._normalize_color(color)

                    if img_array.shape[2] == 4:
                        img_array[y1:y2, x1:x2, 0] = color_tuple[0]
                        img_array[y1:y2, x1:x2, 1] = color_tuple[1]
                        img_array[y1:y2, x1:x2, 2] = color_tuple[2]
                    else:
                        img_array[y1:y2, x1:x2] = color_tuple

            editor.image = Image.fromarray(img_array.astype(np.uint8))
            
            # Удаляем замененный цвет из палитры, так как все ячейки теперь используют ближайший цвет
            # Проверяем, есть ли еще ячейки с удаляемым цветом
            remaining_cells_with_old_color = 0
            if editor.painted_cells:
                palette_colors_after = editor.palette.astype(np.float32)
                for cell_color in editor.painted_cells.values():
                    cell_rgb = self._normalize_color(cell_color)
                    if cell_rgb is None:
                        continue
                    cell_color_array = np.array(cell_rgb, dtype=np.float32)
                    cell_distances = np.sqrt(np.sum((cell_color_array - palette_colors_after) ** 2, axis=1))
                    cell_closest_idx = int(np.argmin(cell_distances))
                    if cell_closest_idx == color_idx:
                        remaining_cells_with_old_color += 1
            
            # Удаляем цвет из палитры только если нет ячеек с этим цветом
            if remaining_cells_with_old_color == 0 and color_idx < len(editor.palette):
                editor.palette = np.delete(editor.palette, color_idx, axis=0)
                # Обновляем palette_manager
                if hasattr(editor, 'palette_manager'):
                    editor.palette_manager.set_palette(editor.palette)

        # Упорядочиваем палитру по возрастанию (по Гамме или RGB)
        self.sort_palette_by_gamma()
        
        editor.update_display()
        self.display_palette()
        
        # Обновляем информацию в футере
        editor.update_footer_info()

        messagebox.showinfo(
            "Успех",
            f"Заменено {cells_replaced} ячеек на ближайший цвет из палитры",
        )
    
    def replace_with_gamma_color(self, color_idx):
        """Заменяет все ячейки с выбранным цветом на цвет из палитры Гаммы"""
        editor = self.editor
        
        if color_idx < 0 or color_idx >= len(editor.palette):
            return
        
        palette_color = editor.palette[color_idx]
        palette_rgb = self._normalize_color(palette_color)
        
        if palette_rgb is None:
            messagebox.showerror("Ошибка", "Не удалось определить цвет")
            return
        
        # Номер Гаммы для этого цвета палитры — тот же, что показывается в палитре (из Excel)
        target_gamma_code = None
        if HAS_GAMMA_FUNCTION:
            from utils.path_utils import get_static_path
            gamma_excel_path = get_static_path("DMCtoGamma_with_Gamma_OFF_formattedColor.xlsx")
            if os.path.exists(gamma_excel_path):
                gamma_num, gamma_rgb, _ = find_closest_gamma_color(palette_rgb, gamma_excel_path)
                if gamma_num:
                    gamma_str = str(gamma_num).strip().upper()
                    if gamma_str.startswith('G'):
                        gamma_str = gamma_str[1:]
                    target_gamma_code = gamma_str
        
        # Показываем диалог выбора цвета из Гаммы
        from ui.gamma_color_picker import GammaColorPicker
        
        picker = GammaColorPicker(editor.root, target_color_rgb=palette_rgb, target_gamma_code=target_gamma_code)
        new_color_rgb, color_info = picker.show()
        
        if new_color_rgb is None:
            return  # Пользователь отменил
        
        # Сохраняем состояние перед заменой
        editor.save_state()
        
        # Находим все ячейки с этим цветом
        cells_to_replace = []
        if editor.painted_cells:
            palette_colors = editor.palette.astype(np.float32)
            
            for (col, row), cell_color in editor.painted_cells.items():
                cell_rgb = self._normalize_color(cell_color)
                if cell_rgb is None:
                    continue
                
                cell_color_array = np.array(cell_rgb, dtype=np.float32)
                distances = np.sqrt(np.sum((cell_color_array - palette_colors) ** 2, axis=1))
                closest_idx = int(np.argmin(distances))
                
                if closest_idx == color_idx:
                    cells_to_replace.append((col, row))
        
        if not cells_to_replace:
            messagebox.showinfo("Информация", "Нет ячеек с выбранным цветом")
            return
        
        # Убеждаемся, что new_color_rgb - это кортеж целых чисел
        if isinstance(new_color_rgb, (list, tuple)):
            new_color_tuple = (int(new_color_rgb[0]), int(new_color_rgb[1]), int(new_color_rgb[2]))
        else:
            messagebox.showerror("Ошибка", "Неверный формат цвета")
            return
        
        # Заменяем цвет во всех найденных ячейках
        img_array = np.array(editor.image)
        cells_replaced = 0
        
        for (col, row) in cells_to_replace:
            if 0 <= col < len(editor.vertical_lines) - 1 and 0 <= row < len(editor.horizontal_lines) - 1:
                x1 = editor.vertical_lines[col]
                x2 = editor.vertical_lines[col + 1]
                y1 = editor.horizontal_lines[row]
                y2 = editor.horizontal_lines[row + 1]
                
                # Обновляем изображение
                if len(img_array.shape) == 3:
                    if img_array.shape[2] == 4:
                        img_array[y1:y2, x1:x2, 0] = new_color_tuple[0]
                        img_array[y1:y2, x1:x2, 1] = new_color_tuple[1]
                        img_array[y1:y2, x1:x2, 2] = new_color_tuple[2]
                    else:
                        img_array[y1:y2, x1:x2] = new_color_tuple
                
                # Обновляем информацию о закрашенной ячейке
                editor.painted_cells[(col, row)] = new_color_tuple
                cells_replaced += 1
        
        # Обновляем изображение
        editor.image = Image.fromarray(img_array.astype(np.uint8))
        
        # Обновляем цвет в палитре
        if editor.palette is not None and color_idx < len(editor.palette):
            editor.palette[color_idx] = np.array(new_color_tuple, dtype=np.uint8)
        
        # Упорядочиваем палитру по возрастанию (по Гамме или RGB)
        self.sort_palette_by_gamma()
        
        # Обновляем отображение
        editor.update_display()
        
        if editor.palette is not None:
            self.display_palette()
        
        # Обновляем информацию в футере
        editor.update_footer_info()
        
        # Показываем информацию о замене
        color_name = color_info.get('name', 'N/A')
        messagebox.showinfo(
            "Успех",
            f"Заменено {cells_replaced} ячеек на цвет из Гаммы: {color_name}\n"
            f"RGB: {new_color_tuple}\n"
            f"Gamma: {color_info.get('gamma', 'N/A')}"
        )

    def highlight_color_in_palette(self, color_idx):
        """Выделяет цвет в палитре по индексу."""
        editor = self.editor

        if editor.palette_canvas is None:
            return

        for i in range(len(editor.palette)):
            try:
                item_id = editor.palette_canvas.find_withtag(f"color_{i}")[0]
                editor.palette_canvas.itemconfig(item_id, outline='black', width=1)
            except (IndexError, tk.TclError):
                continue

        try:
            selected_item = editor.palette_canvas.find_withtag(f"color_{color_idx}")[0]
            editor.palette_canvas.itemconfig(selected_item, outline='yellow', width=3)
        except (IndexError, tk.TclError):
            pass

    @staticmethod
    def _normalize_color(color):
        """Приводит цвет к кортежу RGB из трех целых значений."""
        if color is None:
            return None

        try:
            if isinstance(color, np.ndarray):
                if color.size >= 3:
                    return tuple(int(float(c)) for c in color[:3])
            elif isinstance(color, (list, tuple)):
                if len(color) >= 3:
                    return tuple(int(float(c)) for c in color[:3])
            else:
                color_list = list(color)[:3] if hasattr(color, '__iter__') else []
                if len(color_list) >= 3:
                    return tuple(int(float(c)) for c in color_list)
        except (ValueError, TypeError):
            return None

        return None

    @staticmethod
    def _find_connected_regions(cells_set):
        """Находит связанные области (connected components) из набора ячеек."""
        if not cells_set:
            return []

        regions = []
        visited = set()

        def get_neighbors(col, row):
            neighbors = []
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                neighbor = (col + dx, row + dy)
                if neighbor in cells_set:
                    neighbors.append(neighbor)
            return neighbors

        # Итеративный DFS с использованием стека вместо рекурсии
        def dfs_iterative(start_col, start_row, region):
            stack = [(start_col, start_row)]
            while stack:
                col, row = stack.pop()
                if (col, row) in visited:
                    continue
                visited.add((col, row))
                region.add((col, row))
                
                for neighbor in get_neighbors(col, row):
                    if neighbor not in visited:
                        stack.append(neighbor)

        for cell in cells_set:
            if cell not in visited:
                region = set()
                dfs_iterative(cell[0], cell[1], region)
                if region:
                    regions.append(region)

        return regions
    
    def _add_palette_buttons_tooltips(self, canvas, add_x1, add_y1, add_x2, add_y2, 
                                      refresh_x1, refresh_y1, refresh_x2, refresh_y2):
        """Добавляет tooltip для кнопок добавления и обновления палитры."""
        add_tooltip_text = "Добавить новый цвет"
        refresh_tooltip_text = "Пересчет ячеек и упорядочивание палитры"
        tooltip = None
        
        def on_motion(event):
            nonlocal tooltip
            current_tooltip_text = None
            
            # Проверяем, находится ли мышь над кнопкой добавления
            if add_x1 <= event.x <= add_x2 and add_y1 <= event.y <= add_y2:
                current_tooltip_text = add_tooltip_text
            # Проверяем, находится ли мышь над кнопкой обновления
            elif refresh_x1 <= event.x <= refresh_x2 and refresh_y1 <= event.y <= refresh_y2:
                current_tooltip_text = refresh_tooltip_text
            
            # Если мышь над одной из кнопок и tooltip еще не показан или текст изменился
            if current_tooltip_text:
                if (not hasattr(canvas, 'current_tooltip') or canvas.current_tooltip is None or 
                    not hasattr(canvas, 'current_tooltip_text') or canvas.current_tooltip_text != current_tooltip_text):
                    # Скрываем предыдущий tooltip, если он есть
                    if hasattr(canvas, 'current_tooltip') and canvas.current_tooltip is not None:
                        canvas.current_tooltip.destroy()
                    
                    # Показываем новый tooltip
                    tooltip = tk.Toplevel()
                    tooltip.wm_overrideredirect(True)
                    tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
                    label = tk.Label(tooltip, text=current_tooltip_text, background='yellow', 
                                   font=('Arial', 9), relief=tk.SOLID, borderwidth=1)
                    label.pack()
                    canvas.current_tooltip = tooltip
                    canvas.current_tooltip_text = current_tooltip_text
            else:
                # Если мышь не над кнопками, скрываем tooltip
                if hasattr(canvas, 'current_tooltip') and canvas.current_tooltip is not None:
                    canvas.current_tooltip.destroy()
                    canvas.current_tooltip = None
                    if hasattr(canvas, 'current_tooltip_text'):
                        del canvas.current_tooltip_text
        
        def on_leave(event):
            """Скрываем tooltip при выходе мыши из canvas."""
            if hasattr(canvas, 'current_tooltip') and canvas.current_tooltip is not None:
                canvas.current_tooltip.destroy()
                canvas.current_tooltip = None
                if hasattr(canvas, 'current_tooltip_text'):
                    del canvas.current_tooltip_text
        
        canvas.bind('<Motion>', on_motion)
        canvas.bind('<Leave>', on_leave)
    
    def refresh_palette_counts(self):
        """Пересчитывает количество ячеек для каждого цвета в палитре, упорядочивает палитру и обновляет отображение."""
        editor = self.editor
        
        if editor.palette is None or len(editor.palette) == 0:
            return
        
        # Упорядочиваем палитру по возрастанию (по Гамме или RGB)
        self.sort_palette_by_gamma()
        
        # Перерисовываем палитру (пересчитывает количество ячеек на основе painted_cells)
        self.display_palette()
        
        # Обновляем информацию в футере
        editor.update_footer_info()
        
        # Показываем информационное окно
        from utils.version_utils import get_app_name_with_version
        app_name = get_app_name_with_version()
        messagebox.showinfo(f"Информация - {app_name}", "Палитра упорядочена, количество цветных ячеек пересчитано")
    
    def _add_color_to_palette(self):
        """Добавляет новый цвет в палитру через диалог выбора цвета."""
        editor = self.editor
        
        if editor.palette is None:
            # Если палитры нет, создаем пустую
            editor.palette = np.array([], dtype=np.uint8).reshape(0, 3)
        
        # Открываем диалог выбора цвета
        new_color = colorchooser.askcolor(title="Выберите цвет для добавления в палитру")
        
        if new_color[1] is None:  # Пользователь отменил выбор
            return
        
        # Сохраняем состояние перед изменением
        editor.save_state()
        
        # Преобразуем выбранный цвет в numpy массив
        new_color_rgb = tuple(int(c) for c in new_color[0])
        new_color_array = np.array([new_color_rgb], dtype=np.uint8)
        
        # Добавляем цвет в палитру
        editor.palette = np.vstack([editor.palette, new_color_array])
        
        # Обновляем палитру в palette_manager
        if hasattr(editor, 'palette_manager'):
            editor.palette_manager.set_palette(editor.palette)
        
        # Упорядочиваем палитру по номерам Гаммы (как при получении палитры)
        self.sort_palette_by_gamma()
        
        # Обновляем отображение палитры
        self.display_palette()
        
        # Находим индекс добавленного цвета после упорядочивания
        # Ищем цвет в упорядоченной палитре
        new_color_idx = None
        for i, color in enumerate(editor.palette):
            if np.array_equal(color, new_color_array[0]):
                new_color_idx = i
                break
        
        # Если цвет найден, выбираем его
        if new_color_idx is not None:
            editor.selected_color = editor.palette[new_color_idx]
            self.highlight_color_in_palette(new_color_idx)
        else:
            # Если не найден (не должно произойти), выбираем последний
            if len(editor.palette) > 0:
                editor.selected_color = editor.palette[-1]
                self.highlight_color_in_palette(len(editor.palette) - 1)
        
        # Обновляем информацию в футере
        editor.update_footer_info()
        
        from utils.version_utils import get_app_name_with_version
        app_name = get_app_name_with_version()
        messagebox.showinfo(f"Успех - {app_name}", f"Цвет добавлен в палитру!\nRGB: {new_color_rgb}")

