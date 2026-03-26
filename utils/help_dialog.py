"""Диалог справки"""
import tkinter as tk
from .help_text import get_help_text


class HelpDialog:
    """Утилита для отображения диалога справки."""
    
    def __init__(self, editor):
        """
        Args:
            editor: Экземпляр GridEditor
        """
        self.editor = editor
    
    def show_instructions(self):
        """Показывает инструкции по управлению в отдельном окне с прокруткой"""
        instructions = get_help_text()
        
        # Создаем отдельное окно для справки
        help_window = tk.Toplevel(self.editor.root)
        help_window.title("Справка - NexelSoftware")
        help_window.geometry("700x600")
        help_window.resizable(True, True)
        
        # Создаем текстовое поле с прокруткой
        text_frame = tk.Frame(help_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set,
                             font=('Arial', 10), padx=10, pady=10)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_widget.yview)
        
        # Вставляем текст справки
        text_widget.insert('1.0', instructions)
        text_widget.config(state=tk.DISABLED)  # Делаем текст только для чтения
        
        # Кнопка закрытия
        button_frame = tk.Frame(help_window)
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="Закрыть", command=help_window.destroy,
                 font=('Arial', 10), bg='lightgray', width=15).pack()

