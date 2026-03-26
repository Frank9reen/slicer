"""Точка входа в приложение"""
# КРИТИЧЕСКИ ВАЖНО: Перенаправление stdout/stderr должно быть ПЕРВЫМ,
# до любых других импортов, чтобы предотвратить открытие консоли
import sys
import os

# Класс для перенаправления stdout/stderr в никуда
class NullWriter:
    def write(self, s):
        pass
    def flush(self):
        pass
    def isatty(self):
        return False
    def close(self):
        pass
    def readable(self):
        return False
    def writable(self):
        return True
    def seekable(self):
        return False
    def fileno(self):
        # Возвращаем фиктивный файловый дескриптор
        return -1

# В скомпилированном GUI приложении (cx_Freeze) перенаправляем stderr и stdout,
# чтобы библиотеки (sklearn, scipy, numpy) не открывали консоль
# Проверяем как sys.frozen, так и наличие cx_Freeze атрибутов
is_frozen = (hasattr(sys, 'frozen') and sys.frozen) or hasattr(sys, '_MEIPASS')

if is_frozen:
    # Сохраняем оригинальные потоки на случай, если понадобятся
    sys._original_stderr = sys.stderr
    sys._original_stdout = sys.stdout
    
    # Перенаправляем в NullWriter
    null_writer = NullWriter()
    sys.stderr = null_writer
    sys.stdout = null_writer
    
    # Также перенаправляем sys.__stderr__ и sys.__stdout__ для полной блокировки
    sys.__stderr__ = null_writer
    sys.__stdout__ = null_writer

# Подавляем все warnings для GUI приложения
import warnings
warnings.filterwarnings('ignore')
# Дополнительно подавляем все warnings на уровне модуля
warnings.simplefilter('ignore')

import tkinter as tk
from grid_editor import GridEditor


def main():
    """Главная функция запуска приложения"""
    root = tk.Tk()
    app = GridEditor(root)
    root.mainloop()


if __name__ == "__main__":
    main()

