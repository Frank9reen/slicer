"""Управление проектами"""
import json
import zipfile
import io
import numpy as np
from PIL import Image


class ProjectManager:
    """Класс для сохранения и загрузки проектов"""
    
    @staticmethod
    def convert_to_json_serializable(obj):
        """
        Конвертирует numpy типы и другие несериализуемые объекты в стандартные Python типы.
        
        Args:
            obj: Объект для конвертации
        
        Returns:
            Сериализуемый объект
        """
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return [ProjectManager.convert_to_json_serializable(item) for item in obj]
        elif isinstance(obj, (list, tuple)):
            return [ProjectManager.convert_to_json_serializable(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: ProjectManager.convert_to_json_serializable(value) for key, value in obj.items()}
        else:
            return obj
    
    @staticmethod
    def save_project(file_path, original_image, fragmented_image, image_path,
                     vertical_lines, horizontal_lines,
                     num_vertical, num_horizontal, step_vertical, step_horizontal, num_colors,
                     view_mode, show_grid, grid_line_width, background_color,
                     painted_cells, palette, selected_color,
                     palette_method_kmeans=False, palette_method_kmeans_improved=False,
                     palette_method_kmeans_weighted=False, palette_method_hierarchical_kmeans=False,
                     palette_method_median_cut=False, palette_method_octree=False,
                     sort_palette_by_gamma_var=True, focus_on_center_var=False,
                     adaptive_method_gradients=False, manual_grid_enabled=False,
                     project_name=None, project_article=None, qr_url=None):
        """
        Сохраняет проект в zip-архив.
        
        Args:
            file_path: Путь для сохранения файла
            original_image: PIL.Image - оригинальное изображение
            fragmented_image: PIL.Image или None - фрагментированное изображение
            image_path: str - путь к исходному изображению
            vertical_lines: list - список вертикальных линий
            horizontal_lines: list - список горизонтальных линий
            num_vertical: int - количество вертикальных линий
            num_horizontal: int - количество горизонтальных линий
            step_vertical: int - шаг вертикальных линий
            step_horizontal: int - шаг горизонтальных линий
            num_colors: int - количество цветов в палитре
            view_mode: int - режим просмотра
            show_grid: bool - показывать ли сетку
            grid_line_width: int - толщина линий сетки
            background_color: str - цвет фона
            painted_cells: dict - словарь закрашенных ячеек {(col, row): color}
            palette: np.ndarray или None - палитра цветов
            selected_color: tuple или None - выбранный цвет
        
        Returns:
            bool: True если успешно, False в случае ошибки
        """
        try:
            # Убеждаемся, что файл имеет расширение .slicer
            if not file_path.lower().endswith('.slicer'):
                file_path += '.slicer'
            
            # Создаем zip-архив
            with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Сохраняем оригинальное изображение
                if original_image:
                    img_buffer = io.BytesIO()
                    original_image.save(img_buffer, format='PNG')
                    zipf.writestr('original_image.png', img_buffer.getvalue())
                
                # Сохраняем фрагментированное изображение, если есть
                if fragmented_image:
                    img_buffer = io.BytesIO()
                    fragmented_image.save(img_buffer, format='PNG')
                    zipf.writestr('fragmented_image.png', img_buffer.getvalue())
                
                # Подготавливаем данные для сохранения
                project_data = {
                    'version': '1.0',
                    'image_path': image_path if image_path else '',
                    'vertical_lines': list(vertical_lines),
                    'horizontal_lines': list(horizontal_lines),
                    'num_vertical': int(num_vertical),
                    'num_horizontal': int(num_horizontal),
                    'step_vertical': int(step_vertical),
                    'step_horizontal': int(step_horizontal),
                    'num_colors': int(num_colors),
                    'view_mode': int(view_mode),
                    'show_grid': bool(show_grid),
                    'grid_line_width': int(grid_line_width),
                    'background_color': str(background_color),
                    'painted_cells': {},
                    # Чекбоксы методов фрагментации
                    'palette_method_kmeans': bool(palette_method_kmeans),
                    'palette_method_kmeans_improved': bool(palette_method_kmeans_improved),
                    'palette_method_kmeans_weighted': bool(palette_method_kmeans_weighted),
                    'palette_method_hierarchical_kmeans': bool(palette_method_hierarchical_kmeans),
                    'palette_method_median_cut': bool(palette_method_median_cut),
                    'palette_method_octree': bool(palette_method_octree),
                    'sort_palette_by_gamma_var': bool(sort_palette_by_gamma_var),
                    'focus_on_center_var': bool(focus_on_center_var),
                    # Чекбоксы методов сетки
                    'adaptive_method_gradients': bool(adaptive_method_gradients),
                    'manual_grid_enabled': bool(manual_grid_enabled),
                    # Дополнительные настройки проекта
                    'project_name': project_name if project_name else '',
                    'project_article': project_article if project_article else '',
                    'qr_url': qr_url if qr_url else ''
                }
                
                # Сохраняем закрашенные ячейки (конвертируем цвета в списки)
                for (col, row), color in painted_cells.items():
                    key = f"{int(col)},{int(row)}"
                    if isinstance(color, (list, tuple, np.ndarray)):
                        project_data['painted_cells'][key] = [
                            int(c) if isinstance(c, (np.integer, int)) 
                            else float(c) if isinstance(c, (np.floating, float)) 
                            else c 
                            for c in color
                        ]
                    else:
                        project_data['painted_cells'][key] = (
                            int(color) if isinstance(color, np.integer) 
                            else float(color) if isinstance(color, np.floating) 
                            else color
                        )
                
                # Сохраняем палитру, если есть
                if palette is not None:
                    palette_list = []
                    for color in palette:
                        if isinstance(color, (list, tuple, np.ndarray)):
                            palette_list.append([
                                int(c) if isinstance(c, (np.integer, int)) 
                                else float(c) if isinstance(c, (np.floating, float)) 
                                else c 
                                for c in color
                            ])
                        else:
                            palette_list.append(
                                int(color) if isinstance(color, np.integer) 
                                else float(color) if isinstance(color, np.floating) 
                                else color
                            )
                    project_data['palette'] = palette_list
                
                # Сохраняем выбранный цвет, если есть
                if selected_color is not None:
                    if isinstance(selected_color, (list, tuple, np.ndarray)):
                        project_data['selected_color'] = [
                            int(c) if isinstance(c, (np.integer, int)) 
                            else float(c) if isinstance(c, (np.floating, float)) 
                            else c 
                            for c in selected_color
                        ]
                    else:
                        project_data['selected_color'] = (
                            int(selected_color) if isinstance(selected_color, np.integer) 
                            else float(selected_color) if isinstance(selected_color, np.floating) 
                            else selected_color
                        )
                
                # Конвертируем все numpy типы в стандартные Python типы
                project_data = ProjectManager.convert_to_json_serializable(project_data)
                
                # Сохраняем метаданные в JSON
                json_str = json.dumps(project_data, indent=2, ensure_ascii=False)
                zipf.writestr('project.json', json_str.encode('utf-8'))
            
            return True
        except Exception as e:
            raise Exception(f"Не удалось сохранить проект: {str(e)}")
    
    @staticmethod
    def load_project(file_path):
        """
        Загружает проект из zip-архива.
        
        Args:
            file_path: Путь к файлу проекта
        
        Returns:
            dict: Словарь с данными проекта или None в случае ошибки
            {
                'original_image': PIL.Image,
                'fragmented_image': PIL.Image или None,
                'image_path': str,
                'vertical_lines': list,
                'horizontal_lines': list,
                'num_vertical': int,
                'num_horizontal': int,
                'step_vertical': int,
                'step_horizontal': int,
                'num_colors': int,
                'view_mode': int,
                'show_grid': bool,
                'grid_line_width': int,
                'background_color': str,
                'painted_cells': dict,
                'palette': np.ndarray или None,
                'selected_color': tuple или None
            }
        """
        try:
            with zipfile.ZipFile(file_path, 'r') as zipf:
                # Проверяем наличие файла проекта
                if 'project.json' not in zipf.namelist():
                    raise ValueError("Неверный формат файла проекта")
                
                # Загружаем метаданные
                json_str = zipf.read('project.json').decode('utf-8')
                project_data = json.loads(json_str)
                
                # Загружаем оригинальное изображение
                original_image = None
                if 'original_image.png' in zipf.namelist():
                    img_data = zipf.read('original_image.png')
                    loaded_image = Image.open(io.BytesIO(img_data))
                    
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
                        original_image = Image.alpha_composite(
                            white_bg.convert('RGBA'), 
                            loaded_image
                        ).convert('RGB')
                    else:
                        # Если нет альфа-канала, просто конвертируем в RGB
                        original_image = loaded_image.convert('RGB')
                else:
                    raise ValueError("В проекте отсутствует изображение")
                
                # Загружаем фрагментированное изображение, если есть
                fragmented_image = None
                if 'fragmented_image.png' in zipf.namelist():
                    img_data = zipf.read('fragmented_image.png')
                    loaded_image = Image.open(io.BytesIO(img_data))
                    
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
                        fragmented_image = Image.alpha_composite(
                            white_bg.convert('RGBA'), 
                            loaded_image
                        ).convert('RGB')
                    else:
                        # Если нет альфа-канала, просто конвертируем в RGB
                        fragmented_image = loaded_image.convert('RGB')
                
                # Восстанавливаем закрашенные ячейки
                painted_cells = {}
                painted_cells_data = project_data.get('painted_cells', {})
                for key, color in painted_cells_data.items():
                    col, row = map(int, key.split(','))
                    painted_cells[(col, row)] = tuple(color) if isinstance(color, list) else color
                
                # Восстанавливаем палитру
                palette = None
                if 'palette' in project_data and project_data['palette']:
                    palette_data = project_data['palette']
                    # Преобразуем в numpy массив для совместимости с кодом, использующим astype()
                    palette_list = [tuple(c) if isinstance(c, list) else c for c in palette_data]
                    if palette_list:
                        # Убеждаемся, что все элементы имеют одинаковую длину (RGB или RGBA)
                        try:
                            palette = np.array(palette_list, dtype=np.uint8)
                        except (ValueError, TypeError) as e:
                            print(f"Ошибка при загрузке палитры: {e}")
                            palette = None
                
                # Восстанавливаем выбранный цвет
                selected_color = None
                if 'selected_color' in project_data:
                    color = project_data['selected_color']
                    selected_color = tuple(color) if isinstance(color, list) else color
                
                return {
                    'original_image': original_image,
                    'fragmented_image': fragmented_image,
                    'image_path': project_data.get('image_path', ''),
                    'vertical_lines': project_data.get('vertical_lines', []),
                    'horizontal_lines': project_data.get('horizontal_lines', []),
                    'num_vertical': project_data.get('num_vertical', 150),
                    'num_horizontal': project_data.get('num_horizontal', 150),
                    'step_vertical': project_data.get('step_vertical', 7),
                    'step_horizontal': project_data.get('step_horizontal', 7),
                    'num_colors': project_data.get('num_colors', 24),
                    'view_mode': project_data.get('view_mode', 1),
                    'show_grid': project_data.get('show_grid', True),
                    'grid_line_width': project_data.get('grid_line_width', 1),
                    'background_color': project_data.get('background_color', 'white'),
                    'painted_cells': painted_cells,
                    'palette': palette,
                    'selected_color': selected_color,
                    # Чекбоксы методов фрагментации
                    'palette_method_kmeans': project_data.get('palette_method_kmeans', False),
                    'palette_method_kmeans_improved': project_data.get('palette_method_kmeans_improved', False),
                    'palette_method_kmeans_weighted': project_data.get('palette_method_kmeans_weighted', False),
                    'palette_method_hierarchical_kmeans': project_data.get('palette_method_hierarchical_kmeans', False),
                    'palette_method_median_cut': project_data.get('palette_method_median_cut', False),
                    'palette_method_octree': project_data.get('palette_method_octree', False),
                    'sort_palette_by_gamma_var': project_data.get('sort_palette_by_gamma_var', True),
                    'focus_on_center_var': project_data.get('focus_on_center_var', False),
                    # Чекбоксы методов сетки
                    'adaptive_method_gradients': project_data.get('adaptive_method_gradients', False),
                    'manual_grid_enabled': project_data.get('manual_grid_enabled', False),
                    # Дополнительные настройки проекта
                    'project_name': project_data.get('project_name', ''),
                    'project_article': project_data.get('project_article', ''),
                    'qr_url': project_data.get('qr_url', '')
                }
        except Exception as e:
            raise Exception(f"Не удалось загрузить проект: {str(e)}")

