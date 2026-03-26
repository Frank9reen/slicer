"""Операции закрашивания и фрагментации изображений"""
import warnings
# Подавляем warnings от numpy, sklearn и других библиотек
warnings.filterwarnings('ignore')

import numpy as np
from PIL import Image, ImageDraw
from tkinter import messagebox
from utils.version_utils import get_app_name_with_version
from utils.logger import setup_logger

logger = setup_logger(__name__)


class PaintOperations:
    """Управляет операциями автоматического закрашивания и фрагментации изображений."""
    
    def __init__(self, editor):
        """
        Args:
            editor: Экземпляр GridEditor
        """
        self.editor = editor
    
    def fragment_image(self):
        """Фрагментирует изображение на блоки и создает палитру цветов"""
        if self.editor.image is None:
            messagebox.showwarning("Предупреждение", "Сначала откройте изображение!")
            return
        
        if len(self.editor.vertical_lines) < 2 or len(self.editor.horizontal_lines) < 2:
            messagebox.showwarning("Предупреждение", "Сначала постройте сетку!")
            return
        
        try:
            # Используем оригинальное изображение, если оно доступно, иначе текущее
            # Это гарантирует, что фрагментация всегда работает с исходным изображением,
            # а не с уже обработанным (например, после автозакрашивания)
            source_image = self.editor.original_image if self.editor.original_image is not None else self.editor.image
            
            # Получаем RGB массив изображения
            img_array = np.array(source_image)
            if img_array.shape[2] == 4:
                rgb_array = img_array[:, :, :3]
                alpha_channel = img_array[:, :, 3]
                # Создаем маску прозрачности (True для непрозрачных пикселей)
                opacity_mask = alpha_channel > 10
            else:
                rgb_array = img_array
                alpha_channel = None
                opacity_mask = None
            
            # Вычисляем размеры блоков
            block_widths = []
            for i in range(len(self.editor.vertical_lines) - 1):
                block_widths.append(self.editor.vertical_lines[i+1] - self.editor.vertical_lines[i])
            
            block_heights = []
            for i in range(len(self.editor.horizontal_lines) - 1):
                block_heights.append(self.editor.horizontal_lines[i+1] - self.editor.horizontal_lines[i])
            
            # Нормализуем размеры блоков (берем минимальный размер)
            normalized_width = min(block_widths) if block_widths else 10
            normalized_height = min(block_heights) if block_heights else 10
            
            # Создаем палитру цветов, если указано количество цветов
            num_colors_input = self.editor.num_colors.get()
            palette = None
            quantized_image = None
            
            # Проверяем, выбраны ли методы автоматического определения палитры
            selected_palette_methods = []
            if hasattr(self.editor, 'palette_method_kmeans') and self.editor.palette_method_kmeans.get():
                selected_palette_methods.append('kmeans')
            if hasattr(self.editor, 'palette_method_kmeans_improved') and self.editor.palette_method_kmeans_improved.get():
                selected_palette_methods.append('kmeans_improved')
            if hasattr(self.editor, 'palette_method_kmeans_weighted') and self.editor.palette_method_kmeans_weighted.get():
                selected_palette_methods.append('kmeans_weighted')
            if hasattr(self.editor, 'palette_method_hierarchical_kmeans') and self.editor.palette_method_hierarchical_kmeans.get():
                selected_palette_methods.append('hierarchical_kmeans')
            if hasattr(self.editor, 'palette_method_median_cut') and self.editor.palette_method_median_cut.get():
                selected_palette_methods.append('median_cut')
            if hasattr(self.editor, 'palette_method_octree') and self.editor.palette_method_octree.get():
                selected_palette_methods.append('octree')
            
            # Если выбран хотя бы один метод, используем автоматическое определение
            auto_palette_enabled = len(selected_palette_methods) > 0
            
            if auto_palette_enabled:
                # Автоматически определяем оптимальное количество цветов
                # Используем значение из поля ввода как максимальное ограничение
                from color.palette_methods import estimate_optimal_colors
                if num_colors_input > 0:
                    # Используем значение из поля ввода как максимальное ограничение
                    max_colors = num_colors_input
                    estimated_colors = estimate_optimal_colors(rgb_array, opacity_mask, min_colors=8, max_colors=max_colors)
                    # Ограничиваем до указанного пользователем количества
                    num_colors = min(estimated_colors, max_colors)
                    logger.info(f"Автоматическое определение палитры: определено {estimated_colors} цветов, ограничено до {num_colors} (максимум из поля ввода: {max_colors})")
                else:
                    # Если 0, используем автоматическое определение без ограничений (максимум 128)
                    num_colors = estimate_optimal_colors(rgb_array, opacity_mask, min_colors=8, max_colors=128)
                    logger.info(f"Автоматическое определение палитры: определено {num_colors} цветов (без ограничений)")
            else:
                # Если методы не выбраны, используем значение из поля ввода
                num_colors = num_colors_input
                
                # Если методы не выбраны и указано количество цветов > 0, 
                # показываем предупреждение и не создаем палитру
                # Если num_colors = 0, то палитра не нужна, предупреждение не показываем
                if num_colors > 0:
                    messagebox.showwarning(
                        "Предупреждение", 
                        "Не выбран ни один метод автоматического определения палитры!\n\n"
                        "Для создания палитры выберите хотя бы один метод:\n"
                        "• KMeans\n"
                        "• KMeans Improved\n"
                        "• KMeans Weighted\n"
                        "• Hierarchical KMeans\n"
                        "• Median Cut\n"
                        "• Octree\n\n"
                        "Или установите количество цветов в 0 для фрагментации без ограничения палитры."
                    )
                    return
            
            if auto_palette_enabled:
                # Устанавливаем выбранные методы в palette_manager
                self.editor.palette_manager.method_kmeans = (
                    hasattr(self.editor, 'palette_method_kmeans') and 
                    self.editor.palette_method_kmeans.get()
                )
                self.editor.palette_manager.method_kmeans_improved = (
                    hasattr(self.editor, 'palette_method_kmeans_improved') and 
                    self.editor.palette_method_kmeans_improved.get()
                )
                self.editor.palette_manager.method_kmeans_weighted = (
                    hasattr(self.editor, 'palette_method_kmeans_weighted') and 
                    self.editor.palette_method_kmeans_weighted.get()
                )
                self.editor.palette_manager.method_hierarchical_kmeans = (
                    hasattr(self.editor, 'palette_method_hierarchical_kmeans') and 
                    self.editor.palette_method_hierarchical_kmeans.get()
                )
                self.editor.palette_manager.method_median_cut = (
                    hasattr(self.editor, 'palette_method_median_cut') and 
                    self.editor.palette_method_median_cut.get()
                )
                self.editor.palette_manager.method_octree = (
                    hasattr(self.editor, 'palette_method_octree') and 
                    self.editor.palette_method_octree.get()
                )
                
                # Устанавливаем фокусировку на центре
                self.editor.palette_manager.focus_on_center = (
                    hasattr(self.editor, 'focus_on_center_var') and 
                    self.editor.focus_on_center_var.get()
                )
            else:
                # Если автоматическое определение выключено и num_colors = 0,
                # отключаем все методы (палитра не будет создана)
                self.editor.palette_manager.method_kmeans = False
                self.editor.palette_manager.method_kmeans_improved = False
                self.editor.palette_manager.method_kmeans_weighted = False
                self.editor.palette_manager.method_hierarchical_kmeans = False
                self.editor.palette_manager.method_median_cut = False
                self.editor.palette_manager.method_octree = False
                self.editor.palette_manager.focus_on_center = False
            
            # Используем новый модуль для создания палитры
            palette, quantized_image = self.editor.palette_manager.create_palette(
                rgb_array, num_colors, opacity_mask, color_space='RGB'
            )
            
            if num_colors == 0:
                logger.info("Фрагментация без ограничения палитры")
                quantized_image = rgb_array
            
            # Создаем новое изображение с нормализованными блоками
            num_cols = len(self.editor.vertical_lines) - 1
            num_rows = len(self.editor.horizontal_lines) - 1
            
            fragmented_array = np.zeros((num_rows * normalized_height, 
                                        num_cols * normalized_width, 3), dtype=np.uint8)
            
            # Используем квантованное изображение, если палитра применена
            source_image = quantized_image if quantized_image is not None else rgb_array
            
            # Обрабатываем каждый блок
            for row in range(num_rows):
                y1 = self.editor.horizontal_lines[row]
                y2 = self.editor.horizontal_lines[row + 1]
                
                for col in range(num_cols):
                    x1 = self.editor.vertical_lines[col]
                    x2 = self.editor.vertical_lines[col + 1]
                    
                    # Извлекаем блок из квантованного изображения
                    block = source_image[y1:y2, x1:x2]
                    
                    if block.size == 0:
                        continue
                    
                    # Определяем доминирующий цвет блока
                    block_flat = block.reshape(-1, 3)
                    
                    # Фильтруем прозрачные и белые пиксели
                    if opacity_mask is not None:
                        # Получаем маску прозрачности для этого блока
                        block_alpha = alpha_channel[y1:y2, x1:x2]
                        block_alpha_flat = block_alpha.flatten()
                        # Исключаем прозрачные пиксели (альфа < 10)
                        valid_alpha_mask = block_alpha_flat > 10
                    else:
                        valid_alpha_mask = np.ones(len(block_flat), dtype=bool)
                    
                    # Исключаем белые пиксели (255, 255, 255)
                    white_mask = ~np.all(block_flat == [255, 255, 255], axis=1)
                    valid_mask = valid_alpha_mask & white_mask
                    
                    # Если есть валидные пиксели, используем их, иначе пропускаем блок
                    if not np.any(valid_mask):
                        # Если все пиксели прозрачные или белые, пропускаем этот блок
                        continue
                    
                    block_flat_filtered = block_flat[valid_mask]
                    
                    # Если есть палитра, находим наиболее частый цвет из палитры в блоке
                    if palette is not None:
                        # Находим ближайший цвет палитры для каждого пикселя блока
                        # Более эффективный способ: вычисляем расстояния для каждого пикселя
                        block_colors = block_flat_filtered.astype(np.float32)
                        palette_colors = palette.astype(np.float32)
                        
                        # Вычисляем расстояния от каждого пикселя до каждого цвета палитры
                        distances = np.sqrt(np.sum((block_colors[:, np.newaxis, :] - palette_colors[np.newaxis, :, :]) ** 2, axis=2))
                        closest_indices = np.argmin(distances, axis=1)
                        
                        # Находим наиболее частый цвет палитры в блоке
                        if len(closest_indices) > 0:
                            # Используем bincount для подсчета частоты
                            counts = np.bincount(closest_indices, minlength=len(palette))
                            most_common_idx = np.argmax(counts)
                            quantized = palette[most_common_idx]
                        else:
                            quantized = palette[0]  # Fallback
                    else:
                        # Улучшенный алгоритм определения доминирующего цвета
                        # Используем медиану для удаления выбросов (теней)
                        median_color = np.median(block_flat_filtered, axis=0).astype(np.uint8)
                        
                        # Адаптивный порог на основе дисперсии цветов в блоке
                        color_std = np.std(block_flat_filtered, axis=0)
                        avg_std = np.mean(color_std)
                        
                        # Если цвета очень однородны (низкая дисперсия), используем более строгий порог
                        # Если цвета разнообразны, используем более мягкий порог
                        if avg_std < 20:
                            percentile = 60  # Более строгий отбор для однородных блоков
                        elif avg_std > 50:
                            percentile = 80  # Более мягкий отбор для разнообразных блоков
                        else:
                            percentile = 70  # Стандартный порог
                        
                        # Находим цвета, близкие к медиане (убираем тени)
                        distances = np.sqrt(np.sum((block_flat_filtered - median_color) ** 2, axis=1))
                        threshold = np.percentile(distances, percentile)
                        similar_colors = block_flat_filtered[distances < threshold]
                        
                        if len(similar_colors) > 0:
                            # Используем медиану похожих цветов
                            dominant_color = np.median(similar_colors, axis=0).astype(np.uint8)
                        else:
                            dominant_color = median_color
                        
                        # Улучшенное квантование: более точное, но все еще удаляет градиенты
                        # Используем шаг 16 вместо 32 для лучшей точности
                        quantized = (dominant_color // 16) * 16
                        # Ограничиваем значения диапазоном [0, 255]
                        quantized = np.clip(quantized, 0, 255).astype(np.uint8)
                    
                    # Закрашиваем нормализованный блок этим цветом
                    frag_y1 = row * normalized_height
                    frag_y2 = (row + 1) * normalized_height
                    frag_x1 = col * normalized_width
                    frag_x2 = (col + 1) * normalized_width
                    
                    fragmented_array[frag_y1:frag_y2, frag_x1:frag_x2] = quantized
            
            # Создаем изображение из массива
            self.editor.fragmented_image = Image.fromarray(fragmented_array)
            
            # Сохраняем палитру
            if palette is not None:
                self.editor.palette = palette
                self.editor.palette_manager.set_palette(palette)
            else:
                # Если палитры нет, собираем уникальные цвета из фрагментированного изображения
                unique_colors = np.unique(fragmented_array.reshape(-1, 3), axis=0)
                # Исключаем белый цвет (255, 255, 255) из палитры
                white_mask = ~np.all(unique_colors == [255, 255, 255], axis=1)
                unique_colors = unique_colors[white_mask]
                
                # Если в палитре есть белый цвет (хотя мы его исключили, но проверим на всякий случай),
                # или если был белый до исключения, то исключаем черный
                has_white_in_original = np.any(np.all(np.unique(fragmented_array.reshape(-1, 3), axis=0) == [255, 255, 255], axis=1))
                if has_white_in_original:
                    # Исключаем черный цвет (0, 0, 0) из палитры
                    black_mask = ~np.all(unique_colors == [0, 0, 0], axis=1)
                    unique_colors = unique_colors[black_mask]
                    self.editor.palette = unique_colors
                    logger.info(f"Найдено уникальных цветов: {len(self.editor.palette)} (белый и черный исключены)")
                else:
                    self.editor.palette = unique_colors
                    logger.info(f"Найдено уникальных цветов: {len(self.editor.palette)} (белый цвет исключен)")
            
            # Очищаем закрашенные ячейки при создании новой палитры
            # Это необходимо, чтобы при повторной фрагментации старые цвета не мешали проверке неиспользуемых цветов
            self.editor.painted_cells = {}
            
            # Упорядочиваем палитру по номерам Гаммы
            self.editor.palette_ui.sort_palette_by_gamma()
            
            # Обновляем отображение после упорядочивания
            self.editor.update_display()
            
            # Отображаем палитру
            self.editor.display_palette()
            
            # Обновляем информацию в футере после создания палитры
            self.editor.update_footer_info()
            
            # Блокируем сетку после получения палитры
            self.editor.grid_locked = True
            # Отключаем кнопки управления сеткой
            if hasattr(self.editor, 'grid_panel'):
                self.editor.grid_panel.disable_grid_controls()
            
            # Используем реальное количество цветов в палитре после удаления дубликатов и упорядочивания
            # Берем значение после всех операций с палитрой
            if self.editor.palette is not None and len(self.editor.palette) > 0:
                actual_palette_size = len(self.editor.palette)
                palette_info = f"Палитра: {actual_palette_size} уникальных цветов"
            else:
                palette_info = "Палитра: не создана"
            
            app_name = get_app_name_with_version()
            messagebox.showinfo(f"Успех - {app_name}", f"Изображение фрагментировано!\n"
                                        f"Размер: {fragmented_array.shape[1]}x{fragmented_array.shape[0]}\n"
                                        f"Блоков: {num_cols}x{num_rows}\n"
                                        f"{palette_info}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось фрагментировать изображение:\n{str(e)}")
    
    def auto_paint_cells(self, palette=None, rgb_array=None):
        """
        Автоматически закрашивает все ячейки сетки ближайшими цветами из палитры
        
        Параметры:
        ----------
        palette : numpy.ndarray, optional
            Палитра цветов. Если None, используется self.palette
        rgb_array : numpy.ndarray, optional
            RGB массив изображения. Если None, создается из self.image
        """
        # Убираем фокус с полей ввода
        self.editor.canvas.focus_set()
        
        if self.editor.palette is None or len(self.editor.palette) == 0:
            messagebox.showwarning("Предупреждение", "Сначала создайте палитру!\nНажмите 'Получить палитру'.")
            return
        
        if len(self.editor.vertical_lines) < 2 or len(self.editor.horizontal_lines) < 2:
            messagebox.showwarning("Предупреждение", "Сначала постройте сетку!")
            return
        
        if self.editor.image is None:
            messagebox.showwarning("Предупреждение", "Сначала откройте изображение!")
            return
        
        try:
            # Сохраняем состояние перед автоматическим закрашиванием
            self.editor.save_state()
            
            # Используем переданную палитру или self.palette
            working_palette = palette if palette is not None else self.editor.palette
            
            # Получаем RGB массив изображения для анализа цвета
            # ВАЖНО: Используем original_image для анализа, чтобы всегда брать цвета из оригинала,
            # а не из уже закрашенного изображения
            if rgb_array is None:
                # Используем оригинальное изображение для анализа цвета ячеек
                source_image = self.editor.original_image if self.editor.original_image is not None else self.editor.image
                img_array = np.array(source_image)
                if img_array.shape[2] == 4:
                    rgb_array = img_array[:, :, :3]
                else:
                    rgb_array = img_array
            
            # Создаем копию изображения для рисования
            img_copy = self.editor.image.copy()
            draw = ImageDraw.Draw(img_copy)
            
            num_cols = len(self.editor.vertical_lines) - 1
            num_rows = len(self.editor.horizontal_lines) - 1
            
            logger.info(f"Автоматическое закрашивание {num_cols}x{num_rows} ячеек...")
            
            # Преобразуем палитру в float32 для вычислений
            palette_colors = working_palette.astype(np.float32)
            
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
            
            for row in range(num_rows):
                y1 = self.editor.horizontal_lines[row]
                y2 = self.editor.horizontal_lines[row + 1]
                
                for col in range(num_cols):
                    x1 = self.editor.vertical_lines[col]
                    x2 = self.editor.vertical_lines[col + 1]
                    
                    # Извлекаем блок из исходного изображения для анализа цвета
                    block = rgb_array[y1:y2, x1:x2]
                    if block.size == 0:
                        continue
                    
                    block_flat = block.reshape(-1, 3)
                    
                    # Проверяем, не является ли блок в основном белым
                    # Если большинство пикселей белые (255, 255, 255), пропускаем этот блок
                    white_pixels = np.all(block_flat == [255, 255, 255], axis=1)
                    white_ratio = np.sum(white_pixels) / len(block_flat)
                    if white_ratio > 0.5:  # Если больше 50% пикселей белые, пропускаем
                        continue
                    
                    # Фильтруем белые пиксели из анализа
                    non_white_mask = ~np.all(block_flat == [255, 255, 255], axis=1)
                    if np.sum(non_white_mask) == 0:
                        # Если все пиксели белые, пропускаем
                        continue
                    
                    block_flat_filtered = block_flat[non_white_mask]
                    
                    # Улучшенный алгоритм: вычисляем средний цвет ячейки (убираем тени через медиану)
                    median_color = np.median(block_flat_filtered, axis=0).astype(np.uint8)
                    
                    # Проверяем, не является ли медианный цвет близким к белому
                    # Если медианный цвет близок к белому (например, все компоненты > 240), пропускаем
                    if np.all(median_color >= 240):
                        continue
                    
                    # Используем ту же логику, что и при фрагментации:
                    # Находим ближайший цвет палитры для каждого пикселя блока
                    # и выбираем наиболее частый цвет из палитры
                    block_colors = block_flat_filtered.astype(np.float32)
                    
                    # Вычисляем расстояния от каждого пикселя до каждого цвета палитры
                    distances = np.sqrt(np.sum((block_colors[:, np.newaxis, :] - palette_colors[np.newaxis, :, :]) ** 2, axis=2))
                    closest_indices = np.argmin(distances, axis=1)
                    
                    # Находим наиболее частый цвет палитры в блоке (как при фрагментации)
                    if len(closest_indices) > 0:
                        # Используем bincount для подсчета частоты
                        counts = np.bincount(closest_indices, minlength=len(working_palette))
                        most_common_idx = np.argmax(counts)
                        closest_color = working_palette[most_common_idx]
                    else:
                        # Fallback: используем медиану и находим ближайший цвет
                        median_color = np.median(block_flat_filtered, axis=0).astype(np.float32)
                        distances = np.sqrt(np.sum((palette_colors - median_color) ** 2, axis=1))
                        closest_idx = np.argmin(distances)
                        closest_color = working_palette[closest_idx]
                    
                    # Закрашиваем ячейку ближайшим цветом из палитры
                    color_tuple = tuple(closest_color.astype(int))
                    
                    # Не закрашиваем почти белый цвет (почти белый - это цвет подложки)
                    # Если цвет есть в палитре (включая черный и белый), используем его
                    # closest_color всегда из палитры, поэтому если он был создан на этапе фрагментации, используем его
                    # Теперь белый (255, 255, 255) можно закрашивать
                    is_background = color_tuple[:3] == (254, 254, 254)
                    
                    # Используем цвет, если он не почти белый (цвет подложки)
                    # Если цвет (включая черный и белый) есть в палитре, значит он был создан на этапе фрагментации и должен использоваться
                    if not is_background:
                        # Вычисляем нормализованные координаты для закрашивания
                        # Центрируем нормализованную ячейку внутри исходной ячейки
                        cell_w = x2 - x1
                        cell_h = y2 - y1
                        
                        # Убеждаемся, что нормализованные размеры не больше размера ячейки
                        actual_width = min(normalized_width, cell_w)
                        actual_height = min(normalized_height, cell_h)
                        
                        offset_x = (cell_w - actual_width) // 2
                        offset_y = (cell_h - actual_height) // 2
                        
                        # Закрашиваем нормализованную область
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
                            draw.rectangle([paint_x1, paint_y1, paint_x2-1, paint_y2-1], fill=color_tuple, outline=None)
                        
                        # Сохраняем информацию о закрашенной ячейке
                        self.editor.painted_cells[(col, row)] = color_tuple
            
            logger.info("Автоматическое закрашивание завершено")
            
            # Обновляем изображение
            self.editor.image = img_copy
            
            # Автоматически переключаемся на режим 2 при автоматическом закрашивании
            if self.editor.view_mode == 1:
                self.editor.set_view_mode(2)
            else:
                self.editor.update_display()
            
            # Подсчитываем количество ячеек для каждого цвета палитры
            # и находим неиспользуемые цвета (с 0 ячеек)
            # Проверка выполняется всегда после автозакрашивания, даже при повторной сборке палитры
            unused_color_indices = []
            if self.editor.palette is not None and len(self.editor.palette) > 0:
                # Проверяем, есть ли закрашенные ячейки
                if self.editor.painted_cells and len(self.editor.painted_cells) > 0:
                    palette_colors = self.editor.palette.astype(np.float32)
                    color_counts = {i: 0 for i in range(len(self.editor.palette))}
                    
                    # Используем ту же логику нормализации, что и в display_palette
                    for cell_color in self.editor.painted_cells.values():
                        # Нормализуем цвет ячейки (используем ту же логику, что в palette_ui)
                        # _normalize_color - это метод экземпляра PaletteUI
                        cell_rgb = self.editor.palette_ui._normalize_color(cell_color)
                        if cell_rgb is None:
                            continue
                        
                        cell_color_array = np.array(cell_rgb, dtype=np.float32)
                        distances = np.sqrt(np.sum((cell_color_array - palette_colors) ** 2, axis=1))
                        closest_idx = int(np.argmin(distances))
                        color_counts[closest_idx] = color_counts.get(closest_idx, 0) + 1
                    
                    # Находим индексы цветов с 0 ячеек
                    unused_color_indices = [i for i, count in color_counts.items() if count == 0]
                else:
                    # Если нет закрашенных ячеек, значит все цвета в палитре неиспользуемые
                    # (хотя это не должно происходить после автозакрашивания, но на всякий случай)
                    unused_color_indices = list(range(len(self.editor.palette)))
            
            # Обновляем палитру для отображения новых счетчиков
            if self.editor.palette is not None:
                self.editor.display_palette()
            
            app_name = get_app_name_with_version()
            
            # Если есть неиспользуемые цвета, предупреждаем пользователя
            if unused_color_indices:
                unused_count = len(unused_color_indices)
                result = messagebox.askyesno(
                    f"Информация - {app_name}",
                    f"Автоматическое закрашивание выполнено!\n"
                    f"Закрашено ячеек: {num_cols}x{num_rows}\n\n"
                    f"Обнаружено {unused_count} цветов в палитре, которые не используются "
                    f"(0 ячеек).\n\n"
                    f"Удалить неиспользуемые цвета из палитры?",
                    icon='question'
                )
                
                if result:
                    # Удаляем неиспользуемые цвета из палитры
                    # Удаляем в обратном порядке, чтобы индексы не сдвигались
                    for idx in sorted(unused_color_indices, reverse=True):
                        self.editor.palette = np.delete(self.editor.palette, idx, axis=0)
                    
                    # Обновляем отображение палитры
                    self.editor.display_palette()
                    
                    messagebox.showinfo(
                        f"Успех - {app_name}",
                        f"Удалено {unused_count} неиспользуемых цветов из палитры."
                    )
            else:
                messagebox.showinfo(f"Успех - {app_name}", f"Автоматическое закрашивание выполнено!\n"
                                        f"Закрашено ячеек: {num_cols}x{num_rows}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось выполнить автоматическое закрашивание:\n{str(e)}")
            import traceback
            logger.error(traceback.format_exc())

