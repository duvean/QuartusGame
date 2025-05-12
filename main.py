import sys
from PyQt6.QtWidgets import QApplication
from core import GameModel, InputElement, AndElement, OutputElement
from gui.gui import LogicGameUI


def main() -> None:
    app = QApplication(sys.argv)
    game_model = GameModel()
    game_model.start_level(0)
    ui = LogicGameUI(game_model)
    ui.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()