import itertools
import math
from typing import Tuple, Set, Dict, List

from PyQt6.QtWidgets import QMainWindow, QWidget, QPushButton, QGraphicsScene, \
    QGraphicsView, QGraphicsItem, QGraphicsLineItem, QHBoxLayout, QListWidget, \
    QCheckBox, QGraphicsProxyWidget, QGraphicsPathItem, QTableWidget, QTableWidgetItem, QAbstractItemView, QLabel, \
    QVBoxLayout
from PyQt6.QtGui import QPen, QBrush, QColor, QPainter, QTransform, QPainterPath
from PyQt6.QtCore import Qt, QPointF, QRectF, QPointF

from core import InputElement
from core.core import TruthTable
from .render_strategy import get_render_strategy_for

CELL_SIZE = 15

class LogicElementItem(QGraphicsItem):
    def __init__(self, logic_element, x, y):
        super().__init__()
        self.logic_element = logic_element
        self.setPos(x, y)
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

        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            new_pos = value  # QPointF

            # Привязываем к сетке
            snapped_x = round(new_pos.x() / CELL_SIZE)
            snapped_y = round(new_pos.y() / CELL_SIZE)
            snapped_pos = QPointF(snapped_x * CELL_SIZE, snapped_y * CELL_SIZE)

            # Проверка — можно ли туда поставить элемент?
            if self.scene() and hasattr(self.scene(), "parent") and self.scene().parent():
                model = self.scene().parent().game_model
                success = model.grid.move_element(self.logic_element, snapped_x, snapped_y)
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
        ports = []
        for i in range(self.logic_element.num_inputs):
            ports.append((10, 10 + i * 15, 'input', i))
        for i in range(self.logic_element.num_outputs):
            ports.append((40, 10 + i * 15, 'output', i))
        return ports

    def paint(self, painter: QPainter, option, widget):
        rect = self.boundingRect()
        is_selected = self.scene().selected_element == self
        painter_strategy = get_render_strategy_for(self.logic_element)
        painter_strategy.paint(painter, rect, self.logic_element, is_selected, self)


class TruthTableView(QTableWidget):
    def __init__(self):
        super().__init__()
        self._truth_table = {}

    def set_table(self, truth_table):
        """Отображает таблицу истинности."""
        self._truth_table = truth_table
        self.clear()
        self.setRowCount(len(truth_table))
        self.setColumnCount(len(next(iter(truth_table))) + len(next(iter(truth_table.values()))))

        input_count = len(next(iter(truth_table)))
        self.setHorizontalHeaderLabels(
            [f'In {i+1}' for i in range(input_count)] +
            [f'Out {i+1}' for i in range(len(next(iter(truth_table.values()))))]
        )

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
    def __init__(self):
        super().__init__()
        self.setSceneRect(0, 0, 700, 700)
        self._parent_ui = None
        self.selected_port = None
        self.selected_element = None
        self.connections = []
        self.draw_grid()

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

    def addItem(self, item: QGraphicsItem):
        super().addItem(item)
        if isinstance(item, LogicElementItem) and isinstance(item.logic_element, InputElement):
            self.add_input_switch(item)

    def add_input_switch(self, item: LogicElementItem):
        button = QCheckBox()
        button.setChecked(item.logic_element.get_output_values()[0] == 1)

        proxy = QGraphicsProxyWidget(item)
        proxy.setWidget(button)
        proxy.setPos(5, 35)

        def on_toggle():
            item.logic_element.set_value(1 if button.isChecked() else 0)
            self.update_outputs()
            self.update()

        button.toggled.connect(on_toggle)

    def select_item(self, item: LogicElementItem):
        self.clear_selection()
        self.selected_element = item
        item.is_selected = True

    def mousePressEvent(self, event):
        item = self.itemAt(event.scenePos(), QTransform())

        if isinstance(item, LogicElementItem):
            clicked_on_port = False
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
            if self._parent_ui.selected_element_type:
                scene_pos = event.scenePos()
                x = math.floor(scene_pos.x() / CELL_SIZE) * CELL_SIZE
                y = math.floor(scene_pos.y() / CELL_SIZE) * CELL_SIZE
                element_type = self._parent_ui.selected_element_type
                element = self._parent_ui.game_model.create_element(element_type)
                if self._parent_ui.game_model.place_element(element, x // CELL_SIZE, y // CELL_SIZE):
                    item = LogicElementItem(element, x, y)
                    self.addItem(item)
            else:
                self.clear_selection()

        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Backspace:
            if self.selected_element:
                self.removeItem(self.selected_element)
                self.remove_connections_of(self.selected_element.logic_element)
                if self.selected_element.logic_element in self._parent_ui.game_model.grid.elements:
                    self._parent_ui.game_model.grid.elements.remove(self.selected_element.logic_element)
                self.selected_element = None

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
        level = self._parent_ui.game_model.current_level
        if level:
            input_values = {
                inp: inp.value()
                for inp in level.get_input_elements()
            }
            level.compute_outputs(input_values)

    def update_connections(self):
        for conn in self.connections:
            self.removeItem(conn)
        self.connections.clear()

        for element_item in self.items():
            if isinstance(element_item, LogicElementItem):
                for output_index, output_conns in enumerate(element_item.logic_element.output_connections):
                    for target, target_port in output_conns:
                        for other_item in self.items():
                            if isinstance(other_item, LogicElementItem) and other_item.logic_element == target:
                                '''
                                x1 = element_item.scenePos().x() + 40
                                y1 = element_item.scenePos().y() + 10 + output_index * 15
                                x2 = other_item.scenePos().x() + 10
                                y2 = other_item.scenePos().y() + 10 + target_port * 15
                                line = QGraphicsLineItem(x1, y1, x2, y2)
                                self.connections.append(line)
                                self.addItem(line)
                                '''
                                # Для ортогональных линий (работает, но пока некрасиво)
                                x1 = element_item.scenePos().x() + 40
                                y1 = element_item.scenePos().y() + 10 + output_index * 15
                                x2 = other_item.scenePos().x() + 10
                                y2 = other_item.scenePos().y() + 10 + target_port * 15

                                path = QPainterPath(QPointF(x1, y1))

                                mid_x = (x1 + x2) / 2
                                path.lineTo(mid_x, y1)  # горизонтально до середины
                                path.lineTo(mid_x, y2)  # вертикально до нужной высоты
                                path.lineTo(x2, y2)  # горизонтально к точке назначения

                                path_item = QGraphicsPathItem(path)
                                path_item.setPen(QPen(Qt.GlobalColor.black, 2))
                                self.connections.append(path_item)
                                self.addItem(path_item)



class LogicGameUI(QMainWindow):
    def __init__(self, game_model):
        super().__init__()
        self.game_model = game_model
        self.selected_element_type = None
        self.selected_port = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Logic Game")
        self.setGeometry(100, 100, 1000, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Левая часть — графическая сцена
        self.scene = LogicGameScene()
        self.scene.set_parent_ui(self)

        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        main_layout.addWidget(self.view, stretch=3)

        # Правая часть — вертикальная панель управления
        side_panel = QVBoxLayout()

        # Toolbox
        self.toolbox = QListWidget()
        for element_type in self.game_model.toolbox:
            self.toolbox.addItem(element_type.__name__)
        self.toolbox.itemClicked.connect(self.select_element)
        side_panel.addWidget(QLabel("Элементы:"))
        side_panel.addWidget(self.toolbox)

        self.truth_table_view = TruthTableView()
        self.truth_table_view.set_table(self.game_model.current_level.truth_table)
        side_panel.addWidget(self.truth_table_view)

        # Кнопка проверки
        self.test_button = QPushButton("Проверить уровень")
        self.test_button.clicked.connect(self.check_level)
        side_panel.addWidget(self.test_button)

        # Оборачиваем в QWidget и добавляем в главный layout
        side_widget = QWidget()
        side_widget.setLayout(side_panel)
        main_layout.addWidget(side_widget, stretch=1)

    def select_element(self, item):
        element_name = item.text()
        for element_type in self.game_model.toolbox:
            if element_type.__name__ == element_name:
                self.selected_element_type = element_type
                break

    def add_element_to_scene(self, element_type, x, y):
        element = self.game_model.create_element(element_type)
        if self.game_model.place_element(element, x // CELL_SIZE, y // CELL_SIZE):
            item = LogicElementItem(element, x, y)
            self.scene.addItem(item)

    def check_level(self):
        errors = self.game_model.check_level()

        if not self.game_model.current_level:
            print("Уровень не загружен.")
            return
        elif not self.game_model.current_level.is_valid_circuit():
            print("Схема не собрана.")
            self.truth_table_view.reset_highlight()
            return

        if errors:
            print("Ошибки в схеме:", errors)
            # Передаём индексы строк с ошибками
            self.truth_table_view.highlight_errors(errors)
        else:
            print("Уровень пройден!")
            self.truth_table_view.reset_highlight()  # Убираем подсветку