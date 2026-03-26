"""
Модуль для работы с палитрой Гаммы
Загружает цвета из Excel файла DMCtoGamma_with_Gamma_OFF_formattedColor.xlsx
"""
import os
import pandas as pd
import numpy as np
from typing import List, Tuple, Dict, Optional


class GammaPalette:
    """Класс для работы с палитрой Гаммы"""
    
    def __init__(self, excel_path: str = None):
        """
        Args:
            excel_path: Путь к Excel файлу с палитрой Гаммы
        """
        if excel_path is None:
            # Ищем файл в static/
            from utils.path_utils import get_static_path
            excel_path = get_static_path("DMCtoGamma_with_Gamma_OFF_formattedColor.xlsx")
        
        self.excel_path = excel_path
        self.colors_df = None
        self.colors_list = []  # Список цветов в формате [(name, rgb, hex, dmc, ...), ...]
        self.load_palette()
    
    def load_palette(self) -> bool:
        """Загружает палитру из Excel файла"""
        if not os.path.exists(self.excel_path):
            try:
                from utils.logger import setup_logger
                logger = setup_logger(__name__)
                logger.warning(f"Файл палитры Гаммы не найден: {self.excel_path}")
            except:
                pass
            return False
        
        try:
            # Загружаем Excel файл
            self.colors_df = pd.read_excel(self.excel_path)
            
            # Создаем список цветов
            self.colors_list = []
            
            # Определяем названия колонок (могут быть на русском)
            name_col = None
            rgb_cols = ['R', 'G', 'B']
            hex_col = None
            dmc_col = 'DMC'
            gamma_col = 'Gamma'
            
            # Ищем колонку с названием (обычно первая или с "названием")
            for col in self.colors_df.columns:
                if 'наз' in str(col).lower() or 'name' in str(col).lower() or col == self.colors_df.columns[0]:
                    name_col = col
                    break
            
            # Ищем колонку с HEX
            for col in self.colors_df.columns:
                if '#' in str(col) or 'hex' in str(col).lower() or 'цвет' in str(col).lower():
                    hex_col = col
                    break
            
            # Если не нашли, используем последнюю колонку как HEX
            if hex_col is None:
                for col in reversed(self.colors_df.columns):
                    if self.colors_df[col].dtype == object:
                        # Проверяем, содержит ли колонка HEX значения
                        sample_val = str(self.colors_df[col].iloc[0]) if len(self.colors_df) > 0 else ''
                        if '#' in sample_val:
                            hex_col = col
                            break
            
            # Формируем список цветов
            for idx, row in self.colors_df.iterrows():
                try:
                    # Получаем название
                    name = str(row[name_col]) if name_col and name_col in row.index else f"Color {idx + 1}"
                    
                    # Получаем RGB - если все значения пустые, ставим None
                    r_val = row['R'] if 'R' in row.index else None
                    g_val = row['G'] if 'G' in row.index else None
                    b_val = row['B'] if 'B' in row.index else None
                    
                    # Проверяем, все ли значения пустые
                    if pd.isna(r_val) and pd.isna(g_val) and pd.isna(b_val):
                        rgb = None
                        hex_color = None
                    else:
                        # Если хотя бы одно значение есть, используем его (для отсутствующих ставим 0)
                        r = int(r_val) if pd.notna(r_val) else 0
                        g = int(g_val) if pd.notna(g_val) else 0
                        b = int(b_val) if pd.notna(b_val) else 0
                        rgb = (r, g, b)
                        
                        # Получаем HEX - всегда генерируем из RGB для надежности
                        # Используем колонку 'Цвет' если она есть и содержит валидный HEX
                        hex_color = None
                        if hex_col and hex_col in row.index and pd.notna(row[hex_col]):
                            hex_val = str(row[hex_col]).strip()
                            # Проверяем, что это валидный HEX (начинается с # и содержит 6 шестнадцатеричных символов)
                            if hex_val.startswith('#') and len(hex_val) >= 7:
                                # Проверяем, что после # идут только hex символы
                                hex_part = hex_val[1:7] if len(hex_val) >= 7 else hex_val[1:]
                                try:
                                    # Пытаемся преобразовать в число для валидации
                                    int(hex_part, 16)
                                    hex_color = f"#{hex_part}"
                                except ValueError:
                                    # Невалидный HEX, будем генерировать из RGB
                                    pass
                        
                        # Если HEX не найден или невалидный, генерируем из RGB
                        if hex_color is None:
                            hex_color = f"#{r:02x}{g:02x}{b:02x}"
                    
                    # Получаем DMC код
                    dmc_code = str(row[dmc_col]) if dmc_col in row.index and pd.notna(row[dmc_col]) else None
                    
                    # Получаем Gamma код
                    gamma_code = str(row[gamma_col]) if gamma_col in row.index and pd.notna(row[gamma_col]) else None
                    
                    color_info = {
                        'name': name,
                        'rgb': rgb,
                        'hex': hex_color,
                        'dmc': dmc_code,
                        'gamma': gamma_code,
                        'index': idx
                    }
                    
                    self.colors_list.append(color_info)
                    
                except Exception as e:
                    try:
                        from utils.logger import setup_logger
                        logger = setup_logger(__name__)
                        logger.warning(f"Ошибка при обработке строки {idx}: {e}")
                    except:
                        pass
                    continue
            
            try:
                from utils.logger import setup_logger
                logger = setup_logger(__name__)
                logger.info(f"Загружено цветов из палитры Гаммы: {len(self.colors_list)}")
            except:
                pass
            return True
            
        except Exception as e:
            try:
                from utils.logger import setup_logger
                logger = setup_logger(__name__)
                logger.error(f"Ошибка при загрузке палитры Гаммы: {e}")
            except:
                pass
            import traceback
            traceback.print_exc()
            return False
    
    def get_all_colors(self) -> List[Dict]:
        """Возвращает список всех цветов"""
        return self.colors_list
    
    def find_closest_color(self, target_rgb: Tuple[int, int, int]) -> Optional[Dict]:
        """
        Находит ближайший цвет в палитре Гаммы к заданному RGB
        
        Args:
            target_rgb: Целевой цвет (R, G, B)
        
        Returns:
            Информация о ближайшем цвете или None
        """
        if not self.colors_list:
            return None
        
        target_rgb = np.array(target_rgb, dtype=np.float32)
        min_distance = float('inf')
        closest_color = None
        
        for color_info in self.colors_list:
            # Пропускаем цвета с пустым RGB
            if color_info['rgb'] is None:
                continue
                
            palette_rgb = np.array(color_info['rgb'], dtype=np.float32)
            distance = np.sqrt(np.sum((target_rgb - palette_rgb) ** 2))
            
            if distance < min_distance:
                min_distance = distance
                closest_color = color_info
        
        return closest_color
    
    def get_color_by_index(self, index: int) -> Optional[Dict]:
        """Получает цвет по индексу"""
        if 0 <= index < len(self.colors_list):
            return self.colors_list[index]
        return None
    
    def search_colors(self, query: str) -> List[Dict]:
        """
        Ищет цвета по названию, DMC коду или Gamma коду
        
        Args:
            query: Поисковый запрос
        
        Returns:
            Список найденных цветов
        """
        if not query:
            return self.colors_list
        
        query_lower = query.lower()
        results = []
        
        for color_info in self.colors_list:
            name = str(color_info['name']).lower()
            dmc = str(color_info.get('dmc', '')).lower()
            gamma = str(color_info.get('gamma', '')).lower()
            
            if query_lower in name or query_lower in dmc or query_lower in gamma:
                results.append(color_info)
        
        return results
    
    def save_palette(self) -> bool:
        """
        Сохраняет изменения палитры в Excel файл
        
        Returns:
            bool: True если успешно, False при ошибке
        """
        if not os.path.exists(self.excel_path):
            try:
                from utils.logger import setup_logger
                logger = setup_logger(__name__)
                logger.warning(f"Файл палитры Гаммы не найден: {self.excel_path}")
            except:
                pass
            return False
        
        if self.colors_df is None:
            try:
                from utils.logger import setup_logger
                logger = setup_logger(__name__)
                logger.warning("DataFrame не загружен. Невозможно сохранить.")
            except:
                pass
            return False
        
        try:
            # Определяем названия колонок
            name_col = None
            hex_col = None
            dmc_col = 'DMC'
            gamma_col = 'Gamma'
            
            for col in self.colors_df.columns:
                if 'наз' in str(col).lower() or 'name' in str(col).lower() or col == self.colors_df.columns[0]:
                    name_col = col
                if '#' in str(col) or 'hex' in str(col).lower() or 'цвет' in str(col).lower():
                    hex_col = col
            
            # Обновляем DataFrame из colors_list
            for color_info in self.colors_list:
                idx = color_info.get('index')
                if idx is None or idx < 0 or idx >= len(self.colors_df):
                    continue
                
                # Обновляем название
                if name_col and name_col in self.colors_df.columns:
                    self.colors_df.at[idx, name_col] = color_info.get('name', '')
                
                # Обновляем RGB (если RGB = None, оставляем пустые значения)
                rgb = color_info.get('rgb')
                if rgb is None:
                    # Если RGB пустой, ставим пустые значения в Excel
                    if 'R' in self.colors_df.columns:
                        self.colors_df.at[idx, 'R'] = None
                    if 'G' in self.colors_df.columns:
                        self.colors_df.at[idx, 'G'] = None
                    if 'B' in self.colors_df.columns:
                        self.colors_df.at[idx, 'B'] = None
                else:
                    # Если RGB есть, сохраняем значения
                    if 'R' in self.colors_df.columns:
                        self.colors_df.at[idx, 'R'] = rgb[0]
                    if 'G' in self.colors_df.columns:
                        self.colors_df.at[idx, 'G'] = rgb[1]
                    if 'B' in self.colors_df.columns:
                        self.colors_df.at[idx, 'B'] = rgb[2]
                
                # Обновляем HEX
                if hex_col and hex_col in self.colors_df.columns:
                    self.colors_df.at[idx, hex_col] = color_info.get('hex', '')
                
                # Обновляем DMC
                if dmc_col in self.colors_df.columns:
                    self.colors_df.at[idx, dmc_col] = color_info.get('dmc', '')
                
                # Обновляем Gamma
                if gamma_col in self.colors_df.columns:
                    self.colors_df.at[idx, gamma_col] = color_info.get('gamma', '')
            
            # Сохраняем в файл
            self.colors_df.to_excel(self.excel_path, index=False)
            
            # Перезагружаем палитру для синхронизации
            self.load_palette()
            
            try:
                from utils.logger import setup_logger
                logger = setup_logger(__name__)
                logger.info(f"Палитра успешно сохранена в {self.excel_path}")
            except:
                pass
            return True
            
        except Exception as e:
            try:
                from utils.logger import setup_logger
                logger = setup_logger(__name__)
                logger.error(f"Ошибка при сохранении палитры Гаммы: {e}")
            except:
                pass
            import traceback
            traceback.print_exc()
            return False


# Глобальный экземпляр палитры (загружается один раз)
_gamma_palette_instance = None


def get_gamma_palette(excel_path: str = None, force_reload: bool = False) -> GammaPalette:
    """
    Получает глобальный экземпляр палитры Гаммы
    
    Args:
        excel_path: Путь к Excel файлу (используется только при первом вызове)
        force_reload: Если True, перезагружает палитру из файла
    
    Returns:
        GammaPalette: Экземпляр палитры Гаммы
    """
    global _gamma_palette_instance
    
    if _gamma_palette_instance is None or force_reload:
        _gamma_palette_instance = GammaPalette(excel_path)
    
    return _gamma_palette_instance

