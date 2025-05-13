from PyQt6.QtWidgets import QApplication
from core import GameModel, InputElement, AndElement, OutputElement
from gui.gui import LogicGameUI, MainWindow


def main() -> None:
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()  # инициализируется только главное окно
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()