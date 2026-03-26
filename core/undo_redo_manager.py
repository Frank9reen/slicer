"""Управление undo/redo операциями"""
from tkinter import messagebox
import numpy as np


class UndoRedoManager:
    """Управляет операциями отмены и повтора действий."""
    
    def __init__(self, editor):
        """
        Args:
            editor: Экземпляр GridEditor
        """
        self.editor = editor
    
    def save_state(self):
        """Сохраняет текущее состояние для отмены (включая палитру)"""
        if self.editor.image is None:
            return
        
        # Используем state_manager для сохранения состояния
        self.editor.state_manager.save_state(
            self.editor.image,
            self.editor.painted_cells,
            self.editor.vertical_lines,
            self.editor.horizontal_lines,
            self.editor.palette
        )
        
        # Обновляем состояние кнопок отмены/возврата
        self.editor.update_undo_redo_buttons()
    
    def undo_last_action(self, event=None):
        """Отменяет последнее действие (включая палитру)"""
        if not self.editor.state_manager.can_undo():
            self.editor.info_label.config(text="Нет действий для отмены")
            return
        
        # Используем state_manager для отмены
        previous_state = self.editor.state_manager.undo(
            self.editor.image,
            self.editor.painted_cells,
            self.editor.vertical_lines,
            self.editor.horizontal_lines,
            self.editor.palette
        )
        
        if previous_state:
            self.editor.image = previous_state['image']
            self.editor.painted_cells = previous_state['painted_cells']
            
            # Восстанавливаем линии сетки
            if 'vertical_lines' in previous_state:
                self.editor.vertical_lines = previous_state['vertical_lines']
                self.editor.grid_manager.vertical_lines = self.editor.vertical_lines
            if 'horizontal_lines' in previous_state:
                self.editor.horizontal_lines = previous_state['horizontal_lines']
                self.editor.grid_manager.horizontal_lines = self.editor.horizontal_lines
            
            # Восстанавливаем палитру в предыдущее состояние
            if 'palette' in previous_state:
                self.editor.palette = np.copy(previous_state['palette'])
                if hasattr(self.editor, 'palette_manager'):
                    self.editor.palette_manager.set_palette(self.editor.palette)
            
            # Обновляем отображение и палитру
            self.editor.update_display()
            if hasattr(self.editor, 'display_palette') and self.editor.palette is not None:
                self.editor.display_palette()
            self.editor.info_label.config(text="Последнее действие отменено")
            
            # Сбрасываем фрагментированное изображение
            self.editor.fragmented_image = None
    
    def redo_last_action(self, event=None):
        """Повторяет последнее отмененное действие (включая палитру)"""
        if not self.editor.state_manager.can_redo():
            self.editor.info_label.config(text="Нет действий для повтора")
            return
        
        # Используем state_manager для повтора
        next_state = self.editor.state_manager.redo(
            self.editor.image,
            self.editor.painted_cells,
            self.editor.vertical_lines,
            self.editor.horizontal_lines,
            self.editor.palette
        )
        
        if next_state:
            self.editor.image = next_state['image']
            self.editor.painted_cells = next_state['painted_cells']
            
            # Восстанавливаем линии сетки
            if 'vertical_lines' in next_state:
                self.editor.vertical_lines = next_state['vertical_lines']
                self.editor.grid_manager.vertical_lines = self.editor.vertical_lines
            if 'horizontal_lines' in next_state:
                self.editor.horizontal_lines = next_state['horizontal_lines']
                self.editor.grid_manager.horizontal_lines = self.editor.horizontal_lines
            
            # Восстанавливаем палитру в состояние после повтора
            if 'palette' in next_state:
                self.editor.palette = np.copy(next_state['palette'])
                if hasattr(self.editor, 'palette_manager'):
                    self.editor.palette_manager.set_palette(self.editor.palette)
            
            # Обновляем отображение и палитру
            self.editor.update_display()
            if hasattr(self.editor, 'display_palette') and self.editor.palette is not None:
                self.editor.display_palette()
            self.editor.info_label.config(text="Последнее действие повторено")
            
            # Сбрасываем фрагментированное изображение
            self.editor.fragmented_image = None

