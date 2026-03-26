"""Кластеризация цветов с использованием KMeans"""
import warnings
# Подавляем warnings от sklearn и numpy
warnings.filterwarnings('ignore')

import numpy as np
from sklearn.cluster import KMeans


def create_palette_from_image(rgb_array, num_colors, opacity_mask=None, random_state=42):
    """
    Создает палитру цветов из изображения с использованием KMeans кластеризации.
    
    Args:
        rgb_array: Массив изображения в формате (height, width, 3) RGB
        num_colors: Количество цветов в палитре
        opacity_mask: Маска прозрачности (True для непрозрачных пикселей)
        random_state: Seed для воспроизводимости результатов
    
    Returns:
        numpy.ndarray: Палитра цветов в формате (num_colors, 3) RGB
    """
    if num_colors <= 1 or num_colors > 256:
        raise ValueError("Количество цветов должно быть от 2 до 256")
    
    # Логгер для вывода сообщений
    try:
        from utils.logger import setup_logger
        logger = setup_logger(__name__)
        logger.info(f"Создание палитры из {num_colors} цветов...")
    except:
        pass
    
    # Улучшенная выборка пикселей: используем более плотную выборку
    # Адаптивный шаг в зависимости от размера изображения
    h, w = rgb_array.shape[:2]
    step = max(1, min(5, (h * w) // 100000))  # Более плотная выборка для малых изображений
    sampled_rgb = rgb_array[::step, ::step]
    
    # Фильтруем пиксели: исключаем прозрачные и белые
    if opacity_mask is not None:
        sampled_mask = opacity_mask[::step, ::step]
        # Исключаем прозрачные пиксели
        valid_mask = sampled_mask.flatten()
    else:
        valid_mask = np.ones(sampled_rgb.shape[0] * sampled_rgb.shape[1], dtype=bool)
    
    sampled_pixels_flat = sampled_rgb.reshape(-1, 3)
    # Исключаем белые пиксели (255, 255, 255)
    white_mask = ~np.all(sampled_pixels_flat == [255, 255, 255], axis=1)
    valid_mask = valid_mask & white_mask
    
    sample_pixels = sampled_pixels_flat[valid_mask]
    
    # Дополнительно добавляем случайные пиксели для лучшего покрытия
    if len(sample_pixels) < 10000:
        # Если выборка мала, добавляем случайные пиксели
        all_pixels_flat = rgb_array.reshape(-1, 3)
        
        # Создаем маску для всех пикселей
        if opacity_mask is not None:
            all_valid_mask = opacity_mask.flatten()
        else:
            all_valid_mask = np.ones(len(all_pixels_flat), dtype=bool)
        
        # Исключаем белые пиксели
        all_white_mask = ~np.all(all_pixels_flat == [255, 255, 255], axis=1)
        all_valid_mask = all_valid_mask & all_white_mask
        
        valid_indices = np.where(all_valid_mask)[0]
        if len(valid_indices) > 0:
            num_random = min(5000, len(valid_indices))
            random_indices = np.random.choice(valid_indices, num_random, replace=False)
            random_pixels = all_pixels_flat[random_indices]
            sample_pixels = np.vstack([sample_pixels, random_pixels])
    
    # Используем K-means с улучшенными параметрами
    # Увеличиваем n_init для большей стабильности
    n_init_value = min(20, max(10, num_colors // 2))
    kmeans = KMeans(n_clusters=num_colors, random_state=random_state, n_init=n_init_value, 
                   max_iter=300, tol=1e-4)
    kmeans.fit(sample_pixels)
    palette = kmeans.cluster_centers_.astype(np.uint8)
    
    # Если в палитре есть белый цвет, исключаем черный цвет
    has_white = np.any(np.all(palette == [255, 255, 255], axis=1))
    if has_white:
        # Исключаем черный цвет (0, 0, 0) из палитры
        black_mask = ~np.all(palette == [0, 0, 0], axis=1)
        palette = palette[black_mask]
        try:
            from utils.logger import setup_logger
            logger = setup_logger(__name__)
            logger.info(f"Палитра создана: {len(palette)} цветов (черный исключен, т.к. есть белый)")
        except:
            pass
    else:
        try:
            from utils.logger import setup_logger
            logger = setup_logger(__name__)
            logger.info(f"Палитра создана: {len(palette)} цветов")
        except:
            pass
    
    return palette


def apply_palette_to_image(rgb_array, palette, opacity_mask=None):
    """
    Применяет палитру ко всему изображению, заменяя каждый пиксель ближайшим цветом из палитры.
    
    Args:
        rgb_array: Массив изображения в формате (height, width, 3) RGB
        palette: Палитра цветов в формате (num_colors, 3) RGB
        opacity_mask: Маска прозрачности (True для непрозрачных пикселей)
    
    Returns:
        numpy.ndarray: Квантованное изображение в формате (height, width, 3) RGB
    """
    try:
        from utils.logger import setup_logger
        logger = setup_logger(__name__)
        logger.info("Применение палитры ко всему изображению...")
    except:
        pass
    h, w = rgb_array.shape[:2]
    pixels = rgb_array.reshape(-1, 3)
    
    # Находим ближайший цвет из палитры для каждого пикселя
    # Используем более эффективный метод для больших изображений
    if len(pixels) > 1000000:
        # Для очень больших изображений используем батчи
        batch_size = 100000
        labels = np.zeros(len(pixels), dtype=np.int32)
        palette_float = palette.astype(np.float32)
        
        for i in range(0, len(pixels), batch_size):
            batch = pixels[i:i+batch_size].astype(np.float32)
            # Вычисляем расстояния от каждого пикселя до каждого цвета палитры
            distances = np.sqrt(np.sum((batch[:, np.newaxis, :] - palette_float[np.newaxis, :, :]) ** 2, axis=2))
            labels[i:i+batch_size] = np.argmin(distances, axis=1)
    else:
        # Для небольших изображений используем весь массив сразу
        pixels_float = pixels.astype(np.float32)
        palette_float = palette.astype(np.float32)
        distances = np.sqrt(np.sum((pixels_float[:, np.newaxis, :] - palette_float[np.newaxis, :, :]) ** 2, axis=2))
        labels = np.argmin(distances, axis=1)
    
    quantized_pixels = palette[labels]
    quantized_image = quantized_pixels.reshape(h, w, 3).astype(np.uint8)
    try:
        from utils.logger import setup_logger
        logger = setup_logger(__name__)
        logger.info("Палитра применена")
    except:
        pass
    
    return quantized_image


def find_closest_color_in_palette(color, palette):
    """
    Находит ближайший цвет в палитре для заданного цвета.
    
    Args:
        color: Цвет в формате (R, G, B) или (3,) массив
        palette: Палитра цветов в формате (num_colors, 3) RGB
    
    Returns:
        tuple: Индекс ближайшего цвета в палитре и сам цвет
    """
    color_array = np.array(color, dtype=np.float32)
    palette_float = palette.astype(np.float32)
    distances = np.sqrt(np.sum((palette_float - color_array) ** 2, axis=1))
    closest_idx = np.argmin(distances)
    return closest_idx, palette[closest_idx]

