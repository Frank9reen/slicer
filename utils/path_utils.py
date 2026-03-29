"""
Утилиты для работы с путями в скомпилированном приложении
"""
import os
import sys


def _py2app_resources_dir():
    """Путь к .../MyApp.app/Contents/Resources (py2app)."""
    env = os.environ.get("RESOURCEPATH")
    if env and os.path.isdir(env):
        return env
    # Запасной вариант, если переменная не выставлена
    if getattr(sys, "frozen", None) == "macosx_app" and getattr(sys, "executable", None):
        macos_dir = os.path.dirname(os.path.abspath(sys.executable))
        contents = os.path.dirname(macos_dir)
        resources = os.path.join(contents, "Resources")
        if os.path.isdir(resources):
            return resources
    return None


def get_base_path():
    """
    Возвращает базовый путь к приложению.
    В скомпилированном приложении возвращает путь к папке с exe,
    в исходниках - путь к корню проекта.
    
    Returns:
        str: Базовый путь к приложению
    """
    rp = _py2app_resources_dir()
    if rp:
        return rp

    if getattr(sys, 'frozen', False):
        # Скомпилированное приложение
        # В cx_Freeze sys.executable указывает на exe файл
        # В PyInstaller может быть sys._MEIPASS (временная папка)
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller: базовый путь - папка с exe файлом
            return os.path.dirname(sys.executable)
        else:
            # cx_Freeze: базовый путь - папка с exe файлом
            # sys.argv[0] может быть относительным, используем sys.executable
            if hasattr(sys, 'executable') and sys.executable:
                return os.path.dirname(os.path.abspath(sys.executable))
            else:
                return os.path.dirname(os.path.abspath(sys.argv[0]))
    else:
        # Запуск из исходников
        # Возвращаем путь к корню проекта (на уровень выше utils)
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_resource_path(relative_path):
    """
    Возвращает абсолютный путь к ресурсу.
    Работает как в скомпилированном приложении, так и в исходниках.
    
    Args:
        relative_path: Относительный путь к ресурсу (например, 'static/file.png')
        
    Returns:
        str: Абсолютный путь к ресурсу
    """
    base_path = get_base_path()
    
    if getattr(sys, 'frozen', False):
        # В скомпилированном приложении
        if _py2app_resources_dir():
            return os.path.join(base_path, relative_path)
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller: ресурсы могут быть в _MEIPASS или в папке с exe
            # Проверяем оба варианта
            resource_path = os.path.join(sys._MEIPASS, relative_path)
            if os.path.exists(resource_path):
                return resource_path
            
            # Если не найдено в _MEIPASS, пробуем в папке с exe
            resource_path = os.path.join(base_path, relative_path)
            if os.path.exists(resource_path):
                return resource_path
            
            # Возвращаем путь к _MEIPASS (для файлов, упакованных PyInstaller)
            return os.path.join(sys._MEIPASS, relative_path)
        else:
            # cx_Freeze: ресурсы находятся в папке с exe (включены через include_files)
            return os.path.join(base_path, relative_path)
    else:
        # В исходниках используем базовый путь
        return os.path.join(base_path, relative_path)


def get_module_path(module_file):
    """
    Возвращает путь к папке модуля.
    Работает корректно в скомпилированном приложении.
    
    Args:
        module_file: __file__ из модуля
        
    Returns:
        str: Путь к папке модуля
    """
    if getattr(sys, 'frozen', False):
        # В скомпилированном приложении __file__ может быть в library.zip (cx_Freeze)
        # или указывать на временную папку (PyInstaller)
        module_file_str = str(module_file)
        
        if 'library.zip' in module_file_str:
            # В cx_Freeze модули могут быть в library.zip
            # Извлекаем путь относительно базовой директории
            # Формат: library.zip/export/slicer_utils/module.py
            parts = module_file_str.split('library.zip')
            if len(parts) > 1:
                # Убираем library.zip и получаем относительный путь
                rel_path = parts[1].lstrip('/\\')
                # Получаем директорию модуля
                module_dir = os.path.dirname(rel_path)
                # Комбинируем с базовым путем
                base_path = get_base_path()
                # В cx_Freeze модули находятся в lib/ внутри папки с exe
                lib_path = os.path.join(base_path, 'lib', module_dir)
                if os.path.exists(lib_path):
                    return lib_path
                # Если не найдено, возвращаем базовый путь с относительным путем
                return os.path.join(base_path, module_dir)
        
        # Для PyInstaller или если путь нормальный
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller: модули в _MEIPASS
            return os.path.dirname(os.path.join(sys._MEIPASS, os.path.basename(module_file_str)))
        
        # Fallback: используем базовый путь
        return get_base_path()
    else:
        # В исходном коде просто используем __file__
        return os.path.dirname(os.path.abspath(module_file))


def get_static_path(relative_path):
    """
    Возвращает путь к файлу в папке static.
    
    Args:
        relative_path: Относительный путь внутри static (например, 'fonts/file.ttf')
        
    Returns:
        str: Абсолютный путь к файлу
    """
    return get_resource_path(os.path.join('static', relative_path))
