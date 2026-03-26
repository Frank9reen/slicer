"""Различные методы автоматического определения палитры цветов"""
import warnings
# Подавляем warnings от sklearn и других библиотек
warnings.filterwarnings('ignore')

import numpy as np
from collections import defaultdict, Counter

try:
    from sklearn.cluster import KMeans, AgglomerativeClustering
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    KMeans = None
    AgglomerativeClustering = None

# Логгер для вывода сообщений (не открывает консоль в GUI приложении)
def _get_logger():
    try:
        from utils.logger import setup_logger
        return setup_logger(__name__)
    except:
        return None

def _log_info(msg):
    logger = _get_logger()
    if logger:
        logger.info(msg)

def _log_warning(msg):
    logger = _get_logger()
    if logger:
        logger.warning(msg)


def _calculate_center_weights(rgb_array, opacity_mask=None, step=1):
    """
    Вычисляет веса пикселей на основе их расстояния от центра изображения.
    Пиксели ближе к центру получают больший вес.
    
    Args:
        rgb_array: Массив изображения в формате (height, width, 3) RGB
        opacity_mask: Маска прозрачности (True для непрозрачных пикселей)
        step: Шаг выборки пикселей
    
    Returns:
        numpy.ndarray: Веса пикселей в формате (N,) для отфильтрованных пикселей
    """
    h, w = rgb_array.shape[:2]
    sampled_rgb = rgb_array[::step, ::step]
    sampled_h, sampled_w = sampled_rgb.shape[:2]
    
    # Центр изображения
    center_y = sampled_h / 2.0
    center_x = sampled_w / 2.0
    
    # Максимальное расстояние от центра (до угла)
    max_distance = np.sqrt(center_x ** 2 + center_y ** 2)
    
    # Создаем сетку координат
    y_coords, x_coords = np.ogrid[:sampled_h, :sampled_w]
    
    # Вычисляем расстояние от центра для каждого пикселя
    distances = np.sqrt((x_coords - center_x) ** 2 + (y_coords - center_y) ** 2)
    
    # Нормализуем расстояния (0 = центр, 1 = край)
    normalized_distances = distances / max_distance if max_distance > 0 else distances
    
    # Вычисляем веса: центр = 1.0, край = 0.1 (экспоненциальное затухание)
    # Используем квадратичную функцию для более плавного перехода
    weights = 1.0 - (normalized_distances ** 2) * 0.9
    weights = np.maximum(weights, 0.1)  # Минимальный вес 0.1
    
    # Фильтруем веса так же, как пиксели
    if opacity_mask is not None:
        sampled_mask = opacity_mask[::step, ::step]
        valid_mask = sampled_mask.flatten()
    else:
        valid_mask = np.ones(sampled_h * sampled_w, dtype=bool)
    
    sampled_pixels_flat = sampled_rgb.reshape(-1, 3)
    white_mask = ~np.all(sampled_pixels_flat == [255, 255, 255], axis=1)
    valid_mask = valid_mask & white_mask
    
    weights_flat = weights.flatten()
    filtered_weights = weights_flat[valid_mask]
    
    return filtered_weights


def _prepare_pixels(rgb_array, opacity_mask=None, focus_on_center=False):
    """
    Подготавливает пиксели для анализа: фильтрует прозрачные и белые.
    
    Args:
        rgb_array: Массив изображения в формате (height, width, 3) RGB
        opacity_mask: Маска прозрачности (True для непрозрачных пикселей)
        focus_on_center: Если True, возвращает также веса для фокусировки на центре
    
    Returns:
        numpy.ndarray или tuple: Отфильтрованные пиксели в формате (N, 3) RGB
                                 Если focus_on_center=True, возвращает (pixels, weights)
    """
    h, w = rgb_array.shape[:2]
    
    # Адаптивная выборка в зависимости от размера изображения
    step = max(1, min(5, (h * w) // 100000))
    sampled_rgb = rgb_array[::step, ::step]
    
    # Фильтруем пиксели
    if opacity_mask is not None:
        sampled_mask = opacity_mask[::step, ::step]
        valid_mask = sampled_mask.flatten()
    else:
        valid_mask = np.ones(sampled_rgb.shape[0] * sampled_rgb.shape[1], dtype=bool)
    
    sampled_pixels_flat = sampled_rgb.reshape(-1, 3)
    # Исключаем белые пиксели
    white_mask = ~np.all(sampled_pixels_flat == [255, 255, 255], axis=1)
    valid_mask = valid_mask & white_mask
    
    sample_pixels = sampled_pixels_flat[valid_mask]
    
    # Вычисляем веса для фокусировки на центре, если нужно
    weights = None
    if focus_on_center:
        weights = _calculate_center_weights(rgb_array, opacity_mask, step)
    
    # Дополнительно добавляем случайные пиксели для лучшего покрытия
    if len(sample_pixels) < 10000:
        all_pixels_flat = rgb_array.reshape(-1, 3)
        
        if opacity_mask is not None:
            all_valid_mask = opacity_mask.flatten()
        else:
            all_valid_mask = np.ones(len(all_pixels_flat), dtype=bool)
        
        all_white_mask = ~np.all(all_pixels_flat == [255, 255, 255], axis=1)
        all_valid_mask = all_valid_mask & all_white_mask
        
        valid_indices = np.where(all_valid_mask)[0]
        if len(valid_indices) > 0:
            num_random = min(5000, len(valid_indices))
            random_indices = np.random.choice(valid_indices, num_random, replace=False)
            random_pixels = all_pixels_flat[random_indices]
            sample_pixels = np.vstack([sample_pixels, random_pixels])
            
            # Для случайных пикселей добавляем минимальные веса (они не из центра)
            if focus_on_center and weights is not None:
                random_weights = np.full(len(random_pixels), 0.1)
                weights = np.concatenate([weights, random_weights])
    
    if focus_on_center and weights is not None:
        return sample_pixels, weights
    return sample_pixels


def estimate_optimal_colors(rgb_array, opacity_mask=None, min_colors=8, max_colors=128):
    """
    Автоматически определяет оптимальное количество цветов для палитры.
    
    Args:
        rgb_array: Массив изображения в формате (height, width, 3) RGB
        opacity_mask: Маска прозрачности (True для непрозрачных пикселей)
        min_colors: Минимальное количество цветов
        max_colors: Максимальное количество цветов
    
    Returns:
        int: Оптимальное количество цветов
    """
    sample_pixels = _prepare_pixels(rgb_array, opacity_mask)
    
    if len(sample_pixels) == 0:
        return min_colors
    
    # Метод 1: Подсчет уникальных цветов после квантования
    # Квантуем цвета для группировки похожих
    quantize_level = 8  # 8 уровней на канал = 512 возможных групп
    quantized = (sample_pixels // (256 // quantize_level)).astype(np.int32)
    unique_quantized = len(set(map(tuple, quantized)))
    
    # Метод 2: Анализ распределения цветов
    # Используем более грубое квантование для оценки разнообразия
    coarse_quantize = 4  # 4 уровня на канал = 64 возможных групп
    coarse_quantized = (sample_pixels // (256 // coarse_quantize)).astype(np.int32)
    unique_coarse = len(set(map(tuple, coarse_quantized)))
    
    # Метод 3: Анализ через гистограмму
    # Подсчитываем количество значимых цветовых групп
    color_counts = Counter(map(tuple, quantized))
    # Берем цвета, которые встречаются достаточно часто (больше 0.1% от выборки)
    threshold = max(1, len(sample_pixels) // 1000)
    significant_colors = sum(1 for count in color_counts.values() if count >= threshold)
    
    # Комбинируем результаты
    # Берем среднее между уникальными квантованными цветами и значимыми цветами
    estimated = int((unique_quantized + significant_colors) / 2)
    
    # Ограничиваем диапазоном
    estimated = max(min_colors, min(max_colors, estimated))
    
    # Округляем до удобного числа (кратно 4 или 8)
    if estimated < 16:
        estimated = ((estimated + 3) // 4) * 4  # Кратно 4
    else:
        estimated = ((estimated + 7) // 8) * 8  # Кратно 8
    
    _log_info(f"Автоматически определено оптимальное количество цветов: {estimated}")
    return estimated


def _postprocess_palette(palette):
    """
    Постобработка палитры: исключает черный, если есть белый.
    
    Args:
        palette: Палитра цветов в формате (N, 3) RGB
    
    Returns:
        numpy.ndarray: Обработанная палитра
    """
    has_white = np.any(np.all(palette == [255, 255, 255], axis=1))
    if has_white:
        black_mask = ~np.all(palette == [0, 0, 0], axis=1)
        palette = palette[black_mask]
    
    return palette


def create_palette_kmeans(rgb_array, num_colors, opacity_mask=None, random_state=42, focus_on_center=False):
    """
    Создает палитру с использованием KMeans кластеризации.
    Хорошо работает для большинства изображений, дает сбалансированные результаты.
    
    Args:
        rgb_array: Массив изображения в формате (height, width, 3) RGB
        num_colors: Количество цветов в палитре
        opacity_mask: Маска прозрачности
        random_state: Seed для воспроизводимости
        focus_on_center: Если True, фокусируется на центре изображения
    
    Returns:
        numpy.ndarray: Палитра цветов в формате (num_colors, 3) RGB
    """
    if not SKLEARN_AVAILABLE:
        raise ImportError("Для метода KMeans требуется библиотека scikit-learn")
    
    if num_colors <= 1 or num_colors > 256:
        raise ValueError("Количество цветов должно быть от 2 до 256")
    
    _log_info(f"Создание палитры методом KMeans ({num_colors} цветов, focus_on_center={focus_on_center})...")
    
    result = _prepare_pixels(rgb_array, opacity_mask, focus_on_center)
    if focus_on_center:
        sample_pixels, sample_weights = result
    else:
        sample_pixels = result
        sample_weights = None
    
    # KMeans кластеризация
    n_init_value = min(20, max(10, num_colors // 2))
    kmeans = KMeans(n_clusters=num_colors, random_state=random_state, 
                   n_init=n_init_value, max_iter=300, tol=1e-4)
    
    if focus_on_center and sample_weights is not None:
        # Нормализуем веса
        sample_weights = sample_weights / sample_weights.sum()
        kmeans.fit(sample_pixels, sample_weight=sample_weights)
    else:
        kmeans.fit(sample_pixels)
    
    palette = kmeans.cluster_centers_.astype(np.uint8)
    
    palette = _postprocess_palette(palette)
    # Ограничиваем до num_colors на случай, если постобработка не изменила количество
    if len(palette) > num_colors:
        palette = palette[:num_colors]
    _log_info(f"Палитра KMeans создана: {len(palette)} цветов")
    
    return palette


def create_palette_kmeans_improved(rgb_array, num_colors, opacity_mask=None, random_state=42, focus_on_center=False):
    """
    Создает палитру с использованием KMeans кластеризации с улучшенными параметрами.
    Использует больше итераций и попыток для более точных результатов.
    
    Args:
        rgb_array: Массив изображения в формате (height, width, 3) RGB
        num_colors: Количество цветов в палитре
        opacity_mask: Маска прозрачности
        random_state: Seed для воспроизводимости
        focus_on_center: Если True, фокусируется на центре изображения
    
    Returns:
        numpy.ndarray: Палитра цветов в формате (num_colors, 3) RGB
    """
    if not SKLEARN_AVAILABLE:
        raise ImportError("Для метода KMeans требуется библиотека scikit-learn")
    
    if num_colors <= 1 or num_colors > 256:
        raise ValueError("Количество цветов должно быть от 2 до 256")
    
    _log_info(f"Создание палитры методом KMeans (улучшенный) ({num_colors} цветов, focus_on_center={focus_on_center})...")
    
    result = _prepare_pixels(rgb_array, opacity_mask, focus_on_center)
    if focus_on_center:
        sample_pixels, sample_weights = result
    else:
        sample_pixels = result
        sample_weights = None
    
    # KMeans кластеризация с улучшенными параметрами
    # Увеличиваем n_init для большей стабильности
    n_init_value = min(50, max(20, num_colors * 2))
    # Увеличиваем max_iter для лучшей сходимости
    # Уменьшаем tol для более точной сходимости
    kmeans = KMeans(n_clusters=num_colors, random_state=random_state, 
                   n_init=n_init_value, max_iter=500, tol=1e-6,
                   algorithm='lloyd')  # Используем классический алгоритм Lloyd
    
    if focus_on_center and sample_weights is not None:
        # Нормализуем веса
        sample_weights = sample_weights / sample_weights.sum()
        kmeans.fit(sample_pixels, sample_weight=sample_weights)
    else:
        kmeans.fit(sample_pixels)
    
    palette = kmeans.cluster_centers_.astype(np.uint8)
    
    palette = _postprocess_palette(palette)
    # Ограничиваем до num_colors на случай, если постобработка не изменила количество
    if len(palette) > num_colors:
        palette = palette[:num_colors]
    _log_info(f"Палитра KMeans (улучшенный) создана: {len(palette)} цветов")
    
    return palette


def create_palette_kmeans_weighted(rgb_array, num_colors, opacity_mask=None, random_state=42, focus_on_center=False):
    """
    Создает палитру с использованием взвешенной KMeans кластеризации.
    Учитывает частоту цветов в изображении для более точной кластеризации.
    
    Args:
        rgb_array: Массив изображения в формате (height, width, 3) RGB
        num_colors: Количество цветов в палитре
        opacity_mask: Маска прозрачности
        random_state: Seed для воспроизводимости
        focus_on_center: Если True, фокусируется на центре изображения
    
    Returns:
        numpy.ndarray: Палитра цветов в формате (num_colors, 3) RGB
    """
    if not SKLEARN_AVAILABLE:
        raise ImportError("Для метода KMeans требуется библиотека scikit-learn")
    
    if num_colors <= 1 or num_colors > 256:
        raise ValueError("Количество цветов должно быть от 2 до 256")
    
    _log_info(f"Создание палитры методом KMeans (взвешенный) ({num_colors} цветов, focus_on_center={focus_on_center})...")
    
    result = _prepare_pixels(rgb_array, opacity_mask, focus_on_center)
    if focus_on_center:
        sample_pixels, center_weights = result
    else:
        sample_pixels = result
        center_weights = None
    
    # Подсчитываем частоту каждого цвета для весов
    # Квантуем цвета для группировки похожих
    quantize_level = 8  # 8 уровней на канал для группировки похожих цветов
    quantized = (sample_pixels // (256 // quantize_level)).astype(np.int32)
    
    # Создаем словарь частот квантованных цветов
    color_counts = Counter(map(tuple, quantized))
    
    # Создаем веса для каждого пикселя на основе частоты его квантованного цвета
    sample_weights = np.array([color_counts[tuple(q)] for q in quantized], dtype=np.float64)
    
    # Если включена фокусировка на центре, комбинируем веса
    if focus_on_center and center_weights is not None:
        # Комбинируем веса: частота цвета * вес центра
        sample_weights = sample_weights * center_weights
    
    # Нормализуем веса
    sample_weights = sample_weights / sample_weights.sum()
    
    # KMeans кластеризация с весами
    n_init_value = min(30, max(15, num_colors))
    kmeans = KMeans(n_clusters=num_colors, random_state=random_state, 
                   n_init=n_init_value, max_iter=400, tol=1e-5)
    kmeans.fit(sample_pixels, sample_weight=sample_weights)
    palette = kmeans.cluster_centers_.astype(np.uint8)
    
    palette = _postprocess_palette(palette)
    # Ограничиваем до num_colors на случай, если постобработка не изменила количество
    if len(palette) > num_colors:
        palette = palette[:num_colors]
    _log_info(f"Палитра KMeans (взвешенный) создана: {len(palette)} цветов")
    
    return palette


def create_palette_hierarchical_kmeans(rgb_array, num_colors, opacity_mask=None, random_state=42, focus_on_center=False):
    """
    Создает палитру с использованием иерархической кластеризации + KMeans.
    Сначала применяется иерархическая кластеризация для предварительной группировки,
    затем KMeans для уточнения результатов.
    
    Args:
        rgb_array: Массив изображения в формате (height, width, 3) RGB
        num_colors: Количество цветов в палитре
        opacity_mask: Маска прозрачности
        random_state: Seed для воспроизводимости
        focus_on_center: Если True, фокусируется на центре изображения
    
    Returns:
        numpy.ndarray: Палитра цветов в формате (num_colors, 3) RGB
    """
    if not SKLEARN_AVAILABLE:
        raise ImportError("Для метода требуется библиотека scikit-learn")
    
    if num_colors <= 1 or num_colors > 256:
        raise ValueError("Количество цветов должно быть от 2 до 256")
    
    _log_info(f"Создание палитры методом Иерархическая + KMeans ({num_colors} цветов, focus_on_center={focus_on_center})...")
    
    result = _prepare_pixels(rgb_array, opacity_mask, focus_on_center)
    if focus_on_center:
        sample_pixels, sample_weights = result
    else:
        sample_pixels = result
        sample_weights = None
    
    # Если выборка слишком большая, уменьшаем её для иерархической кластеризации
    # (иерархическая кластеризация медленная на больших данных)
    max_samples_for_hierarchical = 10000
    if len(sample_pixels) > max_samples_for_hierarchical:
        # Выбираем случайную выборку
        np.random.seed(random_state)
        indices = np.random.choice(len(sample_pixels), max_samples_for_hierarchical, replace=False)
        hierarchical_sample = sample_pixels[indices]
    else:
        hierarchical_sample = sample_pixels
    
    # Первый этап: иерархическая кластеризация для предварительной группировки
    # Используем больше кластеров, чем нужно, для лучшего покрытия
    n_clusters_hierarchical = min(num_colors * 2, len(hierarchical_sample))
    if n_clusters_hierarchical < num_colors:
        n_clusters_hierarchical = num_colors
    
    hierarchical = AgglomerativeClustering(n_clusters=n_clusters_hierarchical, 
                                          linkage='ward')
    hierarchical_labels = hierarchical.fit_predict(hierarchical_sample)
    
    # Вычисляем центроиды иерархических кластеров
    hierarchical_centers = []
    for i in range(n_clusters_hierarchical):
        cluster_mask = hierarchical_labels == i
        if np.any(cluster_mask):
            center = np.mean(hierarchical_sample[cluster_mask], axis=0)
            hierarchical_centers.append(center)
    
    hierarchical_centers = np.array(hierarchical_centers)
    
    # Второй этап: KMeans на центроидах иерархической кластеризации
    # Используем центроиды как начальные точки для KMeans
    n_init_value = 1  # Используем только одну инициализацию с нашими центрами
    if len(hierarchical_centers) >= num_colors:
        # Используем центроиды как начальные точки
        init_centers = hierarchical_centers[:num_colors]
        kmeans = KMeans(n_clusters=num_colors, random_state=random_state, 
                       n_init=n_init_value, max_iter=300, tol=1e-4,
                       init=init_centers)
    else:
        # Если центроидов меньше, используем k-means++
        kmeans = KMeans(n_clusters=num_colors, random_state=random_state, 
                       n_init=min(20, max(10, num_colors // 2)), max_iter=300, tol=1e-4,
                       init='k-means++')
    
    # Применяем KMeans к полной выборке пикселей
    if focus_on_center and sample_weights is not None:
        # Нормализуем веса
        sample_weights = sample_weights / sample_weights.sum()
        kmeans.fit(sample_pixels, sample_weight=sample_weights)
    else:
        kmeans.fit(sample_pixels)
    palette = kmeans.cluster_centers_.astype(np.uint8)
    
    palette = _postprocess_palette(palette)
    # Ограничиваем до num_colors на случай, если постобработка не изменила количество
    if len(palette) > num_colors:
        palette = palette[:num_colors]
    _log_info(f"Палитра Иерархическая + KMeans создана: {len(palette)} цветов")
    
    return palette


def create_palette_median_cut(rgb_array, num_colors, opacity_mask=None, focus_on_center=False):
    """
    Создает палитру с использованием алгоритма Median Cut.
    Хорошо работает для изображений с большим количеством различных цветов.
    
    Args:
        rgb_array: Массив изображения в формате (height, width, 3) RGB
        num_colors: Количество цветов в палитре (должно быть степенью 2)
        opacity_mask: Маска прозрачности
        focus_on_center: Если True, фокусируется на центре изображения
    
    Returns:
        numpy.ndarray: Палитра цветов в формате (num_colors, 3) RGB
    """
    if num_colors <= 1 or num_colors > 256:
        raise ValueError("Количество цветов должно быть от 2 до 256")
    
    _log_info(f"Создание палитры методом Median Cut ({num_colors} цветов, focus_on_center={focus_on_center})...")
    
    result = _prepare_pixels(rgb_array, opacity_mask, focus_on_center)
    if focus_on_center:
        sample_pixels, sample_weights = result
        # Взвешиваем пиксели: дублируем их пропорционально весу
        # Нормализуем веса и умножаем на коэффициент для дублирования
        sample_weights = sample_weights / sample_weights.sum()
        max_weight = sample_weights.max()
        # Масштабируем веса для разумного количества дубликатов
        scale_factor = 10.0 / max_weight if max_weight > 0 else 1.0
        weights_scaled = (sample_weights * scale_factor).astype(int)
        weights_scaled = np.maximum(weights_scaled, 1)  # Минимум 1 раз
        
        # Дублируем пиксели согласно весам
        weighted_pixels = []
        for pixel, weight in zip(sample_pixels, weights_scaled):
            weighted_pixels.extend([pixel] * weight)
        sample_pixels = np.array(weighted_pixels)
    else:
        sample_pixels = result
    
    # Округляем до ближайшей степени 2
    actual_colors = 2 ** int(np.log2(num_colors))
    if actual_colors != num_colors:
        _log_info(f"Округление до {actual_colors} цветов (ближайшая степень 2)")
    
    # Реализация Median Cut
    def median_cut(pixels, depth, max_depth):
        if depth == max_depth or len(pixels) == 0:
            # Возвращаем средний цвет
            return [np.mean(pixels, axis=0).astype(np.uint8)]
        
        # Находим канал с наибольшим диапазоном
        ranges = np.max(pixels, axis=0) - np.min(pixels, axis=0)
        channel = np.argmax(ranges)
        
        # Сортируем по этому каналу
        sorted_indices = np.argsort(pixels[:, channel])
        sorted_pixels = pixels[sorted_indices]
        
        # Разделяем пополам
        mid = len(sorted_pixels) // 2
        left = sorted_pixels[:mid]
        right = sorted_pixels[mid:]
        
        # Рекурсивно обрабатываем обе части
        result = []
        result.extend(median_cut(left, depth + 1, max_depth))
        result.extend(median_cut(right, depth + 1, max_depth))
        return result
    
    max_depth = int(np.log2(actual_colors))
    palette = np.array(median_cut(sample_pixels, 0, max_depth))
    
    # Если получилось меньше цветов, дополняем случайными
    while len(palette) < actual_colors:
        random_color = sample_pixels[np.random.randint(len(sample_pixels))]
        palette = np.vstack([palette, random_color.reshape(1, -1)])
    
    palette = palette[:actual_colors]
    palette = _postprocess_palette(palette)
    # Ограничиваем до actual_colors на случай, если постобработка не изменила количество
    if len(palette) > actual_colors:
        palette = palette[:actual_colors]
    _log_info(f"Палитра Median Cut создана: {len(palette)} цветов")
    
    return palette


def create_palette_octree(rgb_array, num_colors, opacity_mask=None, focus_on_center=False):
    """
    Создает палитру с использованием Octree (дерево октантов).
    Эффективен для изображений с большим количеством уникальных цветов.
    
    Args:
        rgb_array: Массив изображения в формате (height, width, 3) RGB
        num_colors: Количество цветов в палитре
        opacity_mask: Маска прозрачности
        focus_on_center: Если True, фокусируется на центре изображения
    
    Returns:
        numpy.ndarray: Палитра цветов в формате (num_colors, 3) RGB
    """
    if num_colors <= 1 or num_colors > 256:
        raise ValueError("Количество цветов должно быть от 2 до 256")
    
    _log_info(f"Создание палитры методом Octree ({num_colors} цветов, focus_on_center={focus_on_center})...")
    
    result = _prepare_pixels(rgb_array, opacity_mask, focus_on_center)
    if focus_on_center:
        sample_pixels, sample_weights = result
        # Взвешиваем пиксели: дублируем их пропорционально весу
        sample_weights = sample_weights / sample_weights.sum()
        max_weight = sample_weights.max()
        scale_factor = 10.0 / max_weight if max_weight > 0 else 1.0
        weights_scaled = (sample_weights * scale_factor).astype(int)
        weights_scaled = np.maximum(weights_scaled, 1)
        
        weighted_pixels = []
        for pixel, weight in zip(sample_pixels, weights_scaled):
            weighted_pixels.extend([pixel] * weight)
        sample_pixels = np.array(weighted_pixels)
    else:
        sample_pixels = result
    
    # Упрощенная реализация Octree
    # Группируем похожие цвета
    # Квантуем цвета для группировки
    quantize_level = 8  # 8 уровней на канал = 512 возможных групп
    quantized = (sample_pixels // (256 // quantize_level)).astype(np.int32)
    
    # Группируем по квантованным значениям
    color_groups = defaultdict(list)
    for i, q_color in enumerate(quantized):
        key = tuple(q_color)
        color_groups[key].append(sample_pixels[i])
    
    # Вычисляем средние цвета для каждой группы
    group_colors = []
    for group in color_groups.values():
        if len(group) > 0:
            group_colors.append(np.mean(group, axis=0).astype(np.uint8))
    
    # Если групп больше, чем нужно, используем KMeans для финальной кластеризации
    if len(group_colors) > num_colors:
        if SKLEARN_AVAILABLE:
            kmeans = KMeans(n_clusters=num_colors, random_state=42, n_init=10)
            kmeans.fit(group_colors)
            palette = kmeans.cluster_centers_.astype(np.uint8)
        else:
            # Просто берем первые num_colors
            palette = np.array(group_colors[:num_colors])
    else:
        palette = np.array(group_colors)
        # Дополняем, если нужно
        while len(palette) < num_colors and len(sample_pixels) > 0:
            random_color = sample_pixels[np.random.randint(len(sample_pixels))]
            palette = np.vstack([palette, random_color.reshape(1, -1)])
    
    palette = palette[:num_colors]
    palette = _postprocess_palette(palette)
    # Ограничиваем до num_colors на случай, если постобработка не изменила количество
    if len(palette) > num_colors:
        palette = palette[:num_colors]
    _log_info(f"Палитра Octree создана: {len(palette)} цветов")
    
    return palette


def create_palette_dominant(rgb_array, num_colors, opacity_mask=None):
    """
    Создает палитру на основе доминирующих цветов через анализ гистограмм.
    Хорошо работает для изображений с четко выраженными основными цветами.
    
    Args:
        rgb_array: Массив изображения в формате (height, width, 3) RGB
        num_colors: Количество цветов в палитре
        opacity_mask: Маска прозрачности
    
    Returns:
        numpy.ndarray: Палитра цветов в формате (num_colors, 3) RGB
    """
    if num_colors <= 1 or num_colors > 256:
        raise ValueError("Количество цветов должно быть от 2 до 256")
    
    _log_info(f"Создание палитры методом Dominant Colors ({num_colors} цветов)...")
    
    sample_pixels = _prepare_pixels(rgb_array, opacity_mask)
    
    # Квантуем цвета для построения гистограммы
    quantize_level = 16  # 16 уровней на канал
    quantized = (sample_pixels // (256 // quantize_level)).astype(np.int32)
    
    # Создаем гистограмму
    color_counts = Counter(map(tuple, quantized))
    
    # Берем наиболее частые цвета
    most_common = color_counts.most_common(num_colors * 2)  # Берем больше для фильтрации
    
    # Преобразуем обратно в RGB и усредняем
    palette_colors = []
    for q_color, count in most_common:
        # Находим все пиксели с этим квантованным цветом
        mask = np.all(quantized == q_color, axis=1)
        if np.any(mask):
            avg_color = np.mean(sample_pixels[mask], axis=0).astype(np.uint8)
            palette_colors.append(avg_color)
    
    # Если получилось меньше, дополняем
    palette = np.array(palette_colors[:num_colors])
    while len(palette) < num_colors and len(sample_pixels) > 0:
        random_color = sample_pixels[np.random.randint(len(sample_pixels))]
        palette = np.vstack([palette, random_color.reshape(1, -1)])
    
    palette = palette[:num_colors]
    palette = _postprocess_palette(palette)
    # Ограничиваем до num_colors на случай, если постобработка не изменила количество
    if len(palette) > num_colors:
        palette = palette[:num_colors]
    _log_info(f"Палитра Dominant Colors создана: {len(palette)} цветов")
    
    return palette


def create_palette_quantization(rgb_array, num_colors, opacity_mask=None):
    """
    Создает палитру через равномерное квантование цветового пространства.
    Быстрый метод, дает равномерное распределение цветов.
    
    Args:
        rgb_array: Массив изображения в формате (height, width, 3) RGB
        num_colors: Количество цветов в палитре
        opacity_mask: Маска прозрачности
    
    Returns:
        numpy.ndarray: Палитра цветов в формате (num_colors, 3) RGB
    """
    if num_colors <= 1 or num_colors > 256:
        raise ValueError("Количество цветов должно быть от 2 до 256")
    
    _log_info(f"Создание палитры методом Color Quantization ({num_colors} цветов)...")
    
    sample_pixels = _prepare_pixels(rgb_array, opacity_mask)
    
    # Вычисляем количество уровней квантования для каждого канала
    # Для num_colors цветов: levels_per_channel = cube_root(num_colors)
    levels = int(np.ceil(np.power(num_colors, 1.0/3.0)))
    
    # Создаем равномерную сетку в RGB пространстве
    step = 256 // levels
    palette = []
    
    for r in range(0, 256, step):
        for g in range(0, 256, step):
            for b in range(0, 256, step):
                palette.append([r, g, b])
                if len(palette) >= num_colors:
                    break
            if len(palette) >= num_colors:
                break
        if len(palette) >= num_colors:
            break
    
    # Если получилось меньше, дополняем
    palette = np.array(palette[:num_colors])
    
    # Находим ближайшие реальные цвета из изображения
    if len(sample_pixels) > 0:
        palette_float = palette.astype(np.float32)
        sample_float = sample_pixels.astype(np.float32)
        
        # Для каждого цвета палитры находим ближайший реальный цвет
        for i in range(len(palette)):
            distances = np.sqrt(np.sum((sample_float - palette_float[i]) ** 2, axis=1))
            closest_idx = np.argmin(distances)
            palette[i] = sample_pixels[closest_idx]
    
    palette = _postprocess_palette(palette)
    # Ограничиваем до num_colors на случай, если постобработка не изменила количество
    if len(palette) > num_colors:
        palette = palette[:num_colors]
    _log_info(f"Палитра Color Quantization создана: {len(palette)} цветов")
    
    return palette

