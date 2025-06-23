from PyQt6.QtWidgets import QGraphicsItem
from PyQt6.QtGui import QPainter
from PyQt6.QtCore import QRectF, QPointF, Qt

from gui.ElementRenderStrategy import get_render_strategy_for

CELL_SIZE = 15

class LogicElementItem(QGraphicsItem):
    def __init__(self, logic_element, x, y):
        super().__init__()
        self.logic_element = logic_element
        self.setPos(x, y)
        self.render_strategy = get_render_strategy_for(self.logic_element)
        self.ports = self.create_ports()
        self.is_selected = False
        self.selected_port_index = None
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            new_pos = value  # QPointF

            # Привязываем к сетке
            snapped_x = round(new_pos.x() / CELL_SIZE)
            snapped_y = round(new_pos.y() / CELL_SIZE)
            snapped_pos = QPointF(snapped_x * CELL_SIZE, snapped_y * CELL_SIZE)

            # Проверка — можно ли туда поставить элемент?
            if self.scene() and hasattr(self.scene(), "parent") and self.scene().parent():
                success = self.scene().grid.move_element(self.logic_element, snapped_x, snapped_y)
                if success:
                    return snapped_pos
                else:
                    # Вернуть старую позицию
                    if self.logic_element.position:
                        old_x, old_y = self.logic_element.position
                        return QPointF(old_x * CELL_SIZE, old_y * CELL_SIZE)

        return super().itemChange(change, value)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.scene() and hasattr(self.scene(), "update_connections"):
                self.scene().update_connections()
            if self.scene() and hasattr(self.scene(), 'notify_modified'):
                self.scene().notify_modified()
        super().mouseReleaseEvent(event)

    def boundingRect(self) -> QRectF:
        w = self.logic_element.width
        h = self.logic_element.height
        return QRectF(0, 0, w * CELL_SIZE, h * CELL_SIZE)

    def create_ports(self):
        return self.render_strategy.create_ports(self.logic_element, self)

    def paint(self, painter: QPainter, option, widget):
        rect = self.boundingRect()
        is_selected = self in self.scene().selected_elements
        painter_strategy = get_render_strategy_for(self.logic_element)
        painter_strategy.paint(painter, rect, self.logic_element, is_selected, self)
