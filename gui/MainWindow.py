from PyQt6.QtWidgets import QMainWindow, QWidget, QPushButton, QLabel, QVBoxLayout, QStackedWidget
from PyQt6.QtCore import pyqtSignal

from core import GameModel, LevelFactory
from gui.GameUI import GameUI

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
            btn = QPushButton(level.name)
            btn.clicked.connect(lambda checked, index=i: self.level_selected.emit(index))
            layout.addWidget(btn)

        self.setLayout(layout)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Logic Circuit Game")
        self.setGeometry(100, 100, 1000, 700)

        self.levels = LevelFactory.get_all_levels()

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.menu = MainMenuWidget(self.levels)
        self.menu.level_selected.connect(self.load_level)

        self.stack.addWidget(self.menu)
        self.stack.setCurrentWidget(self.menu)

    def load_level(self, level_index: int):
        level = self.levels[level_index]
        model = GameModel(level)
        self.game_ui = GameUI(model)
        self.game_ui.back_to_menu_requested.connect(self.show_menu)

        self.stack.addWidget(self.game_ui)
        self.stack.setCurrentWidget(self.game_ui)

    def show_menu(self):
        self.stack.setCurrentWidget(self.menu)
