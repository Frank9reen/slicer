"""Операции укрупнения ячеек сетки"""
import numpy as np
from PIL import Image
from tkinter import messagebox
from collections import Counter
from utils.version_utils import get_app_name_with_version


class CellUpscaling:
    """Класс для укрупнения ячеек сетки (объединение 4 ячеек в одну)"""
    
    def __init__(self, editor):
        """
        Args:
            editor: Экземпляр GridEditor
        """
        self.editor = editor
    
    def upscale_cells(self, method='mean'):
        """
        Укрупняет ячейки сетки в 4 раза (объединяет 2x2 ячейки в одну).
        
        Args:
            method: Метод расчета цвета новой ячейки
                - 'mean': Средний цвет
                - 'median': Медианный цвет
                - 'dominant': Доминирующий цвет (наиболее частый)
                - 'weighted': Взвешенный средний (по площади ячеек)
        """
        if self.editor.image is None:
            messagebox.showwarning("Предупреждение", "Сначала откройте изображение!")
            return
        
        if len(self.editor.vertical_lines) < 3 or len(self.editor.horizontal_lines) < 3:
            messagebox.showwarning("Предупреждение", "Недостаточно линий сетки для укрупнения!")
            return
        
        # Сохраняем состояние перед укрупнением
        self.editor.save_state()
        
        try:
            # Создаем новую сетку (каждая вторая линия)
            new_vertical_lines = []
            new_horizontal_lines = []
            
            # Берем каждую вторую вертикальную линию (начиная с первой)
            for i in range(0, len(self.editor.vertical_lines), 2):
                new_vertical_lines.append(self.editor.vertical_lines[i])
            # Убеждаемся, что последняя линия включена
            if len(self.editor.vertical_lines) > 0 and new_vertical_lines[-1] != self.editor.vertical_lines[-1]:
                new_vertical_lines.append(self.editor.vertical_lines[-1])
            
            # Берем каждую вторую горизонтальную линию (начиная с первой)
            for i in range(0, len(self.editor.horizontal_lines), 2):
                new_horizontal_lines.append(self.editor.horizontal_lines[i])
            # Убеждаемся, что последняя линия включена
            if len(self.editor.horizontal_lines) > 0 and new_horizontal_lines[-1] != self.editor.horizontal_lines[-1]:
                new_horizontal_lines.append(self.editor.horizontal_lines[-1])
            
            # Создаем новый словарь закрашенных ячеек
            new_painted_cells = {}
            
            # Получаем изображение для расчета цветов
            img_array = np.array(self.editor.original_image if self.editor.original_image is not None else self.editor.image)
            
            # Обрабатываем каждую новую ячейку (2x2 старых ячеек)
            for new_col in range(len(new_vertical_lines) - 1):
                for new_row in range(len(new_horizontal_lines) - 1):
                    # Координаты новой ячейки
                    new_x1 = new_vertical_lines[new_col]
                    new_x2 = new_vertical_lines[new_col + 1]
                    new_y1 = new_horizontal_lines[new_row]
                    new_y2 = new_horizontal_lines[new_row + 1]
                    
                    # Находим соответствующие старые ячейки (2x2)
                    old_col_start = new_col * 2
                    old_row_start = new_row * 2
                    
                    # Собираем цвета из 4 старых ячеек
                    cell_colors = []
                    cell_areas = []
                    
                    for col_offset in range(2):
                        for row_offset in range(2):
                            old_col = old_col_start + col_offset
                            old_row = old_row_start + row_offset
                            
                            # Проверяем границы
                            if old_col >= len(self.editor.vertical_lines) - 1:
                                continue
                            if old_row >= len(self.editor.horizontal_lines) - 1:
                                continue
                            
                            # Получаем координаты старой ячейки
                            old_x1 = self.editor.vertical_lines[old_col]
                            old_x2 = self.editor.vertical_lines[old_col + 1]
                            old_y1 = self.editor.horizontal_lines[old_row]
                            old_y2 = self.editor.horizontal_lines[old_row + 1]
                            
                            # Получаем цвет ячейки
                            cell_color = None
                            
                            # Сначала проверяем, закрашена ли ячейка
                            if (old_col, old_row) in self.editor.painted_cells:
                                cell_color = self.editor.painted_cells[(old_col, old_row)]
                            else:
                                # Если не закрашена, берем цвет из изображения
                                # Вычисляем цвет из изображения
                                cell_region = img_array[old_y1:old_y2, old_x1:old_x2]
                                if cell_region.size > 0:
                                    cell_color = self._calculate_cell_color(cell_region, method)
                            
                            if cell_color is not None:
                                cell_colors.append(cell_color)
                                # Вычисляем площадь ячейки
                                area = (old_x2 - old_x1) * (old_y2 - old_y1)
                                cell_areas.append(area)
                    
                    # Вычисляем итоговый цвет для новой ячейки
                    if cell_colors:
                        new_color = self._merge_colors(cell_colors, cell_areas, method)
                        new_painted_cells[(new_col, new_row)] = new_color
            
            # Обновляем сетку
            self.editor.vertical_lines = new_vertical_lines
            self.editor.horizontal_lines = new_horizontal_lines
            self.editor.grid_manager.vertical_lines = new_vertical_lines
            self.editor.grid_manager.horizontal_lines = new_horizontal_lines
            
            # Обновляем закрашенные ячейки
            self.editor.painted_cells = new_painted_cells
            
            # Сбрасываем выделение
            self.editor.selected_line = None
            self.editor.selected_line_type = None
            self.editor.grid_manager.selected_line = None
            self.editor.grid_manager.selected_line_type = None
            
            # Сбрасываем фрагментированное изображение и палитру
            self.editor.fragmented_image = None
            self.editor.palette = None
            self.editor.selected_color = None
            for widget in self.editor.palette_frame.winfo_children():
                widget.destroy()
            self.editor.palette_canvas = None
            
            # Обновляем отображение
            self.editor.update_display()
            self.editor.update_footer_info()
            
            app_name = get_app_name_with_version()
            messagebox.showinfo(f"Успех - {app_name}", 
                              f"Ячейки укрупнены!\n"
                              f"Метод: {self._get_method_name(method)}\n"
                              f"Новая сетка: {len(new_vertical_lines)-1}x{len(new_horizontal_lines)-1} ячеек")
        
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось укрупнить ячейки:\n{str(e)}")
    
    def _calculate_cell_color(self, cell_region, method='mean'):
        """
        Вычисляет цвет ячейки из области изображения.
        
        Args:
            cell_region: numpy array - область изображения ячейки
            method: Метод расчета цвета
        
        Returns:
            tuple: Цвет (R, G, B)
        """
        if cell_region.size == 0:
            return None
        
        # Преобразуем в плоский массив пикселей
        if len(cell_region.shape) == 3:
            pixels = cell_region.reshape(-1, cell_region.shape[2])
        else:
            pixels = cell_region.reshape(-1)
            pixels = np.stack([pixels, pixels, pixels], axis=1)
        
        # Берем только RGB (первые 3 канала)
        if pixels.shape[1] > 3:
            pixels = pixels[:, :3]
        
        if method == 'mean':
            color = np.mean(pixels, axis=0).astype(np.uint8)
        elif method == 'median':
            color = np.median(pixels, axis=0).astype(np.uint8)
        elif method == 'dominant':
            # Находим доминирующий цвет (квантуем и берем наиболее частый)
            # Квантуем цвета для группировки похожих
            quantized = (pixels // 16) * 16  # Квантуем с шагом 16
            # Находим наиболее частый квантованный цвет
            color_strs = [tuple(c) for c in quantized]
            counter = Counter(color_strs)
            most_common = counter.most_common(1)[0][0]
            # Берем средний цвет всех пикселей с этим квантованным цветом
            mask = np.all(quantized == most_common, axis=1)
            if np.any(mask):
                color = np.mean(pixels[mask], axis=0).astype(np.uint8)
            else:
                color = np.mean(pixels, axis=0).astype(np.uint8)
        elif method == 'weighted':
            # Взвешенный средний (в данном случае просто средний)
            color = np.mean(pixels, axis=0).astype(np.uint8)
        else:
            color = np.mean(pixels, axis=0).astype(np.uint8)
        
        return tuple(color)
    
    def _merge_colors(self, colors, areas, method='mean'):
        """
        Объединяет цвета из нескольких ячеек в один.
        
        Args:
            colors: list of tuples - список цветов (R, G, B)
            areas: list of ints - список площадей ячеек
            method: Метод объединения
        
        Returns:
            tuple: Итоговый цвет (R, G, B)
        """
        if not colors:
            return (255, 255, 255)  # Белый по умолчанию
        
        colors_array = np.array(colors, dtype=np.float32)
        
        if method == 'mean':
            result = np.mean(colors_array, axis=0).astype(np.uint8)
        elif method == 'median':
            result = np.median(colors_array, axis=0).astype(np.uint8)
        elif method == 'dominant':
            # Находим доминирующий цвет среди ячеек
            # Квантуем цвета
            quantized = (colors_array // 16) * 16
            color_strs = [tuple(c) for c in quantized.astype(np.uint8)]
            counter = Counter(color_strs)
            most_common = counter.most_common(1)[0][0]
            # Берем средний цвет всех ячеек с этим квантованным цветом
            mask = np.all(quantized.astype(np.uint8) == most_common, axis=1)
            if np.any(mask):
                result = np.mean(colors_array[mask], axis=0).astype(np.uint8)
            else:
                result = np.mean(colors_array, axis=0).astype(np.uint8)
        elif method == 'weighted':
            # Взвешенный средний по площади
            if areas and len(areas) == len(colors):
                weights = np.array(areas, dtype=np.float32)
                weights = weights / weights.sum()  # Нормализуем
                result = np.average(colors_array, axis=0, weights=weights).astype(np.uint8)
            else:
                result = np.mean(colors_array, axis=0).astype(np.uint8)
        else:
            result = np.mean(colors_array, axis=0).astype(np.uint8)
        
        return tuple(result)
    
    def _get_method_name(self, method):
        """Возвращает читаемое имя метода"""
        names = {
            'mean': 'Средний цвет',
            'median': 'Медианный цвет',
            'dominant': 'Доминирующий цвет',
            'weighted': 'Взвешенный средний'
        }
        return names.get(method, method)

