"""UI блок для работы с выделенной областью."""
import tkinter as tk


class SelectionPanel:
    """Инкапсулирует элементы управления выделением области.
    Теперь все кнопки перенесены в верхнюю панель (ViewControlPanel).
    Этот класс оставлен для совместимости, но не создает никаких элементов."""

    def __init__(self, editor, parent_frame):
        self.editor = editor
        self.frame = tk.Frame(parent_frame)
        # Не размещаем фрейм - панель теперь пустая
        # Все элементы управления перенесены в ViewControlPanel


