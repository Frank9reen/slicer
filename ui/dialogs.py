"""UI-диалоги для работы с изображениями"""
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from PIL import Image, ImageTk
from utils.version_utils import get_app_name_with_version


class ImageDialogs:
    """Класс для управления UI-диалогами работы с изображениями."""
    
    def __init__(self, editor):
        """
        Args:
            editor: Экземпляр GridEditor
        """
        self.editor = editor
    
    def crop_image(self):
        """Открывает диалог кадрирования изображения"""
        if self.editor.image is None:
            messagebox.showwarning("Предупреждение", "Сначала загрузите изображение")
            return
        
        # Создаем окно для кадрирования
        crop_window = tk.Toplevel(self.editor.root)
        crop_window.title("Кадрирование изображения")
        crop_window.geometry("800x600")
        
        # Переменные для выделения
        crop_start_x = None
        crop_start_y = None
        crop_end_x = None
        crop_end_y = None
        crop_rect = None
        
        # Загружаем изображение для отображения
        display_img = self.editor.image.copy()
        # Масштабируем для отображения, если изображение слишком большое
        max_display_size = 700
        scale = 1.0
        if display_img.width > max_display_size or display_img.height > max_display_size:
            scale = min(max_display_size / display_img.width, max_display_size / display_img.height)
            new_width = int(display_img.width * scale)
            new_height = int(display_img.height * scale)
            display_img = display_img.resize((new_width, new_height), Image.Resampling.NEAREST)
        
        # Конвертируем в PhotoImage
        photo = ImageTk.PhotoImage(display_img)
        
        # Инструкция
        instruction_label = tk.Label(crop_window, 
                                    text="Нажмите и перетащите мышь, чтобы выбрать область для кадрирования",
                                    font=('Arial', 10))
        instruction_label.pack(pady=5)
        
        # Canvas для отображения изображения
        canvas = tk.Canvas(crop_window, width=display_img.width, height=display_img.height, 
                          cursor="crosshair", bg='gray')
        canvas.pack(padx=10, pady=10)
        canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        canvas.image = photo  # Сохраняем ссылку
        
        # Функция начала выделения
        def start_crop(event):
            nonlocal crop_start_x, crop_start_y, crop_rect
            crop_start_x = event.x
            crop_start_y = event.y
            if crop_rect:
                canvas.delete(crop_rect)
        
        # Функция обновления выделения
        def update_crop(event):
            nonlocal crop_end_x, crop_end_y, crop_rect
            if crop_start_x is None or crop_start_y is None:
                return
            crop_end_x = event.x
            crop_end_y = event.y
            
            # Удаляем предыдущий прямоугольник
            if crop_rect:
                canvas.delete(crop_rect)
            
            # Рисуем новый прямоугольник
            x1 = min(crop_start_x, crop_end_x)
            y1 = min(crop_start_y, crop_end_y)
            x2 = max(crop_start_x, crop_end_x)
            y2 = max(crop_start_y, crop_end_y)
            
            crop_rect = canvas.create_rectangle(x1, y1, x2, y2, outline='red', width=2)
        
        # Функция завершения выделения
        def end_crop(event):
            nonlocal crop_end_x, crop_end_y
            if crop_start_x is None or crop_start_y is None:
                return
            crop_end_x = event.x
            crop_end_y = event.y
        
        # Привязываем события
        canvas.bind("<Button-1>", start_crop)
        canvas.bind("<B1-Motion>", update_crop)
        canvas.bind("<ButtonRelease-1>", end_crop)
        
        # Функция применения кадрирования
        def apply_crop():
            if crop_start_x is None or crop_end_x is None:
                messagebox.showwarning("Предупреждение", "Выберите область для кадрирования")
                return
            
            # Преобразуем координаты обратно в координаты оригинального изображения
            x1 = int(min(crop_start_x, crop_end_x) / scale)
            y1 = int(min(crop_start_y, crop_end_y) / scale)
            x2 = int(max(crop_start_x, crop_end_x) / scale)
            y2 = int(max(crop_start_y, crop_end_y) / scale)
            
            # Ограничиваем координаты размерами изображения
            x1 = max(0, min(x1, self.editor.image.width))
            y1 = max(0, min(y1, self.editor.image.height))
            x2 = max(0, min(x2, self.editor.image.width))
            y2 = max(0, min(y2, self.editor.image.height))
            
            # Проверяем, что выделена область
            if x1 == x2 or y1 == y2:
                messagebox.showwarning("Предупреждение", "Выберите область с ненулевой площадью")
                return
            
            # Кадрируем изображение
            try:
                cropped = self.editor.image.crop((x1, y1, x2, y2))
                self.editor.image = cropped
                self.editor.original_image = cropped.copy()
                self.editor.display_image = cropped.copy()
                
                # Сбрасываем линии и другие данные
                self.editor.vertical_lines = []
                self.editor.horizontal_lines = []
                self.editor.selected_line = None
                self.editor.fragmented_image = None
                self.editor.palette = None
                self.editor.selected_color = None
                self.editor.painted_cells = {}
                self.editor.view_mode = 1
                self.editor.undo_history = []
                self.editor.redo_history = []
                self.editor.state_saved_for_action = False
                self.editor.zoom = 1.0
                self.editor.pan_x = 0
                self.editor.pan_y = 0
                
                # Очищаем палитру
                for widget in self.editor.palette_frame.winfo_children():
                    widget.destroy()
                self.editor.palette_canvas = None
                
                # Обновляем отображение
                self.editor.update_display()
                self.editor.info_label.config(text=f"Изображение кадрировано\n"
                                                   f"Размер: {self.editor.image.width}x{self.editor.image.height}")
                self.editor.update_footer_info()
                
                crop_window.destroy()
                app_name = get_app_name_with_version()
                messagebox.showinfo(f"Успех - {app_name}", "Изображение успешно кадрировано")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось кадрировать изображение:\n{str(e)}")
        
        # Фрейм с кнопками (создаем в конце, чтобы кнопки были видны)
        button_frame = tk.Frame(crop_window)
        button_frame.pack(pady=10, fill=tk.X)
        
        # Кнопки
        tk.Button(button_frame, text="Применить кадрирование", command=apply_crop,
                 font=('Arial', 10), bg='lightgreen', width=20).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Отмена", command=crop_window.destroy,
                 font=('Arial', 10), bg='lightcoral', width=15).pack(side=tk.LEFT, padx=5)
    
    def show_upscale_method_dialog(self):
        """Показывает диалог выбора метода укрупнения ячеек"""
        dialog = tk.Toplevel(self.editor.root)
        dialog.title("Укрупнение ячеек")
        dialog.resizable(False, False)
        dialog.transient(self.editor.root)
        dialog.grab_set()
        
        selected_method = tk.StringVar(value='mean')
        
        # Заголовок
        tk.Label(dialog, text="Выберите метод расчета цвета при укрупнении:",
                font=('Arial', 11, 'bold')).pack(pady=10)
        
        tk.Label(dialog, text="Объединяет 4 ячейки (2x2) в одну",
                font=('Arial', 9)).pack(pady=(0, 15))
        
        # Методы
        methods_frame = tk.Frame(dialog)
        methods_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        methods = [
            ('mean', 'Средний цвет', 'Вычисляет среднее арифметическое цветов всех 4 ячеек'),
            ('median', 'Медианный цвет', 'Использует медиану цветов (устойчив к выбросам)'),
            ('dominant', 'Доминирующий цвет', 'Выбирает наиболее часто встречающийся цвет'),
            ('weighted', 'Взвешенный средний', 'Учитывает площадь каждой ячейки при расчете')
        ]
        
        for method_value, method_name, method_desc in methods:
            frame = tk.Frame(methods_frame)
            frame.pack(fill=tk.X, pady=5)
            
            rb = tk.Radiobutton(frame, text=method_name, variable=selected_method,
                              value=method_value, font=('Arial', 10))
            rb.pack(anchor=tk.W)
            
            tk.Label(frame, text=method_desc, font=('Arial', 8),
                    fg='gray', wraplength=350).pack(anchor=tk.W, padx=(25, 0))
        
        # Кнопки
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=15)
        
        def apply_upscale():
            method = selected_method.get()
            dialog.destroy()
            # Вызываем метод укрупнения напрямую через cell_upscaling
            self.editor.cell_upscaling.upscale_cells(method)
        
        tk.Button(button_frame, text="Применить", command=apply_upscale,
                 font=('Arial', 10), bg='lightgreen', width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Отмена", command=dialog.destroy,
                 font=('Arial', 10), bg='lightcoral', width=15).pack(side=tk.LEFT, padx=5)
        
        # Размер по содержимому и центрирование
        dialog.update_idletasks()
        w = dialog.winfo_reqwidth()
        h = dialog.winfo_reqheight()
        x = (dialog.winfo_screenwidth() // 2) - (w // 2)
        y = (dialog.winfo_screenheight() // 2) - (h // 2)
        dialog.geometry(f"{w}x{h}+{x}+{y}")

