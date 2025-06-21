import json
import os

from typing import Tuple, List, Optional

from PyQt6.QtWidgets import (QMainWindow, QWidget, QPushButton, QGraphicsView, QHBoxLayout, QListWidget,
                             QLabel, QVBoxLayout, QFrame, QMessageBox, QMenu, QInputDialog, QTabWidget, QListWidgetItem,
                             QHeaderView, QGroupBox)
from PyQt6.QtGui import QPainter, QIcon
from PyQt6.QtCore import Qt, pyqtSignal, QPoint

from core.Level import Level
from core.CustomElementFactory import CustomElementFactory
from core.Grid import Grid
from core.LogicElements import ClockGeneratorElement
from gui import LogicElementItem
from gui.GameScene import GameScene
from gui.TruthTableView import TruthTableView

USER_ELEMENTS_DIR = "user_elements"

class GameUI(QMainWindow):
    back_to_menu_requested = pyqtSignal()
    level_completed = pyqtSignal(Level)

    def __init__(self, game_model):
        super().__init__()
        self.game_model = game_model
        self.selected_element_type = None
        self.is_menu_expanded = False
        self.tab_metadata = {}
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Logic Game")
        self.setGeometry(100, 100, 1000, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # === ЛЕВОЕ БОКОВОЕ МЕНЮ ===
        self.is_menu_expanded = False
        self.side_menu = QFrame()
        self.side_menu.setFixedWidth(40)

        menu_layout = QVBoxLayout(self.side_menu)
        menu_layout.setContentsMargins(5, 0, 0, 5)

        # Кнопка сворачивания меню
        self.toggle_menu_button = QPushButton()
        self.toggle_menu_button.setIcon(QIcon.fromTheme(QIcon.ThemeIcon.EditUndo))
        self.toggle_menu_button.setStyleSheet("QPushButton.side-menu-button { text-align: left; }")
        self.toggle_menu_button.setFixedHeight(40)
        self.toggle_menu_button.setObjectName("side-menu-button")
        self.toggle_menu_button.clicked.connect(self.toggle_side_menu)
        menu_layout.addWidget(self.toggle_menu_button)

        # Кнопка "Назад на главную"
        self.back_button = QPushButton()
        self.back_button.setIcon(QIcon.fromTheme("go-home"))
        self.back_button.setStyleSheet("QPushButton.side-menu-button { text-align: left; }")
        self.back_button.setFixedHeight(40)
        self.back_button.setObjectName("side-menu-button")
        self.back_button.clicked.connect(self.back_to_menu_requested.emit)
        self.back_button.setEnabled(False)
        menu_layout.addWidget(self.back_button)

        menu_layout.addStretch()
        main_layout.addWidget(self.side_menu)

        # === ЦЕНТРАЛЬНАЯ ЧАСТЬ - ГРАФИЧЕСКОЕ ПОЛЕ ===
        self.scene = GameScene(self.game_model.grid)
        self.scene.set_parent_ui(self)
        self.scene.grid.set_level(self.game_model.current_level)

        # Вкладка текущего уровня
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self._handle_tab_close_requested)
        main_layout.addWidget(self.tab_widget, stretch=3)
        self.tabs: List[Tuple[GameScene, QGraphicsView]] = []
        self.add_new_scene_tab(self.game_model.grid.level.name, self.game_model.grid)

        # === ПРАВАЯ ЧАСТЬ - ПАНЕЛЬ УПРАВЛЕНИЯ ===
        side_panel = QVBoxLayout()

        toolbox_group = QGroupBox("Панель элементов")
        toolbox_layout = QVBoxLayout()
        toolbox_group.setLayout(toolbox_layout)

        # Тулбокс (панель элементов)
        self.toolbox = QListWidget()
        self.toolbox.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.toolbox.customContextMenuRequested.connect(self.show_toolbox_context_menu)
        for element_type in self.game_model.toolbox:
            self.toolbox.addItem(element_type.__name__)
        self.toolbox.itemClicked.connect(self.select_element)
        #side_panel.addWidget(QLabel("Элементы:"))
        toolbox_layout.addWidget(self.toolbox)



        # Кнопки удаления и сохранения для элементов
        self.new_element_button = QPushButton("Новый элемент")
        self.new_element_button.clicked.connect(self.create_new_custom_element)
        self.save_element_button = QPushButton("Сохранить")
        self.save_element_button.clicked.connect(self.save_custom_element)
        button_row_layout = QHBoxLayout()
        button_row_layout.setSpacing(5)
        button_row_layout.addWidget(self.new_element_button)
        button_row_layout.addWidget(self.save_element_button)
        toolbox_layout.addLayout(button_row_layout)

        side_panel.addWidget(toolbox_group)

        # Группа "Симуляция"
        simulation_group = QGroupBox("Симуляция")
        simulation_layout = QVBoxLayout()
        simulation_group.setLayout(simulation_layout)

        # Кнопка "Старт симуляции"
        self.start_simulation_button = QPushButton("Старт")
        self.start_simulation_button.setIcon(QIcon.fromTheme("media-playback-start"))
        self.start_simulation_button.clicked.connect(self._handle_start_simulation)

        # Кнопка "Стоп симуляции"
        self.stop_simulation_button = QPushButton("Стоп")
        self.stop_simulation_button.setIcon(QIcon.fromTheme("media-playback-stop"))
        self.stop_simulation_button.clicked.connect(self._handle_stop_simulation)

        simulation_layout.addWidget(self.start_simulation_button)
        simulation_layout.addWidget(self.stop_simulation_button)

        side_panel.addWidget(simulation_group)

        # Таблица истинности (если вкладка - уровень)
        level = self.game_model.current_level
        if level.truth_table != {}:
            self.truth_table_view = TruthTableView()
            self.truth_table_view.set_table(
                level.truth_table,
                input_names=level.input_names,
                output_names=level.output_names
            )
            self.truth_table_view.horizontalHeader().setStretchLastSection(True)
            self.truth_table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            self.truth_table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            side_panel.addWidget(self.truth_table_view)

            # Кнопка проверки уровня
            self.test_button = QPushButton("Проверить уровень")
            self.test_button.clicked.connect(self.check_level)
            side_panel.addWidget(self.test_button)

        side_widget = QWidget()
        side_widget.setLayout(side_panel)
        main_layout.addWidget(side_widget, stretch=1)

        self.setStyleSheet("""
                QWidget {
                    background-color: #f0f2f5;
                    font-family: 'Segoe UI', sans-serif;
                    font-size: 14px;
                }
                QPushButton {
                    background-color: #ffffff;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    border: 1px solid #ccc;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: #dedede;
                }
                QPushButton:pressed {
                    background-color: #c4c4c4;
                }
                QPushButton.side-menu-button {
                    background-color: #ffffff;
                    border: 1px solid #ccc;
                    border-radius: 6px; 
                    padding: 100px;
                    margin: 0px;
                    text-align: left;
                }
                QPushButton.side-menu-button:disabled {
                    background-color: #ffffff;
                    color: #888888;
                    border: 1px solid #ccc;
                    opacity: 0.4;
                }
                QTabWidget::pane {
                    border: 1px solid #ccc;
                    border-radius: 4px;
                    background: white;
                }
                QTabBar::tab {
                    background: #ddd;
                    border: 1px solid #ccc;
                    border-bottom: none;
                    padding: 6px 10px;
                    border-top-left-radius: 5px;
                    border-top-right-radius: 5px;
                }
                QTabBar::tab:selected {
                    background: #f2f2f2;
                    font-weight: 500;
                }
                QListWidget {
                    background-color: white;
                    border: 1px solid #ccc;
                    border-radius: 6px;
                }
                QListWidget::item {
                    padding: 6px;
                }
                QListWidget::item:selected {
                    background-color: #d0e8ff;
                    color: black;
                }
                QListWidget::item:selected:hover {
                    background-color: #bdbdff;
                }
                QListWidget::item:hover {
                    background-color: #f5f5f5;
                }
                QTableWidget {
                    background-color: #ffffff;
                    border: 1px solid #e0e0e0;
                    border-radius: 6px;
                    gridline-color: #e0e0e0;
                    font-size: 14px;
                }
                QHeaderView::section {
                    background-color: #f5f5f5;
                    padding: 6px;
                    border: 1px solid #dcdcdc;
                }
                QTableWidget::item {
                    padding: 6px;
                    selection-background-color: #1976D2;
                    selection-color: #ffffff;
                }
                QTableCornerButton::section {
                    background-color: #f5f5f5;
                    border: 1px solid #dcdcdc;
                }
                
                QScrollBar:vertical {
                    background: transparent;
                    width: 8px;
                    margin: 0px;
                }
                QScrollBar::handle:vertical {
                    background: #dcdcdc;
                    border-radius: 4px;
                    min-height: 20px;
                }
            
                QScrollBar::add-line:vertical,
                QScrollBar::sub-line:vertical {
                    height: 0px;
                }
            
                QScrollBar::add-page:vertical,
                QScrollBar::sub-page:vertical {
                    background: none;
                }
            
                QScrollBar:horizontal {
                    background: transparent;
                    height: 8px;
                    margin: 0px;
                }
            
                QScrollBar::handle:horizontal {
                    background: #dcdcdc;
                    border-radius: 4px;
                    min-width: 20px;
                }
            
                QScrollBar::add-line:horizontal,
                QScrollBar::sub-line:horizontal {
                    width: 0px;
                }
            
                QScrollBar::add-page:horizontal,
                QScrollBar::sub-page:horizontal {
                    background: none;
                }
            """)

    def toggle_side_menu(self):
        self.is_menu_expanded = not self.is_menu_expanded
        is_expanded = self.is_menu_expanded

        # Меняем ширину меню
        self.side_menu.setFixedWidth(200 if is_expanded else 40)

        # Меняем текст кнопок
        self.toggle_menu_button.setText("  Свернуть" if is_expanded else "")
        self.back_button.setText("  Вернуться в меню" if is_expanded else "")

        # Меняем иконку кнопки сворачивания
        icon_name = "go-previous" if is_expanded else "go-next"
        self.toggle_menu_button.setIcon(QIcon.fromTheme(icon_name))

        # Включаем/выключаем остальные кнопки
        self.back_button.setEnabled(is_expanded)

    def select_element(self, item: QListWidgetItem):
        element_name = item.text()
        for element_type in self.game_model.toolbox:
            if element_type.__name__ == element_name:
                self.selected_element_type = element_type
                break

    def _handle_tab_close_requested(self, index: int):
        metadata = self.tab_metadata.get(index)
        if not metadata:
            self.tab_widget.removeTab(index)
            return

        if metadata.get("modified", False):
            tab_title = self.tab_widget.tabText(index).removeprefix("*").strip()
            reply = QMessageBox.question(
                self,
                "Несохранённые изменения",
                f"Сохранить изменения перед закрытием вкладки '{tab_title}'?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
            )
            if reply == QMessageBox.StandardButton.Cancel:
                return
            elif reply == QMessageBox.StandardButton.Save:
                self.save_custom_element()

        self.tab_metadata.pop(index, None)
        self.tab_widget.removeTab(index)

        if self.tab_widget.count() == 0:
            self.back_to_menu_requested.emit()

    def _handle_delete_action(self, item: QListWidgetItem):
        element_name = item.text()
        file_path = os.path.join(USER_ELEMENTS_DIR, f"{element_name}.json")

        if not os.path.isfile(file_path):
            QMessageBox.information(
                self,
                "Удаление запрещено",
                f"Элемент '{element_name}' является встроенным и не может быть удалён."
            )
            return

        confirm = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Удалить кастомный элемент '{element_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.delete_custom_element(element_name)

    def _handle_edit_action(self, item: QListWidgetItem):
        element_name = item.text()
        file_path = os.path.join(USER_ELEMENTS_DIR, f"{element_name}.json")

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    # Пытаемся загрузить весь JSON напрямую как Grid
                    grid = Grid()
                    grid.load_from_dict(data)
                    self.add_new_scene_tab(f"Редакт: {element_name}", grid,
                                           element_name=element_name)
                except Exception as e:
                    QMessageBox.warning(self, "Ошибка загрузки", f"Не удалось загрузить элемент: {e}")
        else:
            QMessageBox.information(self, "Нельзя редактировать", "Этот элемент нельзя редактировать.")

    def _handle_start_simulation(self):
        self.scene.start_simulation()
        self.start_simulation_button.setEnabled(False)

    def _handle_stop_simulation(self):
        self.scene.stop_simulation()
        self.start_simulation_button.setEnabled(True)

    def show_toolbox_context_menu(self, position: QPoint):
        item = self.toolbox.itemAt(position)
        if item is None:
            return

        menu = QMenu()
        edit_action = menu.addAction("Редактировать")
        delete_action = menu.addAction("Удалить")

        action = menu.exec(self.toolbox.viewport().mapToGlobal(position))
        if action == delete_action:
            self._handle_delete_action(item)
        elif action == edit_action:
            self._handle_edit_action(item)

    def refresh_toolbox(self):
        self.toolbox.clear()
        for element_type in self.game_model.toolbox:
            self.toolbox.addItem(element_type.__name__)

    def create_new_custom_element(self):
        name, ok = QInputDialog.getText(self, "Новый элемент", "Введите название элемента:")
        if not ok or not name.strip():
            return

        name = name.strip()

        # Проверим на уникальность
        if any(cls.__name__ == name for cls in self.game_model.toolbox):
            QMessageBox.warning(self, "Ошибка", "Элемент с таким именем уже существует.")
            return

        # Создаём новый пустой grid и сцену
        grid = Grid()
        self.add_new_scene_tab(f"*Редакт: {name}", grid, element_name=name)

    def mark_tab_modified(self, index: int):
        if (self.tab_metadata[index]["modified"] is not None) and (self.tab_metadata[index]["element_name"]):
            tab_name = self.tab_widget.tabText(index)
            if not tab_name.startswith("*"):
                self.tab_widget.setTabText(index, f'*{tab_name}')
            self.tab_metadata[index]["modified"] = True

    def notify_scene_modified(self, scene):
        for index, meta in self.tab_metadata.items():
            if meta["scene"] == scene:
                self.mark_tab_modified(index)
                break

    def save_custom_element(self):
        index = self.tab_widget.currentIndex()
        if index == -1:
            QMessageBox.warning(self, "Нет сцены", "Нет открытой сцены для сохранения.")
            return
        metadata = self.tab_metadata.get(index)
        if not metadata or not metadata.get("element_name"):
            QMessageBox.warning(self, "Нельзя сохранить", "Эта вкладка не является пользовательским элементом.")
            return

        name = metadata["element_name"]
        grid = metadata["grid"]
        grid_dict = grid.to_dict()

        os.makedirs(USER_ELEMENTS_DIR, exist_ok=True)
        filepath = os.path.join(USER_ELEMENTS_DIR, f"{name}.json")

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(grid_dict, f, indent=2)

            # Перегружаем только что сохранённый элемент
            new_class = CustomElementFactory.make_custom_element_class(name, grid_dict)

            # Обновляем имена портов согласно subgrid
            temp_instance = new_class()
            temp_instance.update_port_names_from_subgrid()

            # Если элемента ещё нет в тулбоксе - добавляем
            if not any(cls.__name__ == new_class.__name__ for cls in self.game_model.toolbox):
                self.game_model.toolbox.append(new_class)
                self.toolbox.addItem(new_class.__name__)

            # Убираем звёздочку - признак несохранённых изменений
            tab_name = self.tab_widget.tabText(index)
            if tab_name.startswith("*"):
                self.tab_widget.setTabText(index, tab_name[1:])
            self.tab_metadata[index]["modified"] = False

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить элемент: {e}")

    def delete_custom_element(self, name: str):
        # Удаляем из модели
        self.game_model.toolbox = [
            cls for cls in self.game_model.toolbox if cls.__name__ != name
        ]

        # Удаляем из QListWidget
        items = self.toolbox.findItems(name, Qt.MatchFlag.MatchExactly)
        for item in items:
            row = self.toolbox.row(item)
            self.toolbox.takeItem(row)

        # Удаляем json-файл
        path = os.path.join("user_elements", f"{name}.json")
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось удалить файл:\n{e}")

    def add_new_scene_tab(self, name: str, grid: Grid, element_name: Optional[str] = None):
        scene = GameScene(grid)
        scene.set_parent_ui(self)

        view = QGraphicsView(scene)
        view.setRenderHint(QPainter.RenderHint.Antialiasing)

        index = self.tab_widget.addTab(view, name)
        self.tab_widget.setCurrentIndex(index)

        self.tab_metadata[index] = {
            "scene": scene,
            "grid": grid,
            "element_name": element_name,
            "modified": False
        }

    def check_level(self):
        if not self.game_model.current_level:
            QMessageBox.information(self, "Проверка уровня", "Уровень не загружен.")
            return

        if not self.game_model.grid.is_valid_circuit():
            QMessageBox.warning(self, "Проверка уровня", "Схема не собрана.")
            self.truth_table_view.reset_highlight()
            return

        level = self.game_model.current_level
        input_names = level.input_names
        output_names = level.output_names

        available_inputs = {e.name for e in self.game_model.grid.get_input_elements()}
        available_outputs = {e.name for e in self.game_model.grid.get_output_elements()}

        missing_inputs = [name for name in input_names if name not in available_inputs]
        missing_outputs = [name for name in output_names if name not in available_outputs]

        if missing_inputs or missing_outputs:
            msg = "Отсутствующие элементы схемы:\n"
            if missing_inputs:
                msg += f" - Входы: {', '.join(missing_inputs)}\n"
            if missing_outputs:
                msg += f" - Выходы: {', '.join(missing_outputs)}"
            QMessageBox.warning(self, "Проверка уровня", msg)
            self.truth_table_view.reset_highlight()
            return

        errors = self.game_model.check_level()

        if errors:
            self.truth_table_view.highlight_errors(errors)
            QMessageBox.warning(self, "Проверка уровня", f"Ошибки в схеме: {len(errors)} строк(и) не совпадают.")
        else:
            QMessageBox.information(self, "Успех", "Уровень пройден!")
            self.truth_table_view.reset_highlight()
            if self.game_model.current_level:
                self.level_completed.emit(self.game_model.current_level)
