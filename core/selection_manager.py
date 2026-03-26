"""Менеджер работы с выделенными областями"""
import numpy as np
from PIL import Image, ImageDraw
from tkinter import messagebox


class SelectionManager:
    """Управляет операциями с выделенными областями: заливка, очистка, удаление одиночных пикселей."""
    
    def __init__(self, editor):
        """
        Args:
            editor: Экземпляр GridEditor
        """
        self.editor = editor
    
    def fill_selected_area(self):
        """Заливает выделенную область автоматически"""
        # Убираем фокус с полей ввода
        self.editor.canvas.focus_set()
        
        if self.editor.selection_start is None or self.editor.selection_end is None:
            messagebox.showwarning("Предупреждение", "Сначала выделите область!")
            return
        
        # Получаем палитру Гаммы
        from color.gamma_palette import get_gamma_palette
        gamma_palette = get_gamma_palette()
        all_gamma_colors = gamma_palette.get_all_colors()
        
        if not all_gamma_colors:
            messagebox.showwarning("Предупреждение", "Не удалось загрузить палитру Гаммы!")
            return
        
        # Преобразуем палитру Гаммы в numpy массив RGB
        gamma_palette_rgb = np.array([color_info['rgb'] for color_info in all_gamma_colors], dtype=np.uint8)
        
        if self.editor.image is None:
            messagebox.showwarning("Предупреждение", "Нет изображения!")
            return
        
        # Сохраняем состояние перед заливкой
        self.editor.save_state()
        
        # Получаем границы выделенной области
        min_col, min_row = self.editor.selection_start
        max_col, max_row = self.editor.selection_end
        
        # Получаем массив изображения
        img_array = np.array(self.editor.image)
        if img_array.shape[2] == 4:
            rgb_array = img_array[:, :, :3]
        else:
            rgb_array = img_array
        
        # Создаем копию изображения для рисования
        img_copy = self.editor.image.copy()
        draw = ImageDraw.Draw(img_copy)
        
        # Преобразуем палитру Гаммы в float32 для вычислений
        palette_colors = gamma_palette_rgb.astype(np.float32)
        
        # Заливаем только выделенную область
        for row in range(min_row, max_row + 1):
            if row >= len(self.editor.horizontal_lines) - 1:
                break
            y1 = self.editor.horizontal_lines[row]
            y2 = self.editor.horizontal_lines[row + 1]
            
            for col in range(min_col, max_col + 1):
                if col >= len(self.editor.vertical_lines) - 1:
                    break
                x1 = self.editor.vertical_lines[col]
                x2 = self.editor.vertical_lines[col + 1]
                
                # Извлекаем блок
                block = rgb_array[y1:y2, x1:x2]
                if block.size == 0:
                    continue
                
                block_flat = block.reshape(-1, 3)
                
                # Улучшенный алгоритм: вычисляем средний цвет ячейки (убираем тени через медиану)
                median_color = np.median(block_flat, axis=0).astype(np.uint8)
                
                # Адаптивный порог на основе дисперсии цветов в блоке
                color_std = np.std(block_flat, axis=0)
                avg_std = np.mean(color_std)
                
                # Адаптивный порог в зависимости от однородности блока
                if avg_std < 20:
                    percentile = 60  # Более строгий отбор для однородных блоков
                elif avg_std > 50:
                    percentile = 80  # Более мягкий отбор для разнообразных блоков
                else:
                    percentile = 70  # Стандартный порог
                
                # Находим цвета, близкие к медиане (убираем тени)
                distances_to_median = np.sqrt(np.sum((block_flat - median_color) ** 2, axis=1))
                threshold = np.percentile(distances_to_median, percentile)
                similar_colors = block_flat[distances_to_median < threshold]
                
                if len(similar_colors) > 0:
                    # Используем медиану похожих цветов как репрезентативный цвет ячейки
                    cell_color = np.median(similar_colors, axis=0).astype(np.float32)
                else:
                    cell_color = median_color.astype(np.float32)
                
                # Находим ближайший цвет в палитре Гаммы
                distances = np.sqrt(np.sum((palette_colors - cell_color) ** 2, axis=1))
                closest_idx = np.argmin(distances)
                
                # Используем точный цвет из палитры Гаммы без преобразований
                # Берем RGB напрямую из color_info для точности
                closest_color_info = all_gamma_colors[closest_idx]
                color_tuple = tuple(closest_color_info['rgb'])
                # Не закрашиваем почти белый цвет (почти белый - это цвет подложки)
                # Теперь белый (255, 255, 255) можно закрашивать
                if color_tuple[:3] != (254, 254, 254):
                    draw.rectangle([x1, y1, x2-1, y2-1], fill=color_tuple, outline=None)
                    
                    # Сохраняем информацию о закрашенной ячейке
                    self.editor.painted_cells[(col, row)] = color_tuple
        
        # Обновляем изображение
        self.editor.image = img_copy
        
        # Автоматически переключаемся на режим 2 при заливке
        if self.editor.view_mode == 1:
            self.editor.set_view_mode(2)
        else:
            self.editor.update_display()
        
        # Обновляем палитру для отображения новых счетчиков
        if self.editor.palette is not None:
            self.editor.display_palette()
        
        self.editor.info_label.config(text=f"Область [{min_col}, {min_row}] - [{max_col}, {max_row}] залита")
    
    def clear_selected_area(self):
        """Очищает выделенную область (восстанавливает оригинальное изображение)"""
        # Убираем фокус с полей ввода
        self.editor.canvas.focus_set()
        
        if self.editor.selection_start is None or self.editor.selection_end is None:
            messagebox.showwarning("Предупреждение", "Сначала выделите область!")
            return
        
        if self.editor.image is None or self.editor.original_image is None:
            messagebox.showwarning("Предупреждение", "Нет изображения!")
            return
        
        # Сохраняем состояние перед очисткой
        self.editor.save_state()
        
        # Получаем границы выделенной области
        min_col, min_row = self.editor.selection_start
        max_col, max_row = self.editor.selection_end
        
        # Создаем копию изображения для редактирования
        img_copy = self.editor.image.copy()
        
        # Восстанавливаем оригинальное изображение в выделенной области
        for row in range(min_row, max_row + 1):
            if row >= len(self.editor.horizontal_lines) - 1:
                break
            y1 = self.editor.horizontal_lines[row]
            y2 = self.editor.horizontal_lines[row + 1]
            
            for col in range(min_col, max_col + 1):
                if col >= len(self.editor.vertical_lines) - 1:
                    break
                x1 = self.editor.vertical_lines[col]
                x2 = self.editor.vertical_lines[col + 1]
                
                # Копируем оригинальное изображение в эту область
                original_region = self.editor.original_image.crop((x1, y1, x2, y2))
                img_copy.paste(original_region, (x1, y1))
                
                # Удаляем ячейку из закрашенных, если она там была
                if (col, row) in self.editor.painted_cells:
                    del self.editor.painted_cells[(col, row)]
        
        # Обновляем изображение
        self.editor.image = img_copy
        
        # Обновляем отображение
        self.editor.update_display()
        
        # Обновляем палитру для отображения новых счетчиков
        if self.editor.palette is not None:
            self.editor.display_palette()
        
        self.editor.info_label.config(text=f"Область [{min_col}, {min_row}] - [{max_col}, {max_row}] очищена")
    
    def is_single_pixel(self, col, row, color):
        """Проверяет, является ли пиксель одиночным (не имеет соседей того же цвета)"""
        # Проверяем 8 соседей
        neighbors = [
            (col - 1, row - 1), (col, row - 1), (col + 1, row - 1),
            (col - 1, row),                     (col + 1, row),
            (col - 1, row + 1), (col, row + 1), (col + 1, row + 1)
        ]
        
        for neighbor_col, neighbor_row in neighbors:
            if (neighbor_col, neighbor_row) in self.editor.painted_cells:
                neighbor_color = self.editor.painted_cells[(neighbor_col, neighbor_row)]
                # Сравниваем цвета (RGB кортежи)
                if neighbor_color == color:
                    return False  # Найден сосед с тем же цветом
        return True  # Нет соседей с тем же цветом - одиночный пиксель
    
    def get_neighbor_color(self, col, row):
        """Получает цвет соседних ячеек для заполнения удаляемого пикселя из палитры"""
        # Проверяем наличие палитры
        if self.editor.palette is None or len(self.editor.palette) == 0:
            # Если палитры нет, возвращаем белый цвет
            return (255, 255, 255)
        
        # Проверяем 8 соседей
        neighbors = [
            (col - 1, row - 1), (col, row - 1), (col + 1, row - 1),
            (col - 1, row),                     (col + 1, row),
            (col - 1, row + 1), (col, row + 1), (col + 1, row + 1)
        ]
        
        neighbor_colors = []
        for neighbor_col, neighbor_row in neighbors:
            # Проверяем, что сосед в пределах сетки
            if (neighbor_row >= 0 and neighbor_row < len(self.editor.horizontal_lines) - 1 and
                neighbor_col >= 0 and neighbor_col < len(self.editor.vertical_lines) - 1):
                # Сначала проверяем закрашенные ячейки
                if (neighbor_col, neighbor_row) in self.editor.painted_cells:
                    neighbor_color = self.editor.painted_cells[(neighbor_col, neighbor_row)]
                    # Нормализуем цвет в tuple
                    if isinstance(neighbor_color, np.ndarray):
                        neighbor_colors.append(tuple(neighbor_color[:3]))
                    elif isinstance(neighbor_color, (list, tuple)):
                        neighbor_colors.append(tuple(neighbor_color[:3]))
                    else:
                        neighbor_colors.append(tuple(neighbor_color[:3]))
                else:
                    # Если ячейка не закрашена, берем цвет из текущего изображения
                    if self.editor.image is not None:
                        n_x1 = self.editor.vertical_lines[neighbor_col]
                        n_x2 = self.editor.vertical_lines[neighbor_col + 1]
                        n_y1 = self.editor.horizontal_lines[neighbor_row]
                        n_y2 = self.editor.horizontal_lines[neighbor_row + 1]
                        
                        # Получаем средний цвет ячейки из текущего изображения
                        img_array = np.array(self.editor.image)
                        cell_region = img_array[n_y1:n_y2, n_x1:n_x2]
                        if cell_region.size > 0:
                            # Берем медиану цветов в ячейке
                            if len(cell_region.shape) == 3:
                                median_color = np.median(cell_region.reshape(-1, cell_region.shape[2]), axis=0)
                                neighbor_colors.append(tuple(median_color[:3].astype(int)))
        
        # Определяем цвет для поиска в палитре
        if neighbor_colors:
            # Используем медиану цветов соседей для более стабильного результата
            neighbor_colors_array = np.array(neighbor_colors)
            median_color = np.median(neighbor_colors_array, axis=0).astype(np.float32)
        else:
            # Если соседей нет, берем цвет из текущего изображения в этой ячейке
            if self.editor.image is not None:
                x1 = self.editor.vertical_lines[col]
                x2 = self.editor.vertical_lines[col + 1]
                y1 = self.editor.horizontal_lines[row]
                y2 = self.editor.horizontal_lines[row + 1]
                
                img_array = np.array(self.editor.image)
                cell_region = img_array[y1:y2, x1:x2]
                if cell_region.size > 0:
                    if len(cell_region.shape) == 3:
                        median_color = np.median(cell_region.reshape(-1, cell_region.shape[2]), axis=0).astype(np.float32)
                    else:
                        # Если ничего не найдено, возвращаем первый цвет из палитры
                        return tuple(self.editor.palette[0][:3])
                else:
                    # Если ничего не найдено, возвращаем первый цвет из палитры
                    return tuple(self.editor.palette[0][:3])
            else:
                # Если изображения нет, возвращаем первый цвет из палитры
                return tuple(self.editor.palette[0][:3])
        
        # Находим ближайший цвет в палитре
        palette_colors = self.editor.palette.astype(np.float32)
        
        # Вычисляем расстояния от медианного цвета до каждого цвета палитры
        distances = np.sqrt(np.sum((median_color - palette_colors) ** 2, axis=1))
        closest_idx = np.argmin(distances)
        
        # Возвращаем ближайший цвет из палитры
        closest_color = self.editor.palette[closest_idx]
        if isinstance(closest_color, np.ndarray):
            return tuple(closest_color[:3])
        elif isinstance(closest_color, (list, tuple)):
            return tuple(closest_color[:3])
        else:
            return tuple(closest_color[:3])
    
    def remove_single_pixels_all(self):
        """Удаляет одиночные пиксели со всего изображения"""
        # Убираем фокус с полей ввода
        self.editor.canvas.focus_set()
        
        if self.editor.image is None or self.editor.original_image is None:
            messagebox.showwarning("Предупреждение", "Нет изображения!")
            return
        
        if not self.editor.painted_cells:
            messagebox.showinfo("Информация", "Нет закрашенных ячеек для проверки")
            return
        
        if self.editor.palette is None or len(self.editor.palette) == 0:
            messagebox.showwarning("Предупреждение", "Сначала создайте палитру!\nНажмите 'Получить палитру' или 'Фрагментировать изображение'")
            return
        
        # Находим все одиночные пиксели
        single_pixels = []
        for (col, row), color in self.editor.painted_cells.items():
            if self.is_single_pixel(col, row, color):
                single_pixels.append((col, row))
        
        if not single_pixels:
            messagebox.showinfo("Информация", "Одиночные пиксели не найдены")
            return
        
        # Сохраняем состояние перед удалением (только если есть что удалять)
        self.editor.save_state()
        
        # Создаем копию изображения для редактирования
        img_copy = self.editor.image.copy()
        img_array = np.array(img_copy)
        
        # Удаляем одиночные пиксели
        for col, row in single_pixels:
            if row >= len(self.editor.horizontal_lines) - 1 or col >= len(self.editor.vertical_lines) - 1:
                continue
            
            x1 = self.editor.vertical_lines[col]
            x2 = self.editor.vertical_lines[col + 1]
            y1 = self.editor.horizontal_lines[row]
            y2 = self.editor.horizontal_lines[row + 1]
            
            # Получаем цвет соседних ячеек из палитры
            neighbor_color = self.get_neighbor_color(col, row)
            
            # Преобразуем цвет в numpy array для правильного применения
            if isinstance(neighbor_color, tuple):
                fill_color = np.array(neighbor_color, dtype=np.uint8)
            else:
                fill_color = np.array(neighbor_color, dtype=np.uint8)
            
            # Заполняем ячейку цветом из палитры
            if len(img_array.shape) == 3:
                if img_array.shape[2] == 4:
                    # Если есть альфа-канал, обновляем только RGB
                    img_array[y1:y2, x1:x2, 0] = fill_color[0]
                    img_array[y1:y2, x1:x2, 1] = fill_color[1]
                    img_array[y1:y2, x1:x2, 2] = fill_color[2]
                else:
                    # Для RGB изображения
                    img_array[y1:y2, x1:x2] = fill_color
            
            # Добавляем ячейку обратно в закрашенные с новым цветом
            self.editor.painted_cells[(col, row)] = tuple(fill_color[:3])
        
        # Обновляем изображение
        self.editor.image = Image.fromarray(img_array.astype(np.uint8))
        
        # Обновляем отображение
        self.editor.update_display()
        
        # Обновляем палитру для отображения новых счетчиков
        if self.editor.palette is not None:
            self.editor.display_palette()
        
        self.editor.info_label.config(text=f"Удалено одиночных пикселей: {len(single_pixels)}")
    
    def select_single_pixels_all(self):
        """Выделяет одиночные пиксели со всего изображения"""
        # Убираем фокус с полей ввода
        self.editor.canvas.focus_set()
        
        if self.editor.image is None or self.editor.original_image is None:
            messagebox.showwarning("Предупреждение", "Нет изображения!")
            return
        
        if not self.editor.painted_cells:
            messagebox.showinfo("Информация", "Нет закрашенных ячеек для проверки")
            return
        
        # Находим все одиночные пиксели
        single_pixels_set = set()
        for (col, row), color in self.editor.painted_cells.items():
            if self.is_single_pixel(col, row, color):
                single_pixels_set.add((col, row))
        
        if not single_pixels_set:
            messagebox.showinfo("Информация", "Одиночные пиксели не найдены")
            return
        
        # Используем функцию поиска связанных областей для группировки одиночных пикселей
        # (хотя одиночные пиксели по определению не связаны, это создаст отдельные области для каждого)
        from color.palette_ui import PaletteUI
        regions = PaletteUI._find_connected_regions(single_pixels_set)
        
        # Устанавливаем выделенные области
        self.editor.selected_regions = regions
        
        # Обновляем отображение
        self.editor.update_display()
        
        total_cells = sum(len(region) for region in regions)
        self.editor.info_label.config(text=f"Выделено одиночных пикселей: {total_cells} (в {len(regions)} областях)")
        
        messagebox.showinfo(
            "Информация",
            f"Найдено {len(regions)} областей с одиночными пикселями\nВсего ячеек: {total_cells}",
        )
    
    def remove_single_pixels_selection(self):
        """Удаляет одиночные пиксели из выделенной области"""
        # Убираем фокус с полей ввода
        self.editor.canvas.focus_set()
        
        if self.editor.selection_start is None or self.editor.selection_end is None:
            messagebox.showwarning("Предупреждение", "Сначала выделите область!")
            return
        
        if self.editor.image is None or self.editor.original_image is None:
            messagebox.showwarning("Предупреждение", "Нет изображения!")
            return
        
        if not self.editor.painted_cells:
            messagebox.showinfo("Информация", "Нет закрашенных ячеек для проверки")
            return
        
        if self.editor.palette is None or len(self.editor.palette) == 0:
            messagebox.showwarning("Предупреждение", "Сначала создайте палитру!\nНажмите 'Получить палитру' или 'Фрагментировать изображение'")
            return
        
        # Получаем границы выделенной области
        min_col, min_row = self.editor.selection_start
        max_col, max_row = self.editor.selection_end
        
        # Находим одиночные пиксели в выделенной области
        single_pixels = []
        for (col, row), color in self.editor.painted_cells.items():
            # Проверяем, что ячейка находится в выделенной области
            if min_col <= col <= max_col and min_row <= row <= max_row:
                if self.is_single_pixel(col, row, color):
                    single_pixels.append((col, row))
        
        if not single_pixels:
            messagebox.showinfo("Информация", "Одиночные пиксели в выделенной области не найдены")
            return
        
        # Сохраняем состояние перед удалением (только если есть что удалять)
        self.editor.save_state()
        
        # Создаем копию изображения для редактирования
        img_copy = self.editor.image.copy()
        img_array = np.array(img_copy)
        
        # Удаляем одиночные пиксели
        for col, row in single_pixels:
            if row >= len(self.editor.horizontal_lines) - 1 or col >= len(self.editor.vertical_lines) - 1:
                continue
            
            x1 = self.editor.vertical_lines[col]
            x2 = self.editor.vertical_lines[col + 1]
            y1 = self.editor.horizontal_lines[row]
            y2 = self.editor.horizontal_lines[row + 1]
            
            # Получаем цвет соседних ячеек из палитры
            neighbor_color = self.get_neighbor_color(col, row)
            
            # Преобразуем цвет в numpy array для правильного применения
            if isinstance(neighbor_color, tuple):
                fill_color = np.array(neighbor_color, dtype=np.uint8)
            else:
                fill_color = np.array(neighbor_color, dtype=np.uint8)
            
            # Заполняем ячейку цветом из палитры
            if len(img_array.shape) == 3:
                if img_array.shape[2] == 4:
                    # Если есть альфа-канал, обновляем только RGB
                    img_array[y1:y2, x1:x2, 0] = fill_color[0]
                    img_array[y1:y2, x1:x2, 1] = fill_color[1]
                    img_array[y1:y2, x1:x2, 2] = fill_color[2]
                else:
                    # Для RGB изображения
                    img_array[y1:y2, x1:x2] = fill_color
            
            # Добавляем ячейку обратно в закрашенные с новым цветом
            self.editor.painted_cells[(col, row)] = tuple(fill_color[:3])
        
        # Обновляем изображение
        self.editor.image = Image.fromarray(img_array.astype(np.uint8))
        
        # Обновляем отображение
        self.editor.update_display()
        
        # Обновляем палитру для отображения новых счетчиков
        if self.editor.palette is not None:
            self.editor.display_palette()
        
        self.editor.info_label.config(text=f"Удалено одиночных пикселей из области [{min_col}, {min_row}] - [{max_col}, {max_row}]: {len(single_pixels)}")
    
    def mirror_selection_2x_horizontal(self):
        """Зеркалирует выделенную область по горизонтали (влево и вправо)"""
        # Убираем фокус с полей ввода
        self.editor.canvas.focus_set()
        
        if self.editor.selection_start is None or self.editor.selection_end is None:
            messagebox.showwarning("Предупреждение", "Сначала выделите область!")
            return
        
        if self.editor.image is None:
            messagebox.showwarning("Предупреждение", "Нет изображения!")
            return
        
        # Сохраняем состояние перед зеркалированием
        self.editor.save_state()
        
        # Получаем границы выделенной области
        min_col, min_row = self.editor.selection_start
        max_col, max_row = self.editor.selection_end
        
        # Вычисляем центр области
        center_col = (min_col + max_col) / 2.0
        
        # Создаем копию изображения для редактирования
        img_copy = self.editor.image.copy()
        draw = ImageDraw.Draw(img_copy)
        
        # Собираем все закрашенные ячейки из выделенной области
        source_cells = {}
        for (col, row), color in self.editor.painted_cells.items():
            if min_col <= col <= max_col and min_row <= row <= max_row:
                source_cells[(col, row)] = color
        
        if not source_cells:
            messagebox.showinfo("Информация", "В выделенной области нет закрашенных ячеек")
            return
        
        # Зеркалируем ячейки по горизонтали
        mirrored_count = 0
        for (col, row), color in source_cells.items():
            # Вычисляем зеркальную позицию относительно центра
            mirrored_col = int(2 * center_col - col)
            
            # Проверяем, что зеркальная позиция в пределах сетки
            if (0 <= mirrored_col < len(self.editor.vertical_lines) - 1 and
                0 <= row < len(self.editor.horizontal_lines) - 1):
                
                # Получаем координаты ячейки
                x1 = self.editor.vertical_lines[mirrored_col]
                x2 = self.editor.vertical_lines[mirrored_col + 1]
                y1 = self.editor.horizontal_lines[row]
                y2 = self.editor.horizontal_lines[row + 1]
                
                # Закрашиваем зеркальную ячейку
                if isinstance(color, (list, tuple, np.ndarray)):
                    color_tuple = tuple(color[:3]) if len(color) >= 3 else tuple(color)
                else:
                    color_tuple = tuple(color[:3]) if hasattr(color, '__getitem__') else (255, 255, 255)
                
                if color_tuple[:3] != (255, 255, 255):
                    draw.rectangle([x1, y1, x2-1, y2-1], fill=color_tuple, outline=None)
                    self.editor.painted_cells[(mirrored_col, row)] = color_tuple
                    mirrored_count += 1
        
        # Обновляем изображение
        self.editor.image = img_copy
        
        # Обновляем отображение
        if self.editor.view_mode == 1:
            self.editor.set_view_mode(2)
        else:
            self.editor.update_display()
        
        # Обновляем палитру
        if self.editor.palette is not None:
            self.editor.display_palette()
        
        self.editor.info_label.config(text=f"Зеркалировано по горизонтали: {mirrored_count} ячеек")
    
    def mirror_selection_2x_vertical(self):
        """Зеркалирует выделенную область по вертикали (вверх и вниз)"""
        # Убираем фокус с полей ввода
        self.editor.canvas.focus_set()
        
        if self.editor.selection_start is None or self.editor.selection_end is None:
            messagebox.showwarning("Предупреждение", "Сначала выделите область!")
            return
        
        if self.editor.image is None:
            messagebox.showwarning("Предупреждение", "Нет изображения!")
            return
        
        # Сохраняем состояние перед зеркалированием
        self.editor.save_state()
        
        # Получаем границы выделенной области
        min_col, min_row = self.editor.selection_start
        max_col, max_row = self.editor.selection_end
        
        # Вычисляем центр области
        center_row = (min_row + max_row) / 2.0
        
        # Создаем копию изображения для редактирования
        img_copy = self.editor.image.copy()
        draw = ImageDraw.Draw(img_copy)
        
        # Собираем все закрашенные ячейки из выделенной области
        source_cells = {}
        for (col, row), color in self.editor.painted_cells.items():
            if min_col <= col <= max_col and min_row <= row <= max_row:
                source_cells[(col, row)] = color
        
        if not source_cells:
            messagebox.showinfo("Информация", "В выделенной области нет закрашенных ячеек")
            return
        
        # Зеркалируем ячейки по вертикали
        mirrored_count = 0
        for (col, row), color in source_cells.items():
            # Вычисляем зеркальную позицию относительно центра
            mirrored_row = int(2 * center_row - row)
            
            # Проверяем, что зеркальная позиция в пределах сетки
            if (0 <= col < len(self.editor.vertical_lines) - 1 and
                0 <= mirrored_row < len(self.editor.horizontal_lines) - 1):
                
                # Получаем координаты ячейки
                x1 = self.editor.vertical_lines[col]
                x2 = self.editor.vertical_lines[col + 1]
                y1 = self.editor.horizontal_lines[mirrored_row]
                y2 = self.editor.horizontal_lines[mirrored_row + 1]
                
                # Закрашиваем зеркальную ячейку
                if isinstance(color, (list, tuple, np.ndarray)):
                    color_tuple = tuple(color[:3]) if len(color) >= 3 else tuple(color)
                else:
                    color_tuple = tuple(color[:3]) if hasattr(color, '__getitem__') else (255, 255, 255)
                
                if color_tuple[:3] != (255, 255, 255):
                    draw.rectangle([x1, y1, x2-1, y2-1], fill=color_tuple, outline=None)
                    self.editor.painted_cells[(col, mirrored_row)] = color_tuple
                    mirrored_count += 1
        
        # Обновляем изображение
        self.editor.image = img_copy
        
        # Обновляем отображение
        if self.editor.view_mode == 1:
            self.editor.set_view_mode(2)
        else:
            self.editor.update_display()
        
        # Обновляем палитру
        if self.editor.palette is not None:
            self.editor.display_palette()
        
        self.editor.info_label.config(text=f"Зеркалировано по вертикали: {mirrored_count} ячеек")
    
    def mirror_selection_4x(self):
        """Зеркалирует выделенную область в 4 стороны (4-х симметрия)"""
        # Убираем фокус с полей ввода
        self.editor.canvas.focus_set()
        
        if self.editor.selection_start is None or self.editor.selection_end is None:
            messagebox.showwarning("Предупреждение", "Сначала выделите область!")
            return
        
        if self.editor.image is None:
            messagebox.showwarning("Предупреждение", "Нет изображения!")
            return
        
        # Сохраняем состояние перед зеркалированием
        self.editor.save_state()
        
        # Получаем границы выделенной области
        min_col, min_row = self.editor.selection_start
        max_col, max_row = self.editor.selection_end
        
        # Вычисляем центр области
        center_col = (min_col + max_col) / 2.0
        center_row = (min_row + max_row) / 2.0
        
        # Создаем копию изображения для редактирования
        img_copy = self.editor.image.copy()
        draw = ImageDraw.Draw(img_copy)
        
        # Собираем все закрашенные ячейки из выделенной области
        source_cells = {}
        for (col, row), color in self.editor.painted_cells.items():
            if min_col <= col <= max_col and min_row <= row <= max_row:
                source_cells[(col, row)] = color
        
        if not source_cells:
            messagebox.showinfo("Информация", "В выделенной области нет закрашенных ячеек")
            return
        
        # Зеркалируем ячейки в 4 стороны
        mirrored_count = 0
        for (col, row), color in source_cells.items():
            # Вычисляем зеркальные позиции
            mirrored_col_h = int(2 * center_col - col)  # По горизонтали
            mirrored_row_v = int(2 * center_row - row)   # По вертикали
            mirrored_col_hv = int(2 * center_col - col)  # По горизонтали и вертикали одновременно
            mirrored_row_hv = int(2 * center_row - row)
            
            # Нормализуем цвет
            if isinstance(color, (list, tuple, np.ndarray)):
                color_tuple = tuple(color[:3]) if len(color) >= 3 else tuple(color)
            else:
                color_tuple = tuple(color[:3]) if hasattr(color, '__getitem__') else (255, 255, 255)
            
            if color_tuple[:3] == (255, 255, 255):
                continue
            
            # Зеркалирование по горизонтали (вправо)
            if (0 <= mirrored_col_h < len(self.editor.vertical_lines) - 1 and
                0 <= row < len(self.editor.horizontal_lines) - 1):
                x1 = self.editor.vertical_lines[mirrored_col_h]
                x2 = self.editor.vertical_lines[mirrored_col_h + 1]
                y1 = self.editor.horizontal_lines[row]
                y2 = self.editor.horizontal_lines[row + 1]
                draw.rectangle([x1, y1, x2-1, y2-1], fill=color_tuple, outline=None)
                self.editor.painted_cells[(mirrored_col_h, row)] = color_tuple
                mirrored_count += 1
            
            # Зеркалирование по вертикали (вниз)
            if (0 <= col < len(self.editor.vertical_lines) - 1 and
                0 <= mirrored_row_v < len(self.editor.horizontal_lines) - 1):
                x1 = self.editor.vertical_lines[col]
                x2 = self.editor.vertical_lines[col + 1]
                y1 = self.editor.horizontal_lines[mirrored_row_v]
                y2 = self.editor.horizontal_lines[mirrored_row_v + 1]
                draw.rectangle([x1, y1, x2-1, y2-1], fill=color_tuple, outline=None)
                self.editor.painted_cells[(col, mirrored_row_v)] = color_tuple
                mirrored_count += 1
            
            # Зеркалирование по горизонтали и вертикали одновременно (диагональ)
            if (0 <= mirrored_col_hv < len(self.editor.vertical_lines) - 1 and
                0 <= mirrored_row_hv < len(self.editor.horizontal_lines) - 1):
                x1 = self.editor.vertical_lines[mirrored_col_hv]
                x2 = self.editor.vertical_lines[mirrored_col_hv + 1]
                y1 = self.editor.horizontal_lines[mirrored_row_hv]
                y2 = self.editor.horizontal_lines[mirrored_row_hv + 1]
                draw.rectangle([x1, y1, x2-1, y2-1], fill=color_tuple, outline=None)
                self.editor.painted_cells[(mirrored_col_hv, mirrored_row_hv)] = color_tuple
                mirrored_count += 1
        
        # Обновляем изображение
        self.editor.image = img_copy
        
        # Обновляем отображение
        if self.editor.view_mode == 1:
            self.editor.set_view_mode(2)
        else:
            self.editor.update_display()
        
        # Обновляем палитру
        if self.editor.palette is not None:
            self.editor.display_palette()
        
        self.editor.info_label.config(text=f"Зеркалировано в 4 стороны: {mirrored_count} ячеек")

