"""Панель управления изображением"""
import tkinter as tk


class ImageControlPanel:
    """Инкапсулирует элементы управления изображением (открытие, сохранение, цвет подложки)."""
    
    def __init__(self, editor, parent_frame):
        """
        Args:
            editor: Экземпляр GridEditor
            parent_frame: Родительский фрейм для размещения панели
        """
        self.editor = editor
        
        # Создаем основной фрейм
        self.frame = tk.Frame(parent_frame)
        self.frame.pack(pady=5, padx=5, anchor=tk.W)
        
        # Иконка папки для открытия изображения
        folder_button = tk.Button(self.frame, text="📁", command=self.editor.open_image,
                                 font=('Arial', 16), bg='lightgray', width=3, height=1,
                                 relief=tk.RAISED, bd=2, cursor='hand2')
        folder_button.pack(side=tk.LEFT, padx=2)
        self.editor.create_tooltip(folder_button, "Открыть изображение")
        
        # Иконка сохранения изображения (с сеткой)
        save_button = tk.Button(self.frame, text="💾", command=self.editor.save_image,
                               font=('Arial', 16), bg='lightgray', width=3, height=1,
                               relief=tk.RAISED, bd=2, cursor='hand2')
        save_button.pack(side=tk.LEFT, padx=2)
        self.editor.create_tooltip(save_button, "Сохранить изображение с сеткой")
        
        # Иконка сохранения изображения без сетки
        save_no_grid_button = tk.Button(self.frame, text="📷", command=self.editor.save_image_without_grid,
                                       font=('Arial', 16), bg='lightgray', width=3, height=1,
                                       relief=tk.RAISED, bd=2, cursor='hand2')
        save_no_grid_button.pack(side=tk.LEFT, padx=2)
        self.editor.create_tooltip(save_no_grid_button, "Сохранить изображение без сетки")

