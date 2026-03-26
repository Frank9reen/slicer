"""Утилиты для работы с UI"""
import sys
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import os


class UIUtils:
    """Утилиты для работы с UI компонентами."""
    
    def __init__(self, editor):
        """
        Args:
            editor: Экземпляр GridEditor
        """
        self.editor = editor
    
    @staticmethod
    def get_colors_word_form(count: int) -> str:
        """
        Возвращает правильную форму слова "цвет" в зависимости от количества.
        
        :param count: количество цветов
        :return: правильная форма слова
        """
        if count % 10 == 1 and count % 100 != 11:
            return "цвет"
        elif count % 10 in [2, 3, 4] and count % 100 not in [12, 13, 14]:
            return "цвета"
        else:
            return "цветов"
    
    def create_tooltip(self, widget, text):
        """Создает подсказку для виджета при наведении мыши"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = tk.Label(tooltip, text=text, background='yellow', 
                           font=('Arial', 9), relief=tk.SOLID, borderwidth=1)
            label.pack()
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)
    
    def update_footer_info(self):
        """Обновляет информацию в футере"""
        # Проверяем, что footer_info_label существует
        if not hasattr(self.editor, 'footer_info_label') or self.editor.footer_info_label is None:
            return
        
        # Обновляем информацию о программе
        if self.editor.image:
            image_info = f"{self.editor.image.width}x{self.editor.image.height}px"
            if self.editor.image_path:
                filename = os.path.basename(self.editor.image_path)
                image_info += f" | {filename}"
            if self.editor.vertical_lines or self.editor.horizontal_lines:
                # Количество ячеек = количество линий - 1
                num_cells_v = len(self.editor.vertical_lines) - 1 if len(self.editor.vertical_lines) > 0 else 0
                num_cells_h = len(self.editor.horizontal_lines) - 1 if len(self.editor.horizontal_lines) > 0 else 0
                image_info += f" | Ячеек: V:{num_cells_v} H:{num_cells_h}"
                # Рассчитываем размер в см для канвы Aida 16 (16 клеток на дюйм)
                # 1 дюйм = 2.54 см, значит 1 клетка = 2.54 / 16 = 0.15875 см
                cells_per_cm = 16 / 2.54  # Клеток на см
                if len(self.editor.vertical_lines) > 1 and len(self.editor.horizontal_lines) > 1:
                    # Количество ячеек = количество линий - 1
                    num_cells_width = len(self.editor.vertical_lines) - 1
                    num_cells_height = len(self.editor.horizontal_lines) - 1
                    width_cm = num_cells_width / cells_per_cm
                    height_cm = num_cells_height / cells_per_cm
                    # Получаем количество цветов
                    num_colors = 0
                    if self.editor.palette is not None and len(self.editor.palette) > 0:
                        num_colors = len(self.editor.palette)
                    if num_colors > 0:
                        colors_word = self.get_colors_word_form(num_colors)
                        image_info += f" | Размер {width_cm:.1f}x{height_cm:.1f} см | {num_colors} {colors_word}"
                    else:
                        image_info += f" | Размер {width_cm:.1f}x{height_cm:.1f} см"
                    # Добавляем артикул и название проекта
                    if hasattr(self.editor, 'project_article') and self.editor.project_article:
                        image_info += f" | {self.editor.project_article}"
                    if hasattr(self.editor, 'project_name') and self.editor.project_name:
                        image_info += f" | {self.editor.project_name}"
                else:
                    # Если сетка есть, но размер не рассчитывается, выводим только количество цветов
                    if self.editor.palette is not None and len(self.editor.palette) > 0:
                        num_colors = len(self.editor.palette)
                        colors_word = self.get_colors_word_form(num_colors)
                        image_info += f" | {colors_word.capitalize()} в палитре: {num_colors}"
                    # Добавляем артикул и название проекта
                    if hasattr(self.editor, 'project_article') and self.editor.project_article:
                        image_info += f" | {self.editor.project_article}"
                    if hasattr(self.editor, 'project_name') and self.editor.project_name:
                        image_info += f" | {self.editor.project_name}"
            else:
                # Добавляем информацию о количестве цветов в палитре, если палитра есть, но сетки нет
                if self.editor.palette is not None and len(self.editor.palette) > 0:
                    num_colors = len(self.editor.palette)
                    colors_word = self.get_colors_word_form(num_colors)
                    image_info += f" | {colors_word.capitalize()} в палитре: {num_colors}"
                # Добавляем артикул и название проекта
                if hasattr(self.editor, 'project_article') and self.editor.project_article:
                    image_info += f" | {self.editor.project_article}"
                    if hasattr(self.editor, 'project_name') and self.editor.project_name:
                        image_info += f" | {self.editor.project_name}"
            self.editor.footer_info_label.config(text=image_info)
        else:
            self.editor.footer_info_label.config(text="Загрузите изображение или проект (.slicer)")
        
        # Обновляем информацию о лицензии
        is_valid, message = self.editor.license_manager.check_license()
        
        if is_valid:
            days_left = self.editor.license_manager.get_days_left()
            expiry_date_str = self.editor.license_manager.expiry_date.strftime('%d.%m.%Y')
            license_text = f"Действительна до {expiry_date_str} | Осталось дней: {days_left}"
            self.editor.footer_license_label.config(text=license_text, fg='darkgreen')
        else:
            # Лицензия истекла - закрываем программу
            expiry_date_str = self.editor.license_manager.expiry_date.strftime('%d.%m.%Y')
            messagebox.showerror("NexelSoftware - Срок действия истек", 
                               f"Срок действия программы истек {expiry_date_str}.\n\n"
                               f"{message}\n\n"
                               f"Программа будет закрыта.")
            try:
                self.editor.root.quit()
            except:
                pass
            try:
                self.editor.root.destroy()
            except:
                pass
            sys.exit(0)

