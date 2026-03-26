"""
Утилиты для работы с версией программы
Получает версию из названия проекта (например, slicer_2.6 -> 2.6)
"""
import os
import re
from utils.path_utils import get_base_path


def get_version() -> str:
    """
    Получает версию программы из названия проекта или из setup.py
    
    Returns:
        str: Версия программы (например, "2.25")
    """
    # Сначала пробуем получить версию из setup.py (для скомпилированного приложения)
    try:
        import sys
        if getattr(sys, 'frozen', False):
            # В скомпилированном приложении пробуем прочитать версию из метаданных
            # или используем версию по умолчанию из setup.py
            pass
    except:
        pass
    
    # Получаем текущий путь проекта
    current_dir = get_base_path()
    
    # Ищем версию в названии папки (например, slicer_2.25 -> 2.25)
    folder_name = os.path.basename(current_dir)
    
    # Ищем паттерн _X.Y или _X.Y.Z в названии папки
    match = re.search(r'_(\d+\.\d+(?:\.\d+)?)', folder_name)
    if match:
        return match.group(1)
    
    # Если не найдено, возвращаем версию по умолчанию (синхронизировано с setup.py)
    return "4.13"


def get_app_name_with_version() -> str:
    """
    Возвращает полное название приложения с версией
    
    Returns:
        str: "NexelSoftware - Редактор схемы вышивки v{version}"
    """
    version = get_version()
    return f"NexelSoftware - Редактор схемы вышивки v{version}"

