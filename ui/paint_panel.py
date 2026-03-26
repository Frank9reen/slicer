"""UI блок настроек закрашивания."""
import tkinter as tk


class PaintPanel:
    """Секция панели настроек закрашивания с автозаливкой."""

    def __init__(self, editor, parent_frame):
        self.editor = editor
        self.frame = tk.LabelFrame(
            parent_frame, text="Настройки закрашивания", font=('Arial', 10, 'bold')
        )
        self.frame.pack(fill=tk.X, padx=5, pady=5)

        self._build_auto_paint_section()

    def _build_auto_paint_section(self):
        # Кнопка автозакрашивания перенесена в блок "Настройки фрагментации"
        # Оставляем метод пустым, но не удаляем, чтобы не ломать структуру
        pass

