"""Обработка изображений"""
import os
import numpy as np
from PIL import Image


class ImageProcessor:
    """Класс для обработки изображений"""
    
    @staticmethod
    def load_image(file_path):
        """
        Загружает изображение из файла.
        
        Args:
            file_path: Путь к файлу изображения
        
        Returns:
            PIL.Image: Загруженное изображение в формате RGB
        """
        loaded_image = Image.open(file_path)
        
        # Если у изображения есть альфа-канал (прозрачность), заменяем прозрачные пиксели на белые
        if loaded_image.mode in ('RGBA', 'LA', 'P'):
            # Конвертируем в RGBA для работы с альфа-каналом
            if loaded_image.mode == 'P':
                loaded_image = loaded_image.convert('RGBA')
            elif loaded_image.mode == 'LA':
                # LA - это grayscale с альфа-каналом, конвертируем в RGBA
                loaded_image = loaded_image.convert('RGBA')
            
            # Создаем белый фон
            white_bg = Image.new('RGB', loaded_image.size, (255, 255, 255))
            # Накладываем изображение на белый фон (прозрачные пиксели станут белыми)
            image = Image.alpha_composite(
                white_bg.convert('RGBA'), 
                loaded_image
            ).convert('RGB')
        else:
            # Если нет альфа-канала, просто конвертируем в RGB
            image = loaded_image.convert('RGB')
        
        return image
    
    @staticmethod
    def get_image_array(image):
        """
        Получает numpy массив из изображения.
        
        Args:
            image: PIL.Image
        
        Returns:
            tuple: (rgb_array, has_alpha, opacity_mask, alpha_channel)
        """
        img_array = np.array(image)
        
        # Если есть альфа-канал, работаем только с RGB и получаем маску прозрачности
        has_alpha = img_array.shape[2] == 4
        if has_alpha:
            rgb_array = img_array[:, :, :3]
            alpha_channel = img_array[:, :, 3]
            # Создаем маску: True для непрозрачных пикселей (альфа > 10)
            opacity_mask = alpha_channel > 10
        else:
            rgb_array = img_array
            opacity_mask = None
            alpha_channel = None
        
        return rgb_array, has_alpha, opacity_mask, alpha_channel
    
    @staticmethod
    def save_image_with_grid(image, vertical_lines, horizontal_lines, file_path, 
                             grid_color_vertical=(255, 0, 0), grid_color_horizontal=(0, 0, 255), 
                             grid_width=1, painted_cells=None):
        """
        Сохраняет изображение с нарисованной сеткой и закрашенными ячейками.
        
        Args:
            image: PIL.Image - оригинальное изображение
            vertical_lines: list - список вертикальных линий
            horizontal_lines: list - список горизонтальных линий
            file_path: str - путь для сохранения
            grid_color_vertical: tuple - цвет вертикальных линий (R, G, B)
            grid_color_horizontal: tuple - цвет горизонтальных линий (R, G, B)
            grid_width: int - толщина линий сетки
            painted_cells: dict - словарь закрашенных ячеек {(col, row): (r, g, b)}
        """
        from PIL import ImageDraw
        
        # Создаем копию оригинального изображения
        save_image = image.copy()
        draw = ImageDraw.Draw(save_image)
        
        # Рисуем закрашенные ячейки (если есть)
        if painted_cells:
            for (col, row), color in painted_cells.items():
                if 0 <= col < len(vertical_lines) - 1 and 0 <= row < len(horizontal_lines) - 1:
                    x1 = vertical_lines[col]
                    x2 = vertical_lines[col + 1]
                    y1 = horizontal_lines[row]
                    y2 = horizontal_lines[row + 1]
                    # Убеждаемся, что координаты в пределах изображения
                    x1 = max(0, min(x1, save_image.width))
                    x2 = max(0, min(x2, save_image.width))
                    y1 = max(0, min(y1, save_image.height))
                    y2 = max(0, min(y2, save_image.height))
                    if x2 > x1 and y2 > y1:
                        draw.rectangle([x1, y1, x2-1, y2-1], fill=color, outline=None)
        
        # Рисуем вертикальные линии
        for x in vertical_lines:
            if 0 <= x < save_image.width:
                draw.line([(x, 0), (x, save_image.height)], fill=grid_color_vertical, width=grid_width)
        
        # Рисуем горизонтальные линии
        for y in horizontal_lines:
            if 0 <= y < save_image.height:
                draw.line([(0, y), (save_image.width, y)], fill=grid_color_horizontal, width=grid_width)
        
        save_image.save(file_path)
    
    @staticmethod
    def save_image(image, file_path, format=None):
        """
        Сохраняет изображение в файл.
        
        Args:
            image: PIL.Image
            file_path: Путь для сохранения
            format: Формат файла (если None, определяется по расширению)
        """
        image.save(file_path, format=format)
    
    @staticmethod
    def crop_image(image, crop_box):
        """
        Кадрирует изображение.
        
        Args:
            image: PIL.Image
            crop_box: Кортеж (left, top, right, bottom)
        
        Returns:
            PIL.Image: Кадрированное изображение
        """
        return image.crop(crop_box)
    
    @staticmethod
    def resize_image(image, size, resample=Image.NEAREST):
        """
        Изменяет размер изображения.
        
        Args:
            image: PIL.Image
            size: Кортеж (width, height)
            resample: Метод интерполяции
        
        Returns:
            PIL.Image: Измененное изображение
        """
        return image.resize(size, resample=resample)
    
    @staticmethod
    def paint_cell(image, col, row, color, vertical_lines, horizontal_lines):
        """
        Закрашивает ячейку сетки указанным цветом.
        
        Args:
            image: PIL.Image
            col: Номер колонки
            row: Номер строки
            color: Цвет (R, G, B)
            vertical_lines: Список вертикальных линий
            horizontal_lines: Список горизонтальных линий
        
        Returns:
            PIL.Image: Изображение с закрашенной ячейкой
        """
        if col < 0 or col >= len(vertical_lines) - 1:
            return image
        if row < 0 or row >= len(horizontal_lines) - 1:
            return image
        
        x1 = vertical_lines[col]
        x2 = vertical_lines[col + 1]
        y1 = horizontal_lines[row]
        y2 = horizontal_lines[row + 1]
        
        # Обновляем изображение
        img_array = np.array(image)
        if img_array.shape[2] == 4:
            # Если есть альфа-канал, обновляем только RGB
            img_array[y1:y2, x1:x2, 0] = color[0]
            img_array[y1:y2, x1:x2, 1] = color[1]
            img_array[y1:y2, x1:x2, 2] = color[2]
        else:
            img_array[y1:y2, x1:x2] = color
        
        return Image.fromarray(img_array)
    
    @staticmethod
    def get_cell_from_position(img_x, img_y, vertical_lines, horizontal_lines):
        """
        Определяет ячейку сетки по координатам изображения.
        
        Args:
            img_x: X координата на изображении
            img_y: Y координата на изображении
            vertical_lines: Список вертикальных линий
            horizontal_lines: Список горизонтальных линий
        
        Returns:
            tuple: (col, row) или (None, None) если не найдено
        """
        col = -1
        row = -1
        
        for i in range(len(vertical_lines) - 1):
            if vertical_lines[i] <= img_x < vertical_lines[i + 1]:
                col = i
                break
        
        for i in range(len(horizontal_lines) - 1):
            if horizontal_lines[i] <= img_y < horizontal_lines[i + 1]:
                row = i
                break
        
        if col >= 0 and row >= 0:
            return (col, row)
        return (None, None)
    
    @staticmethod
    def get_cell_color(image, col, row, vertical_lines, horizontal_lines):
        """
        Получает цвет ячейки сетки.
        
        Args:
            image: PIL.Image
            col: Номер колонки
            row: Номер строки
            vertical_lines: Список вертикальных линий
            horizontal_lines: Список горизонтальных линий
        
        Returns:
            tuple: Цвет (R, G, B) или None
        """
        if col < 0 or col >= len(vertical_lines) - 1:
            return None
        if row < 0 or row >= len(horizontal_lines) - 1:
            return None
        
        x1 = vertical_lines[col]
        x2 = vertical_lines[col + 1]
        y1 = horizontal_lines[row]
        y2 = horizontal_lines[row + 1]
        
        # Получаем средний цвет ячейки
        img_array = np.array(image)
        cell_region = img_array[y1:y2, x1:x2]
        
        if cell_region.size == 0:
            return None
        
        # Вычисляем средний цвет
        if len(cell_region.shape) == 3:
            avg_color = np.mean(cell_region.reshape(-1, cell_region.shape[2]), axis=0)
            return tuple(avg_color.astype(int))
        else:
            return None

