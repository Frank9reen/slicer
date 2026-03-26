"""Инструмент карандаш"""
from tkinter import messagebox

from .base_tool import BaseTool


class PencilTool(BaseTool):
    """Инструмент для закрашивания ячеек."""

    name = "pencil"
    cursor = "pencil"

    def __init__(self, editor):
        super().__init__(editor)
        self.drawing = False

    def activate(self):
        editor = self.editor
        editor.selection_mode = False
        if hasattr(editor, "selection_mode_var"):
            editor.selection_mode_var.set(False)
        editor.paint_mode = True
        editor.eyedropper_mode = False
        editor.paint_tool = "pencil"
        editor.info_label.config(
            text="Режим: Карандаш\nЗажмите ЛКМ и двигайте мышь для закрашивания"
        )
        editor.update_tool_buttons()
        editor.update_paint_cursor()
        self.drawing = False

    def deactivate(self):
        editor = self.editor
        editor.pencil_drawing = False
        editor.last_painted_cell = None
        editor.state_saved_for_action = False
        self.drawing = False

    def _ensure_grid_ready(self):
        editor = self.editor
        if len(editor.vertical_lines) < 2 or len(editor.horizontal_lines) < 2:
            messagebox.showwarning("Предупреждение", "Сначала постройте сетку!")
            return False
        return True

    def on_mouse_down(self, img_x, img_y):
        editor = self.editor
        if editor.image is None or editor.selected_color is None:
            return False
        if not self._ensure_grid_ready():
            return True
        editor.pencil_drawing = True
        editor.last_painted_cell = None
        editor.state_saved_for_action = False
        self.drawing = True
        editor.paint_cell_at_position(img_x, img_y)
        return True

    def on_mouse_move(self, img_x, img_y):
        editor = self.editor
        if not self.drawing or editor.selected_color is None:
            return False
        editor.paint_cell_at_position(img_x, img_y)
        return True

    def on_mouse_up(self, img_x, img_y):
        if not self.drawing:
            return False
        editor = self.editor
        editor.pencil_drawing = False
        editor.last_painted_cell = None
        editor.state_saved_for_action = False
        self.drawing = False
        # Не обновляем палитру здесь, чтобы избежать зависания (как в slicer_2.5)
        # Палитра будет обновлена при необходимости в других местах
        return True

