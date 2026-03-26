"""
Модуль для логирования ошибок приложения
"""
import os
import sys
import logging
from datetime import datetime
from pathlib import Path


def setup_logger(log_file_name="slicer_errors.log"):
    """
    Настраивает логгер для записи ошибок в файл
    
    Args:
        log_file_name: Имя файла лога
        
    Returns:
        logging.Logger: Настроенный логгер
    """
    # Определяем путь к файлу лога
    from utils.path_utils import get_base_path
    base_path = get_base_path()
    log_path = os.path.join(base_path, log_file_name)
    
    # Создаем логгер
    logger = logging.getLogger('slicer')
    logger.setLevel(logging.DEBUG)
    
    # Проверяем, был ли логгер уже настроен
    has_file_handler = any(isinstance(h, logging.FileHandler) for h in logger.handlers)
    
    # Удаляем существующие обработчики только если их нет или они не файловые
    # Это предотвращает дублирование обработчиков
    if not has_file_handler:
        logger.handlers.clear()
    
    # Создаем форматтер
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Обработчик для файла (только если его еще нет)
    if not has_file_handler:
        try:
            file_handler = logging.FileHandler(log_path, encoding='utf-8', mode='a')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
            # Логируем информацию о запуске только при первом создании файлового обработчика
            # и только если приложение скомпилировано (чтобы не открывать консоль)
            if hasattr(sys, 'frozen') and sys.frozen:
                logger.info("=" * 80)
                logger.info(f"Запуск приложения: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"Python версия: {sys.version}")
                logger.info(f"Путь к Python: {sys.executable}")
                logger.info(f"Аргументы командной строки: {sys.argv}")
                logger.info(f"Приложение скомпилировано: {sys.frozen}")
                if hasattr(sys, '_MEIPASS'):
                    logger.info(f"Временная папка PyInstaller: {sys._MEIPASS}")
                logger.info(f"Путь к файлу лога: {log_path}")
                logger.info("=" * 80)
        except Exception as e:
            # Если не удалось создать файловый обработчик, не создаем обработчик для stderr
            # чтобы не открывать консоль в GUI приложении
            # Просто пропускаем создание файлового обработчика
            pass
    
    # Обработчик для консоли (только для ошибок)
    # В скомпилированном GUI приложении НИКОГДА не добавляем консольный обработчик,
    # чтобы не открывать окно PowerShell
    if not (hasattr(sys, 'frozen') and sys.frozen):
        # Только в режиме разработки добавляем консольный обработчик
        # Проверяем, нет ли уже консольного обработчика
        has_console_handler = any(isinstance(h, logging.StreamHandler) and h.stream == sys.stderr for h in logger.handlers)
        if not has_console_handler:
            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setLevel(logging.ERROR)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
    
    return logger


def log_exception(logger, exc_type, exc_value, exc_traceback):
    """
    Логирует необработанное исключение
    
    Args:
        logger: Экземпляр логгера
        exc_type: Тип исключения
        exc_value: Значение исключения
        exc_traceback: Трассировка стека
    """
    if exc_type is KeyboardInterrupt:
        # Не логируем прерывание пользователем
        return
    
    logger.critical(
        "Необработанное исключение",
        exc_info=(exc_type, exc_value, exc_traceback)
    )

