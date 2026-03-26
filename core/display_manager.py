"""Менеджер отображения изображения на canvas"""
import math
import tkinter as tk
from PIL import Image, ImageDraw, ImageTk, ImageFont


class DisplayManager:
    """Управляет отображением изображения на canvas с учетом режимов просмотра, сетки, выделения и зума."""
    
    def __init__(self, editor):
        """
        Args:
            editor: Экземпляр GridEditor
        """
        self.editor = editor
    
    def update_display(self):
        """Обновляет отображение изображения на canvas"""
        if self.editor.image is None:
            # Показываем фрейм с кнопками, скрываем canvas
            if hasattr(self.editor, 'empty_state_frame'):
                self.editor.empty_state_frame.pack(fill=tk.BOTH, expand=True)
            if hasattr(self.editor, 'canvas'):
                self.editor.canvas.pack_forget()
            return
        
        # Скрываем фрейм с кнопками и показываем canvas, если изображение загружено
        if hasattr(self.editor, 'empty_state_frame'):
            self.editor.empty_state_frame.pack_forget()
        if hasattr(self.editor, 'canvas'):
            self.editor.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Получаем прозрачность изображения (по умолчанию 1.0 - непрозрачное)
        image_opacity = getattr(self.editor, 'image_opacity', 1.0)
        
        # Создаем изображение для отображения в зависимости от режима
        if self.editor.view_mode == 1:
            # Режим 1: только исходное изображение + сетка (без закрашенных ячеек)
            # Используем оригинальное изображение
            if self.editor.original_image is not None:
                original_img = self.editor.original_image.copy()
            else:
                original_img = self.editor.image.copy()
            
            # Применяем прозрачность к оригинальному изображению
            if image_opacity < 1.0:
                # Получаем цвет фона
                bg_color_rgb = self.editor.get_background_color_rgb()
                # Создаем фон
                bg_image = Image.new('RGB', original_img.size, bg_color_rgb)
                # Преобразуем оригинальное изображение в RGBA
                original_rgba = original_img.convert('RGBA')
                # Создаем альфа-канал с нужной прозрачностью
                alpha = int(image_opacity * 255)
                alpha_channel = Image.new('L', original_img.size, alpha)
                original_rgba.putalpha(alpha_channel)
                # Накладываем на фон
                self.editor.display_image = Image.alpha_composite(bg_image.convert('RGBA'), original_rgba).convert('RGB')
            else:
                self.editor.display_image = original_img
        elif self.editor.view_mode == 2 or self.editor.view_mode == 4:
            # Режим 2: исходное изображение + сетка + закрашенные ячейки
            # Используем оригинальное изображение и рисуем закрашенные ячейки поверх
            if self.editor.original_image is not None:
                original_img = self.editor.original_image.copy()
            else:
                original_img = self.editor.image.copy()
            
            # Применяем прозрачность к оригинальному изображению
            if image_opacity < 1.0:
                # Получаем цвет фона
                bg_color_rgb = self.editor.get_background_color_rgb()
                # Создаем фон
                bg_image = Image.new('RGB', original_img.size, bg_color_rgb)
                # Преобразуем оригинальное изображение в RGBA
                original_rgba = original_img.convert('RGBA')
                # Создаем альфа-канал с нужной прозрачностью
                alpha = int(image_opacity * 255)
                alpha_channel = Image.new('L', original_img.size, alpha)
                original_rgba.putalpha(alpha_channel)
                # Накладываем на фон
                self.editor.display_image = Image.alpha_composite(bg_image.convert('RGBA'), original_rgba).convert('RGB')
            else:
                self.editor.display_image = original_img
        else:  # view_mode == 3
            # Режим 3: только закрашенные ячейки (без исходного и без сетки)
            # Создаем изображение с цветом подложки
            # Преобразуем цвет подложки в RGB
            bg_color_rgb = self.editor.get_background_color_rgb()
            if self.editor.original_image is not None:
                self.editor.display_image = Image.new('RGB', (self.editor.original_image.width, self.editor.original_image.height), bg_color_rgb)
            else:
                self.editor.display_image = Image.new('RGB', (self.editor.image.width, self.editor.image.height), bg_color_rgb)
        
        draw = ImageDraw.Draw(self.editor.display_image)
        
        # Рисуем закрашенные ячейки поверх изображения (только в режимах 2, 3 и 4)
        if self.editor.view_mode in [2, 3, 4]:
            # Проверяем, включена ли нормализация размеров ячеек
            if getattr(self.editor, 'normalize_cell_sizes', True):
                # Вычисляем нормализованные размеры ячеек
                # Это нужно для того, чтобы все закрашенные ячейки были одного размера
                cell_widths = []
                for i in range(len(self.editor.vertical_lines) - 1):
                    width = self.editor.vertical_lines[i+1] - self.editor.vertical_lines[i]
                    if width > 0:  # Исключаем нулевые размеры
                        cell_widths.append(width)
                
                cell_heights = []
                for i in range(len(self.editor.horizontal_lines) - 1):
                    height = self.editor.horizontal_lines[i+1] - self.editor.horizontal_lines[i]
                    if height > 0:  # Исключаем нулевые размеры
                        cell_heights.append(height)
                
                # Используем медианный размер для нормализации (исключаем слишком маленькие ячейки)
                # Это лучше, чем минимальный размер, так как исключает выбросы (очень маленькие ячейки)
                if cell_widths:
                    # Используем 25-й процентиль вместо минимума, чтобы исключить слишком маленькие ячейки
                    sorted_widths = sorted(cell_widths)
                    percentile_25_idx = max(0, len(sorted_widths) // 4)
                    normalized_width = max(3, sorted_widths[percentile_25_idx])  # Минимум 3 пикселя
                else:
                    normalized_width = 10  # Значение по умолчанию
                
                if cell_heights:
                    # Используем 25-й процентиль вместо минимума, чтобы исключить слишком маленькие ячейки
                    sorted_heights = sorted(cell_heights)
                    percentile_25_idx = max(0, len(sorted_heights) // 4)
                    normalized_height = max(3, sorted_heights[percentile_25_idx])  # Минимум 3 пикселя
                else:
                    normalized_height = 10  # Значение по умолчанию
                
                for (col, row), color in self.editor.painted_cells.items():
                    if 0 <= col < len(self.editor.vertical_lines) - 1 and 0 <= row < len(self.editor.horizontal_lines) - 1:
                        x1 = self.editor.vertical_lines[col]
                        x2 = self.editor.vertical_lines[col + 1]
                        y1 = self.editor.horizontal_lines[row]
                        y2 = self.editor.horizontal_lines[row + 1]
                        
                        # Вычисляем нормализованные координаты для отображения
                        # Центрируем нормализованную ячейку внутри исходной ячейки
                        cell_w = x2 - x1
                        cell_h = y2 - y1
                        
                        # Убеждаемся, что нормализованные размеры не больше размера ячейки
                        actual_width = min(normalized_width, cell_w)
                        actual_height = min(normalized_height, cell_h)
                        
                        offset_x = (cell_w - actual_width) // 2
                        offset_y = (cell_h - actual_height) // 2
                        
                        # Координаты нормализованной области
                        paint_x1 = x1 + offset_x
                        paint_y1 = y1 + offset_y
                        paint_x2 = paint_x1 + actual_width
                        paint_y2 = paint_y1 + actual_height
                        
                        # Убеждаемся, что координаты в пределах ячейки
                        paint_x1 = max(x1, paint_x1)
                        paint_y1 = max(y1, paint_y1)
                        paint_x2 = min(paint_x2, x2)
                        paint_y2 = min(paint_y2, y2)
                        
                        # Убеждаемся, что размеры валидны
                        if paint_x2 > paint_x1 and paint_y2 > paint_y1:
                            draw.rectangle([paint_x1, paint_y1, paint_x2-1, paint_y2-1], fill=color, outline=None)
            else:
                # Быстрая отрисовка без нормализации (как в slicer_2.5)
                for (col, row), color in self.editor.painted_cells.items():
                    if 0 <= col < len(self.editor.vertical_lines) - 1 and 0 <= row < len(self.editor.horizontal_lines) - 1:
                        x1 = self.editor.vertical_lines[col]
                        x2 = self.editor.vertical_lines[col + 1]
                        y1 = self.editor.horizontal_lines[row]
                        y2 = self.editor.horizontal_lines[row + 1]
                        draw.rectangle([x1, y1, x2-1, y2-1], fill=color, outline=None)
        
        # Рисуем сетку (только в режимах 1, 2, 3 и 4, и если включено отображение сетки)
        if self.editor.view_mode in [1, 2, 3, 4] and self.editor.show_grid:
            # Подстраиваем толщину линий для маленького масштаба:
            # при сильном уменьшении 1px-линии могут "пропадать" после ресайза.
            canvas_width = self.editor.canvas.winfo_width()
            canvas_height = self.editor.canvas.winfo_height()
            if canvas_width > 1 and canvas_height > 1:
                base_scale_w = canvas_width / self.editor.display_image.width
                base_scale_h = canvas_height / self.editor.display_image.height
                preview_scale = max(0.1, min(10.0, min(base_scale_w, base_scale_h) * self.editor.zoom))
            else:
                preview_scale = max(0.1, min(10.0, getattr(self.editor, 'scale', 1.0)))

            base_line_width = max(1, int(self.editor.grid_line_width))
            if preview_scale < 1.0:
                effective_line_width = max(base_line_width, int(math.ceil(base_line_width / preview_scale)))
            else:
                effective_line_width = base_line_width

            # Получаем цвета сетки (используем выбранный цвет или цвет по умолчанию)
            # Приглушенные цвета для лучшей видимости
            default_vertical_color = getattr(self.editor, 'grid_color', (180, 80, 80))  # Приглушенный красный
            default_horizontal_color = getattr(self.editor, 'grid_color_horizontal', (180, 80, 80))  # Приглушенный красный
            selected_vertical_color = (255, 0, 0)  # Яркий красный для выбранной вертикальной линии
            selected_horizontal_color = (0, 0, 255)  # Яркий синий для выбранной горизонтальной линии
            
            # Цвет для разметки каждых 10 ячеек - приглушенный синий
            marker_color = (80, 80, 180)  # Приглушенный синий для разметки по 10 ячейкам
            
            # Загружаем шрифт для цифр (размер зависит от масштаба изображения)
            try:
                # Пробуем загрузить системный шрифт
                font_size = max(10, min(20, int(self.editor.display_image.width / 100)))
                try:
                    # Пробуем Arial на Windows
                    grid_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", font_size)
                except:
                    try:
                        # Пробуем DejaVu на Linux
                        grid_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
                    except:
                        # Используем дефолтный шрифт
                        grid_font = ImageFont.load_default()
            except:
                grid_font = ImageFont.load_default()
            
            # Рисуем вертикальные линии
            for i, x in enumerate(self.editor.vertical_lines):
                if self.editor.selected_line == x and self.editor.selected_line_type == 'v':
                    color = selected_vertical_color
                else:
                    # Каждые 10 линий (индексы 0, 10, 20, 30...) делаем синими
                    if i % 10 == 0:
                        color = marker_color
                    else:
                        color = default_vertical_color
                # Рисуем линию через прямоугольник для избежания антиалиасинга и ореола
                line_width = effective_line_width
                if line_width == 1:
                    # Для тонкой линии рисуем вертикальный прямоугольник шириной 1 пиксель
                    draw.rectangle([x, 0, x, self.editor.display_image.height - 1], fill=color, outline=None)
                else:
                    # Для толстых линий рисуем прямоугольник с центром на x
                    x1 = max(0, x - line_width // 2)
                    x2 = min(self.editor.display_image.width - 1, x + line_width // 2 + (line_width % 2))
                    draw.rectangle([x1, 0, x2, self.editor.display_image.height - 1], fill=color, outline=None)
                
                # Выводим цифры у синих линий (каждые 10, начиная с 10)
                if i % 10 == 0 and i > 0:
                    number_text = str(i)
                    # Получаем размер текста
                    try:
                        bbox = draw.textbbox((0, 0), number_text, font=grid_font)
                        text_width = bbox[2] - bbox[0]
                        text_height = bbox[3] - bbox[1]
                    except:
                        # Если textbbox не поддерживается, используем приблизительные размеры
                        text_width = len(number_text) * font_size * 0.6
                        text_height = font_size
                    
                    # Размещаем цифру справа от линии, вверху
                    text_x = x + 3  # Небольшой отступ от линии
                    text_y = 2  # Вверху изображения
                    # Рисуем белый фон для читаемости (RGB режим, без альфа)
                    draw.rectangle([text_x - 1, text_y - 1, text_x + text_width + 1, text_y + text_height + 1], 
                                 fill=(255, 255, 255), outline=None)
                    draw.text((text_x, text_y), number_text, font=grid_font, fill=(0, 0, 0))
            
            # Рисуем горизонтальные линии
            for i, y in enumerate(self.editor.horizontal_lines):
                if self.editor.selected_line == y and self.editor.selected_line_type == 'h':
                    color = selected_horizontal_color
                else:
                    # Каждые 10 линий (индексы 0, 10, 20, 30...) делаем синими
                    if i % 10 == 0:
                        color = marker_color
                    else:
                        color = default_horizontal_color
                # Рисуем линию через прямоугольник для избежания антиалиасинга и ореола
                line_width = effective_line_width
                if line_width == 1:
                    # Для тонкой линии рисуем горизонтальный прямоугольник высотой 1 пиксель
                    draw.rectangle([0, y, self.editor.display_image.width - 1, y], fill=color, outline=None)
                else:
                    # Для толстых линий рисуем прямоугольник с центром на y
                    y1 = max(0, y - line_width // 2)
                    y2 = min(self.editor.display_image.height - 1, y + line_width // 2 + (line_width % 2))
                    draw.rectangle([0, y1, self.editor.display_image.width - 1, y2], fill=color, outline=None)
                
                # Выводим цифры у синих линий (каждые 10, начиная с 10)
                if i % 10 == 0 and i > 0:
                    number_text = str(i)
                    # Получаем размер текста
                    try:
                        bbox = draw.textbbox((0, 0), number_text, font=grid_font)
                        text_width = bbox[2] - bbox[0]
                        text_height = bbox[3] - bbox[1]
                    except:
                        # Если textbbox не поддерживается, используем приблизительные размеры
                        text_width = len(number_text) * font_size * 0.6
                        text_height = font_size
                    
                    # Размещаем цифру слева от линии, внизу
                    text_x = 2  # Слева от изображения
                    text_y = y - text_height - 2  # Снизу от линии
                    # Рисуем белый фон для читаемости (RGB режим, без альфа)
                    draw.rectangle([text_x - 1, text_y - 1, text_x + text_width + 1, text_y + text_height + 1], 
                                 fill=(255, 255, 255), outline=None)
                    draw.text((text_x, text_y), number_text, font=grid_font, fill=(0, 0, 0))
        
        # Рисуем выделенную область (если есть)
        if self.editor.selection_start is not None and self.editor.selection_end is not None:
            min_col, min_row = self.editor.selection_start
            max_col, max_row = self.editor.selection_end
            
            # Рисуем прямоугольник выделения
            if min_col < len(self.editor.vertical_lines) - 1 and min_row < len(self.editor.horizontal_lines) - 1:
                x1 = self.editor.vertical_lines[min_col]
                y1 = self.editor.horizontal_lines[min_row]
                x2 = self.editor.vertical_lines[min(max_col + 1, len(self.editor.vertical_lines) - 1)]
                y2 = self.editor.horizontal_lines[min(max_row + 1, len(self.editor.horizontal_lines) - 1)]
                
                # Рисуем полупрозрачный прямоугольник и рамку
                # Создаем временное изображение для полупрозрачности
                overlay = Image.new('RGBA', self.editor.display_image.size, (0, 0, 0, 0))
                overlay_draw = ImageDraw.Draw(overlay)
                overlay_draw.rectangle([x1, y1, x2-1, y2-1], fill=(255, 255, 0, 80), outline=(255, 200, 0, 255), width=3)
                self.editor.display_image = Image.alpha_composite(self.editor.display_image.convert('RGBA'), overlay).convert('RGB')
                draw = ImageDraw.Draw(self.editor.display_image)
        
        # Рисуем связанные области (если есть)
        if self.editor.selected_regions:
            overlay = Image.new('RGBA', self.editor.display_image.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            
            for region in self.editor.selected_regions:
                if not region:
                    continue
                
                # Обводим контур области - рисуем границы каждой ячейки области
                region_set = set(region)
                
                for col, row in region:
                    if (col >= len(self.editor.vertical_lines) - 1 or 
                        row >= len(self.editor.horizontal_lines) - 1):
                        continue
                    
                    # Координаты ячейки
                    x1 = self.editor.vertical_lines[col]
                    y1 = self.editor.horizontal_lines[row]
                    x2 = self.editor.vertical_lines[min(col + 1, len(self.editor.vertical_lines) - 1)]
                    y2 = self.editor.horizontal_lines[min(row + 1, len(self.editor.horizontal_lines) - 1)]
                    
                    # Проверяем соседей и рисуем только граничные линии
                    # Верхняя граница
                    if (col, row - 1) not in region_set:
                        overlay_draw.line([(x1, y1), (x2, y1)], fill=(255, 200, 0, 255), width=3)
                    # Нижняя граница
                    if (col, row + 1) not in region_set:
                        overlay_draw.line([(x1, y2), (x2, y2)], fill=(255, 200, 0, 255), width=3)
                    # Левая граница
                    if (col - 1, row) not in region_set:
                        overlay_draw.line([(x1, y1), (x1, y2)], fill=(255, 200, 0, 255), width=3)
                    # Правая граница
                    if (col + 1, row) not in region_set:
                        overlay_draw.line([(x2, y1), (x2, y2)], fill=(255, 200, 0, 255), width=3)
            
            if overlay:
                self.editor.display_image = Image.alpha_composite(self.editor.display_image.convert('RGBA'), overlay).convert('RGB')
                draw = ImageDraw.Draw(self.editor.display_image)
        
        # Масштабируем изображение для отображения с учетом зума
        canvas_width = self.editor.canvas.winfo_width()
        canvas_height = self.editor.canvas.winfo_height()
        
        if canvas_width > 1 and canvas_height > 1:
            # Базовый масштаб для вписывания в canvas
            base_scale_w = canvas_width / self.editor.display_image.width
            base_scale_h = canvas_height / self.editor.display_image.height
            base_scale = min(base_scale_w, base_scale_h)
            
            # Применяем зум
            scale = base_scale * self.editor.zoom
            
            # Ограничиваем зум (от 0.1 до 10)
            scale = max(0.1, min(10.0, scale))
            
            new_width = int(self.editor.display_image.width * scale)
            new_height = int(self.editor.display_image.height * scale)
            
            display_copy = self.editor.display_image.resize((new_width, new_height), Image.Resampling.NEAREST)
            self.editor.photo = ImageTk.PhotoImage(display_copy)
            
            # Очищаем canvas
            self.editor.canvas.delete("all")
            
            # Вычисляем позицию с учетом панорамирования
            # Центрируем изображение и применяем смещение
            img_x = canvas_width // 2 + self.editor.pan_x
            img_y = canvas_height // 2 + self.editor.pan_y
            
            self.editor.canvas.create_image(img_x, img_y, image=self.editor.photo, anchor=tk.CENTER)
            
            # Сохраняем параметры для преобразования координат
            self.editor.scale = scale
            self.editor.offset_x = img_x - new_width // 2
            self.editor.offset_y = img_y - new_height // 2
            
            # Перерисовываем линейку, если она активна
            if (self.editor.active_tool and 
                hasattr(self.editor.active_tool, 'name') and 
                self.editor.active_tool.name == 'ruler' and
                hasattr(self.editor.active_tool, 'update_ruler_display')):
                self.editor.active_tool.update_ruler_display()
        
        # Если режим 4, обновляем также второй canvas с исходным изображением
        if self.editor.view_mode == 4:
            self.editor._update_original_canvas()
        
        if canvas_width <= 1 or canvas_height <= 1:
            # Если canvas еще не инициализирован, просто обновим при следующем событии
            self.editor.root.after(100, self.update_display)

