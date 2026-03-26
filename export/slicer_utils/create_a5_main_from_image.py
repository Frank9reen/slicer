"""
Создание A5 главной страницы из готового изображения.
Логика перенесена из fcrossy_3.10(edit)/create_a5_main_from_image.py
"""
import os
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import sys

# Импортируем конфигурацию
try:
    # Импортируем config из той же папки (slicer_utils)
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Добавляем путь к slicer_utils в sys.path для явного импорта
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # Пробуем использовать уже загруженный модуль config из sys.modules
    # Это гарантирует, что мы используем тот же модуль, что и file_creator.py
    if 'config' in sys.modules:
        config_module = sys.modules['config']
    else:
        # Если модуль еще не загружен, импортируем его
        import config as config_module
    
    # Используем настройки из config.py
    # Сохраняем ссылку на модуль config для доступа к обновленным значениям
    config = config_module
    FOLDERS = config_module.FOLDERS
    FILES = config_module.FILES
    # Используем ссылки на словари, чтобы получать обновленные значения
    EMBROIDERY_SETTINGS = config_module.EMBROIDERY_SETTINGS
    TEXTS = config_module.TEXTS
    FONT_SIZES = config_module.FONT_SIZES
    MARGINS = config_module.MARGINS
    COLORS = config_module.COLORS
except (ImportError, AttributeError) as e:
    # Если config не найден, создаем fallback config объект
    config = None
    print(f"[WARNING] Файл config.py не найден или не содержит нужных атрибутов: {e}. Используются значения по умолчанию.")
    # Значения по умолчанию (fallback)
    FOLDERS = {
        "sheet": "sheet",
        "sheet_legend": "sheet-legend",
        "static": "static",
    }
    FILES = {
        "main_font": "static/fonts/Montserrat-SemiBold.ttf",
        "bar_image": "static/bar.png",
        "main_template": "static/pic/main_template.png",
    }
    EMBROIDERY_SETTINGS = {
        "size": "",  # Будет браться из конфига
        "project_name_text": "",  # Будет браться из конфига
        "article": "",  # Будет браться из конфига
    }
    TEXTS = {
        "top_text": "Набор для вышивания крестом",
        "bottom_text_template": "{project_name} {embroidery_size}",
        "details_text": (
            "В набор входит:\n"
            "мулине {num_colors} {colors_word} (хлопок),\n"
            "канва Aida {canvas_size} ct (хлопок),\n"
            "цветосимвольная схема,\n"
            "игла"
        ),
    }
    FONT_SIZES = {
        "a5_top_text": 60,
        "a5_bottom_text": 60,
        "a5_details_text": 40,
        "a5_bar_min_size": 8,
    }
    MARGINS = {
        "a5_image_area": (120, 300, 1640, 1810),
        "a5_bar_y": 150,
        "a5_corner_radius": 30,
        "a5_border_width": 10,
        "a5_text_area1": (280, 1880, 1460, 1940),
        "a5_text_area2": (280, 1975, 1465, 2025),
        "a5_text_area3": (120, 2110, 720, 2200),
    }
    COLORS = {
        "border": "#232323",
        "details_text": "#303030",
    }


def get_font_path():
    """Возвращает путь к основному шрифту."""
    try:
        from utils.path_utils import get_static_path
        return get_static_path("fonts/Montserrat-SemiBold.ttf")
    except ImportError:
        return FILES["main_font"]


def get_regular_font_path():
    """Возвращает путь к обычному (тонкому) шрифту."""
    try:
        from utils.path_utils import get_static_path
        return get_static_path("fonts/MontserratAlternates-Regular.ttf")
    except ImportError:
        # Fallback на обычный шрифт, если не найден
        try:
            from utils.path_utils import get_static_path
            return get_static_path("fonts/Montserrat-SemiBold.ttf")
        except ImportError:
            return FILES["main_font"]


def get_colors_word_form(count: int) -> str:
    """
    Возвращает правильную форму слова "цвет" в зависимости от количества.
    
    :param count: количество цветов
    :return: правильная форма слова
    """
    if count % 10 == 1 and count % 100 != 11:
        return "цвет"
    elif count % 10 in [2, 3, 4] and count % 100 not in [12, 13, 14]:
        return "цвета"
    else:
        return "цветов"


def get_text_with_colors(num_colors: int, canvas_size: int = 16) -> str:
    """Возвращает текст с правильным склонением слова 'цвет' и размером канвы."""
    colors_word = get_colors_word_form(num_colors)
    return TEXTS["details_text"].format(
        num_colors=num_colors,
        colors_word=colors_word,
        canvas_size=canvas_size
    )


def get_bottom_text(project_name: str = None, embroidery_size: str = None) -> str:
    """Возвращает нижний текст для A5 страницы."""
    # Получаем project_name из config (для использования, если не передан)
    if config and hasattr(config, 'EMBROIDERY_SETTINGS'):
        config_project_name = config.EMBROIDERY_SETTINGS.get("project_name_text", "").strip()
    else:
        config_project_name = EMBROIDERY_SETTINGS.get("project_name_text", "").strip()
    
    # Приоритет: переданный embroidery_size > config > значение по умолчанию
    if embroidery_size is None or (isinstance(embroidery_size, str) and not embroidery_size.strip()):
        # Используем config напрямую, чтобы получить обновленные значения
        if config and hasattr(config, 'EMBROIDERY_SETTINGS'):
            embroidery_size = config.EMBROIDERY_SETTINGS.get("size", "").strip()
        else:
            embroidery_size = EMBROIDERY_SETTINGS.get("size", "").strip()
        
        # Если размер не указан в конфиге, используем значение по умолчанию
        if not embroidery_size:
            embroidery_size = "23 х 23 см"
    else:
        # Если embroidery_size передан и не пустой, используем его
        if isinstance(embroidery_size, str):
            embroidery_size = embroidery_size.strip()
    
    # Приоритет: переданный project_name > config_project_name > пустая строка
    if project_name:
        display_project_name = project_name
    elif config_project_name:
        display_project_name = config_project_name
    else:
        display_project_name = ""
    
    # Используем config напрямую для шаблона
    if config and hasattr(config, 'TEXTS'):
        bottom_template = config.TEXTS.get("bottom_text_template", "{project_name} {embroidery_size}")
    else:
        bottom_template = TEXTS.get("bottom_text_template", "{project_name} {embroidery_size}")
    
    return bottom_template.format(
        project_name=display_project_name,
        embroidery_size=embroidery_size
    )


def get_colors_count_from_gamma(pdf_name: str, project_folder: str = None) -> int:
    """
    Получает количество цветов из gamma файла.
    
    :param pdf_name: название PDF файла (без расширения)
    :param project_folder: папка с проектами или папка проекта
    :return: количество цветов
    """
    if project_folder is None:
        project_folder = FOLDERS["sheet_legend"]
    
    # Пробуем несколько вариантов пути к файлу
    # Вариант 1: project_folder уже является папкой проекта (содержит файл напрямую)
    gamma_file = os.path.join(project_folder, f"legend-{pdf_name}-gamma.xlsx")
    
    # Вариант 2: project_folder - базовая папка, файл в подпапке проекта
    if not os.path.exists(gamma_file):
        gamma_file = os.path.join(project_folder, pdf_name, f"legend-{pdf_name}-gamma.xlsx")
    
    # Вариант 3: ищем любой gamma файл в project_folder
    if not os.path.exists(gamma_file):
        if os.path.isdir(project_folder):
            for file in os.listdir(project_folder):
                if file.endswith('.xlsx') and 'legend' in file.lower() and 'gamma' in file.lower():
                    gamma_file = os.path.join(project_folder, file)
                    print(f"[INFO] Найден gamma файл: {gamma_file}")
                    break
    
    if not os.path.exists(gamma_file):
        print(f"[WARNING] Gamma файл не найден для проекта {pdf_name}")
        print(f"[WARNING] Искали в: {project_folder}")
        print(f"[WARNING] Используем значение по умолчанию: 10 цветов")
        return 10  # Значение по умолчанию
    
    try:
        df = pd.read_excel(gamma_file)
        colors_count = len(df)
        print(f"[INFO] Найдено {colors_count} цветов в gamma файле: {gamma_file}")
        return colors_count
    except Exception as e:
        print(f"[WARNING] Ошибка при чтении gamma файла {gamma_file}: {e}, используем значение по умолчанию")
        return 10


def create_a5_main_page_from_image(
    image_path: str,
    pdf_name: str,
    article_text: str = "ART12345",
    output_folder: str = None,
    template_path: str = None,
    bar_image_path: str = None,
    font_path: str = None,
    num_colors: int = None,  # Если None, будет загружено из gamma файла
    top_text: str = None,
    bottom_text_template: str = None,
    project_name_text: str = None,  # Название проекта для нижнего текста
    embroidery_size: str = None,  # Размер вышивки (если None, берется из config)
    canvas_size: int = 16,  # Размер канвы (ct)
    use_saga_paradise: bool = False  # Вставить картинку saga/paradise под текстом
):
    """
    Создает A5 главную страницу из готового изображения A5.
    
    :param image_path: путь к A5 изображению в папке sheet/
    :param pdf_name: название PDF файла (без расширения, используется для путей)
    :param article_text: артикул для bar'а (по умолчанию: "ART12345")
    :param output_folder: базовая папка для сохранения
    :param template_path: путь к шаблону главной страницы
    :param bar_image_path: путь к изображению bar
    :param font_path: путь к шрифту
    :param num_colors: количество цветов в наборе (если None, загружается из gamma файла)
    :param top_text: верхний текст
    :param bottom_text_template: шаблон нижнего текста
    :param project_name_text: название проекта для нижнего текста (если None, берется из config)
    :param embroidery_size: размер вышивки (если None, берется из config)
    :return: путь к созданной главной странице
    """
    # Используем настройки по умолчанию
    if output_folder is None:
        output_folder = FOLDERS["sheet_legend"]
    try:
        from utils.path_utils import get_static_path
        if template_path is None:
            template_path = get_static_path("pic/main_template.png")
        if bar_image_path is None:
            bar_image_path = get_static_path("bar.png")
        if font_path is None:
            font_path = get_font_path()
    except ImportError:
        if template_path is None:
            template_path = FILES["main_template"]
        if bar_image_path is None:
            bar_image_path = FILES["bar_image"]
        if font_path is None:
            font_path = get_font_path()
    if top_text is None:
        # Используем config напрямую, чтобы получить обновленное значение
        if config and hasattr(config, 'TEXTS'):
            top_text = config.TEXTS.get("top_text", "Набор для вышивания крестом")
        else:
            top_text = TEXTS.get("top_text", "Набор для вышивания крестом")
    if bottom_text_template is None:
        # Используем config напрямую, чтобы получить обновленное значение
        if config and hasattr(config, 'TEXTS'):
            bottom_text_template = config.TEXTS.get("bottom_text_template", "{project_name} {embroidery_size}")
        else:
            bottom_text_template = TEXTS.get("bottom_text_template", "{project_name} {embroidery_size}")
    
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"A5 изображение не найдено: {image_path}")
    
    # Загружаем количество цветов из gamma файла, если не указано
    if num_colors is None:
        num_colors = get_colors_count_from_gamma(pdf_name, output_folder)
    
    # Создаем структуру папок - A5 в папке проекта
    # Проверяем, является ли output_folder уже папкой проекта
    # Ищем gamma файл в разных вариантах
    gamma_file_variants = [
        os.path.join(output_folder, f"legend-{pdf_name}-gamma.xlsx"),
        os.path.join(output_folder, f"{pdf_name}.xlsx"),
        os.path.join(output_folder, pdf_name, f"legend-{pdf_name}-gamma.xlsx"),
    ]
    
    # Проверяем, есть ли gamma файл прямо в output_folder
    has_gamma_in_output = any(os.path.exists(v) for v in gamma_file_variants[:2])
    
    # Проверяем, совпадает ли имя папки с именем проекта
    is_project_folder = os.path.basename(output_folder) == pdf_name
    
    if has_gamma_in_output or is_project_folder:
        # output_folder уже является папкой проекта
        a5_output_folder = output_folder
    else:
        # Создаем подпапку проекта
        a5_output_folder = os.path.join(output_folder, pdf_name)
    
    os.makedirs(a5_output_folder, exist_ok=True)
    
    # Используем article_text (название файла) для бара, игнорируя настройки
    # Это позволяет использовать название файла изображения вместо настроек
    display_article = article_text
    
    # Удаляем старую главную страницу, если она существует
    old_main_page = os.path.join(a5_output_folder, f"{display_article}_главная_страница.jpg")
    if os.path.exists(old_main_page):
        os.remove(old_main_page)
        print(f"[INFO] Удалена старая главная страница: {old_main_page}")
    
    print(f"[INFO] Создание A5 главной страницы для: {pdf_name}")
    print(f"[INFO] Артикул: {display_article}")
    print(f"[INFO] Изображение: {image_path}")
    
    # Загружаем шаблон главной страницы
    if os.path.exists(template_path):
        template = Image.open(template_path).convert("RGBA")
        print(f"[INFO] Загружен шаблон: {template_path}")
    else:
        print(f"[WARNING] Шаблон не найден: {template_path}, создаем простой A5")
        # Создаем простой A5 canvas (5.83" x 8.27" при 300 DPI)
        template = Image.new("RGBA", (1749, 2481), (255, 255, 255, 255))
    
    # Загружаем A5 изображение
    a5_img = Image.open(image_path).convert("RGBA")
    print(f"[INFO] Загружено A5 изображение: {a5_img.size}")
    
    # Координаты области для растяжения
    left, top, right, bottom = MARGINS["a5_image_area"]
    area_width = right - left
    area_height = bottom - top
    
    # --- Создаем маску для области с прямоугольником и скругленными углами ---
    mask = Image.new("L", template.size, 0)
    draw_mask = ImageDraw.Draw(mask)
    corner_radius = MARGINS["a5_corner_radius"]
    draw_mask.rounded_rectangle([left, top, right, bottom], radius=corner_radius, fill=255)
    
    # Растягиваем картинку под область
    img_resized = a5_img.resize((area_width, area_height), Image.NEAREST)
    
    # Создаем пустое изображение под шаблон
    temp_img = Image.new("RGBA", template.size, (0, 0, 0, 0))
    temp_img.paste(img_resized, (left, top))
    
    # Применяем маску
    template = Image.composite(temp_img, template, mask)
    
    # --- Рисуем скругленный прямоугольник поверх ---
    draw = ImageDraw.Draw(template)
    border_color = COLORS["border"]
    border_width = MARGINS["a5_border_width"]
    draw.rounded_rectangle([left-5, top, right, bottom+5], radius=corner_radius, outline=border_color, width=border_width)
    
    # --- Вставка bar.png с артикулом на одной линии с областью ниже ---
    if os.path.exists(bar_image_path):
        bar_img_orig = Image.open(bar_image_path).convert("RGBA")
        
        # Масштабируем по ширине до 1/3 ширины шаблона или максимум 400px для A5
        max_bar_width = min(template.width // 3, 400)
        ratio = max_bar_width / bar_img_orig.width
        new_width = int(bar_img_orig.width * ratio)
        new_height = int(bar_img_orig.height * ratio)
        bar_img = bar_img_orig.resize((new_width, new_height), Image.NEAREST)
        
        # Рисуем текст артикула по центру bar
        font_size_bar = int(bar_img.height * 0.6)
        min_font_size = FONT_SIZES["a5_bar_min_size"]
        try:
            font_bar = ImageFont.truetype(font_path, font_size_bar)
        except:
            font_bar = ImageFont.load_default()
        
        draw_bar = ImageDraw.Draw(bar_img)
        
        # Динамически уменьшаем шрифт, если текст не помещается
        bbox = draw_bar.textbbox((0, 0), display_article, font=font_bar)
        text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        while text_w > bar_img.width - 10 and font_size_bar > min_font_size:
            font_size_bar -= 1
            try:
                font_bar = ImageFont.truetype(font_path, font_size_bar)
            except:
                font_bar = ImageFont.load_default()
            bbox = draw_bar.textbbox((0, 0), display_article, font=font_bar)
            text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        
        tx = (bar_img.width - text_w) // 2
        ty = (bar_img.height - text_h) // 2 - 3  # Уменьшенный отступ для A5
        draw_bar.text((tx, ty), display_article, fill="white", font=font_bar)
        
        # Вставляем на одной линии с областью ниже (left координата области картинки)
        bar_x = left  # по горизонтали совмещаем с областью картинки
        bar_y = MARGINS["a5_bar_y"]
        template.paste(bar_img, (bar_x, bar_y), bar_img)
    else:
        print(f"[WARNING] bar.png не найден: {bar_image_path}")
    
    # --- Верхний текст ---
    text_area1 = MARGINS["a5_text_area1"]
    try:
        font_size1 = FONT_SIZES["a5_top_text"]
        font1 = ImageFont.truetype(font_path, font_size1)
    except:
        font1 = ImageFont.load_default()
    
    bbox = draw.textbbox((0, 0), top_text, font=font1)
    text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x_text = text_area1[0] + (text_area1[2] - text_area1[0] - text_width) // 2
    y_text = text_area1[1] + (text_area1[3] - text_area1[1] - text_height) // 2
    draw.text((x_text, y_text), top_text, fill="white", font=font1)
    
    # --- Нижний текст с названием проекта ---
    text_area2 = MARGINS["a5_text_area2"]
    # Передаем project_name_text и embroidery_size, если они переданы, иначе get_bottom_text будет использовать config
    bottom_text = get_bottom_text(project_name_text, embroidery_size)
    
    # Динамически уменьшаем шрифт, если текст не помещается
    area_width2 = text_area2[2] - text_area2[0]
    area_height2 = text_area2[3] - text_area2[1]
    font_size2 = FONT_SIZES["a5_bottom_text"]
    min_font_size2 = max(12, FONT_SIZES["a5_bar_min_size"])  # Минимальный размер шрифта
    
    try:
        font2 = ImageFont.truetype(font_path, font_size2)
    except:
        font2 = ImageFont.load_default()
    
    # Проверяем, помещается ли текст, и уменьшаем шрифт при необходимости
    bbox2 = draw.textbbox((0, 0), bottom_text, font=font2)
    text_width2, text_height2 = bbox2[2] - bbox2[0], bbox2[3] - bbox2[1]
    
    # Уменьшаем шрифт, пока текст не поместится
    while (text_width2 > area_width2 - 10 or text_height2 > area_height2 - 10) and font_size2 > min_font_size2:
        font_size2 -= 1
        try:
            font2 = ImageFont.truetype(font_path, font_size2)
        except:
            font2 = ImageFont.load_default()
            break
        bbox2 = draw.textbbox((0, 0), bottom_text, font=font2)
        text_width2, text_height2 = bbox2[2] - bbox2[0], bbox2[3] - bbox2[1]
    
    x_text2 = text_area2[0] + (text_area2[2] - text_area2[0] - text_width2) // 2
    y_text2 = text_area2[1] + (text_area2[3] - text_area2[1] - text_height2) // 2
    draw.text((x_text2, y_text2), bottom_text, fill="white", font=font2)
    
    # --- Последний блок текста ---
    text_area3 = MARGINS["a5_text_area3"]
    last_text = get_text_with_colors(num_colors, canvas_size)
    # Используем тот же шрифт, что и для текста "Оттенки готовой вышивки..." (основной шрифт font_path)
    try:
        font_size3 = FONT_SIZES["a5_details_text"]
        font3 = ImageFont.truetype(font_path, font_size3)
    except:
        font3 = ImageFont.load_default()
    
    text_color3 = COLORS["details_text"]
    lines = last_text.split("\n")
    y_offset = text_area3[1]
    for line in lines:
        bbox3 = draw.textbbox((0, 0), line, font=font3)
        text_width3, text_height3 = bbox3[2] - bbox3[0], bbox3[3] - bbox3[1]
        x_text3 = text_area3[0] + (text_area3[2] - text_area3[0] - text_width3) // 2
        draw.text((x_text3, y_offset), line, fill=text_color3, font=font3)
        y_offset += text_height3 + 5  # Как в оригинале
    
    # --- Вставка картинки saga/paradise под текстом, если включено ---
    if use_saga_paradise:
        try:
            from utils.path_utils import get_static_path
            saga_image_path = get_static_path("saga_paradise.png")
        except ImportError:
            # Fallback путь
            saga_image_path = os.path.join(os.path.dirname(__file__), "..", "..", "static", "saga_paradise.png")
        
        if os.path.exists(saga_image_path):
            saga_img = Image.open(saga_image_path).convert("RGBA")
            
            # Вычисляем размер картинки (максимальная ширина = ширина области текста, пропорционально)
            text_area_width = text_area3[2] - text_area3[0]
            max_saga_width = text_area_width
            max_saga_height = 150  # Максимальная высота картинки
            
            # Масштабируем картинку с сохранением пропорций и уменьшаем на 20%
            saga_ratio = min(max_saga_width / saga_img.width, max_saga_height / saga_img.height)
            new_saga_width = int(saga_img.width * saga_ratio * 0.8)  # Уменьшаем на 20%
            new_saga_height = int(saga_img.height * saga_ratio * 0.8)  # Уменьшаем на 20%
            saga_img_resized = saga_img.resize((new_saga_width, new_saga_height), Image.NEAREST)
            
            # Позиционируем картинку по центру области текста, под текстом
            saga_x = text_area3[0] + (text_area3[2] - text_area3[0] - new_saga_width) // 2
            saga_y = y_offset + 30  # Увеличенный отступ после текста
            
            # Вставляем картинку
            template.paste(saga_img_resized, (saga_x, saga_y), saga_img_resized)
            print(f"[INFO] Вставлена картинка saga/paradise: {saga_image_path}")
        else:
            print(f"[WARNING] Картинка saga/paradise не найдена: {saga_image_path}")
    
    # --- Сохраняем A5 главную страницу ---
    output_path = os.path.join(a5_output_folder, f"{display_article}_главная_страница.jpg")
    # Используем качество из конфига, если доступно
    try:
        jpeg_quality = config.JPEG_QUALITY
    except (AttributeError, NameError):
        jpeg_quality = 95
    # Сохраняем с метаданными
    template_rgb = template.convert("RGB")
    title = f"{display_article} - Главная страница"
    try:
        from color_layout_25 import save_jpg_with_metadata
        save_jpg_with_metadata(template_rgb, output_path, quality=jpeg_quality, title=title)
    except ImportError:
        # Fallback если функция не доступна
        template_rgb.save(output_path, 'JPEG', quality=jpeg_quality)
    print(f"Создана A5 главная страница: {output_path}")
    
    return output_path


def process_all_a5_images_in_sheet(sheet_folder=None, output_folder=None, article_text="ART12345", num_colors=None):
    """
    Обрабатывает все A5 изображения в указанной папке
    
    :param sheet_folder: папка с A5 изображениями (если None, используется из конфига)
    :param output_folder: папка для выходных файлов
    :param article_text: текст артикула
    :param num_colors: количество цветов (если None, берется из конфига)
    """
    if num_colors is None:
        try:
            num_colors = config.NUM_COLORS
        except (AttributeError, NameError):
            num_colors = 10
    """
    Обрабатывает все A5 изображения в папке sheet/ и создает главные страницы.
    
    :param sheet_folder: папка с A5 изображениями
    :param output_folder: базовая папка для сохранения результатов
    :param article_text: артикул для bar'а (по умолчанию: "ART12345")
    :param num_colors: количество цветов в наборе
    :return: список путей к созданным главным страницам
    """
    # Используем настройки по умолчанию
    if sheet_folder is None:
        sheet_folder = FOLDERS["sheet"]
    if output_folder is None:
        output_folder = FOLDERS["sheet_legend"]
    
    if not os.path.exists(sheet_folder):
        print(f"[ERROR] Папка {sheet_folder} не найдена")
        return []
    
    # Ищем A5 изображения (предполагаем, что они имеют суффикс _a5 или содержат a5 в имени)
    image_files = []
    for f in os.listdir(sheet_folder):
        if f.lower().endswith(('.png', '.jpg', '.jpeg')) and ('a5' in f.lower() or '_a5' in f.lower()):
            image_files.append(f)
    
    if not image_files:
        print(f"[INFO] A5 изображения в папке {sheet_folder} не найдены")
        print(f"[INFO] Ищем файлы с 'a5' в имени...")
        return []
    
    print(f"[INFO] Найдено {len(image_files)} A5 изображений: {image_files}")
    
    created_pages = []
    
    for image_file in image_files:
        image_path = os.path.join(sheet_folder, image_file)
        
        # Получаем название PDF из имени файла (убираем _a5 и расширение)
        pdf_name = os.path.splitext(image_file)[0]
        if '_a5' in pdf_name.lower():
            pdf_name = pdf_name.replace('_a5', '').replace('_A5', '')
        
        print(f"\n{'='*50}")
        print(f"Обработка A5: {image_file}")
        print(f"PDF: {pdf_name}")
        print(f"{'='*50}")
        
        try:
            output_path = create_a5_main_page_from_image(
                image_path=image_path,
                pdf_name=pdf_name,
                article_text=article_text,
                output_folder=output_folder,
                num_colors=num_colors
            )
            created_pages.append(output_path)
            print(f"✅ Успешно создана A5 главная страница: {output_path}")
        except Exception as e:
            print(f"❌ Ошибка при обработке {image_file}: {e}")
    
    print(f"\n{'='*50}")
    print(f"Обработка A5 завершена. Создано страниц: {len(created_pages)}")
    for page in created_pages:
        print(f"  - {page}")
    print(f"{'='*50}")
    
    return created_pages


if __name__ == "__main__":
    # Пример использования
    print("Создание A5 главной страницы из изображения")
    print("Используйте функцию create_a5_main_page_from_image() для создания главной страницы")
    print("Или process_all_a5_images_in_sheet() для обработки всех A5 изображений в папке sheet/")

