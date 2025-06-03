from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt

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