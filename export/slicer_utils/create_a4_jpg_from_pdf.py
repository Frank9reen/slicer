"""
Создание JPG изображений из PDF файлов A4 с добавлением баров
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont

# Импортируем config из той же папки
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    import importlib.util
    config_path = os.path.join(current_dir, 'config.py')
    if os.path.exists(config_path):
        spec = importlib.util.spec_from_file_location("slicer_config", config_path)
        config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config)
    else:
        import config
except ImportError:
    # Fallback значения
    class Config:
        JPEG_QUALITY = 95
    config = Config()


def create_a4_jpg_from_pdf(pdf_path, output_jpg_path, article_text, project_name, page_number, dpi=300, qr_url=None):
    """
    Создает JPG изображение из PDF файла A4 с добавлением двух верхних баров
    (артикул слева, название проекта справа) и номера страницы между ними.
    
    Args:
        pdf_path: Путь к PDF файлу
        output_jpg_path: Путь для сохранения JPG
        article_text: Текст артикула
        project_name: Название проекта
        page_number: Номер страницы
        dpi: DPI для конвертации (по умолчанию 300)
    
    Returns:
        bool: True если успешно, False в противном случае
    """
    try:
        # Конвертируем PDF в изображение
        # Импортируем pdf_to_jpg из того же модуля
        import sys
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        from color_layout_25 import pdf_to_jpg, save_jpg_with_metadata
        
        # Создаем временный JPG для конвертации PDF
        temp_jpg = output_jpg_path.replace('.jpg', '_temp.jpg')
        if not pdf_to_jpg(pdf_path, temp_jpg, dpi=dpi):
            print(f"[ERROR] Не удалось конвертировать PDF в JPG: {pdf_path}")
            return False
        
        # Загружаем конвертированное изображение
        pdf_image = Image.open(temp_jpg).convert("RGB")
        
        # Размеры A4 в пикселях при заданном DPI
        a4_width_inch = 8.27
        a4_height_inch = 11.69
        width_px = int(a4_width_inch * dpi)
        height_px = int(a4_height_inch * dpi)
        
        # Создаем canvas
        canvas = Image.new("RGB", (width_px, height_px), (255, 255, 255))
        
        # Отступы (в пикселях)
        margin_side = int(5 * dpi / 25.4)  # 5 мм
        margin_top_bar = int(1 * dpi / 25.4)  # 1 мм сверху для баров
        margin_top_text = int(1 * dpi / 25.4)  # 1 мм сверху для текста
        
        # Загружаем bar.png
        try:
            from utils.path_utils import get_static_path
            bar_image_paths = [
                get_static_path("bar.png"),
                get_static_path("pic/bar.png"),
            ]
        except ImportError:
            bar_image_paths = [
                os.path.join("static", "bar.png"),
                os.path.join("static", "pic", "bar.png"),
            ]
        
        bar_img_orig = None
        for bar_path in bar_image_paths:
            if os.path.exists(bar_path):
                bar_img_orig = Image.open(bar_path).convert("RGBA")
                break
        
        if not bar_img_orig:
            print(f"[WARNING] bar.png не найден, используем только текст")
            # Если bar.png не найден, просто вставляем PDF изображение
            canvas.paste(pdf_image, (0, 0))
            # Используем функцию с метаданными
            title = f"{article_text} - {project_name} - Страница {page_number}"
            save_jpg_with_metadata(canvas, output_jpg_path, quality=config.JPEG_QUALITY, dpi=(dpi, dpi), title=title)
            if os.path.exists(temp_jpg):
                os.remove(temp_jpg)
            return True
        
        # Загружаем шрифт для бара
        # Размер шрифта рассчитываем как 60% от высоты бара (как в A5 главной странице)
        try:
            from utils.path_utils import get_static_path
            font_paths = [
                get_static_path("fonts/Montserrat-SemiBold.ttf"),
                get_static_path("fonts/MontserratAlternates-SemiBold.otf"),
            ]
        except ImportError:
            font_paths = [
                os.path.join("static", "fonts", "Montserrat-SemiBold.ttf"),
                os.path.join("static", "fonts", "MontserratAlternates-SemiBold.otf"),
            ]
        
        # Масштабируем bar по ширине страницы (с учетом отступов)
        # Каждый бар занимает примерно половину доступной ширины
        margin_side_px = margin_side
        available_width = width_px - 2 * margin_side_px
        # Каждый бар занимает примерно 45% ширины (оставляем место между ними)
        target_bar_width_px = int(available_width * 0.45)
        ratio = target_bar_width_px / bar_img_orig.width
        bar_width_px = int(bar_img_orig.width * ratio)
        bar_height_px = int(bar_img_orig.height * ratio)
        
        # Масштабируем bar изображение
        bar_img_scaled = bar_img_orig.resize((bar_width_px, bar_height_px), Image.NEAREST)
        
        # Размер шрифта = 50% от высоты бара (уменьшен для A4 страниц)
        font_size_bar = int(bar_height_px * 0.5)
        
        font_bar = None
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    font_bar = ImageFont.truetype(font_path, font_size_bar)
                    break
                except:
                    pass
        
        if not font_bar:
            font_bar = ImageFont.load_default()
        
        # Размер шрифта для номера страницы в 2 раза меньше, чем для баров
        font_page = None
        font_size_page = font_size_bar // 2  # В 2 раза меньше размера шрифта баров
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    font_page = ImageFont.truetype(font_path, font_size_page)
                    break
                except:
                    pass
        
        if not font_page:
            font_page = ImageFont.load_default()
        
        draw = ImageDraw.Draw(canvas)
        
        # Функция для рисования текста на bar с автоматическим уменьшением шрифта, если не влезает
        def draw_bar_with_text(base_img, text, initial_font):
            img = base_img.copy()
            draw_tmp = ImageDraw.Draw(img)
            
            # Пробуем найти оптимальный размер шрифта
            font = initial_font
            max_width = int(img.width * 0.95)  # 95% ширины бара (оставляем небольшие отступы)
            max_height = int(img.height * 0.95)  # 95% высоты бара
            
            # Получаем текущий размер шрифта
            try:
                current_size = initial_font.size
            except AttributeError:
                # Если это дефолтный шрифт, используем примерный размер
                current_size = font_size_bar
            
            # Проверяем, влезает ли текст
            bbox = draw_tmp.textbbox((0, 0), text, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            
            # Если текст не влезает по ширине или высоте, уменьшаем размер шрифта
            if text_w > max_width or text_h > max_height:
                # Начинаем уменьшать размер шрифта пока текст не влезет
                min_size = max(8, current_size // 3)  # Минимальный размер шрифта
                for size in range(current_size, min_size - 1, -1):
                    # Пробуем создать шрифт с уменьшенным размером
                    test_font = None
                    for font_path in font_paths:
                        if os.path.exists(font_path):
                            try:
                                test_font = ImageFont.truetype(font_path, size)
                                break
                            except:
                                pass
                    
                    if not test_font:
                        # Fallback к дефолтному шрифту (но его нельзя масштабировать напрямую)
                        # В этом случае просто используем текущий font
                        break
                    
                    # Проверяем размер текста с новым шрифтом
                    test_bbox = draw_tmp.textbbox((0, 0), text, font=test_font)
                    test_w = test_bbox[2] - test_bbox[0]
                    test_h = test_bbox[3] - test_bbox[1]
                    
                    if test_w <= max_width and test_h <= max_height:
                        font = test_font
                        bbox = test_bbox
                        text_w = test_w
                        text_h = test_h
                        break
            
            # Выравнивание по центру горизонтально
            tx = (img.width - text_w) // 2
            # Выравнивание по центру вертикально
            # В PIL text() использует базовую линию, поэтому нужно учесть bbox[1] (отступ сверху)
            ty = (img.height - text_h) // 2 - bbox[1]  # Центрируем с учетом отступа сверху
            draw_tmp.text((tx, ty), text, fill="white", font=font)
            return img
        
        # Рисуем два верхних бара
        bar_y = margin_top_bar
        
        # Левый бар с артикулом
        bar_img_left = draw_bar_with_text(bar_img_scaled, article_text, font_bar)
        bar_x_left = margin_side
        canvas.paste(bar_img_left, (bar_x_left, bar_y), bar_img_left)
        
        # Правый бар с названием проекта
        bar_img_right = draw_bar_with_text(bar_img_scaled, project_name, font_bar)
        bar_x_right = width_px - margin_side - bar_img_right.width
        canvas.paste(bar_img_right, (bar_x_right, bar_y), bar_img_right)
        
        # Номер страницы между барами (по центру, выровнен по вертикали с текстом в барах)
        page_text = f"Стр. {page_number}"
        page_bbox = draw.textbbox((0, 0), page_text, font=font_page)
        page_text_w = page_bbox[2] - page_bbox[0]
        page_text_h = page_bbox[3] - page_bbox[1]
        page_text_x = (width_px - page_text_w) // 2
        
        # Вычисляем позицию текста в барах для выравнивания
        # Используем ту же логику, что и в draw_bar_with_text:
        # ty = (bar_height_px - text_h) // 2 - bbox[1]
        # Используем артикул как пример для вычисления позиции текста в баре
        bar_text_bbox = draw.textbbox((0, 0), article_text, font=font_bar)
        bar_text_h = bar_text_bbox[3] - bar_text_bbox[1]
        # Позиция Y текста в баре (как в draw_bar_with_text)
        bar_text_ty = (bar_height_px - bar_text_h) // 2 - bar_text_bbox[1]
        # Абсолютная позиция Y текста в баре на canvas
        bar_text_y = bar_y + bar_text_ty
        
        # Выравниваем номер страницы по той же позиции Y (центрируем по высоте текста)
        # Используем ту же формулу центрирования: ty = (bar_height_px - text_h) // 2 - bbox[1]
        page_text_ty = (bar_height_px - page_text_h) // 2 - page_bbox[1]
        page_text_y = bar_y + page_text_ty
        
        draw.text((page_text_x, page_text_y), page_text, fill=(0, 0, 0), font=font_page)
        
        # Вычисляем позицию для вставки PDF изображения (под барами)
        current_y = bar_y + bar_img_left.height + int(1.5 * dpi / 25.4)  # 1.5 мм отступ
        
        # Масштабируем PDF изображение, если нужно
        pdf_width, pdf_height = pdf_image.size
        max_width = width_px - 2 * margin_side
        max_height = height_px - current_y - int(5 * dpi / 25.4)  # 5 мм снизу
        
        # Вычисляем коэффициент масштабирования
        ratio_width = max_width / pdf_width
        ratio_height = max_height / pdf_height
        ratio = min(ratio_width, ratio_height)
        
        if ratio < 1.0:
            new_width = int(pdf_width * ratio)
            new_height = int(pdf_height * ratio)
            pdf_image = pdf_image.resize((new_width, new_height), Image.NEAREST)
        
        # Центрируем PDF изображение по горизонтали
        pdf_x = margin_side + (max_width - pdf_image.width) // 2
        canvas.paste(pdf_image, (pdf_x, current_y))
        
        # QR-код теперь добавляется только на страницу с легендой (палитрой) в PDF
        # Здесь не добавляем QR-код на обычные страницы A4
        
        # Сохраняем результат с метаданными
        title = f"{article_text} - {project_name} - Страница {page_number}"
        save_jpg_with_metadata(canvas, output_jpg_path, quality=config.JPEG_QUALITY, dpi=(dpi, dpi), title=title)
        
        # Удаляем временный файл
        if os.path.exists(temp_jpg):
            os.remove(temp_jpg)
        
        print(f"[INFO] Создан JPG: {output_jpg_path}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Ошибка при создании JPG из PDF: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_a4_jpg_pages_from_pdfs(task_dir, article_text, project_name, base_name="table_symbols", qr_url=None):
    """
    Создает JPG изображения из всех PDF файлов вида {article}_{base_name}_a4_page_*.pdf
    или {project_name}_{base_name}_a4_page_*.pdf (если артикул не используется в имени)
    
    Args:
        task_dir: Папка с проектом
        article_text: Текст артикула
        project_name: Название проекта
        base_name: Базовое имя файлов (по умолчанию "table_symbols")
    
    Returns:
        int: Количество созданных JPG файлов
    """
    # Создаем папку A4 (с большой буквы)
    a4_dir = os.path.join(task_dir, "A4")
    os.makedirs(a4_dir, exist_ok=True)
    
    # Папка с PDF файлами
    pdf_dir = os.path.join(task_dir, "A4-pdf")
    if not os.path.exists(pdf_dir):
        print(f"[WARNING] Папка с PDF файлами не найдена: {pdf_dir}")
        return 0
    
    # Ищем все PDF файлы вида {article}_{base_name}_a4_page_*.pdf
    # Теперь файлы создаются с артикулом, поэтому ищем только по артикулу
    pdf_files = []
    pattern = f"{article_text}_{base_name}_a4_page_"
    
    for filename in os.listdir(pdf_dir):
        if filename.endswith('.pdf') and '_a4_page_' in filename:
            # Проверяем по артикулу
            if filename.startswith(pattern):
                # Извлекаем номер страницы
                try:
                    # Формат: {prefix}_a4_page_{number}.pdf
                    parts = filename.replace('.pdf', '').split('_a4_page_')
                    if len(parts) == 2:
                        page_number = int(parts[1])
                        pdf_files.append((page_number, filename))
                except ValueError:
                    continue
    
    # Сортируем по номеру страницы
    pdf_files.sort(key=lambda x: x[0])
    
    if not pdf_files:
        print(f"[WARNING] PDF файлы не найдены в папке: {pdf_dir}")
        print(f"[INFO] Искали файлы с паттерном: {pattern}*")
        return 0
    
    print(f"[INFO] Найдено {len(pdf_files)} PDF файлов для конвертации в JPG")
    
    created_count = 0
    for page_number, pdf_filename in pdf_files:
        pdf_path = os.path.join(pdf_dir, pdf_filename)
        
        # Создаем имя JPG файла (используем артикул в имени)
        jpg_filename = f"{article_text}_{base_name}_a4_page_{page_number}.jpg"
        jpg_path = os.path.join(a4_dir, jpg_filename)
        
        if create_a4_jpg_from_pdf(pdf_path, jpg_path, article_text, project_name, page_number, qr_url=qr_url):
            created_count += 1
    
    print(f"[INFO] Создано {created_count} JPG файлов в папке: {a4_dir}")
    return created_count

