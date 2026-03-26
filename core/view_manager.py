"""Управление режимами просмотра"""
import tkinter as tk


class ViewManager:
    """Управляет режимами просмотра изображения."""
    
    def __init__(self, editor):
        """
        Args:
            editor: Экземпляр GridEditor
        """
        self.editor = editor
    
    def set_view_mode(self, mode):
        """Устанавливает режим просмотра"""
        self.editor.view_mode = mode
        mode_names = {1: "Сетка и исходное", 2: "Сетка, исходное и закрашенные", 3: "Только закрашенные", 4: "Два окна (текущее + исходное)"}
        self.editor.info_label.config(text=f"Режим просмотра: {mode_names[mode]}")
        
        # Обновляем внешний вид кнопок
        for i, button in enumerate(self.editor.view_mode_buttons, start=1):
            if i == mode:
                button.config(bg='lightblue', relief=tk.SUNKEN)
            else:
                button.config(bg='lightgray', relief=tk.RAISED)
        
        # Для режима 4 создаем/показываем второй canvas
        if mode == 4:
            self.editor._setup_dual_view()
        else:
            self.editor._setup_single_view()
        
        self.editor.update_display()

