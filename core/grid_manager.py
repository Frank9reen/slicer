"""Управление сеткой (линии, ячейки, операции)"""


class GridManager:
    """Класс для управления сеткой"""
    
    def __init__(self):
        self.vertical_lines = []
        self.horizontal_lines = []
        self.selected_line = None
        self.selected_line_type = None  # 'v' для вертикальных, 'h' для горизонтальных
    
    def build_grid(self, image_width, image_height, num_vertical, num_horizontal, 
                   step_vertical, step_horizontal):
        """
        Строит сетку на изображении.
        
        Args:
            image_width: Ширина изображения
            image_height: Высота изображения
            num_vertical: Количество вертикальных линий
            num_horizontal: Количество горизонтальных линий
            step_vertical: Шаг вертикальных линий
            step_horizontal: Шаг горизонтальных линий
        
        Returns:
            tuple: (vertical_lines, horizontal_lines)
        
        Примечание:
            Сетка привязана к левому верхнему углу изображения: первая вертикальная линия — x=0,
            первая горизонтальная — y=0. Так нет «мёртвой» полосы слева/сверху вне ячеек
            (корректная работа резинки и согласованность с экспортом в PDF).
        """
        vertical_lines = []
        horizontal_lines = []
        
        # Строим вертикальные линии от левого края (не по центру кадра)
        start_x = 0
        for i in range(num_vertical):
            x = start_x + i * step_vertical
            if 0 <= x < image_width:
                vertical_lines.append(x)
        
        # Строим горизонтальные линии от верхнего края
        start_y = 0
        for i in range(num_horizontal):
            y = start_y + i * step_horizontal
            if 0 <= y < image_height:
                horizontal_lines.append(y)
        
        self.vertical_lines = vertical_lines
        self.horizontal_lines = horizontal_lines
        self.selected_line = None
        
        return vertical_lines, horizontal_lines
    
    def shift_grid_left(self, image_width, shift_step):
        """
        Сдвигает всю сетку влево.
        
        Args:
            image_width: Ширина изображения
            shift_step: Шаг сдвига
        
        Returns:
            bool: True если сдвиг выполнен, False если невозможно
        """
        if not self.vertical_lines:
            return False
        
        new_lines = []
        for x in self.vertical_lines:
            new_x = x - shift_step
            if new_x >= 0:
                new_lines.append(new_x)
        
        if len(new_lines) == len(self.vertical_lines):
            self.vertical_lines = new_lines
            return True
        return False
    
    def shift_grid_right(self, image_width, shift_step):
        """
        Сдвигает всю сетку вправо.
        
        Args:
            image_width: Ширина изображения
            shift_step: Шаг сдвига
        
        Returns:
            bool: True если сдвиг выполнен, False если невозможно
        """
        if not self.vertical_lines:
            return False
        
        new_lines = []
        for x in self.vertical_lines:
            new_x = x + shift_step
            if new_x < image_width:
                new_lines.append(new_x)
        
        if len(new_lines) == len(self.vertical_lines):
            self.vertical_lines = new_lines
            return True
        return False
    
    def shift_grid_up(self, image_height, shift_step):
        """
        Сдвигает всю сетку вверх.
        
        Args:
            image_height: Высота изображения
            shift_step: Шаг сдвига
        
        Returns:
            bool: True если сдвиг выполнен, False если невозможно
        """
        if not self.horizontal_lines:
            return False
        
        new_lines = []
        for y in self.horizontal_lines:
            new_y = y - shift_step
            if new_y >= 0:
                new_lines.append(new_y)
        
        if len(new_lines) == len(self.horizontal_lines):
            self.horizontal_lines = new_lines
            return True
        return False
    
    def shift_grid_down(self, image_height, shift_step):
        """
        Сдвигает всю сетку вниз.
        
        Args:
            image_height: Высота изображения
            shift_step: Шаг сдвига
        
        Returns:
            bool: True если сдвиг выполнен, False если невозможно
        """
        if not self.horizontal_lines:
            return False
        
        new_lines = []
        for y in self.horizontal_lines:
            new_y = y + shift_step
            if new_y < image_height:
                new_lines.append(new_y)
        
        if len(new_lines) == len(self.horizontal_lines):
            self.horizontal_lines = new_lines
            return True
        return False
    
    def move_line_left(self, line_index, line_type, min_distance=1):
        """
        Сдвигает линию влево (для вертикальных) или вверх (для горизонтальных).
        
        Args:
            line_index: Индекс линии
            line_type: 'v' для вертикальных, 'h' для горизонтальных
            min_distance: Минимальное расстояние между линиями
        
        Returns:
            tuple: (success, new_position) или (False, None)
        """
        if line_type == 'v':
            if line_index < 0 or line_index >= len(self.vertical_lines):
                return False, None
            if line_index > 0:
                min_x = self.vertical_lines[line_index - 1] + min_distance
                if self.vertical_lines[line_index] > min_x:
                    self.vertical_lines[line_index] -= 1
                    self.vertical_lines.sort()
                    new_pos = self.vertical_lines[line_index]
                    return True, new_pos
        else:  # 'h'
            if line_index < 0 or line_index >= len(self.horizontal_lines):
                return False, None
            if line_index > 0:
                min_y = self.horizontal_lines[line_index - 1] + min_distance
                if self.horizontal_lines[line_index] > min_y:
                    self.horizontal_lines[line_index] -= 1
                    self.horizontal_lines.sort()
                    new_pos = self.horizontal_lines[line_index]
                    return True, new_pos
        return False, None
    
    def move_line_right(self, line_index, line_type, max_pos, min_distance=1):
        """
        Сдвигает линию вправо (для вертикальных) или вниз (для горизонтальных).
        
        Args:
            line_index: Индекс линии
            line_type: 'v' для вертикальных, 'h' для горизонтальных
            max_pos: Максимальная позиция (ширина для вертикальных, высота для горизонтальных)
            min_distance: Минимальное расстояние между линиями
        
        Returns:
            tuple: (success, new_position) или (False, None)
        """
        if line_type == 'v':
            if line_index < 0 or line_index >= len(self.vertical_lines):
                return False, None
            if line_index < len(self.vertical_lines) - 1:
                max_x = self.vertical_lines[line_index + 1] - min_distance
                if self.vertical_lines[line_index] < max_x and self.vertical_lines[line_index] < max_pos - 1:
                    self.vertical_lines[line_index] += 1
                    self.vertical_lines.sort()
                    new_pos = self.vertical_lines[line_index]
                    return True, new_pos
        else:  # 'h'
            if line_index < 0 or line_index >= len(self.horizontal_lines):
                return False, None
            if line_index < len(self.horizontal_lines) - 1:
                max_y = self.horizontal_lines[line_index + 1] - min_distance
                if self.horizontal_lines[line_index] < max_y and self.horizontal_lines[line_index] < max_pos - 1:
                    self.horizontal_lines[line_index] += 1
                    self.horizontal_lines.sort()
                    new_pos = self.horizontal_lines[line_index]
                    return True, new_pos
        return False, None
    
    def move_line_to_position(self, line_index, line_type, new_position, max_pos, min_distance=1):
        """
        Перемещает линию на указанную позицию.
        
        Args:
            line_index: Индекс линии
            line_type: 'v' для вертикальных, 'h' для горизонтальных
            new_position: Новая позиция линии
            max_pos: Максимальная позиция (ширина для вертикальных, высота для горизонтальных)
            min_distance: Минимальное расстояние между линиями
        
        Returns:
            tuple: (success, new_position) или (False, None)
        """
        if line_type == 'v':
            if line_index < 0 or line_index >= len(self.vertical_lines):
                return False, None
            
            # Определяем границы для перемещения
            min_x = 0
            max_x = max_pos - 1
            
            if line_index > 0:
                min_x = self.vertical_lines[line_index - 1] + min_distance
            if line_index < len(self.vertical_lines) - 1:
                max_x = self.vertical_lines[line_index + 1] - min_distance
            
            # Ограничиваем новую позицию границами
            new_pos = max(min_x, min(max_x, new_position))
            
            # Проверяем, что позиция изменилась
            if new_pos == self.vertical_lines[line_index]:
                return False, None
            
            # Обновляем позицию и сортируем
            self.vertical_lines[line_index] = new_pos
            self.vertical_lines.sort()
            
            # Находим новую позицию после сортировки
            new_index = self.vertical_lines.index(new_pos)
            return True, new_pos
        else:  # 'h'
            if line_index < 0 or line_index >= len(self.horizontal_lines):
                return False, None
            
            # Определяем границы для перемещения
            min_y = 0
            max_y = max_pos - 1
            
            if line_index > 0:
                min_y = self.horizontal_lines[line_index - 1] + min_distance
            if line_index < len(self.horizontal_lines) - 1:
                max_y = self.horizontal_lines[line_index + 1] - min_distance
            
            # Ограничиваем новую позицию границами
            new_pos = max(min_y, min(max_y, new_position))
            
            # Проверяем, что позиция изменилась
            if new_pos == self.horizontal_lines[line_index]:
                return False, None
            
            # Обновляем позицию и сортируем
            self.horizontal_lines[line_index] = new_pos
            self.horizontal_lines.sort()
            
            # Находим новую позицию после сортировки
            new_index = self.horizontal_lines.index(new_pos)
            return True, new_pos
    
    def add_line(self, position, line_type):
        """
        Добавляет новую линию в сетку.
        
        Args:
            position: Позиция новой линии
            line_type: 'v' для вертикальных, 'h' для горизонтальных
        
        Returns:
            bool: True если линия добавлена
        """
        if line_type == 'v':
            if position not in self.vertical_lines:
                self.vertical_lines.append(position)
                self.vertical_lines.sort()
                return True
        else:  # 'h'
            if position not in self.horizontal_lines:
                self.horizontal_lines.append(position)
                self.horizontal_lines.sort()
                return True
        return False
    
    def remove_line(self, line_position, line_type, min_lines=2):
        """
        Удаляет линию из сетки.
        
        Args:
            line_position: Позиция линии для удаления
            line_type: 'v' для вертикальных, 'h' для горизонтальных
            min_lines: Минимальное количество линий (не удаляем граничные)
        
        Returns:
            bool: True если линия удалена
        """
        if line_type == 'v':
            if len(self.vertical_lines) > min_lines:
                if line_position in self.vertical_lines:
                    self.vertical_lines.remove(line_position)
                    return True
        else:  # 'h'
            if len(self.horizontal_lines) > min_lines:
                if line_position in self.horizontal_lines:
                    self.horizontal_lines.remove(line_position)
                    return True
        return False
    
    def get_cell_from_position(self, img_x, img_y):
        """
        Определяет ячейку сетки по координатам изображения.
        
        Args:
            img_x: X координата на изображении
            img_y: Y координата на изображении
        
        Returns:
            tuple: (col, row) или (None, None) если не найдено
        """
        col = -1
        row = -1
        
        for i in range(len(self.vertical_lines) - 1):
            if self.vertical_lines[i] <= img_x < self.vertical_lines[i + 1]:
                col = i
                break
        
        for i in range(len(self.horizontal_lines) - 1):
            if self.horizontal_lines[i] <= img_y < self.horizontal_lines[i + 1]:
                row = i
                break
        
        if col >= 0 and row >= 0:
            return (col, row)
        return (None, None)
    
    def get_cell_bounds(self, col, row):
        """
        Получает границы ячейки.
        
        Args:
            col: Номер колонки
            row: Номер строки
        
        Returns:
            tuple: (x1, y1, x2, y2) или None если ячейка не найдена
        """
        if col < 0 or col >= len(self.vertical_lines) - 1:
            return None
        if row < 0 or row >= len(self.horizontal_lines) - 1:
            return None
        
        x1 = self.vertical_lines[col]
        x2 = self.vertical_lines[col + 1]
        y1 = self.horizontal_lines[row]
        y2 = self.horizontal_lines[row + 1]
        
        return (x1, y1, x2, y2)
    
    def get_num_cells(self):
        """
        Возвращает количество ячеек в сетке.
        
        Returns:
            tuple: (num_cols, num_rows)
        """
        num_cols = max(0, len(self.vertical_lines) - 1)
        num_rows = max(0, len(self.horizontal_lines) - 1)
        return (num_cols, num_rows)
    
    def find_line_index(self, line_position, line_type):
        """
        Находит индекс линии по позиции.
        
        Args:
            line_position: Позиция линии
            line_type: 'v' для вертикальных, 'h' для горизонтальных
        
        Returns:
            int or None: Индекс линии или None если не найдена
        """
        if line_type == 'v':
            if line_position in self.vertical_lines:
                return self.vertical_lines.index(line_position)
        else:  # 'h'
            if line_position in self.horizontal_lines:
                return self.horizontal_lines.index(line_position)
        return None
    
    def reset(self):
        """Сбрасывает сетку"""
        self.vertical_lines = []
        self.horizontal_lines = []
        self.selected_line = None
        self.selected_line_type = None

