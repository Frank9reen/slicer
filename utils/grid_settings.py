"""Утилиты для работы с настройками сетки и фона"""
import tkinter as tk
from tkinter import colorchooser, messagebox


class GridSettings:
    """Утилиты для работы с настройками сетки и фона."""
    
    def __init__(self, editor):
        """
        Args:
            editor: Экземпляр GridEditor
        """
        self.editor = editor
    
    def choose_background_color(self):
        """Открывает диалог выбора цвета задней подложки"""
        # Преобразуем строку цвета в RGB, если это стандартное имя цвета
        color_map = {
            'white': (255, 255, 255),
            'black': (0, 0, 0),
            'gray': (128, 128, 128),
            'lightgray': (211, 211, 211),
            'darkgray': (169, 169, 169),
            'red': (255, 0, 0),
            'green': (0, 128, 0),
            'blue': (0, 0, 255),
            'yellow': (255, 255, 0),
            'cyan': (0, 255, 255),
            'magenta': (255, 0, 255)
        }
        
        # Получаем начальный цвет
        if self.editor.background_color in color_map:
            initial_color = color_map[self.editor.background_color]
        else:
            # Если это hex-цвет, преобразуем в RGB
            try:
                if self.editor.background_color.startswith('#'):
                    hex_color = self.editor.background_color[1:]
                    initial_color = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                else:
                    initial_color = (255, 255, 255)  # По умолчанию белый
            except:
                initial_color = (255, 255, 255)
        
        # Открываем диалог выбора цвета
        color = colorchooser.askcolor(
            title="Выберите цвет задней подложки",
            color=initial_color
        )
        
        if color[1] is not None:  # Если пользователь не отменил выбор
            # color[1] - это hex-строка вида '#rrggbb'
            self.editor.background_color = color[1]
            # Обновляем цвет canvas
            self.editor.canvas.config(bg=self.editor.background_color)
            # Обновляем кнопку
            self.editor.update_background_color_button()
            # Обновляем отображение
            self.editor.update_display()
    
    def get_background_color_rgb(self):
        """Преобразует цвет подложки в RGB кортеж"""
        try:
            if self.editor.background_color.startswith('#'):
                hex_color = self.editor.background_color[1:]
                r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
                return (r, g, b)
            else:
                # Для именованных цветов получаем RGB через tkinter
                try:
                    rgb = self.editor.root.winfo_rgb(self.editor.background_color)
                    r, g, b = rgb[0] // 256, rgb[1] // 256, rgb[2] // 256
                    return (r, g, b)
                except:
                    # Если не получилось, используем значения по умолчанию для известных цветов
                    color_map = {
                        'white': (254, 254, 254),  # Почти белый для подложки (чтобы белый можно было закрашивать)
                        'black': (0, 0, 0),
                        'gray': (128, 128, 128),
                        'lightgray': (211, 211, 211),
                        'darkgray': (169, 169, 169),
                        'red': (255, 0, 0),
                        'green': (0, 128, 0),
                        'blue': (0, 0, 255),
                        'yellow': (255, 255, 0),
                        'cyan': (0, 255, 255),
                        'magenta': (255, 0, 255)
                    }
                    return color_map.get(self.editor.background_color, (254, 254, 254))  # Почти белый по умолчанию
        except:
            return (255, 255, 255)  # По умолчанию белый
    
    def set_grid_line_width(self):
        """Открывает окно для установки толщины линий сетки с использованием Spinbox"""
        # Сохраняем исходное значение для возможной отмены
        original_width = self.editor.grid_line_width
        
        # Создаем окно
        width_window = tk.Toplevel(self.editor.root)
        width_window.title("Толщина сетки")
        width_window.resizable(False, False)
        width_window.transient(self.editor.root)  # Делаем окно модальным относительно главного окна
        width_window.grab_set()  # Блокируем взаимодействие с другими окнами
        
        # Метка
        label = tk.Label(width_window, text="Толщина линий сетки (1-10):", font=('Arial', 10))
        label.pack(pady=10)
        
        # Spinbox для выбора толщины
        width_var = tk.IntVar(value=self.editor.grid_line_width)
        spinbox = tk.Spinbox(
            width_window,
            from_=1,
            to=10,
            textvariable=width_var,
            width=10,
            font=('Arial', 12)
        )
        spinbox.pack(pady=5)
        
        # Функция для обновления предпросмотра при изменении значения
        def update_preview(*args):
            try:
                value = width_var.get()
                if 1 <= value <= 10:
                    # Временно изменяем толщину для предпросмотра
                    self.editor.grid_line_width = value
                    self.editor.update_display()
            except:
                pass
        
        width_var.trace('w', update_preview)
        
        # Также обновляем при использовании стрелок
        spinbox.config(command=update_preview)
        
        # Кнопки
        button_frame = tk.Frame(width_window)
        button_frame.pack(pady=10)
        
        def apply_width():
            new_width = width_var.get()
            if 1 <= new_width <= 10:
                self.editor.grid_line_width = new_width
                self.editor.update_display()
                width_window.destroy()
            else:
                messagebox.showwarning("Предупреждение", "Толщина должна быть от 1 до 10")
        
        def cancel():
            # Восстанавливаем исходное значение
            self.editor.grid_line_width = original_width
            self.editor.update_display()
            width_window.destroy()
        
        # Обработка закрытия окна (крестик)
        def on_closing():
            cancel()
        
        width_window.protocol("WM_DELETE_WINDOW", on_closing)
        
        tk.Button(button_frame, text="Применить", command=apply_width, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Отмена", command=cancel, width=10).pack(side=tk.LEFT, padx=5)
        
        # Фокус на Spinbox
        spinbox.focus_set()
        
        # Размер по содержимому и центрирование
        width_window.update_idletasks()
        w = width_window.winfo_reqwidth()
        h = width_window.winfo_reqheight()
        x = (width_window.winfo_screenwidth() // 2) - (w // 2)
        y = (width_window.winfo_screenheight() // 2) - (h // 2)
        width_window.geometry(f"{w}x{h}+{x}+{y}")
    
    def update_background_color_button(self):
        """Обновляет внешний вид кнопки выбора цвета подложки"""
        if hasattr(self.editor, 'background_color_button'):
            self.editor.background_color_button.config(bg=self.editor.background_color)
            # Определяем цвет текста в зависимости от яркости фона
            try:
                if self.editor.background_color.startswith('#'):
                    hex_color = self.editor.background_color[1:]
                    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
                else:
                    # Для именованных цветов получаем RGB через tkinter
                    try:
                        # Пробуем получить RGB из tkinter
                        rgb = self.editor.root.winfo_rgb(self.editor.background_color)
                        r, g, b = rgb[0] // 256, rgb[1] // 256, rgb[2] // 256
                    except:
                        # Если не получилось, используем значения по умолчанию для известных цветов
                        color_map = {
                            'white': (255, 255, 255),
                            'black': (0, 0, 0),
                            'gray': (128, 128, 128),
                            'lightgray': (211, 211, 211),
                            'darkgray': (169, 169, 169),
                            'red': (255, 0, 0),
                            'green': (0, 128, 0),
                            'blue': (0, 0, 255),
                            'yellow': (255, 255, 0),
                            'cyan': (0, 255, 255),
                            'magenta': (255, 0, 255)
                        }
                        r, g, b = color_map.get(self.editor.background_color, (128, 128, 128))
                # Вычисляем яркость (luminance)
                luminance = (0.299 * r + 0.587 * g + 0.114 * b)
                text_color = 'black' if luminance > 128 else 'white'
            except:
                text_color = 'black'
            self.editor.background_color_button.config(fg=text_color)
    
    def toggle_grid_visibility(self):
        """Переключает видимость сетки (для совместимости)"""
        self.editor.show_grid = not self.editor.show_grid
        self.editor.update_display()
        # Обновляем внешний вид кнопки
        self.editor.update_grid_button_appearance()
    
    def toggle_grid_with_button(self):
        """Переключает видимость сетки через кнопку"""
        self.editor.show_grid = not self.editor.show_grid
        self.editor.update_display()
        self.editor.update_grid_button_appearance()
    
    def update_grid_button_appearance(self):
        """Обновляет внешний вид кнопки переключения сетки"""
        if hasattr(self.editor, 'grid_toggle_button'):
            if self.editor.show_grid:
                self.editor.grid_toggle_button.config(bg='lightgreen', text="#", relief=tk.SUNKEN)
            else:
                self.editor.grid_toggle_button.config(bg='lightgray', text="#", relief=tk.RAISED)
    
    def toggle_grid_visibility_menu(self):
        """Переключает видимость сетки через меню"""
        self.editor.show_grid = not self.editor.show_grid
        self.editor.update_display()
        # Обновляем текст в меню
        if hasattr(self.editor, 'grid_menu'):
            status = "скрыта" if not self.editor.show_grid else "показана"
            self.editor.grid_menu.entryconfig(0, label=f"Показывать сетку ({status})")
        # Обновляем внешний вид кнопки
        self.editor.update_grid_button_appearance()

