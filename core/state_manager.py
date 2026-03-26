"""Управление состоянием (undo/redo)"""
from PIL import Image
import numpy as np


class StateManager:
    """Класс для управления историей изменений (undo/redo)"""
    
    def __init__(self, max_history=50):
        """
        Инициализация менеджера состояний.
        
        Args:
            max_history: Максимальное количество состояний в истории
        """
        self.max_history = max_history
        self.undo_history = []
        self.redo_history = []
    
    def save_state(self, image, painted_cells, vertical_lines=None, horizontal_lines=None, palette=None):
        """
        Сохраняет текущее состояние для отмены.
        
        Args:
            image: PIL.Image - текущее изображение
            painted_cells: dict - словарь закрашенных ячеек
            vertical_lines: list - список вертикальных линий (опционально)
            horizontal_lines: list - список горизонтальных линий (опционально)
            palette: np.ndarray - палитра цветов (опционально)
        """
        if image is None:
            return
        
        # Сохраняем копию изображения, словарь закрашенных ячеек, линии сетки и палитру
        state = {
            'image': image.copy(),
            'painted_cells': painted_cells.copy(),
            'vertical_lines': vertical_lines.copy() if vertical_lines else [],
            'horizontal_lines': horizontal_lines.copy() if horizontal_lines else []
        }
        if palette is not None:
            state['palette'] = np.copy(palette)
        self.undo_history.append(state)
        
        # Очищаем историю повтора при новом действии
        self.redo_history = []
        
        # Ограничиваем размер истории
        if len(self.undo_history) > self.max_history:
            self.undo_history.pop(0)
    
    def undo(self, current_image, current_painted_cells, current_vertical_lines=None, 
             current_horizontal_lines=None, current_palette=None):
        """
        Отменяет последнее действие.
        
        Args:
            current_image: PIL.Image - текущее изображение
            current_painted_cells: dict - текущий словарь закрашенных ячеек
            current_vertical_lines: list - текущий список вертикальных линий (опционально)
            current_horizontal_lines: list - текущий список горизонтальных линий (опционально)
            current_palette: np.ndarray - текущая палитра (опционально)
        
        Returns:
            dict or None: Состояние для восстановления или None если нет истории
        """
        if len(self.undo_history) == 0:
            return None
        
        # Сохраняем текущее состояние в историю повтора
        current_state = {
            'image': current_image.copy() if current_image else None,
            'painted_cells': current_painted_cells.copy(),
            'vertical_lines': current_vertical_lines.copy() if current_vertical_lines else [],
            'horizontal_lines': current_horizontal_lines.copy() if current_horizontal_lines else []
        }
        if current_palette is not None:
            current_state['palette'] = np.copy(current_palette)
        self.redo_history.append(current_state)
        
        # Ограничиваем размер истории повтора
        if len(self.redo_history) > self.max_history:
            self.redo_history.pop(0)
        
        # Возвращаем предыдущее состояние
        previous_state = self.undo_history.pop()
        return previous_state
    
    def redo(self, current_image, current_painted_cells, current_vertical_lines=None, 
             current_horizontal_lines=None, current_palette=None):
        """
        Повторяет последнее отмененное действие.
        
        Args:
            current_image: PIL.Image - текущее изображение
            current_painted_cells: dict - текущий словарь закрашенных ячеек
            current_vertical_lines: list - текущий список вертикальных линий (опционально)
            current_horizontal_lines: list - текущий список горизонтальных линий (опционально)
            current_palette: np.ndarray - текущая палитра (опционально)
        
        Returns:
            dict or None: Состояние для восстановления или None если нет истории
        """
        if len(self.redo_history) == 0:
            return None
        
        # Сохраняем текущее состояние в историю отмены
        current_state = {
            'image': current_image.copy() if current_image else None,
            'painted_cells': current_painted_cells.copy(),
            'vertical_lines': current_vertical_lines.copy() if current_vertical_lines else [],
            'horizontal_lines': current_horizontal_lines.copy() if current_horizontal_lines else []
        }
        if current_palette is not None:
            current_state['palette'] = np.copy(current_palette)
        self.undo_history.append(current_state)
        
        # Ограничиваем размер истории отмены
        if len(self.undo_history) > self.max_history:
            self.undo_history.pop(0)
        
        # Возвращаем состояние из истории повтора
        next_state = self.redo_history.pop()
        return next_state
    
    def can_undo(self):
        """Проверяет, можно ли отменить действие"""
        return len(self.undo_history) > 0
    
    def can_redo(self):
        """Проверяет, можно ли повторить действие"""
        return len(self.redo_history) > 0
    
    def clear(self):
        """Очищает всю историю"""
        self.undo_history = []
        self.redo_history = []
    
    def get_history_info(self):
        """
        Возвращает информацию о состоянии истории.
        
        Returns:
            dict: Информация о количестве состояний в истории
        """
        return {
            'undo_count': len(self.undo_history),
            'redo_count': len(self.redo_history),
            'max_history': self.max_history
        }

