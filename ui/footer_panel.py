"""Панель футера приложения"""
import tkinter as tk


class FooterPanel:
    """Инкапсулирует футер с информацией о программе и лицензии."""
    
    def __init__(self, editor, root):
        """
        Args:
            editor: Экземпляр GridEditor
            root: Корневое окно Tkinter
        """
        self.editor = editor
        
        # Футер с информацией внизу окна (упаковываем первым, чтобы был всегда виден)
        self.frame = tk.Frame(root, bg='lightgray', height=25)
        self.frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.frame.pack_propagate(False)
        
        # Левая часть футера - информация о программе
        footer_left = tk.Frame(self.frame, bg='lightgray')
        footer_left.pack(side=tk.LEFT, padx=10, pady=3)
        
        self.editor.footer_info_label = tk.Label(footer_left, text="Загрузите изображение или проект (.slicer)", 
                                                 font=('Arial', 9), bg='lightgray', fg='black')
        self.editor.footer_info_label.pack(side=tk.LEFT, padx=5)
        
        # Правая часть футера - информация о лицензии и статусе
        footer_right = tk.Frame(self.frame, bg='lightgray')
        footer_right.pack(side=tk.RIGHT, padx=10, pady=3)
        
        self.editor.footer_license_label = tk.Label(footer_right, text="", 
                                                    font=('Arial', 9), bg='lightgray', fg='darkgreen')
        self.editor.footer_license_label.pack(side=tk.RIGHT, padx=5)

