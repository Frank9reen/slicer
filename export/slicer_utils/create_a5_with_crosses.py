"""
Создание A5 главной страницы с наложением крестиков на каждую ячейку.
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from .create_a5_main_from_image import create_a5_main_page_from_image


def _create_image_from_painted_cells(painted_cells, vertical_lines, horizontal_lines):
    """
    Создает изображение только из закрашенных ячеек.
    
    Args:
        painted_cells: dict - словарь {(col, row): color} с закрашенными ячейками
        vertical_lines: list - вертикальные линии сетки
        horizontal_lines: list - горизонтальные линии сетки
    
    Returns:
        PIL Image - изображение только с закрашенными ячейками на белом фоне
    """
    if not painted_cells or len(painted_cells) == 0:
        return None
    
    if not vertical_lines or not horizontal_lines or len(vertical_lines) < 2 or len(horizontal_lines) < 2:
        return None
    
    # Вычисляем размеры изображения на основе координат сетки
    width = vertical_lines[-1] if vertical_lines else 800
    height = horizontal_lines[-1] if horizontal_lines else 600
    
    # Создаем новое изображение с белым фоном
    result_image = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(result_image)
    
    # Вычисляем количество ячеек
    num_cols = len(vertical_lines) - 1
    num_rows = len(horizontal_lines) - 1
    
    # Заполняем ячейки цветами из painted_cells
    for col in range(num_cols):
        for row in range(num_rows):
            if (col, row) in painted_cells:
                color = painted_cells[(col, row)]
                
                # Определяем границы ячейки
                left = vertical_lines[col]
                right = vertical_lines[col + 1]
                top = horizontal_lines[row]
                bottom = horizontal_lines[row + 1]
                
                # Рисуем прямоугольник с цветом ячейки
                draw.rectangle([left, top, right, bottom], fill=color)
    
    return result_image


def _create_normalized_image_with_crosses(
    fragmented_image,
    vertical_lines,
    horizontal_lines,
    painted_cells,
    cross_img,
    cross_opacity=0.5,
    blend_mode="multiply"
):
    """
    Создает нормализованное изображение с одинаковыми размерами ячеек и крестиками.
    
    Args:
        fragmented_image: PIL Image - исходное изображение
        vertical_lines: list - вертикальные линии сетки
        horizontal_lines: list - горизонтальные линии сетки
        painted_cells: dict - закрашенные ячейки
        cross_img: PIL Image - изображение крестика с оригинальной прозрачностью
        cross_opacity: float - множитель прозрачности (1.0 = оригинальная)
        blend_mode: str - режим смешивания (всегда "multiply")
    
    Returns:
        PIL Image - нормализованное изображение с крестиками
    """
    # Вычисляем количество ячеек
    num_cols = len(vertical_lines) - 1
    num_rows = len(horizontal_lines) - 1
    
    if num_cols == 0 or num_rows == 0:
        return fragmented_image
    
    # Вычисляем нормализованные размеры ячеек
    cell_widths = []
    for i in range(len(vertical_lines) - 1):
        width = vertical_lines[i+1] - vertical_lines[i]
        if width > 0:
            cell_widths.append(width)
    
    cell_heights = []
    for i in range(len(horizontal_lines) - 1):
        height = horizontal_lines[i+1] - horizontal_lines[i]
        if height > 0:
            cell_heights.append(height)
    
    # Используем медианный размер для нормализации
    if cell_widths:
        sorted_widths = sorted(cell_widths)
        percentile_25_idx = max(0, len(sorted_widths) // 4)
        normalized_width = max(10, sorted_widths[percentile_25_idx])
    else:
        normalized_width = 20
    
    if cell_heights:
        sorted_heights = sorted(cell_heights)
        percentile_25_idx = max(0, len(sorted_heights) // 4)
        normalized_height = max(10, sorted_heights[percentile_25_idx])
    else:
        normalized_height = 20
    
    # Создаем нормализованное изображение
    norm_width = num_cols * normalized_width
    norm_height = num_rows * normalized_height
    
    result_image = Image.new("RGBA", (norm_width, norm_height), (255, 255, 255, 255))
    
    # Масштабируем крестик под нормализованный размер ячейки
    cross_resized = cross_img.resize((normalized_width, normalized_height), Image.NEAREST)
    
    # Используем оригинальную прозрачность крестика (не изменяем её)
    # cross.png уже имеет встроенную прозрачность ~50%
    
    # Заполняем нормализованное изображение
    for col in range(num_cols):
        for row in range(num_rows):
            # Координаты в нормализованном изображении
            norm_x = col * normalized_width
            norm_y = row * normalized_height
            
            # Получаем цвет ячейки с приоритетом painted_cells
            if painted_cells:
                # Если есть painted_cells, используем их приоритетно
                if (col, row) in painted_cells:
                    # Ячейка есть в painted_cells - используем цвет из painted_cells
                    cell_color = painted_cells[(col, row)]
                    if isinstance(cell_color, (list, tuple)):
                        cell_color = tuple(int(c) for c in cell_color[:3])
                    
                    # Создаем цветной прямоугольник
                    cell_img = Image.new("RGBA", (normalized_width, normalized_height), cell_color + (255,))
                    result_image.paste(cell_img, (norm_x, norm_y))
                else:
                    # Ячейки нет в painted_cells - используем белый цвет
                    cell_img = Image.new("RGBA", (normalized_width, normalized_height), (255, 255, 255, 255))
                    result_image.paste(cell_img, (norm_x, norm_y))
            elif fragmented_image:
                # Используем fragmented_image только если нет painted_cells
                # Определяем границы ячейки в исходном изображении
                orig_left = vertical_lines[col]
                orig_right = vertical_lines[col + 1]
                orig_top = horizontal_lines[row]
                orig_bottom = horizontal_lines[row + 1]
                
                # Извлекаем область ячейки из исходного изображения
                if (orig_right > orig_left and orig_bottom > orig_top and 
                    orig_left < fragmented_image.width and orig_top < fragmented_image.height):
                    
                    # Обрезаем координаты по границам изображения
                    orig_left = max(0, int(orig_left))
                    orig_right = min(fragmented_image.width, int(orig_right))
                    orig_top = max(0, int(orig_top))
                    orig_bottom = min(fragmented_image.height, int(orig_bottom))
                    
                    if orig_right > orig_left and orig_bottom > orig_top:
                        cell_crop = fragmented_image.crop((orig_left, orig_top, orig_right, orig_bottom))
                        cell_resized = cell_crop.resize((normalized_width, normalized_height), Image.NEAREST)
                        
                        # Конвертируем в RGBA если нужно
                        if cell_resized.mode != "RGBA":
                            cell_resized = cell_resized.convert("RGBA")
                        
                        result_image.paste(cell_resized, (norm_x, norm_y))
            
            # Накладываем крестик на каждую ячейку с blend-эффектом
            # Используем opacity=1.0 чтобы сохранить оригинальную прозрачность крестика
            _apply_cross_with_blend(result_image, cross_resized, norm_x, norm_y, 1.0, blend_mode)
    
    return result_image


def _apply_cross_with_blend(base_image, cross_image, x, y, opacity=1.0, blend_mode="multiply"):
    """
    Применяет крестик к базовому изображению с режимом Multiply.
    
    Args:
        base_image: PIL Image - базовое изображение (RGBA)
        cross_image: PIL Image - изображение крестика (RGBA) с оригинальной прозрачностью
        x, y: int - координаты для размещения крестика
        opacity: float - множитель прозрачности (1.0 = использовать оригинальную прозрачность крестика)
        blend_mode: str - режим смешивания (всегда "multiply")
    """
    # Получаем размеры крестика
    cross_width, cross_height = cross_image.size
    
    # Извлекаем область базового изображения под крестиком
    base_crop = base_image.crop((x, y, x + cross_width, y + cross_height))
    
    # Конвертируем в RGB для blend операций
    base_rgb = base_crop.convert("RGB")
    cross_rgb = cross_image.convert("RGB")
    
    # Применяем Multiply blend: результат = base * cross / 255 (темнее)
    blended = _multiply_blend(base_rgb, cross_rgb)
    # Применяем opacity через обычный blend
    blended = Image.blend(base_rgb, blended, opacity)
    
    # Конвертируем обратно в RGBA
    blended_rgba = blended.convert("RGBA")
    
    # Применяем альфа-канал крестика как маску
    alpha_mask = cross_image.split()[-1]  # Получаем альфа-канал
    
    # Создаем композитное изображение с учетом альфа-канала
    result_crop = Image.new("RGBA", (cross_width, cross_height), (0, 0, 0, 0))
    
    # Применяем blend только там, где крестик не прозрачен
    for px_x in range(cross_width):
        for px_y in range(cross_height):
            alpha_val = alpha_mask.getpixel((px_x, px_y))
            if alpha_val > 0:  # Если пиксель не полностью прозрачен
                # Берем цвет из blended изображения
                blended_color = blended_rgba.getpixel((px_x, px_y))
                # Используем оригинальную прозрачность крестика (не изменяем opacity)
                result_crop.putpixel((px_x, px_y), blended_color[:3] + (alpha_val,))
    
    # Накладываем результат на базовое изображение
    base_image.paste(result_crop, (x, y), result_crop)


def _multiply_blend(base_img, overlay_img):
    """Multiply blend mode: base * overlay / 255"""
    import numpy as np
    
    base_array = np.array(base_img, dtype=np.float32)
    overlay_array = np.array(overlay_img, dtype=np.float32)
    
    # Multiply blend formula
    result_array = (base_array * overlay_array) / 255.0
    result_array = np.clip(result_array, 0, 255).astype(np.uint8)
    
    return Image.fromarray(result_array, 'RGB')






def _make_cross_transparent(cross_image, opacity=0.5):
    """
    Создает прозрачную версию крестика.
    
    Args:
        cross_image: PIL Image - исходное изображение крестика
        opacity: float - уровень прозрачности (0.5 = 50%)
    
    Returns:
        PIL Image - крестик с прозрачностью
    """
    # Конвертируем в RGBA если нужно
    if cross_image.mode != "RGBA":
        cross_image = cross_image.convert("RGBA")
    
    # Создаем копию
    transparent_cross = cross_image.copy()
    
    # Получаем данные пикселей
    pixels = list(transparent_cross.getdata())
    
    # Применяем прозрачность ко всем пикселям
    new_pixels = []
    for pixel in pixels:
        if len(pixel) == 4:  # RGBA
            r, g, b, a = pixel
            # Применяем opacity к альфа-каналу
            new_alpha = int(a * opacity)
            new_pixels.append((r, g, b, new_alpha))
        else:  # RGB
            r, g, b = pixel
            # Добавляем альфа-канал с прозрачностью
            new_alpha = int(255 * opacity)
            new_pixels.append((r, g, b, new_alpha))
    
    # Обновляем изображение
    transparent_cross.putdata(new_pixels)
    
    return transparent_cross


def create_a5_main_with_crosses(
    fragmented_image,
    vertical_lines,
    horizontal_lines,
    painted_cells,
    palette,
    cross_image_path,
    pdf_name: str,
    article_text: str = "ART12345",
    output_folder: str = None,
    project_name_text: str = None,
    embroidery_size: str = None,
    cross_opacity: float = 0.5,
    blend_mode: str = "multiply",
    canvas_size: int = 16,
    use_saga_paradise: bool = False,
    template_path: str = None
):
    """
    Создает A5 главную страницу с наложением крестиков на каждую ячейку.
    
    Args:
        fragmented_image: PIL Image - фрагментированное изображение проекта
        vertical_lines: list - вертикальные линии сетки
        horizontal_lines: list - горизонтальные линии сетки
        painted_cells: dict - закрашенные ячейки {(col, row): color}
        palette: list - палитра цветов проекта
        cross_image_path: str - путь к изображению крестика (static/cross.png)
        pdf_name: str - название проекта
        article_text: str - артикул
        output_folder: str - папка для сохранения
        project_name_text: str - название проекта для текста
        embroidery_size: str - размер вышивки
        cross_opacity: float - множитель прозрачности (1.0 = оригинальная прозрачность крестика ~50%)
        blend_mode: str - режим смешивания (всегда "multiply")
    
    Returns:
        str: путь к созданному файлу
    """
    
    if not os.path.exists(cross_image_path):
        raise FileNotFoundError(f"Изображение крестика не найдено: {cross_image_path}")
    
    # Если нет фрагментированного изображения, создаем его из закрашенных ячеек
    if fragmented_image is None:
        if not painted_cells or len(painted_cells) == 0:
            raise ValueError("Нет ни фрагментированного изображения, ни закрашенных ячеек")
        
        print("[INFO] Создание изображения из закрашенных ячеек...")
        fragmented_image = _create_image_from_painted_cells(
            painted_cells, vertical_lines, horizontal_lines
        )
        
        if fragmented_image is None:
            raise ValueError("Не удалось создать изображение из закрашенных ячеек")
    
    if not vertical_lines or not horizontal_lines or len(vertical_lines) < 2 or len(horizontal_lines) < 2:
        raise ValueError("Недостаточно линий сетки")
    
    # Загружаем изображение крестика
    cross_img = Image.open(cross_image_path).convert("RGBA")
    print(f"[INFO] Загружен крестик: {cross_img.size}, режим: {cross_img.mode}")
    
    # Создаем прозрачную версию крестика (50% прозрачности)
    cross_img = _make_cross_transparent(cross_img, opacity=0.5)
    print(f"[INFO] Создан прозрачный крестик: {cross_img.mode}")
    
    # Вычисляем количество ячеек
    num_cols = len(vertical_lines) - 1
    num_rows = len(horizontal_lines) - 1
    
    print(f"[INFO] Создание нормализованного A5 с крестиками: {num_cols}x{num_rows} ячеек, режим: {blend_mode}")
    print(f"[DEBUG] Fragmented image: {fragmented_image.size if fragmented_image else 'None'}")
    print(f"[DEBUG] Painted cells count: {len(painted_cells) if painted_cells else 0}")
    
    # Создаем нормализованное изображение с крестиками
    result_image = _create_normalized_image_with_crosses(
        fragmented_image,
        vertical_lines,
        horizontal_lines,
        painted_cells,
        cross_img,
        cross_opacity,
        blend_mode
    )
    
    # Сохраняем временное изображение с крестиками
    temp_dir = output_folder if output_folder else "temp"
    os.makedirs(temp_dir, exist_ok=True)
    
    temp_image_path = os.path.join(temp_dir, f"{article_text}_temp_with_crosses.png")
    result_image.save(temp_image_path, "PNG")
    
    print(f"[INFO] Временное изображение с крестиками сохранено: {temp_image_path}")
    
    # Определяем количество цветов из палитры
    num_colors = len(palette) if palette is not None and len(palette) > 0 else len(set(painted_cells.values())) if painted_cells else 10
    
    try:
        # Создаем A5 главную страницу из изображения с крестиками
        output_path = create_a5_main_page_from_image(
            image_path=temp_image_path,
            pdf_name=pdf_name,
            article_text=article_text,
            output_folder=output_folder,
            template_path=template_path,
            num_colors=num_colors,
            project_name_text=project_name_text,
            embroidery_size=embroidery_size,
            canvas_size=canvas_size,
            use_saga_paradise=use_saga_paradise
        )
        
        # Удаляем временный файл
        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)
            print(f"[INFO] Временный файл удален: {temp_image_path}")
        
        # Возвращаем путь к созданному файлу без переименования
        return output_path
        
    except Exception as e:
        # Удаляем временный файл в случае ошибки
        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)
        raise e


def create_a5_main_with_crosses_for_organizer(
    fragmented_image,
    vertical_lines,
    horizontal_lines,
    painted_cells,
    palette,
    pdf_name: str,
    article_text: str = "ART12345",
    output_folder: str = None,
    project_name_text: str = None,
    embroidery_size: str = None,
    cross_opacity: float = 1.0,
    blend_mode: str = "multiply",
    canvas_size: int = 16,
    use_saga_paradise: bool = False,
    template_path: str = None
):
    """
    Создает A5 главную страницу с наложением крестиков для использования в органайзере.
    Автоматически находит изображение крестика в static/cross.png.
    
    Args:
        fragmented_image: PIL Image - фрагментированное изображение проекта
        vertical_lines: list - вертикальные линии сетки
        horizontal_lines: list - горизонтальные линии сетки
        painted_cells: dict - закрашенные ячейки {(col, row): color}
        palette: list - палитра цветов проекта
        pdf_name: str - название проекта
        article_text: str - артикул
        output_folder: str - папка для сохранения
        project_name_text: str - название проекта для текста
        embroidery_size: str - размер вышивки
        cross_opacity: float - множитель прозрачности (1.0 = оригинальная прозрачность крестика ~50%)
        blend_mode: str - режим смешивания (всегда "multiply")
    
    Returns:
        str: путь к созданному файлу
    """
    from utils.path_utils import get_static_path
    
    # Автоматически находим изображение крестика
    cross_image_path = get_static_path("cross.png")
    
    if not os.path.exists(cross_image_path):
        raise FileNotFoundError(f"Изображение крестика не найдено: {cross_image_path}")
    
    # Вызываем основную функцию создания A5 с крестиками
    return create_a5_main_with_crosses(
        fragmented_image=fragmented_image,
        vertical_lines=vertical_lines,
        horizontal_lines=horizontal_lines,
        painted_cells=painted_cells,
        palette=palette,
        cross_image_path=cross_image_path,
        pdf_name=pdf_name,
        article_text=article_text,
        output_folder=output_folder,
        project_name_text=project_name_text,
        template_path=template_path,
        embroidery_size=embroidery_size,
        cross_opacity=cross_opacity,
        blend_mode=blend_mode,
        canvas_size=canvas_size,
        use_saga_paradise=use_saga_paradise
    )


def create_image_with_crosses_only(
    fragmented_image,
    vertical_lines,
    horizontal_lines,
    painted_cells,
    cross_image_path,
    cross_opacity: float = 0.5,
    blend_mode: str = "multiply"
):
    """
    Создает изображение только с крестиками (без создания A5 страницы).
    
    Args:
        fragmented_image: PIL Image - фрагментированное изображение
        vertical_lines: list - вертикальные линии сетки
        horizontal_lines: list - горизонтальные линии сетки
        painted_cells: dict - закрашенные ячейки
        cross_image_path: str - путь к изображению крестика
        cross_opacity: float - множитель прозрачности (1.0 = оригинальная ~50%)
        blend_mode: str - режим смешивания (всегда "multiply")
    
    Returns:
        PIL Image: нормализованное изображение с наложенными крестиками
    """
    
    if not os.path.exists(cross_image_path):
        raise FileNotFoundError(f"Изображение крестика не найдено: {cross_image_path}")
    
    # Если нет фрагментированного изображения, создаем его из закрашенных ячеек
    if fragmented_image is None:
        if not painted_cells or len(painted_cells) == 0:
            raise ValueError("Нет ни фрагментированного изображения, ни закрашенных ячеек")
        
        print("[INFO] Создание изображения из закрашенных ячеек...")
        fragmented_image = _create_image_from_painted_cells(
            painted_cells, vertical_lines, horizontal_lines
        )
        
        if fragmented_image is None:
            raise ValueError("Не удалось создать изображение из закрашенных ячеек")
    
    if not vertical_lines or not horizontal_lines or len(vertical_lines) < 2 or len(horizontal_lines) < 2:
        raise ValueError("Недостаточно линий сетки")
    
    # Загружаем изображение крестика
    cross_img = Image.open(cross_image_path).convert("RGBA")
    
    # Создаем нормализованное изображение с крестиками
    result_image = _create_normalized_image_with_crosses(
        fragmented_image,
        vertical_lines,
        horizontal_lines,
        painted_cells,
        cross_img,
        cross_opacity,
        blend_mode
    )
    
    return result_image
