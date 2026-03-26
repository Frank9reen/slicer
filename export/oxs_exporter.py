"""Экспорт схемы вышивки в формат OXS (Ursa Software MacStitch/WinStitch)"""
import os
import numpy as np
import xml.etree.ElementTree as ET
from tkinter import filedialog, messagebox


def export_to_oxs(fragmented_image, palette, painted_cells, vertical_lines, horizontal_lines, 
                  image_path, parent_window):
    """
    Экспортирует схему в формат OXS (Ursa Software MacStitch/WinStitch).
    
    Args:
        fragmented_image: PIL Image - фрагментированное изображение
        palette: numpy.ndarray - палитра цветов
        painted_cells: dict - словарь закрашенных ячеек {(col, row): color}
        vertical_lines: list - список вертикальных линий сетки
        horizontal_lines: list - список горизонтальных линий сетки
        image_path: str - путь к исходному изображению
        parent_window: tk.Toplevel - родительское окно для диалогов
    
    Returns:
        str or None: Путь к сохраненному файлу или None при отмене/ошибке
    """
    # Проверяем наличие фрагментированного изображения
    if fragmented_image is None:
        messagebox.showwarning("Предупреждение", 
                             "Сначала создайте фрагментированное изображение!\n"
                             "Нажмите 'Получить палитру' после построения сетки.",
                             parent=parent_window)
        return None
    
    # Если палитра отсутствует, но есть фрагментированное изображение,
    # создаем палитру из уникальных цветов изображения
    if palette is None:
        try:
            img_array = np.array(fragmented_image)
            # Собираем уникальные цвета из фрагментированного изображения
            unique_colors = np.unique(img_array.reshape(-1, 3), axis=0)
            # Исключаем белый цвет (255, 255, 255) из палитры
            white_mask = ~np.all(unique_colors == [255, 255, 255], axis=1)
            unique_colors = unique_colors[white_mask]
            
            if len(unique_colors) == 0:
                messagebox.showwarning("Предупреждение", 
                                     "Не удалось создать палитру из фрагментированного изображения.\n"
                                     "Попробуйте создать палитру вручную.",
                                     parent=parent_window)
                return None
            
            palette = unique_colors
        except Exception as e:
            messagebox.showwarning("Предупреждение", 
                                 f"Не удалось создать палитру из фрагментированного изображения:\n{str(e)}\n"
                                 "Попробуйте создать палитру вручную.",
                                 parent=parent_window)
            return None
    
    # Запрашиваем путь для сохранения
    file_path = filedialog.asksaveasfilename(
        title="Экспорт схемы в формат OXS (MacStitch/WinStitch)",
        defaultextension=".oxs",
        filetypes=[("OXS файлы", "*.oxs"), ("Все файлы", "*.*")],
        parent=parent_window
    )
    
    if not file_path:
        return None
    
    try:
        # Получаем массив фрагментированного изображения
        img_array = np.array(fragmented_image)
        
        # Определяем размеры схемы
        if painted_cells and len(vertical_lines) >= 2 and len(horizontal_lines) >= 2:
            num_cols = len(vertical_lines) - 1
            num_rows = len(horizontal_lines) - 1
            use_painted_cells = True
        else:
            num_rows, num_cols = img_array.shape[:2]
            use_painted_cells = False
        
        # Создаем корневой элемент XML
        root = ET.Element("chart")
        
        # Формат
        format_elem = ET.SubElement(root, "format")
        format_elem.set("comments01", "Exported by Grid Editor")
        
        # Свойства схемы
        title = os.path.splitext(os.path.basename(file_path))[0]
        if image_path:
            title = os.path.splitext(os.path.basename(image_path))[0]
        
        properties = ET.SubElement(root, "properties")
        properties.set("oxsversion", "1.0")
        properties.set("software", "Grid Editor")
        properties.set("software_version", "1.0")
        properties.set("chartheight", str(num_rows))
        properties.set("chartwidth", str(num_cols))
        properties.set("charttitle", title)
        properties.set("author", "Zhdanov V.Y, Zhdanov I.Y.")
        properties.set("copyright", "Zhdanov V.Y, Zhdanov I.Y. - Copyright")
        properties.set("instructions", "")
        properties.set("stitchesperinch", "14")
        properties.set("stitchesperinch_y", "14")
        properties.set("palettecount", str(len(palette)))
        properties.set("misc1", "normal")
        properties.set("misc2", "")
        
        # Палитра цветов
        palette_elem = ET.SubElement(root, "palette")
        
        # Добавляем цвет фона (cloth) как первый элемент палитры
        cloth_item = ET.SubElement(palette_elem, "palette_item")
        cloth_item.set("index", "0")
        cloth_item.set("number", "cloth")
        cloth_item.set("name", "cloth")
        cloth_item.set("color", "FFFFFF")  # Белый фон
        cloth_item.set("printcolor", "FFFFFF")
        cloth_item.set("blendcolor", "nil")
        cloth_item.set("comments", "aida")
        cloth_item.set("strands", "2")
        cloth_item.set("symbol", "0")
        cloth_item.set("dashpattern", "")
        cloth_item.set("misc1", "")
        cloth_item.set("bsstrands", "0")
        cloth_item.set("bscolor", "000000")
        
        # Добавляем цвета палитры (начиная с индекса 1)
        for i, color in enumerate(palette):
            r = int(color[0])
            g = int(color[1])
            b = int(color[2])
            color_hex = f"{r:02X}{g:02X}{b:02X}"
            
            palette_item = ET.SubElement(palette_elem, "palette_item")
            palette_item.set("index", str(i + 1))  # Индексы начинаются с 1 (0 - это cloth)
            palette_item.set("number", f"Color {i+1}")
            palette_item.set("name", f"Color {i+1}")
            palette_item.set("color", color_hex)
            palette_item.set("printcolor", color_hex)
            palette_item.set("blendcolor", "nil")
            palette_item.set("comments", "")
            palette_item.set("strands", "2")
            palette_item.set("symbol", str(i + 1))
            palette_item.set("dashpattern", "")
            palette_item.set("misc1", "")
            palette_item.set("bsstrands", "1")
            palette_item.set("bscolor", color_hex)
        
        # Полные стежки
        fullstitches = ET.SubElement(root, "fullstitches")
        
        # Создаем словарь для быстрого поиска цвета в палитре
        # Индексы в OXS начинаются с 1 (0 - это cloth), поэтому добавляем 1
        palette_dict = {}
        for i, color in enumerate(palette):
            color_key = tuple(int(c) for c in color)
            palette_dict[color_key] = i + 1  # Индекс в палитре + 1
        
        # Заполняем схему стежками
        if use_painted_cells:
            # Используем painted_cells для более точного экспорта
            for (col, row), color in painted_cells.items():
                if 0 <= col < num_cols and 0 <= row < num_rows:
                    color_tuple = tuple(int(c) for c in color) if isinstance(color, (list, np.ndarray)) else color
                    if color_tuple in palette_dict:
                        palindex = palette_dict[color_tuple]
                    else:
                        # Если точного совпадения нет, находим ближайший цвет
                        color_array = np.array(color_tuple)
                        distances = np.sqrt(np.sum((palette - color_array) ** 2, axis=1))
                        palindex = int(np.argmin(distances)) + 1
                    
                    stitch = ET.SubElement(fullstitches, "stitch")
                    stitch.set("x", str(col))
                    stitch.set("y", str(row))
                    stitch.set("palindex", str(palindex))
        else:
            # Используем фрагментированное изображение
            for y in range(num_rows):
                for x in range(num_cols):
                    pixel_color = tuple(int(c) for c in img_array[y, x])
                    
                    # Пропускаем белый фон (cloth)
                    if pixel_color == (255, 255, 255):
                        continue
                    
                    # Находим цвет в палитре
                    if pixel_color in palette_dict:
                        palindex = palette_dict[pixel_color]
                    else:
                        # Если точного совпадения нет, находим ближайший цвет
                        distances = np.sqrt(np.sum((palette - img_array[y, x]) ** 2, axis=1))
                        palindex = int(np.argmin(distances)) + 1
                    
                    stitch = ET.SubElement(fullstitches, "stitch")
                    stitch.set("x", str(x))
                    stitch.set("y", str(y))
                    stitch.set("palindex", str(palindex))
        
        # Пустые секции (обязательные элементы)
        partstitches = ET.SubElement(root, "partstitches")
        ET.SubElement(partstitches, "partstitch")
        
        backstitches = ET.SubElement(root, "backstitches")
        ET.SubElement(backstitches, "backstitch")
        
        ornaments = ET.SubElement(root, "ornaments_inc_knots_and_beads")
        ET.SubElement(ornaments, "object")
        
        commentboxes = ET.SubElement(root, "commentboxes")
        
        # Создаем XML дерево
        tree = ET.ElementTree(root)
        
        # Сохраняем XML файл (без форматирования, как в оригинале)
        # Форматируем XML вручную для компактности (как в heart.oxs)
        xml_str = ET.tostring(root, encoding='unicode')
        # Убираем лишние пробелы между тегами для компактности
        xml_str = xml_str.replace('>\n<', '><')
        
        # Добавляем XML декларацию
        xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>'
        full_xml = xml_declaration + xml_str
        
        # Сохраняем файл
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(full_xml)
        
        from utils.version_utils import get_app_name_with_version
        app_name = get_app_name_with_version()
        messagebox.showinfo(f"Успех - {app_name}", 
                          f"Схема успешно экспортирована в формат OXS!\n\n"
                          f"Файл: {file_path}\n"
                          f"Размер: {num_cols}x{num_rows} крестиков\n"
                          f"Цветов: {len(palette)}\n\n"
                          f"Файл можно открыть в MacStitch, WinStitch\n"
                          f"или Cross Stitch Saga.",
                          parent=parent_window)
        
        return file_path
        
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось экспортировать схему:\n{str(e)}", parent=parent_window)
        import traceback
        print(traceback.format_exc())
        return None


def export_to_oxs_to_path(fragmented_image, palette, painted_cells, vertical_lines, horizontal_lines, 
                          image_path, output_path):
    """
    Экспортирует схему в формат OXS (Ursa Software MacStitch/WinStitch) в указанный путь.
    Без диалога сохранения - используется переданный путь.
    
    Args:
        fragmented_image: PIL Image - фрагментированное изображение
        palette: numpy.ndarray - палитра цветов
        painted_cells: dict - словарь закрашенных ячеек {(col, row): color}
        vertical_lines: list - список вертикальных линий сетки
        horizontal_lines: list - список горизонтальных линий сетки
        image_path: str - путь к исходному изображению
        output_path: str - путь для сохранения OXS файла
    
    Returns:
        str or None: Путь к сохраненному файлу или None при ошибке
    """
    # Проверяем наличие фрагментированного изображения
    if fragmented_image is None:
        return None
    
    # Если палитра отсутствует, но есть фрагментированное изображение,
    # создаем палитру из уникальных цветов изображения
    if palette is None:
        try:
            img_array = np.array(fragmented_image)
            # Собираем уникальные цвета из фрагментированного изображения
            unique_colors = np.unique(img_array.reshape(-1, 3), axis=0)
            # Исключаем белый цвет (255, 255, 255) из палитры
            white_mask = ~np.all(unique_colors == [255, 255, 255], axis=1)
            unique_colors = unique_colors[white_mask]
            
            if len(unique_colors) == 0:
                return None
            
            palette = unique_colors
        except Exception as e:
            print(f"Ошибка при создании палитры из фрагментированного изображения: {e}")
            return None
    
    try:
        # Получаем массив фрагментированного изображения
        img_array = np.array(fragmented_image)
        
        # Определяем размеры схемы
        if painted_cells and len(vertical_lines) >= 2 and len(horizontal_lines) >= 2:
            num_cols = len(vertical_lines) - 1
            num_rows = len(horizontal_lines) - 1
            use_painted_cells = True
        else:
            num_rows, num_cols = img_array.shape[:2]
            use_painted_cells = False
        
        # Создаем корневой элемент XML
        root = ET.Element("chart")
        
        # Формат
        format_elem = ET.SubElement(root, "format")
        format_elem.set("comments01", "Exported by Grid Editor")
        
        # Свойства схемы
        title = os.path.splitext(os.path.basename(output_path))[0]
        if image_path:
            title = os.path.splitext(os.path.basename(image_path))[0]
        
        properties = ET.SubElement(root, "properties")
        properties.set("oxsversion", "1.0")
        properties.set("software", "Grid Editor")
        properties.set("software_version", "1.0")
        properties.set("chartheight", str(num_rows))
        properties.set("chartwidth", str(num_cols))
        properties.set("charttitle", title)
        properties.set("author", "Zhdanov V.Y, Zhdanov I.Y.")
        properties.set("copyright", "Zhdanov V.Y, Zhdanov I.Y. - Copyright")
        properties.set("instructions", "")
        properties.set("stitchesperinch", "14")
        properties.set("stitchesperinch_y", "14")
        properties.set("palettecount", str(len(palette)))
        properties.set("misc1", "normal")
        properties.set("misc2", "")
        
        # Палитра цветов
        palette_elem = ET.SubElement(root, "palette")
        
        # Добавляем цвет фона (cloth) как первый элемент палитры
        cloth_item = ET.SubElement(palette_elem, "palette_item")
        cloth_item.set("index", "0")
        cloth_item.set("number", "cloth")
        cloth_item.set("name", "cloth")
        cloth_item.set("color", "FFFFFF")  # Белый фон
        cloth_item.set("printcolor", "FFFFFF")
        cloth_item.set("blendcolor", "nil")
        cloth_item.set("comments", "aida")
        cloth_item.set("strands", "2")
        cloth_item.set("symbol", "0")
        cloth_item.set("dashpattern", "")
        cloth_item.set("misc1", "")
        cloth_item.set("bsstrands", "0")
        cloth_item.set("bscolor", "000000")
        
        # Добавляем цвета палитры (начиная с индекса 1)
        for i, color in enumerate(palette):
            r = int(color[0])
            g = int(color[1])
            b = int(color[2])
            color_hex = f"{r:02X}{g:02X}{b:02X}"
            
            palette_item = ET.SubElement(palette_elem, "palette_item")
            palette_item.set("index", str(i + 1))  # Индексы начинаются с 1 (0 - это cloth)
            palette_item.set("number", f"Color {i+1}")
            palette_item.set("name", f"Color {i+1}")
            palette_item.set("color", color_hex)
            palette_item.set("printcolor", color_hex)
            palette_item.set("blendcolor", "nil")
            palette_item.set("comments", "")
            palette_item.set("strands", "2")
            palette_item.set("symbol", str(i + 1))
            palette_item.set("dashpattern", "")
            palette_item.set("misc1", "")
            palette_item.set("bsstrands", "1")
            palette_item.set("bscolor", color_hex)
        
        # Полные стежки
        fullstitches = ET.SubElement(root, "fullstitches")
        
        # Создаем словарь для быстрого поиска цвета в палитре
        # Индексы в OXS начинаются с 1 (0 - это cloth), поэтому добавляем 1
        palette_dict = {}
        for i, color in enumerate(palette):
            color_key = tuple(int(c) for c in color)
            palette_dict[color_key] = i + 1  # Индекс в палитре + 1
        
        # Заполняем схему стежками
        if use_painted_cells:
            # Используем painted_cells для более точного экспорта
            for (col, row), color in painted_cells.items():
                if 0 <= col < num_cols and 0 <= row < num_rows:
                    color_tuple = tuple(int(c) for c in color) if isinstance(color, (list, np.ndarray)) else color
                    if color_tuple in palette_dict:
                        palindex = palette_dict[color_tuple]
                    else:
                        # Если точного совпадения нет, находим ближайший цвет
                        color_array = np.array(color_tuple)
                        distances = np.sqrt(np.sum((palette - color_array) ** 2, axis=1))
                        palindex = int(np.argmin(distances)) + 1
                    
                    stitch = ET.SubElement(fullstitches, "stitch")
                    stitch.set("x", str(col))
                    stitch.set("y", str(row))
                    stitch.set("palindex", str(palindex))
        else:
            # Используем фрагментированное изображение
            for y in range(num_rows):
                for x in range(num_cols):
                    pixel_color = tuple(int(c) for c in img_array[y, x])
                    
                    # Пропускаем белый фон (cloth)
                    if pixel_color == (255, 255, 255):
                        continue
                    
                    # Находим цвет в палитре
                    if pixel_color in palette_dict:
                        palindex = palette_dict[pixel_color]
                    else:
                        # Если точного совпадения нет, находим ближайший цвет
                        distances = np.sqrt(np.sum((palette - img_array[y, x]) ** 2, axis=1))
                        palindex = int(np.argmin(distances)) + 1
                    
                    stitch = ET.SubElement(fullstitches, "stitch")
                    stitch.set("x", str(x))
                    stitch.set("y", str(y))
                    stitch.set("palindex", str(palindex))
        
        # Пустые секции (обязательные элементы)
        partstitches = ET.SubElement(root, "partstitches")
        ET.SubElement(partstitches, "partstitch")
        
        backstitches = ET.SubElement(root, "backstitches")
        ET.SubElement(backstitches, "backstitch")
        
        ornaments = ET.SubElement(root, "ornaments_inc_knots_and_beads")
        ET.SubElement(ornaments, "object")
        
        commentboxes = ET.SubElement(root, "commentboxes")
        
        # Создаем XML дерево
        tree = ET.ElementTree(root)
        
        # Сохраняем XML файл (без форматирования, как в оригинале)
        # Форматируем XML вручную для компактности (как в heart.oxs)
        xml_str = ET.tostring(root, encoding='unicode')
        # Убираем лишние пробелы между тегами для компактности
        xml_str = xml_str.replace('>\n<', '><')
        
        # Добавляем XML декларацию
        xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>'
        full_xml = xml_declaration + xml_str
        
        # Сохраняем файл
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_xml)
        
        return output_path
        
    except Exception as e:
        print(f"Ошибка при экспорте OXS: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None
