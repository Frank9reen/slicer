"""Управление палитрой цветов"""
import numpy as np
import os
from .color_clustering import create_palette_from_image, apply_palette_to_image, find_closest_color_in_palette
from .palette_methods import (
    create_palette_kmeans,
    create_palette_kmeans_improved,
    create_palette_kmeans_weighted,
    create_palette_hierarchical_kmeans,
    create_palette_median_cut,
    create_palette_octree
)

# Импортируем функцию для поиска номера Гаммы
try:
    from export.slicer_utils.color_layout_25 import find_closest_gamma_color
    HAS_GAMMA_FUNCTION = True
except ImportError:
    HAS_GAMMA_FUNCTION = False
    find_closest_gamma_color = None


class PaletteManager:
    """Класс для управления палитрой цветов"""
    
    def __init__(self):
        self.palette = None
        self.selected_color = None
        self.color_space = 'RGB'  # RGB, LAB, HSV
    
    def create_palette(self, rgb_array, num_colors, opacity_mask=None, color_space='RGB', focus_on_center=None):
        """
        Создает палитру цветов из изображения.
        
        Args:
            rgb_array: Массив изображения в формате (height, width, 3) RGB
            num_colors: Количество цветов в палитре (0 = без ограничения)
            opacity_mask: Маска прозрачности
            color_space: Цветовое пространство для кластеризации ('RGB', 'LAB', 'HSV')
            focus_on_center: Если True, фокусируется на центре изображения (если None, берется из self.focus_on_center)
        
        Returns:
            tuple: (palette, quantized_image) или (None, rgb_array) если num_colors == 0
        """
        # Используем значение из параметра или из атрибута
        if focus_on_center is None:
            focus_on_center = getattr(self, 'focus_on_center', False)
        self.color_space = color_space
        
        if num_colors == 0:
            # Без ограничения палитры
            return None, rgb_array
        
        if num_colors > 1 and num_colors <= 256:
            # Определяем, какие методы выбраны
            selected_methods = []
            
            # Проверяем наличие атрибутов для выбора методов
            if hasattr(self, 'method_kmeans') and self.method_kmeans:
                selected_methods.append('kmeans')
            if hasattr(self, 'method_kmeans_improved') and self.method_kmeans_improved:
                selected_methods.append('kmeans_improved')
            if hasattr(self, 'method_kmeans_weighted') and self.method_kmeans_weighted:
                selected_methods.append('kmeans_weighted')
            if hasattr(self, 'method_hierarchical_kmeans') and self.method_hierarchical_kmeans:
                selected_methods.append('hierarchical_kmeans')
            if hasattr(self, 'method_median_cut') and self.method_median_cut:
                selected_methods.append('median_cut')
            if hasattr(self, 'method_octree') and self.method_octree:
                selected_methods.append('octree')
            
            # Если не выбран ни один метод, возвращаем None (палитра не будет создана)
            # Это должно обрабатываться на уровне вызова функции
            if not selected_methods:
                # Если методы не выбраны, возвращаем None для палитры
                # Это означает, что будет использоваться фрагментация без ограничения палитры
                return None, rgb_array
            
            # Собираем результаты от всех выбранных методов
            all_palettes = []
            
            # Распределяем количество цветов между методами
            # Если один метод - используем все num_colors
            # Если несколько методов - распределяем поровну, но не меньше 2-3 цветов на метод
            num_methods = len(selected_methods)
            remainder = 0  # Инициализируем remainder
            if num_methods == 1:
                colors_per_method = num_colors
            else:
                # Распределяем поровну, но не меньше 2 цветов на метод
                colors_per_method = max(2, num_colors // num_methods)
                # Если остаток, добавляем к первому методу
                remainder = num_colors - (colors_per_method * num_methods)
            
            for i, method in enumerate(selected_methods):
                try:
                    # Для первого метода добавляем остаток, если есть
                    method_colors = colors_per_method + (remainder if i == 0 else 0)
                    # Ограничиваем максимумом num_colors
                    method_colors = min(method_colors, num_colors)
                    
                    if method == 'kmeans':
                        palette = create_palette_kmeans(rgb_array, method_colors, opacity_mask, focus_on_center=focus_on_center)
                    elif method == 'kmeans_improved':
                        palette = create_palette_kmeans_improved(rgb_array, method_colors, opacity_mask, focus_on_center=focus_on_center)
                    elif method == 'kmeans_weighted':
                        palette = create_palette_kmeans_weighted(rgb_array, method_colors, opacity_mask, focus_on_center=focus_on_center)
                    elif method == 'hierarchical_kmeans':
                        palette = create_palette_hierarchical_kmeans(rgb_array, method_colors, opacity_mask, focus_on_center=focus_on_center)
                    elif method == 'median_cut':
                        palette = create_palette_median_cut(rgb_array, method_colors, opacity_mask, focus_on_center=focus_on_center)
                    elif method == 'octree':
                        palette = create_palette_octree(rgb_array, method_colors, opacity_mask, focus_on_center=focus_on_center)
                    else:
                        continue
                    
                    # Ограничиваем результат метода до method_colors (на случай, если метод вернул больше)
                    if len(palette) > method_colors:
                        palette = palette[:method_colors]
                    
                    all_palettes.append(palette)
                except Exception as e:
                    # Используем logger если доступен, иначе ничего не выводим
                    try:
                        from utils.logger import setup_logger
                        logger = setup_logger(__name__)
                        logger.warning(f"Метод {method} не сработал: {str(e)}")
                    except:
                        pass
                    continue
            
            # Объединяем палитры
            if all_palettes:
                # Объединяем все цвета из всех палитр
                combined_palette = np.vstack(all_palettes)
                
                # Удаляем дубликаты по номерам Гаммы (если доступно)
                # И ограничиваем до num_colors
                palette = self._remove_duplicates_by_gamma(combined_palette, num_colors)
                
                # Дополнительная проверка: строго ограничиваем до num_colors
                if len(palette) > num_colors:
                    try:
                        from utils.logger import setup_logger
                        logger = setup_logger(__name__)
                        logger.warning(f"Палитра содержит {len(palette)} цветов, ограничиваем до {num_colors}")
                    except:
                        pass
                    palette = palette[:num_colors]
            else:
                # Fallback на старый метод
                palette = create_palette_from_image(rgb_array, num_colors, opacity_mask)
            
            # Финальная проверка: строго ограничиваем палитру до num_colors
            if len(palette) > num_colors:
                try:
                    from utils.logger import setup_logger
                    logger = setup_logger(__name__)
                    logger.warning(f"Финальная палитра содержит {len(palette)} цветов, ограничиваем до {num_colors}")
                except:
                    pass
                palette = palette[:num_colors]
            
            quantized_image = apply_palette_to_image(rgb_array, palette, opacity_mask)
            self.palette = palette
            return palette, quantized_image
        
        return None, rgb_array
    
    def get_palette(self):
        """Возвращает текущую палитру"""
        return self.palette
    
    def set_palette(self, palette):
        """Устанавливает палитру"""
        self.palette = palette
    
    def select_color(self, color_idx):
        """Выбирает цвет из палитры по индексу"""
        if self.palette is not None and 0 <= color_idx < len(self.palette):
            self.selected_color = tuple(self.palette[color_idx])
            return self.selected_color
        return None
    
    def get_selected_color(self):
        """Возвращает выбранный цвет"""
        return self.selected_color
    
    def find_color_index(self, color):
        """Находит индекс цвета в палитре"""
        if self.palette is None:
            return None
        
        idx, _ = find_closest_color_in_palette(color, self.palette)
        return idx
    
    def delete_color(self, color_idx):
        """
        Удаляет цвет из палитры по индексу.
        
        Args:
            color_idx: Индекс цвета для удаления
        
        Returns:
            numpy.ndarray: Новая палитра без удаленного цвета
        """
        if self.palette is None or color_idx < 0 or color_idx >= len(self.palette):
            return self.palette
        
        # Создаем новую палитру без удаленного цвета
        mask = np.ones(len(self.palette), dtype=bool)
        mask[color_idx] = False
        self.palette = self.palette[mask]
        
        return self.palette
    
    def replace_color_with_closest(self, color_idx):
        """
        Заменяет все вхождения цвета на ближайший цвет из палитры.
        
        Args:
            color_idx: Индекс цвета для замены
        
        Returns:
            tuple: (new_color_idx, new_color) - индекс и цвет замены
        """
        if self.palette is None or color_idx < 0 or color_idx >= len(self.palette):
            return None, None
        
        if len(self.palette) <= 1:
            return None, None
        
        # Исключаем текущий цвет из поиска
        other_colors = np.delete(self.palette, color_idx, axis=0)
        current_color = self.palette[color_idx]
        
        # Находим ближайший цвет
        closest_idx, closest_color = find_closest_color_in_palette(current_color, other_colors)
        
        # Корректируем индекс, так как мы удалили один элемент
        if closest_idx >= color_idx:
            closest_idx += 1
        
        return closest_idx, tuple(closest_color)


    def _remove_duplicates_by_gamma(self, palette, max_colors):
        """
        Удаляет дубликаты цветов по номерам Гаммы и ограничивает палитру до max_colors.
        
        Args:
            palette: Палитра цветов в формате (N, 3) RGB
            max_colors: Максимальное количество цветов в палитре
        
        Returns:
            numpy.ndarray: Палитра без дубликатов по Гамме, ограниченная до max_colors
        """
        if len(palette) == 0:
            return palette
        
        # Получаем путь к Excel файлу Gamma
        from utils.path_utils import get_static_path
        gamma_excel_path = get_static_path("DMCtoGamma_with_Gamma_OFF_formattedColor.xlsx")
        
        # Если нет функции или файла, используем старый метод по RGB
        if not HAS_GAMMA_FUNCTION or not os.path.exists(gamma_excel_path):
            try:
                from utils.logger import setup_logger
                logger = setup_logger(__name__)
                logger.warning("Файл Gamma недоступен, используем удаление дубликатов по RGB")
            except:
                pass
            unique_palette = _remove_duplicate_colors_by_rgb(palette)
            if len(unique_palette) > max_colors:
                # Ограничиваем до max_colors
                try:
                    from sklearn.cluster import KMeans
                    kmeans = KMeans(n_clusters=max_colors, random_state=42, n_init=10)
                    kmeans.fit(unique_palette)
                    return kmeans.cluster_centers_.astype(np.uint8)
                except ImportError:
                    return unique_palette[:max_colors]
            return unique_palette
        
        # Группируем цвета по номерам Гаммы
        gamma_groups = {}  # gamma_number -> list of (color, index)
        
        for i, color in enumerate(palette):
            # Нормализуем цвет
            normalized_color = tuple(int(c) for c in color)
            
            # Находим номер Гаммы для цвета
            gamma_num, gamma_rgb, distance = find_closest_gamma_color(normalized_color, gamma_excel_path)
            
            # Нормализуем номер Гаммы (убираем префикс G, если есть)
            if gamma_num:
                gamma_str = str(gamma_num).strip().upper()
                if gamma_str.startswith('G'):
                    gamma_str = gamma_str[1:]
                gamma_key = gamma_str
            else:
                # Если не нашли номер Гаммы, используем RGB как ключ
                gamma_key = f"NO_GAMMA_{normalized_color[0]}_{normalized_color[1]}_{normalized_color[2]}"
            
            if gamma_key not in gamma_groups:
                gamma_groups[gamma_key] = []
            gamma_groups[gamma_key].append((color, i))
        
        # Объединяем цвета с одинаковой Гаммой (берем первый цвет из группы)
        unique_palette = []
        for gamma_key, color_group in gamma_groups.items():
            # Берем первый цвет из группы (можно было бы усреднить, но первый проще)
            unique_palette.append(color_group[0][0])
        
        unique_palette = np.array(unique_palette)
        
        try:
            from utils.logger import setup_logger
            logger = setup_logger(__name__)
            logger.info(f"После объединения по Гамме: {len(unique_palette)} уникальных цветов (было {len(palette)})")
        except:
            pass
        
        # Ограничиваем до max_colors
        if len(unique_palette) > max_colors:
            # Используем KMeans для финальной кластеризации
            try:
                from sklearn.cluster import KMeans
                kmeans = KMeans(n_clusters=max_colors, random_state=42, n_init=10)
                kmeans.fit(unique_palette)
                final_palette = kmeans.cluster_centers_.astype(np.uint8)
                
                # Снова удаляем дубликаты по Гамме из финальной палитры (без рекурсии)
                final_palette = self._remove_duplicates_by_gamma_single_pass(final_palette)
                if len(final_palette) > max_colors:
                    final_palette = final_palette[:max_colors]
                try:
                    from utils.logger import setup_logger
                    logger = setup_logger(__name__)
                    logger.info(f"Финальная палитра после ограничения: {len(final_palette)} цветов")
                except:
                    pass
                return final_palette
            except ImportError:
                # Если sklearn недоступен, просто берем первые max_colors
                return unique_palette[:max_colors]
        
        return unique_palette
    
    def _remove_duplicates_by_gamma_single_pass(self, palette):
        """
        Удаляет дубликаты по Гамме за один проход (без рекурсии).
        
        Args:
            palette: Палитра цветов в формате (N, 3) RGB
        
        Returns:
            numpy.ndarray: Палитра без дубликатов по Гамме
        """
        if len(palette) == 0:
            return palette
        
        # Получаем путь к Excel файлу Gamma
        from utils.path_utils import get_static_path
        gamma_excel_path = get_static_path("DMCtoGamma_with_Gamma_OFF_formattedColor.xlsx")
        
        if not HAS_GAMMA_FUNCTION or not os.path.exists(gamma_excel_path):
            return _remove_duplicate_colors_by_rgb(palette)
        
        # Группируем цвета по номерам Гаммы
        gamma_groups = {}  # gamma_number -> first color
        
        for color in palette:
            normalized_color = tuple(int(c) for c in color)
            gamma_num, gamma_rgb, distance = find_closest_gamma_color(normalized_color, gamma_excel_path)
            
            if gamma_num:
                gamma_str = str(gamma_num).strip().upper()
                if gamma_str.startswith('G'):
                    gamma_str = gamma_str[1:]
                gamma_key = gamma_str
            else:
                gamma_key = f"NO_GAMMA_{normalized_color[0]}_{normalized_color[1]}_{normalized_color[2]}"
            
            if gamma_key not in gamma_groups:
                gamma_groups[gamma_key] = color
        
        return np.array(list(gamma_groups.values()))


def _remove_duplicate_colors_by_rgb(palette, threshold=15):
    """
    Удаляет дубликаты цветов из палитры по RGB расстоянию.
    
    Args:
        palette: Палитра цветов в формате (N, 3) RGB
        threshold: Порог расстояния для определения дубликатов
    
    Returns:
        numpy.ndarray: Палитра без дубликатов
    """
    if len(palette) == 0:
        return palette
    
    unique_colors = []
    for color in palette:
        is_unique = True
        for existing_color in unique_colors:
            distance = np.sqrt(np.sum((color.astype(float) - existing_color.astype(float)) ** 2))
            if distance < threshold:
                is_unique = False
                break
        if is_unique:
            unique_colors.append(color)
    
    return np.array(unique_colors)

