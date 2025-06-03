import itertools
import json
import math
import os
from typing import Tuple, Set, Dict, List, Optional

from PyQt6.QtWidgets import QMainWindow, QWidget, QPushButton, QGraphicsScene, \
    QGraphicsView, QGraphicsItem, QGraphicsLineItem, QHBoxLayout, QListWidget, \
    QCheckBox, QGraphicsProxyWidget, QGraphicsPathItem, QTableWidget, QTableWidgetItem, QAbstractItemView, QLabel, \
    QVBoxLayout, QStackedWidget, QFrame, QLineEdit, QMessageBox, QMenu, QDialog, QFormLayout, QInputDialog, QTabWidget, \
    QListWidgetItem
from PyQt6.QtGui import QPen, QBrush, QColor, QPainter, QTransform, QPainterPath, QIcon
from PyQt6.QtCore import Qt, QPointF, QRectF, QPointF, pyqtSignal, QPoint

from core import InputElement, GameModel, Grid, Level, LogicElement, make_custom_element_class
from core.level_repository import get_all_levels
from tests.test_core import model
from .render_strategy import get_render_strategy_for

CELL_SIZE = 15
USER_ELEMENTS_DIR = "user_elements"

class LogicElementItem(QGraphicsItem):
    def __init__(self, logic_element, x, y):
        super().__init__()
        self.logic_element = logic_element
        self.setPos(x, y)
        self.painter_strategy = get_render_strategy_for(self.logic_element)
        self.ports = self.create_ports()
        self.is_selected = False
        self.selected_port_index = None
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            if self.scene() and hasattr(self.scene(), "update_connections"):
                self.scene().update_connections()
            if self.scene() and hasattr(self.scene(), 'notify_modified'):
                self.scene().notify_modified()

        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            new_pos = value  # QPointF

            # Привязываем к сетке
            snapped_x = round(new_pos.x() / CELL_SIZE)
            snapped_y = round(new_pos.y() / CELL_SIZE)
            snapped_pos = QPointF(snapped_x * CELL_SIZE, snapped_y * CELL_SIZE)

            # Проверка — можно ли туда поставить элемент?
            if self.scene() and hasattr(self.scene(), "parent") and self.scene().parent():
                success = self.scene().grid.move_element(self.logic_element, snapped_x, snapped_y)
                if success:
                    return snapped_pos
                else:
                    # Вернуть старую позицию
                    if self.logic_element.position:
                        old_x, old_y = self.logic_element.position
                        return QPointF(old_x * CELL_SIZE, old_y * CELL_SIZE)

        return super().itemChange(change, value)

    def boundingRect(self):
        w = self.logic_element.width
        h = self.logic_element.height
        return QRectF(0, 0, w * CELL_SIZE, h * CELL_SIZE)

    def create_ports(self):
        return self.painter_strategy.create_ports(self.logic_element, self)

    def paint(self, painter: QPainter, option, widget):
        rect = self.boundingRect()
        is_selected = self.scene().selected_element == self
        painter_strategy = get_render_strategy_for(self.logic_element)
        painter_strategy.paint(painter, rect, self.logic_element, is_selected, self)


class TruthTableView(QTableWidget):
    def __init__(self):
        super().__init__()
        self._truth_table = {}

    def set_table(self, truth_table, input_names=None, output_names=None):
        """Отображает таблицу истинности."""
        self._truth_table = truth_table
        self.clear()

        if not truth_table:
            self.setRowCount(0)
            self.setColumnCount(0)
            return

        input_count = len(next(iter(truth_table)))
        output_count = len(next(iter(truth_table.values())))

        self.setRowCount(len(truth_table))
        self.setColumnCount(input_count + output_count)

        # Заголовки согласно названиям эл-в определённым в уровне
        if input_names is None:
            input_names = [f'In {i+1}' for i in range(input_count)]
        if output_names is None:
            output_names = [f'Out {i+1}' for i in range(output_count)]

        self.setHorizontalHeaderLabels(input_names + output_names)

        for row_idx, (inputs, outputs) in enumerate(truth_table.items()):
            for col_idx, val in enumerate(inputs + outputs):
                item = QTableWidgetItem(str(val))
                item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.setItem(row_idx, col_idx, item)

        self.resizeColumnsToContents()

    def highlight_errors(self, errors):
        """Подсвечивает ошибки в таблице или очищает подсветку."""
        # Очистка всех предыдущих подсветок
        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                item = self.item(row, col)
                if item:
                    item.setBackground(QColor("white"))

        if not errors:
            return  # Если ошибок нет — выходим

        error_inputs_set = set(e[0] for e in errors)
        for row_idx, (inputs, _) in enumerate(self._truth_table.items()):
            if inputs in error_inputs_set:
                for col in range(self.columnCount()):
                    item = self.item(row_idx, col)
                    if item:
                        item.setBackground(QColor("red"))

    def reset_highlight(self):
        self.highlight_errors([])


class LogicGameScene(QGraphicsScene):
    def __init__(self, grid: Grid):
        super().__init__()
        self.setSceneRect(0, 0, 700, 700)
        self.grid = grid
        self._parent_ui = None
        self.selected_port = None
        self.selected_element = None
        self.connections = []
        self.draw_grid()
        self.render_elements()
        self.update_connections()

    def set_parent_ui(self, ui):
        self._parent_ui = ui

    def parent(self):
        return self._parent_ui

    def draw_grid(self):
        dot_pen = QPen(QColor(200, 200, 200))
        dot_pen.setWidth(2)
        for x in range(0, int(self.width()), CELL_SIZE):
            for y in range(0, int(self.height()), CELL_SIZE):
                self.addEllipse(x, y, 1, 1, dot_pen)

    def render_elements(self):
        # Удаляем старые визуальные элементы
        for item in self.items():
            if isinstance(item, LogicElementItem):
                self.removeItem(item)

        # Добавляем новые
        for element in self.grid.elements:
            x, y = element.position
            item = LogicElementItem(element, x * CELL_SIZE, y * CELL_SIZE)
            self.addItem(item)

    def addItem(self, item: QGraphicsItem):
        super().addItem(item)
        self.notify_modified()
        if isinstance(item, LogicElementItem) and isinstance(item.logic_element, InputElement):
            self._add_input_switch(item)

    def _add_input_switch(self, item: LogicElementItem):
        button = QCheckBox()
        button.setChecked(item.logic_element.get_output_values()[0] == 1)

        proxy = QGraphicsProxyWidget(item)
        proxy.setWidget(button)

        # Получим высоту кнопки после её размещения
        button_height = button.sizeHint().height()

        # Центрирование по высоте элемента
        element_pixel_height = item.logic_element.height * CELL_SIZE
        y = (element_pixel_height - button_height) // 2

        proxy.setPos(5, y)

        def _on_toggle():
            item.logic_element.set_value(1 if button.isChecked() else 0)
            self.update_outputs()
            self.update()

        button.toggled.connect(_on_toggle)

    def select_item(self, item: LogicElementItem):
        self.clear_selection()
        self.selected_element = item
        item.is_selected = True

    def delete_element(self, item: LogicElementItem):
        self.removeItem(item)
        self.remove_connections_of(item.logic_element)
        self.grid.remove_element(item.logic_element)
        self.selected_element = None
        self.notify_modified()

    def mousePressEvent(self, event):
        item = self.itemAt(event.scenePos(), QTransform())

        if isinstance(item, LogicElementItem):
            clicked_on_port = False

            if event.button() == Qt.MouseButton.RightButton:
                # Контекстное меню
                menu = QMenu()
                edit_action = menu.addAction("Редактировать")
                delete_action = menu.addAction("Удалить")
                action = menu.exec(event.screenPos())

                if action == edit_action:
                    self.show_edit_dialog(item)
                elif action == delete_action:
                    self.delete_element(item)
                return

            for x, y, port_type, port_index in item.ports:
                if (event.scenePos() - item.scenePos() - QPointF(x, y)).manhattanLength() < 6:
                    clicked_on_port = True

                    # Повторное нажатие — удаляем соединения
                    if self.selected_element == item and self.selected_port == (port_type, port_index):
                        item.logic_element.disconnect_port(port_type, port_index)
                        self.update_connections()
                        self.clear_selection()
                        return
                    # Первый порт
                    if self.selected_port is None:
                        self.select_item(item)
                        self.selected_port = (port_type, port_index)
                        item.selected_port_index = port_index
                    else:
                        (prev_type, prev_index) = self.selected_port
                        if prev_type != port_type and self.selected_element != item:
                            source, source_idx = (
                                (self.selected_element.logic_element, prev_index)
                                if prev_type == "output" else (item.logic_element, port_index)
                            )
                            target, target_idx = (
                                (item.logic_element, port_index)
                                if prev_type == "output" else (self.selected_element.logic_element, prev_index)
                            )
                            if source.connect_output(source_idx, target, target_idx):
                                self.update_connections()
                                self.update_outputs()
                                self.update()
                        self.clear_selection()
                    break

            if not clicked_on_port:
                self.clear_selection()
                self.selected_element = item
                item.is_selected = True

        else:
            # Клик не по элементу — пробуем разместить новый, если он выбран
            if event.button() == Qt.MouseButton.LeftButton and self._parent_ui.selected_element_type:
                scene_pos = event.scenePos()
                x = math.floor(scene_pos.x() / CELL_SIZE) * CELL_SIZE
                y = math.floor(scene_pos.y() / CELL_SIZE) * CELL_SIZE
                element_type = self._parent_ui.selected_element_type
                element = self.grid.create_element(element_type)
                if self.grid.add_element(element, x // CELL_SIZE, y // CELL_SIZE):
                    item = LogicElementItem(element, x, y)
                    self.addItem(item)
            else:
                self.clear_selection()

        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        item = self.itemAt(event.scenePos(), QTransform())
        if isinstance(item, LogicElementItem):
            scene_pos = item.scenePos() + QPointF(item.boundingRect().width() / 2, item.boundingRect().height() / 2)
            # Пока пустой обработчик, только получаем координаты клика
        super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Backspace:
            if self.selected_element:
                self.delete_element(self.selected_element)

    def notify_modified(self):
        if self._parent_ui:
            self._parent_ui.notify_scene_modified(self)

    def show_edit_dialog(self, item: LogicElementItem):
        dialog = QDialog()
        dialog.setWindowTitle("Редактирование элемента")

        layout = QFormLayout()

        name_edit = QLineEdit(item.logic_element.name)
        layout.addRow("Название элемента:", name_edit)

        input_port_edits = []
        for i in range(item.logic_element.num_inputs):
            edit = QLineEdit(item.logic_element.get_input_port_name(i))
            layout.addRow(f"Вход {i}:", edit)
            input_port_edits.append(edit)

        output_port_edits = []
        for i in range(item.logic_element.num_outputs):
            edit = QLineEdit(item.logic_element.get_output_port_name(i))
            layout.addRow(f"Выход {i}:", edit)
            output_port_edits.append(edit)

        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(lambda: dialog.accept())
        layout.addWidget(save_button)

        dialog.setLayout(layout)

        if dialog.exec():
            # Применяем изменения
            new_name = name_edit.text().strip()
            if new_name != item.logic_element.name:
                success = self.grid.rename_element(item.logic_element, new_name)
                if not success:
                    QMessageBox.warning(None, "Ошибка", "Имя должно быть уникальным.")
                    return

            for i, edit in enumerate(input_port_edits):
                item.logic_element.set_input_port_name(i, edit.text().strip())

            for i, edit in enumerate(output_port_edits):
                item.logic_element.set_output_port_name(i, edit.text().strip())

            self.update()

    def clear_selection(self):
        if self.selected_element:
            self.selected_element.is_selected = False
            self.selected_element.selected_port_index = None
        self.selected_element = None
        self.selected_port = None
        self.update()

    def remove_connections_of(self, element):
        element.disconnect_all()
        self.update_connections()

    def update_outputs(self):
        if self.grid:
            input_values = {
                inp: inp.value()
                for inp in self.grid.get_input_elements()
            }
            self.grid.compute_outputs(input_values)

    def update_connections(self):
        for conn in self.connections:
            self.removeItem(conn)
        self.connections.clear()

        for element_item in self.items():
            if not isinstance(element_item, LogicElementItem):
                continue

            for output_index, output_conns in enumerate(element_item.logic_element.output_connections):
                for target, target_port in output_conns:
                    for other_item in self.items():
                        if isinstance(other_item, LogicElementItem) and other_item.logic_element == target:
                            # Получаем координаты выходного порта по индексу
                            source_port = next(
                                (x for x in element_item.ports if x[2] == 'output' and x[3] == output_index), None
                            )
                            target_port_info = next(
                                (x for x in other_item.ports if x[2] == 'input' and x[3] == target_port), None
                            )

                            if source_port is None or target_port_info is None:
                                continue  # защита от ошибок

                            # Локальные координаты в координаты сцены
                            source_point = element_item.mapToScene(QPointF(source_port[0], source_port[1]))
                            target_point = other_item.mapToScene(QPointF(target_port_info[0], target_port_info[1]))
                            x1, y1 = source_point.x(), source_point.y()
                            x2, y2 = target_point.x(), target_point.y()

                            # Построение ортогонального пути
                            path = QPainterPath(QPointF(x1, y1))
                            mid_x = (x1 + x2) / 2
                            path.lineTo(mid_x, y1)
                            path.lineTo(mid_x, y2)
                            path.lineTo(x2, y2)

                            path_item = QGraphicsPathItem(path)
                            path_item.setPen(QPen(Qt.GlobalColor.black, 2))
                            self.connections.append(path_item)
                            self.addItem(path_item)


class LogicGameUI(QMainWindow):
    back_to_menu_requested = pyqtSignal()

    def __init__(self, game_model):
        super().__init__()
        self.game_model = game_model
        self.selected_element_type = None
        self.selected_port = None
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
        self.side_menu.setFrameShape(QFrame.Shape.StyledPanel)

        menu_layout = QVBoxLayout(self.side_menu)
        menu_layout.setContentsMargins(5, 5, 5, 5)

        # Кнопка сворачивания меню
        self.toggle_menu_button = QPushButton()
        self.toggle_menu_button.setIcon(QIcon.fromTheme(QIcon.ThemeIcon.EditUndo))
        self.toggle_menu_button.setStyleSheet("text-align: left;")
        self.toggle_menu_button.clicked.connect(self.toggle_side_menu)
        self.toggle_menu_button.setFixedHeight(40)
        menu_layout.addWidget(self.toggle_menu_button)

        # Кнопка "Назад на главную"
        self.back_button = QPushButton()
        self.back_button.setIcon(QIcon.fromTheme("go-home"))
        self.back_button.setStyleSheet("text-align: left;")
        self.back_button.setFixedHeight(40)
        self.back_button.clicked.connect(self.back_to_menu_requested.emit)
        menu_layout.addWidget(self.back_button)

        menu_layout.addStretch()
        main_layout.addWidget(self.side_menu)

        # === ЦЕНТРАЛЬНАЯ ЧАСТЬ - ГРАФИЧЕСКОЕ ПОЛЕ ===
        self.scene = LogicGameScene(self.game_model.grid)
        self.scene.set_parent_ui(self)
        self.scene.grid.set_level(self.game_model.current_level)

        # Вкладка текущего уровня
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.tabCloseRequested.connect(self._handle_tab_close_requested)
        main_layout.addWidget(self.tab_widget, stretch=3)
        self.tabs: List[Tuple[LogicGameScene, QGraphicsView]] = []
        self.add_new_scene_tab("Игровое поле", self.game_model.grid)

        # === ПРАВАЯ ЧАСТЬ - ПАНЕЛЬ УПРАВЛЕНИЯ ===
        side_panel = QVBoxLayout()

        # Тулбокс (панель элементов)
        self.toolbox = QListWidget()
        self.toolbox.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.toolbox.customContextMenuRequested.connect(self.show_toolbox_context_menu)
        for element_type in self.game_model.toolbox:
            self.toolbox.addItem(element_type.__name__)
        self.toolbox.itemClicked.connect(self.select_element)
        side_panel.addWidget(QLabel("Элементы:"))
        side_panel.addWidget(self.toolbox)

        # Кнопки удаления и сохранения для элементов
        self.new_element_button = QPushButton("Новый элемент")
        self.new_element_button.clicked.connect(self.create_new_custom_element)
        self.save_element_button = QPushButton("Сохранить")
        self.save_element_button.clicked.connect(self.save_custom_element)
        button_row_layout = QHBoxLayout()
        button_row_layout.setSpacing(5)
        button_row_layout.addWidget(self.new_element_button)
        button_row_layout.addWidget(self.save_element_button)
        side_panel.addLayout(button_row_layout)

        # Таблица истинности
        self.truth_table_view = TruthTableView()
        level = self.game_model.current_level
        self.truth_table_view.set_table(
            level.truth_table,
            input_names=level.input_names,
            output_names=level.output_names
        )
        side_panel.addWidget(self.truth_table_view)

        # Кнопка проверки уровня
        self.test_button = QPushButton("Проверить уровень")
        self.test_button.clicked.connect(self.check_level)
        side_panel.addWidget(self.test_button)

        side_widget = QWidget()
        side_widget.setLayout(side_panel)
        main_layout.addWidget(side_widget, stretch=1)

    def toggle_side_menu(self):
        self.is_menu_expanded = not self.is_menu_expanded
        if self.is_menu_expanded:
            self.side_menu.setFixedWidth(200)
            self.toggle_menu_button.setText("  Свернуть")
            self.back_button.setText("  Вернуться в меню")
        else:
            self.side_menu.setFixedWidth(40)
            self.toggle_menu_button.setText("")
            self.back_button.setText("")

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
                new_class = make_custom_element_class(name, grid_dict)

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
        scene = LogicGameScene(grid)
        scene.set_parent_ui(self)

        view = QGraphicsView(scene)
        view.setRenderHint(QPainter.RenderHint.Antialiasing)

        index = self.tab_widget.addTab(view, name)
        self.tab_widget.setCurrentIndex(index)

        self.tab_metadata[index] = {
            "scene": scene,
            "grid": grid,
            "element_name": element_name,
            "modified": True
        }

    def check_level(self):
        if not self.game_model.current_level:
            print("Уровень не загружен.")
            return

        if not self.game_model.grid.is_valid_circuit():
            print("Схема не собрана.")
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
            print("Отсутствующие элементы схемы (проверьте корректность названий):")
            if missing_inputs:
                print(f"  Входы: {', '.join(missing_inputs)}")
            if missing_outputs:
                print(f"  Выходы: {', '.join(missing_outputs)}")
            self.truth_table_view.reset_highlight()
            return

        errors = self.game_model.check_level()

        if errors:
            print("Ошибки в схеме:", errors)
            self.truth_table_view.highlight_errors(errors)
        else:
            print("Уровень пройден!")
            self.truth_table_view.reset_highlight()


class MainMenuWidget(QWidget):
    level_selected = pyqtSignal(int)  # Сигнал, чтобы передать номер уровня

    def __init__(self, levels):
        super().__init__()
        self.levels = levels
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        title = QLabel("Выберите уровень")
        layout.addWidget(title)

        for i, level in enumerate(self.levels):
            btn = QPushButton(f"Уровень {i + 1}")
            btn.clicked.connect(lambda checked, index=i: self.level_selected.emit(index))
            layout.addWidget(btn)

        self.setLayout(layout)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Logic Circuit Game")
        self.setGeometry(100, 100, 1000, 700)

        self.levels = get_all_levels()

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.menu = MainMenuWidget(self.levels)
        self.menu.level_selected.connect(self.load_level)

        self.stack.addWidget(self.menu)
        self.stack.setCurrentWidget(self.menu)

    def load_level(self, level_index: int):
        level = self.levels[level_index]
        model = GameModel(level)
        self.game_ui = LogicGameUI(model)
        self.game_ui.back_to_menu_requested.connect(self.show_menu)

        self.stack.addWidget(self.game_ui)
        self.stack.setCurrentWidget(self.game_ui)

    def show_menu(self):
        self.stack.setCurrentWidget(self.menu)
