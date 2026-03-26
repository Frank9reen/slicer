"""UI-диалоги для работы с проектами"""
import tkinter as tk
from tkinter import filedialog, messagebox
from utils.version_utils import get_app_name_with_version


class ProjectDialogs:
    """Класс для управления UI-диалогами работы с проектами."""
    
    def __init__(self, editor):
        """
        Args:
            editor: Экземпляр GridEditor
        """
        self.editor = editor
    
    def save_project(self):
        """Сохраняет весь проект в zip-архив"""
        if self.editor.image is None:
            messagebox.showwarning("Предупреждение", "Нет изображения для сохранения проекта")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Сохранить проект",
            defaultextension=".slicer",
            filetypes=[("Проект Slicer", "*.slicer"), ("Все файлы", "*.*")]
        )
        
        if not file_path:
            return
        
        # Убеждаемся, что файл имеет расширение .slicer
        if not file_path.lower().endswith('.slicer'):
            file_path += '.slicer'
        
        # Сохраняем проект
        self.save_project_to_path(file_path)
    
    def save_project_to_path(self, file_path):
        """Сохраняет проект по указанному пути без диалога"""
        try:
            # Получаем значения чекбоксов методов фрагментации
            palette_method_kmeans = (
                hasattr(self.editor, 'palette_method_kmeans') and 
                self.editor.palette_method_kmeans.get()
            )
            palette_method_kmeans_improved = (
                hasattr(self.editor, 'palette_method_kmeans_improved') and 
                self.editor.palette_method_kmeans_improved.get()
            )
            palette_method_kmeans_weighted = (
                hasattr(self.editor, 'palette_method_kmeans_weighted') and 
                self.editor.palette_method_kmeans_weighted.get()
            )
            palette_method_hierarchical_kmeans = (
                hasattr(self.editor, 'palette_method_hierarchical_kmeans') and 
                self.editor.palette_method_hierarchical_kmeans.get()
            )
            palette_method_median_cut = (
                hasattr(self.editor, 'palette_method_median_cut') and 
                self.editor.palette_method_median_cut.get()
            )
            palette_method_octree = (
                hasattr(self.editor, 'palette_method_octree') and 
                self.editor.palette_method_octree.get()
            )
            sort_palette_by_gamma_var = (
                hasattr(self.editor, 'sort_palette_by_gamma_var') and 
                self.editor.sort_palette_by_gamma_var.get()
            )
            focus_on_center_var = (
                hasattr(self.editor, 'focus_on_center_var') and 
                self.editor.focus_on_center_var.get()
            )
            
            # Получаем значения чекбоксов методов сетки
            adaptive_method_gradients = (
                hasattr(self.editor, 'adaptive_method_gradients') and 
                self.editor.adaptive_method_gradients.get()
            )
            manual_grid_enabled = (
                hasattr(self.editor, 'manual_grid_enabled') and 
                self.editor.manual_grid_enabled.get()
            )
            
            self.editor.project_manager.save_project(
                file_path=file_path,
                original_image=self.editor.original_image,
                fragmented_image=self.editor.fragmented_image,
                image_path=self.editor.image_path if self.editor.image_path else '',
                vertical_lines=self.editor.vertical_lines,
                horizontal_lines=self.editor.horizontal_lines,
                num_vertical=int(self.editor.num_vertical.get()),
                num_horizontal=int(self.editor.num_horizontal.get()),
                step_vertical=int(self.editor.step_vertical.get()),
                step_horizontal=int(self.editor.step_horizontal.get()),
                num_colors=int(self.editor.num_colors.get()),
                view_mode=int(self.editor.view_mode),
                show_grid=bool(self.editor.show_grid),
                grid_line_width=int(self.editor.grid_line_width),
                background_color=str(self.editor.background_color),
                painted_cells=self.editor.painted_cells,
                palette=self.editor.palette,
                selected_color=self.editor.selected_color,
                palette_method_kmeans=palette_method_kmeans,
                palette_method_kmeans_improved=palette_method_kmeans_improved,
                palette_method_kmeans_weighted=palette_method_kmeans_weighted,
                palette_method_hierarchical_kmeans=palette_method_hierarchical_kmeans,
                palette_method_median_cut=palette_method_median_cut,
                palette_method_octree=palette_method_octree,
                sort_palette_by_gamma_var=sort_palette_by_gamma_var,
                focus_on_center_var=focus_on_center_var,
                adaptive_method_gradients=adaptive_method_gradients,
                manual_grid_enabled=manual_grid_enabled,
                project_name=self.editor.project_name if self.editor.project_name else None,
                project_article=self.editor.project_article if self.editor.project_article else None,
                qr_url=self.editor.qr_url if self.editor.qr_url else None
            )
            # Сохраняем путь к проекту для быстрого сохранения
            self.editor.current_project_path = file_path
            app_name = get_app_name_with_version()
            self.editor.image_file_manager._show_save_success_with_path(
                f"Успех - {app_name}", "Проект успешно сохранен:", file_path
            )
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить проект:\n{str(e)}")
            import traceback
            print(traceback.format_exc())
            raise
    
    def load_project(self):
        """Загружает проект из zip-архива"""
        file_path = filedialog.askopenfilename(
            title="Загрузить проект",
            filetypes=[("Проект Slicer", "*.slicer"), ("Все файлы", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            # Загружаем проект через ProjectManager
            project_data = self.editor.project_manager.load_project(file_path)
            
            # Восстанавливаем изображения
            self.editor.original_image = project_data['original_image']
            self.editor.image = self.editor.original_image.copy()
            self.editor.display_image = self.editor.image.copy()
            self.editor.fragmented_image = project_data['fragmented_image']
            self.editor.image_path = project_data['image_path']
            
            # Восстанавливаем дополнительные настройки проекта
            self.editor.project_name = project_data.get('project_name', '')
            self.editor.project_article = project_data.get('project_article', '')
            self.editor.qr_url = project_data.get('qr_url', '')
            
            # Восстанавливаем настройки сетки
            self.editor.num_vertical.set(project_data['num_vertical'])
            self.editor.num_horizontal.set(project_data['num_horizontal'])
            self.editor.step_vertical.set(project_data['step_vertical'])
            self.editor.step_horizontal.set(project_data['step_horizontal'])
            self.editor.num_colors.set(project_data['num_colors'])
            
            # Восстанавливаем чекбоксы методов фрагментации
            if hasattr(self.editor, 'palette_method_kmeans'):
                self.editor.palette_method_kmeans.set(project_data.get('palette_method_kmeans', False))
            if hasattr(self.editor, 'palette_method_kmeans_improved'):
                self.editor.palette_method_kmeans_improved.set(project_data.get('palette_method_kmeans_improved', False))
            if hasattr(self.editor, 'palette_method_kmeans_weighted'):
                self.editor.palette_method_kmeans_weighted.set(project_data.get('palette_method_kmeans_weighted', False))
            if hasattr(self.editor, 'palette_method_hierarchical_kmeans'):
                self.editor.palette_method_hierarchical_kmeans.set(project_data.get('palette_method_hierarchical_kmeans', False))
            if hasattr(self.editor, 'palette_method_median_cut'):
                self.editor.palette_method_median_cut.set(project_data.get('palette_method_median_cut', False))
            if hasattr(self.editor, 'palette_method_octree'):
                self.editor.palette_method_octree.set(project_data.get('palette_method_octree', False))
            if hasattr(self.editor, 'sort_palette_by_gamma_var'):
                self.editor.sort_palette_by_gamma_var.set(project_data.get('sort_palette_by_gamma_var', True))
            if hasattr(self.editor, 'focus_on_center_var'):
                self.editor.focus_on_center_var.set(project_data.get('focus_on_center_var', False))
            
            # Восстанавливаем чекбоксы методов сетки
            if hasattr(self.editor, 'adaptive_method_gradients'):
                self.editor.adaptive_method_gradients.set(project_data.get('adaptive_method_gradients', False))
            if hasattr(self.editor, 'manual_grid_enabled'):
                manual_enabled = project_data.get('manual_grid_enabled', False)
                self.editor.manual_grid_enabled.set(manual_enabled)
                # Если ручная настройка была включена, показываем поля ручной настройки
                if manual_enabled and hasattr(self.editor, 'grid_panel'):
                    # Показываем поля ручной настройки напрямую
                    if hasattr(self.editor.grid_panel, 'manual_settings_frame'):
                        self.editor.grid_panel.manual_settings_frame.pack(fill=tk.X, padx=(0, 5), pady=2)
            
            # Восстанавливаем линии (синхронизируем с grid_manager)
            self.editor.grid_manager.vertical_lines = project_data['vertical_lines']
            self.editor.grid_manager.horizontal_lines = project_data['horizontal_lines']
            # Обновляем ссылки (на случай если grid_manager создал новые списки)
            self.editor.vertical_lines = self.editor.grid_manager.vertical_lines
            self.editor.horizontal_lines = self.editor.grid_manager.horizontal_lines
            
            # Восстанавливаем настройки
            self.editor.show_grid = project_data['show_grid']
            self.editor.grid_line_width = project_data['grid_line_width']
            # Восстанавливаем цвет фона
            self.editor.background_color = project_data['background_color']
            self.editor.canvas.config(bg=self.editor.background_color)
            self.editor.update_background_color_button()
            # Обновляем текст в меню "Сетка"
            if hasattr(self.editor, 'grid_menu'):
                status = "скрыта" if not self.editor.show_grid else "показана"
                self.editor.grid_menu.entryconfig(0, label=f"Показывать сетку ({status})")
            # Обновляем внешний вид кнопки
            self.editor.update_grid_button_appearance()
            
            # Восстанавливаем закрашенные ячейки
            self.editor.painted_cells = project_data['painted_cells']
            
            # Восстанавливаем палитру
            self.editor.palette = project_data['palette']
            
            # Если палитра отсутствует, но есть фрагментированное изображение,
            # создаем палитру из уникальных цветов изображения
            if (self.editor.palette is None or len(self.editor.palette) == 0) and self.editor.fragmented_image is not None:
                try:
                    import numpy as np
                    img_array = np.array(self.editor.fragmented_image)
                    # Собираем уникальные цвета из фрагментированного изображения
                    unique_colors = np.unique(img_array.reshape(-1, 3), axis=0)
                    # Исключаем белый цвет (255, 255, 255) из палитры
                    white_mask = ~np.all(unique_colors == [255, 255, 255], axis=1)
                    unique_colors = unique_colors[white_mask]
                    
                    if len(unique_colors) > 0:
                        self.editor.palette = unique_colors
                        try:
                            from utils.logger import setup_logger
                            logger = setup_logger(__name__)
                            logger.info(f"Палитра создана из фрагментированного изображения: {len(self.editor.palette)} цветов")
                        except:
                            pass
                except Exception as e:
                    try:
                        from utils.logger import setup_logger
                        logger = setup_logger(__name__)
                        logger.error(f"Ошибка при создании палитры из фрагментированного изображения: {e}")
                    except:
                        pass
            
            if self.editor.palette is not None and len(self.editor.palette) > 0:
                self.editor.display_palette()
                # Блокируем сетку, если палитра загружена
                if hasattr(self.editor, 'grid_locked'):
                    self.editor.grid_locked = True
                    # Отключаем кнопки управления сеткой
                    if hasattr(self.editor, 'grid_panel'):
                        self.editor.grid_panel.disable_grid_controls()
            else:
                # Разблокируем сетку, если палитры нет
                if hasattr(self.editor, 'grid_locked'):
                    self.editor.grid_locked = False
                    # Включаем кнопки управления сеткой
                    if hasattr(self.editor, 'grid_panel'):
                        self.editor.grid_panel.enable_grid_controls()
            
            # Восстанавливаем выбранный цвет
            self.editor.selected_color = project_data['selected_color']
            
            # Сбрасываем некоторые флаги
            self.editor.selected_line = None
            self.editor.undo_history = []
            self.editor.redo_history = []
            self.editor.state_manager.clear()  # Очищаем историю в менеджере состояний
            self.editor.state_saved_for_action = False
            self.editor.selection_start = None
            self.editor.selection_end = None
            self.editor.selected_regions = []
            self.editor.zoom = 1.0
            self.editor.pan_x = 0
            self.editor.pan_y = 0
            
            # Устанавливаем режим просмотра 2
            self.editor.set_view_mode(2)
            
            # Обновляем отображение (это также скроет фрейм с кнопками и покажет canvas)
            self.editor.update_display()
            
            # Принудительно обновляем интерфейс, чтобы изменения отобразились сразу
            self.editor.root.update_idletasks()
            
            # Обновляем информацию о проекте
            self.editor.info_label.config(text=f"Проект загружен:\n"
                                           f"Вертикальных линий: {len(self.editor.vertical_lines)}\n"
                                           f"Горизонтальных линий: {len(self.editor.horizontal_lines)}\n"
                                           f"Закрашенных ячеек: {len(self.editor.painted_cells)}")
            
            # Сохраняем путь к загруженному проекту для быстрого сохранения
            self.editor.current_project_path = file_path
            
            # Обновляем информацию в футере
            self.editor.update_footer_info()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить проект:\n{str(e)}")
            import traceback
            print(traceback.format_exc())

