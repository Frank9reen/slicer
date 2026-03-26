"""Менеджер работы с файлами изображений"""
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
from utils.version_utils import get_app_name_with_version


class ImageFileManager:
    """Управляет операциями открытия, сохранения и кадрирования изображений."""
    
    def __init__(self, editor):
        """
        Args:
            editor: Экземпляр GridEditor
        """
        self.editor = editor
    
    def open_image(self):
        """Открывает диалог выбора и загружает изображение"""
        file_path = filedialog.askopenfilename(
            title="Выберите изображение",
            filetypes=[("Изображения", "*.png *.jpg *.jpeg *.bmp *.gif"), ("Все файлы", "*.*")]
        )
        
        if file_path:
            try:
                self.editor.image_path = file_path
                # Используем image_processor для загрузки изображения
                self.editor.image = self.editor.image_processor.load_image(file_path)
                
                self.editor.original_image = self.editor.image.copy()  # Сохраняем оригинальное изображение
                self.editor.display_image = self.editor.image.copy()
                self.editor.vertical_lines = []
                self.editor.horizontal_lines = []
                self.editor.selected_line = None
                self.editor.fragmented_image = None  # Сбрасываем фрагментированное изображение
                self.editor.palette = None  # Сбрасываем палитру
                self.editor.selected_color = None  # Сбрасываем выбранный цвет
                self.editor.painted_cells = {}  # Сбрасываем закрашенные ячейки
                self.editor.current_project_path = None  # Сбрасываем путь к проекту
                self.editor.undo_history = []  # Сбрасываем историю отмены
                self.editor.redo_history = []  # Сбрасываем историю повтора
                self.editor.state_saved_for_action = False  # Сбрасываем флаг
                # Разблокируем сетку при открытии нового изображения
                if hasattr(self.editor, 'grid_locked'):
                    self.editor.grid_locked = False
                    # Включаем кнопки управления сеткой
                    if hasattr(self.editor, 'grid_panel'):
                        self.editor.grid_panel.enable_grid_controls()
                # Сбрасываем зум и панорамирование
                self.editor.zoom = 1.0
                self.editor.pan_x = 0
                self.editor.pan_y = 0
                # Очищаем палитру
                for widget in self.editor.palette_frame.winfo_children():
                    widget.destroy()
                self.editor.palette_canvas = None
                # Устанавливаем режим просмотра 2
                self.editor.set_view_mode(2)
                self.editor.info_label.config(text=f"Изображение: {os.path.basename(file_path)}\n"
                                                   f"Размер: {self.editor.image.width}x{self.editor.image.height}")
                # Обновляем информацию в футере
                self.editor.update_footer_info()
                # Обновляем отображение (это также скроет фрейм с кнопками и покажет canvas)
                self.editor.update_display()
                # Принудительно обновляем интерфейс, чтобы изменения отобразились сразу
                self.editor.root.update_idletasks()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось открыть изображение:\n{str(e)}")
    
    def save_image(self):
        """Сохраняет изображение с сеткой"""
        if self.editor.image is None:
            messagebox.showwarning("Предупреждение", "Нет изображения для сохранения")
            return
        
        # Проверяем наличие линий сетки
        if not self.editor.vertical_lines and not self.editor.horizontal_lines:
            messagebox.showwarning("Предупреждение", "Нет линий для сохранения")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Сохранить изображение с сеткой",
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("Все файлы", "*.*")]
        )
        
        if file_path:
            try:
                # Используем фрагментированное изображение, если оно есть, иначе оригинальное
                if self.editor.fragmented_image is not None:
                    base_image = self.editor.fragmented_image
                else:
                    base_image = self.editor.original_image if self.editor.original_image is not None else self.editor.image
                
                self.editor.image_processor.save_image_with_grid(
                    base_image, 
                    self.editor.vertical_lines, 
                    self.editor.horizontal_lines, 
                    file_path,
                    grid_color_vertical=self.editor.grid_color,
                    grid_color_horizontal=self.editor.grid_color_horizontal,
                    grid_width=self.editor.grid_line_width,
                    painted_cells=self.editor.painted_cells if hasattr(self.editor, 'painted_cells') else None
                )
                app_name = get_app_name_with_version()
                self._show_save_success_with_path(f"Успех - {app_name}", "Изображение сохранено:", file_path)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить изображение:\n{str(e)}")
    
    def _show_save_success_with_path(self, title, message, file_path):
        """Показывает диалог об успешном сохранении с кликабельной ссылкой на папку (как в органайзере)."""
        win = tk.Toplevel(self.editor.root)
        win.title(title)
        win.transient(self.editor.root)
        win.grab_set()
        frame = tk.Frame(win, padx=15, pady=12)
        frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(frame, text=message, font=('Arial', 10)).pack(anchor=tk.W)
        path_to_open = os.path.dirname(file_path)
        if path_to_open and os.path.exists(path_to_open):
            path_text = f"Открыть папку с файлом:\n{file_path}"
            path_label = tk.Label(
                frame, text=path_text,
                font=('Arial', 9), fg='blue', cursor='hand2',
                wraplength=450, justify=tk.LEFT
            )
            path_label.pack(anchor=tk.W, pady=(8, 0))

            def open_explorer(event):
                try:
                    normalized = os.path.normpath(path_to_open)
                    if sys.platform == 'win32':
                        os.startfile(normalized)
                    else:
                        import subprocess
                        subprocess.Popen(['open', normalized] if sys.platform == 'darwin' else ['xdg-open', normalized])
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось открыть папку:\n{str(e)}")

            path_label.bind('<Button-1>', open_explorer)
            path_label.bind('<Enter>', lambda e: path_label.config(font=('Arial', 9, 'underline')))
            path_label.bind('<Leave>', lambda e: path_label.config(font=('Arial', 9)))
        else:
            tk.Label(frame, text=file_path, font=('Arial', 9), wraplength=450, justify=tk.LEFT).pack(anchor=tk.W, pady=(8, 0))
        tk.Button(frame, text="OK", command=win.destroy, width=10).pack(pady=(12, 0))
        win.update_idletasks()
        # Центрируем диалог по середине главного окна
        rx = self.editor.root.winfo_rootx()
        ry = self.editor.root.winfo_rooty()
        rw = self.editor.root.winfo_width()
        rh = self.editor.root.winfo_height()
        dw = win.winfo_reqwidth()
        dh = win.winfo_reqheight()
        x = rx + (rw - dw) // 2
        y = ry + (rh - dh) // 2
        win.geometry(f"+{max(0, x)}+{max(0, y)}")
        win.wait_window()

    def save_image_without_grid(self):
        """Сохраняет изображение без сетки (пикселированное/фрагментированное)"""
        if self.editor.image is None:
            messagebox.showwarning("Предупреждение", "Нет изображения для сохранения")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Сохранить изображение без сетки",
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("Все файлы", "*.*")]
        )
        
        if file_path:
            try:
                # Приоритет: фрагментированное изображение (пикселированное)
                if self.editor.fragmented_image is not None:
                    image_to_save = self.editor.fragmented_image
                else:
                    # Если фрагментированного изображения нет, но есть закрашенные ячейки,
                    # создаем изображение на основе закрашенных ячеек
                    if hasattr(self.editor, 'painted_cells') and self.editor.painted_cells:
                        # Создаем изображение из закрашенных ячеек
                        image_to_save = self._create_image_from_painted_cells()
                    else:
                        # Если нет ни фрагментированного, ни закрашенных ячеек, используем оригинальное
                        image_to_save = self.editor.original_image if self.editor.original_image is not None else self.editor.image
                
                self.editor.image_processor.save_image(image_to_save, file_path)
                app_name = get_app_name_with_version()
                self._show_save_success_with_path(f"Успех - {app_name}", "Изображение без сетки сохранено:", file_path)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить изображение:\n{str(e)}")
    
    def _create_image_from_painted_cells(self):
        """Создает изображение на основе закрашенных ячеек"""
        from PIL import Image, ImageDraw
        
        if not self.editor.vertical_lines or not self.editor.horizontal_lines:
            return self.editor.original_image if self.editor.original_image is not None else self.editor.image
        
        # Получаем размеры изображения
        if self.editor.original_image is not None:
            width = self.editor.original_image.width
            height = self.editor.original_image.height
        else:
            width = self.editor.image.width
            height = self.editor.image.height
        
        # Создаем новое изображение с цветом подложки
        bg_color_rgb = self.editor.get_background_color_rgb()
        image = Image.new('RGB', (width, height), bg_color_rgb)
        draw = ImageDraw.Draw(image)
        
        # Рисуем закрашенные ячейки
        for (col, row), color in self.editor.painted_cells.items():
            if 0 <= col < len(self.editor.vertical_lines) - 1 and 0 <= row < len(self.editor.horizontal_lines) - 1:
                x1 = self.editor.vertical_lines[col]
                x2 = self.editor.vertical_lines[col + 1]
                y1 = self.editor.horizontal_lines[row]
                y2 = self.editor.horizontal_lines[row + 1]
                
                # Убеждаемся, что координаты в пределах изображения
                x1 = max(0, min(x1, width))
                x2 = max(0, min(x2, width))
                y1 = max(0, min(y1, height))
                y2 = max(0, min(y2, height))
                
                if x2 > x1 and y2 > y1:
                    draw.rectangle([x1, y1, x2-1, y2-1], fill=color, outline=None)
        
        return image
    
    def crop_image(self):
        """Открывает диалог кадрирования изображения"""
        if self.editor.image is None:
            messagebox.showwarning("Предупреждение", "Сначала загрузите изображение")
            return
        
        # Используем image_processor для кадрирования
        # Но UI для выбора области оставляем в grid_editor.py
        # Здесь только логика кадрирования
        pass  # Пока оставляем в grid_editor.py, так как там сложный UI

