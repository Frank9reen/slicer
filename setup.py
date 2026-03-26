"""
Setup script для сборки приложения с помощью cx_Freeze
"""
import sys
import os
from cx_Freeze import setup, Executable

# Версия: используется в setup() и в имени папки сборки build/slicer_<version>
VERSION = '4.17'

# Список скрытых импортов, которые нужно включить явно
includes = [
    'export',
    'export.slicer_utils',
    'export.slicer_utils.color_layout_25',
    'export.slicer_utils.create_a5_main_from_image',
    'export.slicer_utils.create_a5_with_crosses',
    'export.slicer_utils.create_a4_jpg_from_pdf',
    'export.slicer_utils.config',
    'export.file_creator',
    'export.config_dialog',
    'utils.logger',
    'PIL._imaging',
    'PIL._imagingtk',
    'PIL._webp',
    'PIL._avif',
    'PIL._imagingcms',
    'PIL._imagingft',
    'PIL._imagingmath',
    'PIL._imagingmorph',
    'scipy',
    'sklearn',
    'skimage',
    'cv2',
    'numpy',
    'pandas',
    'openpyxl',
    'reportlab',
    'PyPDF2',
    'piexif',
    'pymupdf',
    'fitz',
    'pdf2image',
    'qrcode',
]

# Пакеты для включения
packages = [
    'encodings',  # Критически важно для работы Python
    'encodings.utf_8',
    'encodings.latin_1',
    'encodings.ascii',
    'collections',
    'importlib',
    'io',
    'PIL',
    'numpy',
    'pandas',
    'openpyxl',
    'scipy',
    'sklearn',
    'skimage',
    'cv2',
    'reportlab',
    'PyPDF2',
    'piexif',
    'pymupdf',
    'fitz',
    'pdf2image',
    'qrcode',
    'tkinter',
    'color',
    'core',
    'export',
    'ui',
    'tools',
    'utils',
    'project',
]

# Исключения
excludes = [
    'matplotlib',
    'pytest',
    'unittest',
    'test',
    'tests',
    'setuptools',
    'distutils',
]

# Данные для включения в сборку
def collect_data_files():
    """Собирает все файлы из директории static"""
    data_files = []
    
    # Добавляем файлы из static
    static_path = 'static'
    if os.path.exists(static_path):
        for root, dirs, files in os.walk(static_path):
            for file in files:
                source_path = os.path.join(root, file)
                if os.path.isfile(source_path):
                    # Сохраняем структуру папок относительно static
                    rel_path = os.path.relpath(root, 'static')
                    if rel_path == '.':
                        target_path = f'static/{file}'
                    else:
                        target_path = f'static/{rel_path}/{file}'
                    data_files.append((source_path, target_path))
    
    return data_files

# Опции сборки (папка сборки: build/slicer_<version>)
build_exe_options = {
    'build_exe': f'build/slicer_{VERSION}',
    'packages': packages,
    'includes': includes,
    'excludes': excludes,
    'include_files': collect_data_files(),
    'optimize': 0,
    'zip_include_packages': ['encodings', 'importlib'],  # Включаем в zip для правильной работы
    'zip_exclude_packages': [],  # Не исключаем стандартную библиотеку
}

# Настройки для Windows
base = None
if sys.platform == 'win32':
    base = 'Win32GUI'  # Для GUI приложения без консоли

# Точка входа
executables = [
    Executable(
        'main.py',
        base=base,
        target_name='slicer.exe',
        icon='static/pixel_17431878.ico' if os.path.exists('static/pixel_17431878.ico') else None,
    )
]

setup(
    name='slicer',
    version=VERSION,
    description='Slicer Application',
    author='',
    options={'build_exe': build_exe_options},
    executables=executables,
)

