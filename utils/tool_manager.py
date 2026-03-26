"""Управление инструментами"""
import tkinter as tk
from tools.selection_tool import SelectionTool


class ToolManager:
    """Управляет активацией и деактивацией инструментов."""
    
    def __init__(self, editor):
        """
        Args:
            editor: Экземпляр GridEditor
        """
        self.editor = editor
    
    def deactivate_active_tool(self):
        """Выключает текущий активный инструмент."""
        if self.editor.active_tool:
            self.editor.active_tool.deactivate()
            self.editor.active_tool = None
    
    def activate_tool(self, tool):
        """Активирует выбранный инструмент"""
        # Убираем фокус с полей ввода, чтобы не печатались буквы
        self.editor.canvas.focus_set()
        
        if tool not in self.editor.tools:
            return
        
        # Сбрасываем состояние рисования
        self.editor.pencil_drawing = False
        self.editor.last_painted_cell = None
        # При переключении инструмента выходим из режима лупы по клику
        if hasattr(self.editor, 'zoom_click_mode'):
            self.editor.zoom_click_mode = None
        
        self.deactivate_active_tool()
        new_tool = self.editor.tools[tool]
        self.editor.active_tool = new_tool
        new_tool.activate()
    
    def update_tool_buttons(self):
        """Обновляет внешний вид кнопок инструментов"""
        # Сбрасываем все кнопки
        for button in self.editor.tool_buttons.values():
            button.config(bg='lightgray', relief=tk.RAISED)
        
        # Выделяем активную кнопку
        if self.editor.active_tool and hasattr(self.editor.active_tool, 'name'):
            tool_name = self.editor.active_tool.name
            if tool_name in self.editor.tool_buttons:
                self.editor.tool_buttons[tool_name].config(bg='lightblue', relief=tk.SUNKEN)
        elif self.editor.eyedropper_mode:
            if 'eyedropper' in self.editor.tool_buttons:
                self.editor.tool_buttons['eyedropper'].config(bg='lightblue', relief=tk.SUNKEN)
        elif self.editor.paint_mode and self.editor.paint_tool:
            if self.editor.paint_tool in self.editor.tool_buttons:
                self.editor.tool_buttons[self.editor.paint_tool].config(bg='lightblue', relief=tk.SUNKEN)
        
        # Обновляем кнопку выделения области
        self.editor.update_selection_button_appearance()
    
    def toggle_selection_mode(self):
        """Переключает режим выделения области"""
        # Убираем фокус с полей ввода
        self.editor.canvas.focus_set()
        
        desired_state = self.editor.selection_mode_var.get()
        if desired_state:
            self.activate_tool('selection')
        else:
            if isinstance(self.editor.active_tool, SelectionTool):
                self.deactivate_active_tool()
            self.editor.selection_mode = False
            self.editor.selection_start = None
            self.editor.selection_end = None
            self.editor.selected_regions = []
            self.editor.update_display()
        
        # Обновляем внешний вид кнопки выделения
        self.editor.update_selection_button_appearance()

