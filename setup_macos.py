"""
Setup script для сборки приложения на macOS с помощью cx_Freeze.

Примеры запуска:
  python setup_macos.py build_exe
  python setup_macos.py bdist_mac
"""
import os
from cx_Freeze import setup, Executable

# Версия: используется в setup() и в имени папки сборки build/slicer_<version>_macos
VERSION = "4.17"

# Список скрытых импортов, которые нужно включить явно
includes = [
    "export",
    "export.slicer_utils",
    "export.slicer_utils.color_layout_25",
    "export.slicer_utils.create_a5_main_from_image",
    "export.slicer_utils.create_a5_with_crosses",
    "export.slicer_utils.create_a4_jpg_from_pdf",
    "export.slicer_utils.config",
    "export.file_creator",
    "export.config_dialog",
    "utils.logger",
    "PIL._imaging",
    "PIL._imagingtk",
    "PIL._webp",
    "PIL._avif",
    "PIL._imagingcms",
    "PIL._imagingft",
    "PIL._imagingmath",
    "PIL._imagingmorph",
    "scipy",
    "sklearn",
    "skimage",
    "cv2",
    "numpy",
    "pandas",
    "openpyxl",
    "reportlab",
    "PyPDF2",
    "piexif",
    "pymupdf",
    "fitz",
    "pdf2image",
    "qrcode",
]

# Пакеты для включения
packages = [
    "encodings",
    "encodings.utf_8",
    "encodings.latin_1",
    "encodings.ascii",
    "collections",
    "importlib",
    "io",
    "PIL",
    "numpy",
    "pandas",
    "openpyxl",
    "scipy",
    "sklearn",
    "skimage",
    "cv2",
    "reportlab",
    "PyPDF2",
    "piexif",
    "pymupdf",
    "fitz",
    "pdf2image",
    "qrcode",
    "tkinter",
    "color",
    "core",
    "export",
    "ui",
    "tools",
    "utils",
    "project",
]

# Исключения
excludes = [
    "matplotlib",
    "pytest",
    "unittest",
    "test",
    "tests",
    "setuptools",
    "distutils",
]


def collect_data_files():
    """Собирает все файлы из директории static."""
    data_files = []
    static_path = "static"

    if os.path.exists(static_path):
        for root, _, files in os.walk(static_path):
            for file in files:
                source_path = os.path.join(root, file)
                if os.path.isfile(source_path):
                    rel_path = os.path.relpath(root, "static")
                    if rel_path == ".":
                        target_path = f"static/{file}"
                    else:
                        target_path = f"static/{rel_path}/{file}"
                    data_files.append((source_path, target_path))

    return data_files


build_exe_options = {
    "build_exe": f"build/slicer_{VERSION}_macos",
    "packages": packages,
    "includes": includes,
    "excludes": excludes,
    "include_files": collect_data_files(),
    "optimize": 0,
    "zip_include_packages": ["encodings", "importlib"],
    "zip_exclude_packages": [],
}

# Опции упаковки .app для macOS
bdist_mac_options = {
    "bundle_name": "slicer",
    "iconfile": "static/pixel_17431878.icns" if os.path.exists("static/pixel_17431878.icns") else None,
}

executables = [
    Executable(
        "main.py",
        base=None,
        target_name="slicer",
    )
]

setup(
    name="slicer",
    version=VERSION,
    description="Slicer Application (macOS build)",
    author="",
    options={
        "build_exe": build_exe_options,
        "bdist_mac": bdist_mac_options,
    },
    executables=executables,
)
