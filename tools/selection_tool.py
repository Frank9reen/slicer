"""Инструмент выделения области"""
from tkinter import messagebox

from .base_tool import BaseTool


class SelectionTool(BaseTool):
    """Инструмент для выбора прямоугольной области сетки."""

    name = "selection"
    cursor = "tcross"

    def activate(self):
        editor = self.editor
        editor.selection_mode = True
        if hasattr(editor, "selection_mode_var"):
            editor.selection_mode_var.set(True)
        editor.paint_mode = False
        editor.eyedropper_mode = False
        editor.paint_tool = None
        editor.selection_start = None
        editor.selection_end = None
        editor.selected_regions = []
        editor.info_label.config(
            text="Режим выделения области\nКликните на начальную и конечную ячейки"
        )
        editor.update_tool_buttons()
        editor.update_paint_cursor()

    def deactivate(self):
        editor = self.editor
        editor.selection_mode = False
        if hasattr(editor, "selection_mode_var"):
            editor.selection_mode_var.set(False)
        editor.selection_start = None
        editor.selection_end = None
        editor.selected_regions = []
        editor.update_display()
        editor.info_label.config(text="Режим выбора линий")
        editor.update_tool_buttons()
        editor.update_paint_cursor()

    def on_mouse_down(self, img_x, img_y):
        editor = self.editor
        col, row = editor.get_cell_indices(img_x, img_y)

        if col is None or row is None:
            messagebox.showwarning("Предупреждение", "Клик вне ячейки сетки!")
            return True

        if editor.selection_start is None:
            editor.selection_start = (col, row)
            editor.selection_end = None
            editor.selected_regions = []
            editor.info_label.config(
                text=f"Начальная точка: [{col}, {row}]\nКликните на конечную точку"
            )
        else:
            editor.selection_end = (col, row)
            min_col = min(editor.selection_start[0], editor.selection_end[0])
            max_col = max(editor.selection_start[0], editor.selection_end[0])
            min_row = min(editor.selection_start[1], editor.selection_end[1])
            max_row = max(editor.selection_start[1], editor.selection_end[1])
            editor.selection_start = (min_col, min_row)
            editor.selection_end = (max_col, max_row)
            editor.info_label.config(
                text=(
                    f"Выделена область: [{min_col}, {min_row}] - "
                    f"[{max_col}, {max_row}]\nНажмите 'Залить выделенную область'"
                )
            )

        editor.update_display()
        return True

