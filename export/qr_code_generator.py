"""
Модуль для генерации QR-кодов
Адаптировано из fcrossy_5.3
"""
import qrcode
from PIL import Image, ImageDraw, ImageFont
import os


def generate_qr_with_text(
    url: str,
    output_path: str = None,
    text: str = "Электронная схема ↓",
    font_path: str = None,
    font_size: int = 40,
    qr_box_size: int = 10,
    qr_border: int = 4,
    qr_version: int = None,
    error_correction: str = "M",
    foreground_color: str = "black",
    background_color: str = "white",
    text_color: str = "black",
    fixed_width: int = None
):
    """
    Создает QR-код с текстом для проекта.
    
    :param url: URL для QR-кода
    :param output_path: путь для сохранения QR-кода
    :param text: текст над QR-кодом
    :param font_path: путь к шрифту
    :param font_size: размер шрифта
    :param qr_box_size: размер ячейки QR-кода
    :param qr_border: размер границы QR-кода
    :param qr_version: версия QR-кода (None для автоматического определения)
    :param error_correction: уровень коррекции ошибок ('L', 'M', 'Q', 'H')
    :param foreground_color: цвет переднего плана QR-кода
    :param background_color: цвет фона QR-кода
    :param text_color: цвет текста
    :param fixed_width: фиксированная ширина итогового изображения (None для автоматического)
    :return: путь к созданному QR-коду или None при ошибке
    """
    if not url or not url.strip():
        print(f"[WARNING] URL не указан, QR-код не будет создан")
        return None
    
    if output_path is None:
        # Создаем временный файл
        import tempfile
        output_path = os.path.join(tempfile.gettempdir(), "qr_code_temp.jpg")
    
    # Создаем папку для QR-кодов если не существует
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Определяем путь к шрифту
    if font_path is None:
        # Пробуем использовать get_static_path, как в других модулях
        try:
            from utils.path_utils import get_static_path
            font_path = get_static_path("fonts/Montserrat-SemiBold.ttf")
            if not os.path.exists(font_path):
                font_path = get_static_path("fonts/MontserratAlternates-SemiBold.otf")
        except ImportError:
            # Если не получилось, пробуем относительный путь
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            font_path = os.path.join(base_path, "static", "fonts", "Montserrat-SemiBold.ttf")
            if not os.path.exists(font_path):
                font_path = os.path.join(base_path, "static", "fonts", "MontserratAlternates-SemiBold.otf")
                if not os.path.exists(font_path):
                    font_path = None
    
    # --- Загружаем шрифт ---
    try:
        if font_path and os.path.exists(font_path):
            font = ImageFont.truetype(font_path, font_size)
            print(f"[INFO] Шрифт для QR-кода загружен: {font_path}")
        else:
            font = ImageFont.load_default()
            print("[WARNING] Не удалось загрузить шрифт, используется шрифт по умолчанию.")
    except Exception as e:
        font = ImageFont.load_default()
        print(f"[WARNING] Ошибка при загрузке шрифта: {e}, используется шрифт по умолчанию.")
    
    # --- Вычисляем размер текста корректно для UTF-8 ---
    temp_img = Image.new("RGB", (1, 1))
    draw_temp = ImageDraw.Draw(temp_img)
    bbox = draw_temp.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Создаем QR-код
    try:
        qr = qrcode.QRCode(
            version=qr_version,
            error_correction=getattr(qrcode.constants, f"ERROR_CORRECT_{error_correction}"),
            box_size=qr_box_size,
            border=qr_border
        )
        qr.add_data(url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color=foreground_color, back_color=background_color).convert("RGB")
        
        # --- Создаем новое изображение под текст и QR ---
        text_padding = 20
        if fixed_width is not None:
            new_width = fixed_width
        else:
            new_width = max(qr_img.width, text_width + text_padding)
        new_height = qr_img.height + text_height + text_padding
        final_img = Image.new("RGB", (new_width, new_height), background_color)
        draw_final = ImageDraw.Draw(final_img)
        
        # --- Рисуем текст ---
        text_x = (new_width - text_width) // 2
        text_y = 10
        draw_final.text((text_x, text_y), text, font=font, fill=text_color)
        
        # --- Вставляем QR-код под текстом ---
        qr_x = (new_width - qr_img.width) // 2
        qr_y = text_height + text_padding
        final_img.paste(qr_img, (qr_x, qr_y))
        
        final_img.save(output_path, format='JPEG', quality=95)
        print(f"[INFO] QR-код сохранен: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"[ERROR] Ошибка при создании QR-кода: {e}")
        import traceback
        traceback.print_exc()
        return None


def generate_qr_without_text(
    url: str,
    output_path: str = None,
    qr_box_size: int = 10,
    qr_border: int = 4,
    qr_version: int = None,
    error_correction: str = "M",
    foreground_color: str = "black",
    background_color: str = "white"
):
    """
    Создает QR-код БЕЗ текста (только сам QR-код).
    Используется когда текст будет добавлен отдельно в PDF.
    
    :param url: URL для QR-кода
    :param output_path: путь для сохранения QR-кода
    :param qr_box_size: размер ячейки QR-кода
    :param qr_border: размер границы QR-кода
    :param qr_version: версия QR-кода (None для автоматического определения)
    :param error_correction: уровень коррекции ошибок ('L', 'M', 'Q', 'H')
    :param foreground_color: цвет переднего плана QR-кода
    :param background_color: цвет фона QR-кода
    :return: путь к созданному QR-коду или None при ошибке
    """
    if not url or not url.strip():
        print(f"[WARNING] URL не указан, QR-код не будет создан")
        return None
    
    if output_path is None:
        # Создаем временный файл
        import tempfile
        output_path = os.path.join(tempfile.gettempdir(), "qr_code_temp.jpg")
    
    # Создаем папку для QR-кодов если не существует
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Создаем QR-код
    try:
        qr = qrcode.QRCode(
            version=qr_version,
            error_correction=getattr(qrcode.constants, f"ERROR_CORRECT_{error_correction}"),
            box_size=qr_box_size,
            border=qr_border
        )
        qr.add_data(url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color=foreground_color, back_color=background_color).convert("RGB")
        
        # Сохраняем QR-код как есть, без текста
        qr_img.save(output_path, format='JPEG', quality=95)
        print(f"[INFO] QR-код (без текста) сохранен: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"[ERROR] Ошибка при создании QR-кода: {e}")
        import traceback
        traceback.print_exc()
        return None


def generate_telegram_qr_with_text(
    url: str = "https://t.me/marfa_igolkina",
    output_path: str = None,
    text: str = "Поддержка ↓",
    font_path: str = None,
    font_size: int = 40,
    qr_box_size: int = 10,
    qr_border: int = 4,
    qr_version: int = None,
    error_correction: str = "M",
    foreground_color: str = "black",
    background_color: str = "white",
    text_color: str = "black",
    fixed_width: int = None
):
    """
    Создает QR-код со ссылкой на Telegram-группу поддержки.
    Использует ту же логику, что и generate_qr_with_text.
    
    :param url: URL Telegram-группы (по умолчанию https://t.me/marfa_igolkina)
    :param output_path: путь для сохранения QR-кода
    :param text: текст над QR-кодом (по умолчанию "Поддержка ↓")
    :param font_path: путь к шрифту
    :param font_size: размер шрифта
    :param qr_box_size: размер ячейки QR-кода
    :param qr_border: размер границы QR-кода
    :param qr_version: версия QR-кода (None для автоматического определения)
    :param error_correction: уровень коррекции ошибок ('L', 'M', 'Q', 'H')
    :param foreground_color: цвет переднего плана QR-кода
    :param background_color: цвет фона QR-кода
    :param text_color: цвет текста
    :param fixed_width: фиксированная ширина итогового изображения (None для автоматического)
    :return: путь к созданному QR-коду или None при ошибке
    """
    # Используем основную функцию generate_qr_with_text
    return generate_qr_with_text(
        url=url,
        output_path=output_path,
        text=text,
        font_path=font_path,
        font_size=font_size,
        qr_box_size=qr_box_size,
        qr_border=qr_border,
        qr_version=qr_version,
        error_correction=error_correction,
        foreground_color=foreground_color,
        background_color=background_color,
        text_color=text_color,
        fixed_width=fixed_width
    )


def insert_qr_on_image(
    image_path: str,
    qr_url: str,
    qr_area: tuple = None,  # (x1, y1, x2, y2) или None для автоматического размещения
    text: str = "Электронная схема ↓",
    font_path: str = None,
    font_size: int = 40,
    qr_box_size: int = 10,
    qr_border: int = 4,
    output_path: str = None
):
    """
    Вставляет QR-код на изображение.
    
    :param image_path: путь к изображению
    :param qr_url: URL для QR-кода
    :param qr_area: область для размещения QR-кода (x1, y1, x2, y2) или None
    :param text: текст над QR-кодом
    :param font_path: путь к шрифту
    :param font_size: размер шрифта
    :param qr_box_size: размер ячейки QR-кода
    :param qr_border: размер границы QR-кода
    :param output_path: путь для сохранения (если None, перезаписывает исходный файл)
    :return: путь к обновленному изображению или None при ошибке
    """
    if not os.path.exists(image_path):
        print(f"[ERROR] Изображение не найдено: {image_path}")
        return None
    
    if not qr_url or not qr_url.strip():
        print(f"[WARNING] URL не указан, QR-код не будет вставлен")
        return image_path
    
    # Создаем QR-код
    import tempfile
    temp_qr_path = os.path.join(tempfile.gettempdir(), "qr_temp_insert.jpg")
    qr_path = generate_qr_with_text(
        url=qr_url,
        output_path=temp_qr_path,
        text=text,
        font_path=font_path,
        font_size=font_size,
        qr_box_size=qr_box_size,
        qr_border=qr_border
    )
    
    if not qr_path or not os.path.exists(qr_path):
        print(f"[WARNING] Не удалось создать QR-код")
        return image_path
    
    try:
        # Загружаем изображение
        img = Image.open(image_path).convert("RGB")
        qr_img = Image.open(qr_path).convert("RGBA")
        
        # Определяем область для QR-кода
        if qr_area is None:
            # Автоматическое размещение: справа внизу с отступом
            margin = 50
            qr_area_width = min(500, img.width // 4)
            qr_area_height = min(500, img.height // 4)
            qr_area = (
                img.width - qr_area_width - margin,
                img.height - qr_area_height - margin,
                img.width - margin,
                img.height - margin
            )
        
        # Вычисляем размеры области для QR-кода
        qr_area_width = qr_area[2] - qr_area[0]
        qr_area_height = qr_area[3] - qr_area[1]
        
        # Масштабируем QR-код под область
        qr_ratio = min(qr_area_width / qr_img.width, qr_area_height / qr_img.height)
        qr_resized = qr_img.resize(
            (int(qr_img.width * qr_ratio), int(qr_img.height * qr_ratio)),
            Image.NEAREST
        )
        
        # Вычисляем позицию для центрирования
        qr_x = qr_area[0] + (qr_area_width - qr_resized.width) // 2
        qr_y = qr_area[1] + (qr_area_height - qr_resized.height) // 2
        
        # Вставляем QR-код на изображение
        img.paste(qr_resized, (qr_x, qr_y), qr_resized)
        
        # Сохраняем
        if output_path is None:
            output_path = image_path
        
        img.save(output_path, format='JPEG', quality=95)
        print(f"[INFO] QR-код вставлен на изображение: {output_path}")
        
        # Удаляем временный файл QR-кода
        try:
            os.remove(qr_path)
        except:
            pass
        
        return output_path
        
    except Exception as e:
        print(f"[ERROR] Ошибка при вставке QR-кода: {e}")
        import traceback
        traceback.print_exc()
        return image_path


def insert_telegram_qr_on_image(
    image_path: str,
    qr_url: str = "https://t.me/marfa_igolkina",
    qr_area: tuple = None,  # (x1, y1, x2, y2) или None для автоматического размещения
    text: str = "Поддержка ↓",
    font_path: str = None,
    font_size: int = 40,
    qr_box_size: int = 10,
    qr_border: int = 4,
    output_path: str = None
):
    """
    Вставляет QR-код со ссылкой на Telegram-группу поддержки на изображение.
    Использует ту же логику, что и insert_qr_on_image.
    
    :param image_path: путь к изображению
    :param qr_url: URL Telegram-группы (по умолчанию https://t.me/marfa_igolkina)
    :param qr_area: область для размещения QR-кода (x1, y1, x2, y2) или None
    :param text: текст над QR-кодом (по умолчанию "Поддержка ↓")
    :param font_path: путь к шрифту
    :param font_size: размер шрифта
    :param qr_box_size: размер ячейки QR-кода
    :param qr_border: размер границы QR-кода
    :param output_path: путь для сохранения (если None, перезаписывает исходный файл)
    :return: путь к обновленному изображению или None при ошибке
    """
    if not os.path.exists(image_path):
        print(f"[ERROR] Изображение не найдено: {image_path}")
        return None
    
    if not qr_url or not qr_url.strip():
        print(f"[WARNING] URL не указан, QR-код не будет вставлен")
        return image_path
    
    # Создаем QR-код с текстом для Telegram
    import tempfile
    temp_qr_path = os.path.join(tempfile.gettempdir(), "qr_temp_telegram_insert.jpg")
    qr_path = generate_telegram_qr_with_text(
        url=qr_url,
        output_path=temp_qr_path,
        text=text,
        font_path=font_path,
        font_size=font_size,
        qr_box_size=qr_box_size,
        qr_border=qr_border
    )
    
    if not qr_path or not os.path.exists(qr_path):
        print(f"[WARNING] Не удалось создать QR-код для Telegram")
        return image_path
    
    try:
        # Загружаем изображение
        img = Image.open(image_path).convert("RGB")
        qr_img = Image.open(qr_path).convert("RGBA")
        
        # Определяем область для QR-кода
        if qr_area is None:
            # Автоматическое размещение: справа внизу с отступом
            margin = 50
            qr_area_width = min(500, img.width // 4)
            qr_area_height = min(500, img.height // 4)
            qr_area = (
                img.width - qr_area_width - margin,
                img.height - qr_area_height - margin,
                img.width - margin,
                img.height - margin
            )
        
        # Вычисляем размеры области для QR-кода
        qr_area_width = qr_area[2] - qr_area[0]
        qr_area_height = qr_area[3] - qr_area[1]
        
        # Масштабируем QR-код под область
        qr_ratio = min(qr_area_width / qr_img.width, qr_area_height / qr_img.height)
        qr_resized = qr_img.resize(
            (int(qr_img.width * qr_ratio), int(qr_img.height * qr_ratio)),
            Image.NEAREST
        )
        
        # Вычисляем позицию для центрирования
        qr_x = qr_area[0] + (qr_area_width - qr_resized.width) // 2
        qr_y = qr_area[1] + (qr_area_height - qr_resized.height) // 2
        
        # Вставляем QR-код на изображение
        img.paste(qr_resized, (qr_x, qr_y), qr_resized)
        
        # Сохраняем
        if output_path is None:
            output_path = image_path
        
        img.save(output_path, format='JPEG', quality=95)
        print(f"[INFO] QR-код Telegram вставлен на изображение: {output_path}")
        
        # Удаляем временный файл QR-кода
        try:
            os.remove(qr_path)
        except:
            pass
        
        return output_path
        
    except Exception as e:
        print(f"[ERROR] Ошибка при вставке QR-кода Telegram: {e}")
        import traceback
        traceback.print_exc()
        return image_path

