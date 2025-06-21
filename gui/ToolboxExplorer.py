import os
import json
import shutil
from collections import defaultdict

from PyQt6.QtWidgets import QTreeView, QMenu, QInputDialog, QMessageBox, QTreeWidgetItem, QTreeWidget
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QAction
from PyQt6.QtCore import Qt, QModelIndex, QPoint

from core import USER_ELEMENTS_DIR
from core.Grid import Grid
from core.CustomElementFactory import CustomElementFactory


class ToolboxExplorer(QTreeWidget):
    def __init__(self, game_ui: 'GameUI'):
        super().__init__()
        self.game_ui = game_ui
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.setHeaderHidden(True)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.itemClicked.connect(self.handle_item_clicked)
        self.reload()

    def reload(self):
        def _get_expanded_paths():
            """Собирает пути (tuple из текстов) до раскрытых узлов"""
            expanded = []

            def recurse(item, path):
                if item.isExpanded():
                    expanded.append(tuple(path))
                for i in range(item.childCount()):
                    recurse(item.child(i), path + [item.child(i).text(0)])

            for i in range(self.topLevelItemCount()):
                recurse(self.topLevelItem(i), [self.topLevelItem(i).text(0)])
            return expanded

        def _restore_expanded_paths(expanded_paths):
            """Восстанавливает раскрытие узлов по путям"""

            def recurse(item, path):
                if tuple(path) in expanded_paths:
                    item.setExpanded(True)
                for i in range(item.childCount()):
                    recurse(item.child(i), path + [item.child(i).text(0)])

            for i in range(self.topLevelItemCount()):
                recurse(self.topLevelItem(i), [self.topLevelItem(i).text(0)])

        # 1. Сохраняем раскрытые пути
        expanded_paths = _get_expanded_paths()

        # 2. Очищаем и загружаем заново
        self.clear()
        self._load_builtin_elements()
        self._load_user_elements()

        # 3. Восстанавливаем раскрытие
        _restore_expanded_paths(expanded_paths)

    def _load_builtin_elements(self):
        primitives_item = QTreeWidgetItem(self, ["Примитивы"])
        groups = defaultdict(list)
        for cls in self.game_ui.game_model.toolbox:
            if getattr(cls, "_is_custom", False):
                continue
            group = getattr(cls, "category", "Вентили")
            groups[group].append(cls)

        for group, classes in groups.items():
            group_item = QTreeWidgetItem(primitives_item, [group])
            for cls in classes:
                item = QTreeWidgetItem(group_item, [cls.__name__])
                item.setData(0, Qt.ItemDataRole.UserRole, cls)

    def _load_user_elements(self):
        if not os.path.exists(USER_ELEMENTS_DIR):
            return

        user_root = QTreeWidgetItem(self, ["Пользовательские"])
        user_root.setData(0, Qt.ItemDataRole.UserRole, {"type": "folder", "path": USER_ELEMENTS_DIR})
        self._load_user_elements_recursive(USER_ELEMENTS_DIR, user_root)

    def _load_user_elements_recursive(self, path: str, parent_item: QTreeWidgetItem):
        for entry in sorted(os.listdir(path)):
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path):
                folder_item = QTreeWidgetItem(parent_item, [entry])
                folder_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "folder", "path": full_path})
                self._load_user_elements_recursive(full_path, folder_item)
            elif entry.endswith(".json"):
                with open(full_path, encoding="utf-8") as f:
                    try:
                        data = json.load(f)
                        cls = CustomElementFactory.make_custom_element_class(entry[:-5], data)
                        cls._is_custom = True  # <-- обязательно!
                        item = QTreeWidgetItem(parent_item, [cls.__name__])
                        item.setData(0, Qt.ItemDataRole.UserRole, cls)
                        item.setData(1, Qt.ItemDataRole.UserRole, {"path": full_path})
                    except Exception:
                        continue

    def handle_item_clicked(self, item: QTreeWidgetItem, _column: int):
        element_class = item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(element_class, type):
            self.game_ui.selected_element_type = element_class

    def show_context_menu(self, position: QPoint):
        item = self.itemAt(position)
        if not item:
            return

        element_data = item.data(0, Qt.ItemDataRole.UserRole)
        menu = QMenu()

        if isinstance(element_data, type):  # логический элемент
            edit_action = menu.addAction("Редактировать")
            delete_action = menu.addAction("Удалить")
            action = menu.exec(self.viewport().mapToGlobal(position))
            if action == delete_action:
                self._handle_delete_element(item)
            elif action == edit_action:
                self._handle_edit_element(item)
        elif isinstance(element_data, dict) and element_data.get("type") == "folder":
            create_file = menu.addAction("Создать элемент")
            create_folder = menu.addAction("Создать папку")
            menu.addSeparator()
            delete_folder = menu.addAction("Удалить папку")
            action = menu.exec(self.viewport().mapToGlobal(position))
            if action == create_file:
                self._handle_create_element(item)
            elif action == create_folder:
                self._handle_create_folder(item)
            elif action == delete_folder:
                self._handle_delete_folder(item)

    def _handle_create_element(self, folder_item: QTreeWidgetItem):
        folder_data = folder_item.data(0, Qt.ItemDataRole.UserRole)
        if not folder_data:
            return
        path = folder_data.get("path")
        name, ok = QInputDialog.getText(self, "Новый элемент", "Введите название элемента:")
        if not ok or not name.strip():
            return

        name = name.strip()
        filepath = os.path.join(path, f"{name}.json")

        if os.path.exists(filepath):
            QMessageBox.warning(self, "Ошибка", "Элемент с таким именем уже существует.")
            return

        self.game_ui.add_new_scene_tab(f"*Редакт: {name}", Grid(), element_name=name, save_path=filepath)

    def _handle_create_folder(self, folder_item: QTreeWidgetItem):
        folder_data = folder_item.data(0, Qt.ItemDataRole.UserRole)
        if not folder_data:
            return
        path = folder_data.get("path")
        name, ok = QInputDialog.getText(self, "Новая папка", "Введите название папки:")
        if not ok or not name.strip():
            return
        new_path = os.path.join(path, name.strip())
        os.makedirs(new_path, exist_ok=True)
        self.reload()

    def _handle_delete_folder(self, item: QTreeWidgetItem):
        folder_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not folder_data or folder_data.get("path") == "builtin":
            QMessageBox.information(self, "Удаление запрещено", "Эту папку нельзя удалить.")
            return

        path = folder_data["path"]
        confirm = QMessageBox.question(
            self, "Подтвердите", f"Удалить папку '{item.text(0)}' и всё содержимое?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            shutil.rmtree(path)
            self.reload()

    def _handle_edit_element(self, item: QTreeWidgetItem):
        path_data = item.data(1, Qt.ItemDataRole.UserRole)
        if not path_data:
            QMessageBox.information(self, "Нельзя редактировать", "Этот элемент нельзя редактировать.")
            return

        path = path_data["path"]
        element_name = item.text(0)

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                grid = Grid()
                grid.load_from_dict(data)
                self.game_ui.add_new_scene_tab(f"Редакт: {element_name}", grid,
                                               element_name=element_name, save_path=path)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить элемент: {e}")

    def _handle_delete_element(self, item: QTreeWidgetItem):
        path_data = item.data(1, Qt.ItemDataRole.UserRole)
        if not path_data:
            QMessageBox.information(self, "Удаление запрещено", "Элемент нельзя удалить.")
            return

        path = path_data["path"]
        element_name = item.text(0)
        confirm = QMessageBox.question(
            self, "Подтвердите", f"Удалить пользовательский элемент '{element_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            os.remove(path)
            self.reload()