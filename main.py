from PyQt6.QtWidgets import QApplication
from gui.gui import MainWindow


def main() -> None:
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()