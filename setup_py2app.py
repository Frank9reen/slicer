"""
Сборка macOS .app через py2app.

Запускать на macOS:
  python3.11 -m pip install py2app
  python3.11 setup_py2app.py py2app
"""
import os
from setuptools import setup

APP = ["main.py"]
VERSION = "4.17"

INCLUDES = [
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

PACKAGES = [
    "encodings",
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

EXCLUDES = [
    "matplotlib",
    "pytest",
    "unittest",
    "test",
    "tests",
    "setuptools",
    "distutils",
]


def collect_data_files_for_py2app():
    """
    Формат для setuptools data_files:
    [
      ("target/dir", ["source/file1", "source/file2"]),
      ...
    ]
    """
    data_map = {}
    static_dir = "static"

    if not os.path.isdir(static_dir):
        return []

    for root, _, files in os.walk(static_dir):
        if not files:
            continue
        rel = os.path.relpath(root, ".")
        target = rel.replace("\\", "/")
        sources = [os.path.join(root, name) for name in files]
        data_map[target] = sources

    return [(target, sources) for target, sources in data_map.items()]


iconfile = "static/pixel_17431878.icns" if os.path.exists("static/pixel_17431878.icns") else None

OPTIONS = {
    "argv_emulation": False,
    "iconfile": iconfile,
    "includes": INCLUDES,
    "packages": PACKAGES,
    "excludes": EXCLUDES,
    "plist": {
        "CFBundleName": "slicer",
        "CFBundleDisplayName": "slicer",
        "CFBundleIdentifier": "com.local.slicer",
        "CFBundleShortVersionString": VERSION,
        "CFBundleVersion": VERSION,
    },
}

setup(
    app=APP,
    name="slicer",
    version=VERSION,
    description="Slicer Application (macOS py2app build)",
    options={"py2app": OPTIONS},
    data_files=collect_data_files_for_py2app(),
    setup_requires=["py2app"],
)
