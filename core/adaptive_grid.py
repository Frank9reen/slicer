"""Адаптивная сетка на основе анализа ячеистости изображения"""
import numpy as np
from PIL import Image

try:
    from scipy.signal import find_peaks
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


class AdaptiveGrid:
    """Класс для построения адаптивной сетки на основе анализа изображения"""
    
    def __init__(self):
        self.vertical_lines = []
        self.horizontal_lines = []
    
    def detect_by_gradients(self, image, min_cell_size=3, max_cell_size=50):
        """
        Анализ градиентов яркости.
        Эффективен для изображений с плавными переходами цветов.
        
        Args:
            image: PIL Image или numpy array
            min_cell_size: Минимальный размер ячейки в пикселях
            max_cell_size: Максимальный размер ячейки в пикселях
        
        Returns:
            tuple: (vertical_lines, horizontal_lines) - списки позиций линий
        """
        if not CV2_AVAILABLE or not SCIPY_AVAILABLE:
            raise ImportError("Для адаптивной сетки требуются библиотеки opencv-python и scipy")
        
        # Преобразуем изображение в numpy array
        if isinstance(image, Image.Image):
            img_array = np.array(image.convert('RGB'))
        else:
            img_array = image
        
        height, width = img_array.shape[:2]
        
        # Преобразуем в grayscale
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        # Вычисляем градиенты по X и Y
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        
        # Вычисляем магнитуду градиента
        magnitude = np.sqrt(grad_x**2 + grad_y**2)
        magnitude = np.uint8(255 * magnitude / magnitude.max())
        
        # Применяем пороговую обработку
        _, thresh = cv2.threshold(magnitude, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Находим вертикальные линии (анализируем градиент по X)
        vertical_projection = np.sum(np.abs(grad_x), axis=0)
        vertical_lines = self._detect_lines_from_projection(
            vertical_projection, width, min_cell_size, max_cell_size
        )
        
        # Находим горизонтальные линии (анализируем градиент по Y)
        horizontal_projection = np.sum(np.abs(grad_y), axis=1)
        horizontal_lines = self._detect_lines_from_projection(
            horizontal_projection, height, min_cell_size, max_cell_size
        )
        
        # Добавляем граничные линии
        if not vertical_lines or vertical_lines[0] > 0:
            vertical_lines.insert(0, 0)
        if not vertical_lines or vertical_lines[-1] < width - 1:
            vertical_lines.append(width - 1)
        
        if not horizontal_lines or horizontal_lines[0] > 0:
            horizontal_lines.insert(0, 0)
        if not horizontal_lines or horizontal_lines[-1] < height - 1:
            horizontal_lines.append(height - 1)
        
        vertical_lines = sorted(list(set(vertical_lines)))
        horizontal_lines = sorted(list(set(horizontal_lines)))
        
        self.vertical_lines = vertical_lines
        self.horizontal_lines = horizontal_lines
        
        return vertical_lines, horizontal_lines
    
    def _detect_lines_from_projection(self, projection, size, min_cell_size, max_cell_size):
        """Вспомогательный метод для детектирования линий из проекции"""
        from scipy.ndimage import gaussian_filter1d
        smoothed = gaussian_filter1d(projection.astype(float), sigma=2)
        
        threshold = np.percentile(smoothed, 70)
        peaks, _ = find_peaks(smoothed, height=threshold, distance=min_cell_size)
        
        filtered_peaks = []
        for peak in peaks:
            if len(filtered_peaks) == 0:
                filtered_peaks.append(peak)
            elif peak - filtered_peaks[-1] >= min_cell_size:
                filtered_peaks.append(peak)
        
        if len(filtered_peaks) < 3:
            avg_cell_size = (min_cell_size + max_cell_size) // 2
            filtered_peaks = list(range(0, size, avg_cell_size))
            if filtered_peaks[-1] < size - 1:
                filtered_peaks.append(size - 1)
        
        return filtered_peaks
