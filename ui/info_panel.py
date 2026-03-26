"""Панель информации"""
import tkinter as tk


class InfoPanel:
    """Инкапсулирует информационную панель."""
    
    def __init__(self, editor, parent_frame):
        """
        Args:
            editor: Экземпляр GridEditor
            parent_frame: Родительский фрейм для размещения панели
        """
        self.editor = editor
        
        # Создаем основной фрейм
        self.frame = tk.LabelFrame(parent_frame, text="Информация", font=('Arial', 10, 'bold'))
        self.frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Информационная метка
        self.editor.info_label = tk.Label(self.frame, text="Откройте изображение", 
                                         wraplength=220, justify=tk.LEFT)
        self.editor.info_label.pack(padx=5, pady=5)

