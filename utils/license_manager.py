"""Менеджер лицензии - проверка срока действия программы"""
from datetime import datetime, date
from tkinter import messagebox


class LicenseManager:
    """Простой менеджер лицензии с проверкой срока действия"""
    
    # Дата окончания действия программы: 29.03.2026 (+2 недели)
    EXPIRY_DATE = datetime(2026, 3, 29, 23, 59, 59)
    
    def __init__(self, license_file=None):
        """Инициализация менеджера лицензии"""
        # Параметр license_file оставлен для совместимости, но не используется
        self.expiry_date = self.EXPIRY_DATE
        self.is_valid = False
        self.license_key = None  # Оставлено для совместимости
    
    def _get_expiry_date_only(self):
        """Возвращает только дату окончания (без времени)"""
        return self.expiry_date.date()
    
    def _get_current_date_only(self):
        """Возвращает только текущую дату (без времени)"""
        return datetime.now().date()
    
    def check_license(self):
        """Проверяет текущее состояние лицензии"""
        current_date_only = self._get_current_date_only()
        expiry_date_only = self._get_expiry_date_only()
        
        if current_date_only > expiry_date_only:
            self.is_valid = False
            return False, f"Срок действия программы истек {expiry_date_only.strftime('%d.%m.%Y')}"
        
        self.is_valid = True
        days_left = (expiry_date_only - current_date_only).days
        return True, f"Программа действительна до {expiry_date_only.strftime('%d.%m.%Y')} (осталось дней: {days_left})"
    
    def get_days_left(self):
        """Возвращает количество оставшихся дней"""
        current_date_only = self._get_current_date_only()
        expiry_date_only = self._get_expiry_date_only()
        
        if current_date_only > expiry_date_only:
            return 0
        days_left = (expiry_date_only - current_date_only).days
        return max(0, days_left)
    
    def load_license(self):
        """Загружает лицензию (для совместимости, всегда проверяет дату)"""
        return self.check_license()
    
    def validate_license_key(self, license_key):
        """Заглушка для совместимости"""
        return False, "Активация лицензии отключена"
    
    def activate_license(self, license_key, days=30):
        """Заглушка для совместимости"""
        return False, "Активация лицензии отключена"


class LicenseDialog:
    """Заглушка диалога лицензии для совместимости"""
    def __init__(self, parent, license_manager):
        self.parent = parent
        self.license_manager = license_manager
        self.result = None
        
        messagebox.showinfo("NexelSoftware - Информация", 
                          "Активация лицензии не требуется.\nПрограмма работает до 29.03.2026")
        self.result = False
