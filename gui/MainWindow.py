from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QMainWindow, QWidget, QPushButton, QLabel, QVBoxLayout, QStackedWidget, QFrame, QScrollArea, \
    QSizePolicy
from PyQt6.QtCore import pyqtSignal, Qt

from core.Level import Level
from core.GameModel import GameModel
from core.LevelFactory import LevelFactory
from gui.GameUI import GameUI

class MainMenuWidget(QWidget):
    level_selected = pyqtSignal(int)

    def __init__(self, levels, unlocked_levels=1):
        super().__init__()
        self.levels = levels
        self.level_buttons = []
        self.unlocked_levels = unlocked_levels
        self.init_ui()

    def init_ui(self):
        outer_layout = QVBoxLayout()
        outer_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        outer_layout.setContentsMargins(40, 40, 40, 40)

        title = QLabel("Logic Circuit Game")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer_layout.addWidget(title)

        level_list = QVBoxLayout()
        level_list.setSpacing(15)

        for i, level in enumerate(self.levels):
            btn = QPushButton(level.name)
            btn.clicked.connect(lambda checked, index=i: self.level_selected.emit(index))
            btn.setEnabled(level.unlocked)  # блокируем, если уровень не открыт
            self.level_buttons.append(btn)  # сохраняем кнопку
            level_list.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)

        container = QFrame()
        container.setLayout(level_list)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(container)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        outer_layout.addWidget(scroll)
        self.setLayout(outer_layout)
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
            }
            QPushButton {
                padding: 10px;
                width: 500px;
                font-size: 14px;
                border-radius: 10px;
                background-color: #ffffff;
                border: 1px solid #cccccc;
            }
            QPushButton:hover {
                background-color: #e6f2ff;
            }
            QPushButton:disabled {
                color: #999999;
                background-color: #dddddd;
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

    def update_buttons(self):
        for i, btn in enumerate(self.level_buttons):
            btn.setEnabled(self.levels[i].unlocked)

    def unlock_next_level_by_level(self, completed_level: Level):
        for i, level in enumerate(self.levels):
            if level == completed_level:
                next_index = i + 1
                if next_index < len(self.levels):
                    self.levels[next_index].unlocked = True
                    self.update_buttons()
                break


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Logic Circuit Game")
        self.setGeometry(100, 100, 1000, 700)
        self.levels = LevelFactory.get_all_levels()
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.main_menu = MainMenuWidget(levels=self.levels, unlocked_levels=1)
        self.main_menu.level_selected.connect(self.load_level)
        self.stack.addWidget(self.main_menu)
        self.stack.setCurrentWidget(self.main_menu)

    def load_level(self, level_index: int):
        level = self.levels[level_index]
        model = GameModel(level)
        self.game_ui = GameUI(model)
        self.game_ui.back_to_menu_requested.connect(self.show_menu)
        self.game_ui.level_completed.connect(
            lambda level: self.main_menu.unlock_next_level_by_level(level)
        )

        self.stack.addWidget(self.game_ui)
        self.stack.setCurrentWidget(self.game_ui)

    def show_menu(self):
        self.stack.setCurrentWidget(self.main_menu)
