"""Утилиты для работы с лицензией"""
import sys
from tkinter import messagebox
from datetime import datetime
from utils.version_utils import get_app_name_with_version


class LicenseUtils:
    """Утилиты для работы с лицензией приложения."""
    
    def __init__(self, editor):
        """
        Args:
            editor: Экземпляр GridEditor
        """
        self.editor = editor
    
    def check_license_on_startup(self):
        """Проверяет лицензию при запуске приложения"""
        success, message = self.editor.license_manager.check_license()
        
        # Обновляем информацию в футере
        self.editor.update_footer_info()
        
        # Если лицензия валидна, ничего не показываем
        if success:
            return  # Программа действительна, не показываем никаких сообщений
        
        # Лицензия истекла - показываем предупреждение и закрываем программу
        app_name = get_app_name_with_version()
        expiry_date_str = self.editor.license_manager.expiry_date.strftime('%d.%m.%Y')
        
        messagebox.showerror(
            f"{app_name} - Срок действия истек", 
            f"Срок действия программы истек {expiry_date_str}.\n\n"
            f"{message}\n\n"
            f"Программа будет закрыта."
        )
        
        # Закрываем программу
        try:
            self.editor.root.quit()
        except:
            pass
        try:
            self.editor.root.destroy()
        except:
            pass
        sys.exit(0)
    
    def update_license_menu(self):
        """Обновляет меню лицензии в зависимости от состояния"""
        # Удаляем пункт "Активировать лицензию", если он существует
        if hasattr(self.editor, 'activate_menu_item_id') and self.editor.activate_menu_item_id is not None:
            try:
                if hasattr(self.editor, 'about_menu'):
                    self.editor.about_menu.delete(self.editor.activate_menu_item_id)
            except:
                pass
            self.editor.activate_menu_item_id = None
    
    def show_license_status(self):
        """Показывает статус лицензии в диалоговом окне"""
        is_valid, message = self.editor.license_manager.check_license()
        
        app_name = get_app_name_with_version()
        expiry_date_str = self.editor.license_manager.expiry_date.strftime('%d.%m.%Y')
        
        if is_valid:
            days_left = self.editor.license_manager.get_days_left()
            status_text = f"{app_name}\n\n"
            status_text += f"Статус: ДЕЙСТВИТЕЛЬНА\n\n"
            status_text += f"Дата окончания: {expiry_date_str}\n"
            status_text += f"Осталось дней: {days_left}\n"
            messagebox.showinfo("Статус лицензии", status_text)
        else:
            status_text = f"{app_name}\n\n"
            status_text += f"Статус: ИСТЕКЛА\n\n"
            status_text += f"Дата окончания: {expiry_date_str}\n"
            status_text += f"{message}\n\n"
            status_text += "Программа будет закрыта."
            messagebox.showerror("Статус лицензии", status_text)
            
            # Закрываем программу
            try:
                self.editor.root.quit()
            except:
                pass
            try:
                self.editor.root.destroy()
            except:
                pass
            sys.exit(0)
    
    def show_license_dialog(self):
        """Показывает диалог активации лицензии (заглушка)"""
        app_name = get_app_name_with_version()
        expiry_date_str = self.editor.license_manager.expiry_date.strftime('%d.%m.%Y')
        messagebox.showinfo(
            f"Информация - {app_name}", 
            f"{app_name}\n\n"
            f"Активация лицензии не требуется.\n"
            f"Программа работает до {expiry_date_str}."
        )
