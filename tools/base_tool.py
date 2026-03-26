"""Базовые классы инструментов"""


class BaseTool:
    """Базовый класс для инструментов редактора."""

    name = "base"
    cursor = "crosshair"

    def __init__(self, editor):
        self.editor = editor

    def activate(self):
        """Включает инструмент."""

    def deactivate(self):
        """Выключает инструмент."""

    def on_mouse_down(self, img_x, img_y):
        """Обрабатывает нажатие кнопки мыши."""
        return False

    def on_mouse_move(self, img_x, img_y):
        """Обрабатывает движение мыши при нажатой кнопке."""
        return False

    def on_mouse_up(self, img_x, img_y):
        """Обрабатывает отпускание кнопки мыши."""
        return False

    def get_cursor(self):
        """Возвращает курсор, который должен использовать инструмент."""
        return self.cursor

