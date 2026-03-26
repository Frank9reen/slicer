"""Диалог дополнительных настроек проекта"""
import tkinter as tk
from tkinter import ttk


class ProjectSettingsDialog:
    """Диалоговое окно для настройки названия проекта и артикула"""
    
    def __init__(self, parent, project_name=None, project_article=None, qr_url=None):
        """
        Args:
            parent: Родительское окно
            project_name: Текущее название проекта (по умолчанию)
            project_article: Текущий артикул проекта (по умолчанию)
            qr_url: Текущая ссылка для QR-кода (по умолчанию)
        """
        self.parent = parent
        self.result = None
        self.project_name = project_name or ''
        self.project_article = project_article or ''
        self.qr_url = qr_url or ''
        
        self.dialog = None
        self.project_name_var = None
        self.project_article_var = None
        self.qr_url_var = None
    
    def show(self):
        """Показывает диалог и возвращает словарь с настройками или None при отмене"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Дополнительные настройки проекта")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Основной фрейм
        main_frame = ttk.Frame(self.dialog, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Заголовок
        header_label = tk.Label(main_frame, text="Настройки проекта", 
                               font=('Arial', 12, 'bold'))
        header_label.pack(pady=(0, 15))
        
        # Создаем переменные для значений
        self.project_name_var = tk.StringVar(value=self.project_name)
        self.project_article_var = tk.StringVar(value=self.project_article)
        self.qr_url_var = tk.StringVar(value=self.qr_url)
        
        # Название проекта
        name_frame = ttk.Frame(main_frame)
        name_frame.pack(fill=tk.X, pady=5)
        ttk.Label(name_frame, text="Название проекта:", width=20).pack(side=tk.LEFT, padx=5)
        name_entry = ttk.Entry(name_frame, textvariable=self.project_name_var, width=30)
        name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Артикул
        article_frame = ttk.Frame(main_frame)
        article_frame.pack(fill=tk.X, pady=5)
        ttk.Label(article_frame, text="Артикул:", width=20).pack(side=tk.LEFT, padx=5)
        article_entry = ttk.Entry(article_frame, textvariable=self.project_article_var, width=30)
        article_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Ссылка на QR-код
        qr_frame = ttk.Frame(main_frame)
        qr_frame.pack(fill=tk.X, pady=5)
        ttk.Label(qr_frame, text="Ссылка на QR-код:", width=20).pack(side=tk.LEFT, padx=5)
        qr_entry = ttk.Entry(qr_frame, textvariable=self.qr_url_var, width=30)
        qr_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Кнопки
        button_frame = tk.Frame(main_frame)
        button_frame.pack(pady=(20, 0), anchor=tk.E)
        
        cancel_button = tk.Button(button_frame, text="Отмена", command=self.cancel, width=12, height=1, relief=tk.RAISED)
        cancel_button.pack(side=tk.RIGHT, padx=5)
        ok_button = tk.Button(button_frame, text="ОК", command=self.ok, width=12, height=1, relief=tk.RAISED)
        ok_button.pack(side=tk.RIGHT, padx=5)
        
        # Устанавливаем фокус на первое поле
        name_entry.focus()
        
        # Обработчик нажатия Enter
        name_entry.bind('<Return>', lambda e: article_entry.focus())
        article_entry.bind('<Return>', lambda e: qr_entry.focus())
        qr_entry.bind('<Return>', lambda e: self.ok())
        
        # Размер по содержимому и центрирование
        self.dialog.update_idletasks()
        w = self.dialog.winfo_reqwidth()
        h = self.dialog.winfo_reqheight()
        x = (self.dialog.winfo_screenwidth() // 2) - (w // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (h // 2)
        self.dialog.geometry(f"{w}x{h}+{x}+{y}")
        
        # Ждем закрытия диалога
        self.dialog.wait_window()
        
        return self.result
    
    def ok(self):
        """Сохраняет настройки и закрывает диалог"""
        self.result = {
            'project_name': self.project_name_var.get().strip(),
            'project_article': self.project_article_var.get().strip(),
            'qr_url': self.qr_url_var.get().strip()
        }
        self.dialog.destroy()
    
    def cancel(self):
        """Закрывает диалог без сохранения"""
        self.result = None
        self.dialog.destroy()

