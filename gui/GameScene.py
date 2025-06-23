import math
from typing import Set

from PyQt6.QtWidgets import (
    QPushButton, QGraphicsScene, QGraphicsItem,
    QCheckBox, QGraphicsProxyWidget, QGraphicsPathItem, QLineEdit, QMessageBox,
    QMenu, QDialog, QFormLayout, QComboBox, QVBoxLayout, QTabWidget, QWidget,
    QHBoxLayout, QListWidgetItem, QListWidget
)
from PyQt6.QtGui import QPen, QColor, QTransform, QPainterPath, QIcon, QIntValidator, QCursor
from PyQt6.QtCore import Qt, QPointF

from core.LogicElements import InputElement, ClockGeneratorElement
from core.Grid import Grid
from gui.LogicElementItem import LogicElementItem

from core.BehaviorModifiersRegistry import (
    get_available_modifier_names,
    create_modifier_by_name,
    create_modifier_editor,
)

CELL_SIZE = 15

class GameScene(QGraphicsScene):
    def __init__(self, grid: Grid):
        super().__init__()
        self.setSceneRect(0, 0, 1200, 800)
        self.grid = grid
        self._parent_ui = None
        self.selected_port = None
        self.selected_element = None
        self.selected_elements: Set[LogicElementItem] = set()
        self.clipboard_data = None
        self.clipboard_offset = QPointF(20, 20)
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
        elif isinstance(item, LogicElementItem) and isinstance(item.logic_element, ClockGeneratorElement):
            item.logic_element.get_timer().timeout.connect(self.update_scene)
            self._add_clock_controls(item)

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
            self.update_scene()

        button.toggled.connect(_on_toggle)

    def _add_clock_controls(self, item: LogicElementItem):
        from PyQt6.QtWidgets import QPushButton

        # Поле ввода интервала
        interval_input = QLineEdit(str(item.logic_element.interval_ms))
        interval_input.setFixedWidth(50)
        interval_input.setFixedHeight(15)
        interval_input.setStyleSheet("""
                        QLineEdit {
                            background: #fffff0;
                            border: 1px solid #cccccc;
                        }
                    """)
        interval_input.setValidator(QIntValidator(10, 10000))  # от 10 до 10_000 мс
        interval_proxy = QGraphicsProxyWidget(item)
        interval_proxy.setWidget(interval_input)

        # Кнопка "Старт"
        start_button = QPushButton()
        start_button.setIcon(QIcon.fromTheme("media-playback-start"))
        start_button.setToolTip("Start Clock")
        start_button.setObjectName("startButton")
        start_button.setStyleSheet("background-color: #ddffdd; border: 1px solid #77aa77;")

        start_proxy = QGraphicsProxyWidget(item)
        start_proxy.setWidget(start_button)

        # Кнопка "Стоп"
        stop_button = QPushButton()
        stop_button.setIcon(QIcon.fromTheme("media-playback-stop"))
        stop_button.setToolTip("Stop Clock")
        stop_button.setObjectName("stopButton")
        stop_button.setStyleSheet("background-color: #ffdddd; border: 1px solid #aa7777;")

        stop_proxy = QGraphicsProxyWidget(item)
        stop_proxy.setWidget(stop_button)

        # CSS для кнопок
        style = """
        QPushButton#startButton {
            background-color: #ddffdd;
            border: 1px solid #77aa77;
            border-radius: 0px;
        }
        QPushButton#startButton:hover {
            background-color: #bbffbb;
            border-color: #559955;
        }
        QPushButton#startButton:pressed {
            background-color: #99cc99;
            border-color: #336633;
        }

        QPushButton#stopButton {
            background-color: #ffdddd;
            border: 1px solid #aa7777;
            border-radius: 0px;
        }
        QPushButton#stopButton:hover {
            background-color: #ffbbbb;
            border-color: #aa5555;
        }
        QPushButton#stopButton:pressed {
            background-color: #cc9999;
            border-color: #883333;
        }
        """
        start_button.setStyleSheet(style)
        stop_button.setStyleSheet(style)

        interval_proxy.setPos(57, 23)
        start_proxy.setPos(29, 21)
        stop_proxy.setPos(6, 21)

        def on_start():
            item.logic_element.start()

        def on_stop():
            item.logic_element.stop()

        def on_interval_changed():
            try:
                val = int(interval_input.text())
                item.logic_element.interval_ms = val
                if item.logic_element._timer.isActive():
                    item.logic_element.stop()
                    item.logic_element.start()
            except ValueError:
                pass

        start_button.clicked.connect(on_start)
        stop_button.clicked.connect(on_stop)
        interval_input.editingFinished.connect(on_interval_changed)

    def start_simulation(self):
        for element in self.grid.elements:
            if isinstance(element, ClockGeneratorElement):
                element.start()

    def stop_simulation(self):
        for element in self.grid.elements:
            if isinstance(element, ClockGeneratorElement):
                element.stop()

    def select_item(self, item: LogicElementItem, additive=False):
        if not additive:
            self.clear_selection()

        if not item.is_selected:
            self.selected_elements.add(item)
            item.is_selected = True
            self.selected_element = item  # основной (для редактирования/соединения)
        else:
            self.selected_elements.remove(item)
            item.is_selected = False
            self.selected_element = None

    def clear_selection(self):
        for item in self.selected_elements:
            item.is_selected = False
            item.selected_port_index = None
        self.selected_elements.clear()
        self.selected_port = None
        self.selected_element = None
        self.update()

    def place_element(self, type, pos):
        x = math.floor(pos.x() / CELL_SIZE) * CELL_SIZE
        y = math.floor(pos.y() / CELL_SIZE) * CELL_SIZE

        element = self.grid.create_element(type)
        if not element:
            return

        success = self.grid.add_element(element, x // CELL_SIZE, y // CELL_SIZE)
        if not success:
            return

        item = LogicElementItem(element, x, y)
        self.addItem(item)

    @staticmethod
    def connect_elements(source, source_idx, target, target_idx) -> bool:
        return source.connect_output(source_idx, target, target_idx)

    def delete_element(self, item: LogicElementItem):
        if item.scene() is self:
            self.removeItem(item)
        self.remove_connections_of(item.logic_element)
        self.grid.remove_element(item.logic_element)
        self.selected_element = None
        self.notify_modified()

    def mousePressEvent(self, event):
        item = self.itemAt(event.scenePos(), QTransform())

        if isinstance(item, LogicElementItem):
            additive = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
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
                            if self.connect_elements(source, source_idx, target, target_idx):
                                self.update_connections()
                                self.tick()
                                self.update()
                        self.clear_selection()
                    break

            if not clicked_on_port:
                self.select_item(item, additive=additive)

        else:
            # Клик не по элементу — пробуем разместить новый, если он выбран
            if event.button() == Qt.MouseButton.LeftButton and self._parent_ui.selected_element_type:
                element_type = self._parent_ui.selected_element_type
                scene_pos = event.scenePos()
                self.place_element(element_type, scene_pos)
            else:
                self.clear_selection()

        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        item = self.itemAt(event.scenePos(), QTransform())
        if isinstance(item, LogicElementItem):
            # Получаем координаты в сцене
            scene_pos = item.scenePos() + QPointF(item.boundingRect().width() / 2, item.boundingRect().height() / 2)

            # Создаем QLineEdit
            view = self.views()[0]  # QGraphicsView
            edit = QLineEdit(item.logic_element.name, view)
            edit.move(view.mapFromScene(scene_pos))
            edit.setFixedWidth(100)
            edit.setFocus()
            edit.selectAll()
            edit.show()

            def finish_editing():
                new_name = edit.text().strip()
                if new_name and new_name != item.logic_element.name:
                    success = self.grid.rename_element(item.logic_element, new_name)
                    if success:
                        self.update()
                    else:
                        QMessageBox.warning(view, "Ошибка", "Имя должно быть уникальным.")
                edit.deleteLater()

            edit.editingFinished.connect(finish_editing)
            return

        super().mouseDoubleClickEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.update()
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        modifiers = event.modifiers()
        key = event.key()

        if modifiers == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_C:
            self.copy_selected()
            event.accept()
            return
        elif modifiers == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_X:
            self.copy_selected()
            for item in list(self.selected_elements):
                self.delete_element(item)
            self.update()
            event.accept()
            return
        elif modifiers == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_V:
            self.paste_clipboard()
            self.update()
            event.accept()
            return
        elif key in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete):
            for item in list(self.selected_elements):
                self.delete_element(item)
            self.update()
            event.accept()
            return

        super().keyPressEvent(event)
        event.accept()

    def copy_selected(self):
        elements_data = []
        connections = []
        selected = list(self.selected_elements)
        if not selected:
            return

        selected_names = {item.logic_element.name for item in selected}

        # Вычисляем самую левую верхнюю точку
        min_x = min(item.x() for item in selected)
        min_y = min(item.y() for item in selected)
        top_left = QPointF(min_x, min_y)

        for item in selected:
            element = item.logic_element
            rel_pos = QPointF(item.x(), item.y()) - top_left
            data = {
                'type': type(element),
                'name': element.name,
                'rel_pos': rel_pos,
                'element': element
            }
            elements_data.append(data)

            # сохраняем только входящие соединения от других выделенных
            for input_index, input_conns in enumerate(element.input_connections):
                for src_element, src_index in input_conns:
                    if src_element.name in selected_names:
                        connections.append((src_element.name, src_index, element.name, input_index))

        self.clipboard_data = {
            'elements': elements_data,
            'connections': connections
        }

    def paste_clipboard(self):
        if not self.clipboard_data:
            return

        elements_data = self.clipboard_data['elements']
        connections = self.clipboard_data['connections']
        name_map = {}
        new_items = []
        mouse_pos = self.views()[0].mapToScene(self.views()[0].mapFromGlobal(QCursor.pos()))

        for data in elements_data:
            orig_element = data['element']
            new_name = self.grid.generate_unique_name(orig_element.name.split()[0])
            new_element = type(orig_element)()
            new_element.name = new_name

            offset_pos = data['rel_pos'] + mouse_pos
            x = int(offset_pos.x()) // CELL_SIZE * CELL_SIZE
            y = int(offset_pos.y()) // CELL_SIZE * CELL_SIZE

            if self.grid.add_element(new_element, x // CELL_SIZE, y // CELL_SIZE):
                item = LogicElementItem(new_element, x, y)
                self.addItem(item)
                new_items.append(item)
                name_map[data['name']] = new_element

        # восстановление связей между новыми элементами
        for src_name, src_idx, dst_name, dst_idx in connections:
            src_elem = name_map.get(src_name)
            dst_elem = name_map.get(dst_name)
            if src_elem and dst_elem:
                try:
                    src_elem.output_connections[src_idx].append((dst_elem, dst_idx))
                    dst_elem.input_connections[dst_idx].append((src_elem, src_idx))
                except Exception as e:
                    print(f"Ошибка при восстановлении соединения: {e}")

        # обновление сцены
        self.clear_selection()
        for item in new_items:
            self.select_item(item, additive=True)
        self.update_connections()

    def notify_modified(self):
        if self._parent_ui:
            self._parent_ui.notify_scene_modified(self)

    def show_edit_dialog(self, item: LogicElementItem):
        dialog = EditElementInstanceDialog(self.grid, item.logic_element)
        if dialog.exec():
            if dialog.apply_changes():
                self.notify_modified()
                self.update()

    def remove_connections_of(self, element):
        element.disconnect_all()
        self.update_connections()

    def tick(self):
        if self.grid:
            input_values = {
                inp: inp.value()
                for inp in self.grid.get_input_elements()
            }
            self.grid.compute_outputs(input_values)

    def update_scene(self):
        self.tick()
        self.update()

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


class EditElementInstanceDialog(QDialog):
    def __init__(self, grid, logic_element, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Редактирование элемента")
        self.grid = grid
        self.logic_element = logic_element
        self._modifier_editors = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()

        self.tabs.addTab(self._create_general_tab(), "Общие")
        self.tabs.addTab(self._create_modifiers_tab(), "Модификаторы")

        layout.addWidget(self.tabs)

        buttons = QHBoxLayout()
        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

    def _create_general_tab(self):
        self._name_edit = QLineEdit(self.logic_element.name)
        self._name_edit.selectAll()

        self._input_port_edits = []
        self._output_port_edits = []

        form = QFormLayout()
        form.addRow("Название элемента:", self._name_edit)

        for i in range(self.logic_element.num_inputs):
            edit = QLineEdit(self.logic_element.get_input_port_name(i))
            self._input_port_edits.append(edit)
            form.addRow(f"Вход {i}:", edit)

        for i in range(self.logic_element.num_outputs):
            edit = QLineEdit(self.logic_element.get_output_port_name(i))
            self._output_port_edits.append(edit)
            form.addRow(f"Выход {i}:", edit)

        container = QWidget()
        container.setLayout(form)
        return container

    def _create_modifiers_tab(self):
        self._modifier_list = QListWidget()

        for mod in self.logic_element.modifiers:
            editor = create_modifier_editor(mod)
            if editor:
                self._modifier_editors[mod] = editor
                self._modifier_list.addItem(QListWidgetItem(mod.__class__.__name__))

        self._modifier_editor_container = QWidget()
        self._modifier_editor_layout = QVBoxLayout(self._modifier_editor_container)
        self._modifier_editor_container.setLayout(self._modifier_editor_layout)

        self._modifier_list.currentRowChanged.connect(self._on_modifier_selected)

        add_layout = QHBoxLayout()
        self._modifier_combo = QComboBox()
        self._modifier_combo.addItems(get_available_modifier_names())
        add_btn = QPushButton("Добавить")
        add_btn.clicked.connect(self._on_add_modifier)
        del_btn = QPushButton("Удалить")
        del_btn.clicked.connect(self._on_remove_modifier)
        add_layout.addWidget(self._modifier_combo)
        add_layout.addWidget(add_btn)
        add_layout.addWidget(del_btn)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self._modifier_list)
        main_layout.addLayout(add_layout)
        main_layout.addWidget(self._modifier_editor_container)

        container = QWidget()
        container.setLayout(main_layout)
        return container

    def _on_modifier_selected(self, index):
        for i in reversed(range(self._modifier_editor_layout.count())):
            widget = self._modifier_editor_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        if index < 0 or index >= len(self.logic_element.modifiers):
            return

        mod = self.logic_element.modifiers[index]
        editor = self._modifier_editors.get(mod)
        if editor:
            self._modifier_editor_layout.addWidget(editor)

    def _on_add_modifier(self):
        name = self._modifier_combo.currentText()
        new_mod = create_modifier_by_name(name)
        if new_mod is None:
            return

        editor = create_modifier_editor(new_mod)
        if editor is None:
            return

        self.logic_element.modifiers.append(new_mod)
        self._modifier_editors[new_mod] = editor
        self._modifier_list.addItem(name)

    def _on_remove_modifier(self):
        index = self._modifier_list.currentRow()
        if index < 0:
            return

        mod = self.logic_element.modifiers.pop(index)
        self._modifier_editors.pop(mod, None)
        self._modifier_list.takeItem(index)
        self._on_modifier_selected(-1)

    def apply_changes(self):
        new_name = self._name_edit.text().strip()
        if new_name != self.logic_element.name:
            success = self.grid.rename_element(self.logic_element, new_name)
            if not success:
                QMessageBox.warning(self, "Ошибка", "Имя должно быть уникальным.")
                return False

        for i, edit in enumerate(self._input_port_edits):
            self.logic_element.set_input_port_name(i, edit.text().strip())

        for i, edit in enumerate(self._output_port_edits):
            self.logic_element.set_output_port_name(i, edit.text().strip())

        # Применяем параметры модификаторов
        for i, mod in enumerate(self.logic_element.modifiers):
            editor = self._modifier_editors.get(mod)
            if editor:
                self.logic_element.modifiers[i] = editor.get_modifier()

        return True
