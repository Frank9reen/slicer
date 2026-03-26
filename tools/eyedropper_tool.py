"""Инструмент пипетка"""

from .base_tool import BaseTool


class EyedropperTool(BaseTool):
    """Инструмент выбора цвета из ячейки."""

    name = "eyedropper"
    cursor = "cross"

    def activate(self):
        editor = self.editor
        editor.selection_mode = False
        if hasattr(editor, "selection_mode_var"):
            editor.selection_mode_var.set(False)
        editor.paint_mode = False
        editor.eyedropper_mode = True
        editor.paint_tool = None
        editor.info_label.config(text="Режим: Пипетка\nКликните на ячейку для выбора цвета")
        editor.update_tool_buttons()
        editor.update_paint_cursor()

    def deactivate(self):
        editor = self.editor
        editor.eyedropper_mode = False
        editor.update_tool_buttons()
        editor.update_paint_cursor()

    def on_mouse_down(self, img_x, img_y):
        editor = self.editor
        if editor.image is None:
            return False
        editor.pick_color_from_cell(img_x, img_y)
        return True

