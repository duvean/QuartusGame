import math

from PyQt6.QtWidgets import (QPushButton, QGraphicsScene, QGraphicsItem,
     QCheckBox, QGraphicsProxyWidget, QGraphicsPathItem, QLineEdit, QMessageBox,
     QMenu, QDialog, QFormLayout)
from PyQt6.QtGui import QPen, QColor, QTransform, QPainterPath
from PyQt6.QtCore import Qt, QPointF

from core import InputElement, Grid
from gui.LogicElementItem import LogicElementItem

CELL_SIZE = 15

class GameScene(QGraphicsScene):
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
