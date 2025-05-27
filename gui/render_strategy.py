from abc import ABC, abstractmethod

from PyQt6.QtGui import QPainter, QBrush, QColor, QPen
from PyQt6.QtCore import QRectF, Qt, QPointF
from core import AndElement, NotElement

CELL_SIZE = 25

class AbstractElementPainter(ABC):
    @abstractmethod
    def paint(self, painter: QPainter, rect: QRectF, element, is_selected: bool, game_item) -> None:
        raise NotImplementedError

    def draw_ports(self, painter: QPainter, element, game_item) -> None:
        for x, y, port_type, port_index in game_item.ports:
            scene = game_item.scene()
            is_selected_port = (
                    scene and
                    scene.selected_element == game_item and
                    scene.selected_port == (port_type, port_index)
            )
            color = QColor(29, 16, 24) if is_selected_port else QColor(255, 0, 0)

            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(x, y), 6, 6)

            # Отображение значения
            port_name = None
            value = None
            if port_type == "input" and port_index < len(element.input_connections):
                port_name = element.input_names[port_index]
                conn = element.input_connections[port_index]
                if conn is not None:
                    value = conn[0].get_output_values()[conn[1]]
            elif port_type == "output":
                port_name = element.output_names[port_index]
                value = element.get_output_values()[port_index]

            if value is not None:
                painter.setPen(Qt.GlobalColor.black)
                painter.drawText(x - 20, y + 4, f"[{str(value)}]")

            if port_name is not None:
                painter.setPen(Qt.GlobalColor.black)
                painter.drawText(x + 8, y + 4, port_name)


class DefaultElementPainter(AbstractElementPainter):
    def paint(self, painter, rect, element, is_selected, game_item):
        painter.setBrush(QBrush(QColor(180, 220, 255) if is_selected else QColor(200, 200, 255)))
        painter.setPen(QPen(Qt.GlobalColor.black, 2 if is_selected else 1))
        painter.drawRect(rect)
        painter.setPen(Qt.GlobalColor.black)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, element.name)
        self.draw_ports(painter, element, game_item)


class AndRenderStrategy(AbstractElementPainter):
    def paint(self, painter, rect, element, is_selected, game_item):
        painter.setBrush(QBrush(QColor(180, 220, 255) if is_selected else QColor(200, 200, 255)))
        painter.setPen(QPen(Qt.GlobalColor.black, 2 if is_selected else 1))
        painter.drawRect(rect)
        painter.setPen(Qt.GlobalColor.black)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, element.name)
        self.draw_ports(painter, element, game_item)


class NotRenderStrategy(AbstractElementPainter):
    def paint(self, painter, rect, element, is_selected, game_item):
        painter.setBrush(QBrush(QColor(180, 220, 255) if is_selected else QColor(200, 200, 255)))
        painter.setPen(QPen(Qt.GlobalColor.black, 2 if is_selected else 1))
        painter.drawRect(rect)
        painter.setPen(Qt.GlobalColor.black)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, element.name)
        self.draw_ports(painter, element, game_item)


painter_registry = {
    AndElement: AndRenderStrategy(),
    NotElement: NotRenderStrategy(),
}

default_painter = DefaultElementPainter()

def get_render_strategy_for(element):
    return painter_registry.get(type(element), default_painter)