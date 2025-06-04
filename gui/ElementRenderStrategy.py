from abc import ABC, abstractmethod

from PyQt6.QtGui import QPainter, QBrush, QColor, QPen, QPainterPath
from PyQt6.QtCore import QRectF, Qt, QPointF
from core.LogicElements import AndElement, NotElement, InputElement, OutputElement, OrElement, XorElement

CELL_SIZE = 25

class AbstractElementPainter(ABC):
    @abstractmethod
    def paint(self, painter: QPainter, rect: QRectF, element, is_selected: bool, game_item) -> None:
        raise NotImplementedError

    @abstractmethod
    def create_ports(self, element, game_item) -> list[tuple[int, int, str, int]]:
        raise NotImplementedError

    @staticmethod
    def paint_ports(painter: QPainter, element, game_item) -> None:
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

            port_name = None
            value = None

            if port_type == "input" and port_index < len(element.input_connections):
                port_name = element.input_names[port_index]
                conns = element.input_connections[port_index]

                if isinstance(conns, list):
                    for conn in conns:
                        if conn is None:
                            continue
                        source, source_port = conn
                        if 0 <= source_port < len(source.get_output_values()):
                            if source.get_output_values()[source_port]:
                                value = 1
                                break
                    else:
                        value = 0
                elif isinstance(conns, tuple):
                    source, source_port = conns
                    if 0 <= source_port < len(source.get_output_values()):
                        value = source.get_output_values()[source_port]
            elif port_type == "output":
                port_name = element.output_names[port_index]
                if 0 <= port_index < len(element.get_output_values()):
                    value = element.get_output_values()[port_index]

            # Отображение значения
            if value is not None:
                painter.setPen(Qt.GlobalColor.black)
                if port_type == "output":
                    painter.drawText(QPointF(x + 5, y + 4), f"[{str(value)}]")
                elif port_type == "input":
                    painter.drawText(QPointF(x - 20, y + 4), f"[{str(value)}]")

            # Отображение имени
            if port_name is not None:
                painter.setPen(Qt.GlobalColor.black)
                if port_type == "output":
                    painter.drawText(QPointF(x - 6 - painter.fontMetrics().horizontalAdvance(port_name), y + 4), port_name)
                elif port_type == "input":
                    painter.drawText(QPointF(x + 8, y + 4), port_name)


class DefaultElementPainter(AbstractElementPainter):
    def paint(self, painter, rect, element, is_selected, game_item):
        # Внешний прямоугольник
        painter.setBrush(QBrush(QColor(240, 240, 255)))
        painter.setPen(QPen(Qt.GlobalColor.black, 2 if is_selected else 1))
        painter.drawRect(rect)

        # Параметры внутреннего прямоугольника
        margin = 5
        inner_rect = rect.adjusted(margin, margin + 15, -margin, -margin)

        # Внутренний прямоугольник
        painter.setBrush(QBrush(QColor(200, 200, 255)))
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        painter.drawRect(inner_rect)

        # Название элемента сверху, между прямоугольниками
        painter.setPen(Qt.GlobalColor.black)
        name_rect = QRectF(rect.left(), rect.top(), rect.width(), 15)
        painter.drawText(name_rect, Qt.AlignmentFlag.AlignCenter, element.name)

        # Порты
        self.paint_ports(painter, element, game_item)

    def create_ports(self, element, game_item):
        ports = []

        rect = game_item.boundingRect()
        margin = 5
        inner_rect = rect.adjusted(margin, margin + 15, -margin, -margin)
        total_height = inner_rect.height()
        left_x = inner_rect.left()
        right_x = inner_rect.right()

        def get_centered_ys(num_ports):
            if num_ports == 0:
                return []

            if num_ports == 1:
                return [inner_rect.top() + total_height / 2]

            max_total_spacing = total_height - CELL_SIZE
            spacing = min(CELL_SIZE, max_total_spacing / (num_ports - 1))
            group_height = spacing * (num_ports - 1)
            start_y = inner_rect.top() + (total_height - group_height) / 2
            return [start_y + i * spacing for i in range(num_ports)]

        input_ys = get_centered_ys(element.num_inputs)
        output_ys = get_centered_ys(element.num_outputs)

        for i, y in enumerate(input_ys):
            ports.append((left_x - 3, y, 'input', i))  # левее внутреннего прямоугольника

        for i, y in enumerate(output_ys):
            ports.append((right_x + 3, y, 'output', i))  # правее внутреннего прямоугольника

        return ports


class PrimitiveElementPainter(AbstractElementPainter):
    @abstractmethod
    def paint(self, painter: QPainter, rect: QRectF, element, is_selected: bool, game_item) -> None:
        raise NotImplementedError

    def create_ports(self, element, game_item) -> list[tuple[int, int, str, int]]:
        rect = game_item.boundingRect()

        total_height = rect.height()
        left_x = rect.left()
        right_x = rect.right()

        def get_centered_ys(num_ports):
            if num_ports == 0:
                return []

            if num_ports == 1:
                return [rect.top() + total_height / 2]

            max_total_spacing = total_height - CELL_SIZE
            spacing = min(CELL_SIZE, max_total_spacing / (num_ports - 1))
            group_height = spacing * (num_ports - 1)
            start_y = rect.top() + (total_height - group_height) / 2
            return [start_y + i * spacing for i in range(num_ports)]

        input_ys = get_centered_ys(element.num_inputs)
        output_ys = get_centered_ys(element.num_outputs)

        ports = []
        for i, y in enumerate(input_ys):
            ports.append((left_x + 8, y, 'input', i))
        for i, y in enumerate(output_ys):
            ports.append((right_x - 8, y, 'output', i))

        return ports


class InOutElementPainter(PrimitiveElementPainter):
    def paint(self, painter, rect, element, is_selected, game_item):
        painter.setBrush(QBrush(QColor(180, 220, 255) if is_selected else QColor(200, 200, 255)))
        painter.setPen(QPen(Qt.GlobalColor.black, 2 if is_selected else 1))
        painter.drawRect(rect)
        painter.setPen(Qt.GlobalColor.black)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, element.name)
        self.paint_ports(painter, element, game_item)


class AndElementPainter(PrimitiveElementPainter):
    def paint(self, painter, rect, element, is_selected, game_item):
        painter.setBrush(QBrush(QColor(180, 220, 255) if is_selected else QColor(200, 200, 255)))
        painter.setPen(QPen(Qt.GlobalColor.black, 2 if is_selected else 1))

        left = rect.left()
        right = rect.right()
        top = rect.top()
        bottom = rect.bottom()
        center_y = rect.center().y()
        width = rect.width()
        height = rect.height()
        radius = height / 2

        path = QPainterPath()
        path.moveTo(left + width * 0.08, top)
        path.lineTo(left + width * 0.08 + width / 2, top)
        path.arcTo(left + width * 0.08 + width / 2 - radius, top, height, height, 90, -180)
        path.lineTo(left + width * 0.08, bottom)
        path.closeSubpath()

        painter.drawPath(path)
        painter.setPen(Qt.GlobalColor.black)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, element.name)
        self.paint_ports(painter, element, game_item)


class OrElementPainter(PrimitiveElementPainter):
    def paint(self, painter, rect, element, is_selected, game_item):
        painter.setBrush(QBrush(QColor(180, 220, 255) if is_selected else QColor(200, 200, 255)))
        painter.setPen(QPen(Qt.GlobalColor.black, 2 if is_selected else 1))

        left = rect.left()
        right = rect.right()
        top = rect.top()
        bottom = rect.bottom()
        center_y = rect.center().y()
        width = rect.width()
        height = rect.height()

        path = QPainterPath()
        path.moveTo(left, top)
        path.quadTo(left + width * 0.2, center_y, left, bottom)
        path.quadTo(right - width * 0.2, bottom, right- width * 0.1, center_y)
        path.quadTo(right - width * 0.2, top, left + width * 0.2, top)
        path.closeSubpath()

        painter.drawPath(path)
        painter.setPen(Qt.GlobalColor.black)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, element.name)
        self.paint_ports(painter, element, game_item)


class NotElementPainter(PrimitiveElementPainter):
    def paint(self, painter, rect, element, is_selected, game_item):
        painter.setBrush(QBrush(QColor(180, 220, 255) if is_selected else QColor(200, 200, 255)))
        painter.setPen(QPen(Qt.GlobalColor.black, 2 if is_selected else 1))

        left = rect.left()
        right = rect.right()
        top = rect.top()
        bottom = rect.bottom()
        center_y = rect.center().y()
        width = rect.width()
        height = rect.height()

        path = QPainterPath()
        path.moveTo(left + width * 0.08, top)
        path.lineTo(right - height * 0.2, center_y)
        path.lineTo(left + width * 0.08, bottom)
        path.closeSubpath()
        painter.drawPath(path)

        # Если нужен кружочек
        # circle_radius = rect.height() * 0.1
        # circle_center = QPointF(rect.right() - circle_radius * 2, rect.center().y())
        # painter.drawEllipse(circle_center, circle_radius, circle_radius)

        painter.setPen(Qt.GlobalColor.black)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, element.name)
        self.paint_ports(painter, element, game_item)


class XorElementPainter(PrimitiveElementPainter):
    def paint(self, painter, rect, element, is_selected, game_item):
        painter.setBrush(QBrush(QColor(180, 220, 255) if is_selected else QColor(200, 200, 255)))
        painter.setPen(QPen(Qt.GlobalColor.black, 2 if is_selected else 1))

        left = rect.left()
        right = rect.right()
        top = rect.top()
        bottom = rect.bottom()
        center_y = rect.center().y()
        width = rect.width()
        height = rect.height()

        path = QPainterPath()
        path.moveTo(left + width * 0.15, top)
        path.quadTo(left + width * 0.4, center_y, left + width * 0.15, bottom)
        path.quadTo(right - width * 0.22, bottom, right - width * 0.1, center_y)
        path.quadTo(right - width * 0.22, top, left + width * 0.2, top)
        path.closeSubpath()

        # Внешняя левая дуга (для XOR)
        xor_path = QPainterPath()
        xor_path.moveTo(left, top)
        xor_path.lineTo(left + width * 0.08, top)
        xor_path.quadTo(left + width * 0.33, center_y, left + width * 0.08, bottom)
        xor_path.lineTo(left, bottom)
        xor_path.quadTo(left + width * 0.2, center_y, left, top)
        xor_path.closeSubpath()

        painter.drawPath(path)
        painter.drawPath(xor_path)
        painter.setPen(Qt.GlobalColor.black)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, element.name)
        self.paint_ports(painter, element, game_item)


painter_registry = {
    InputElement: InOutElementPainter(),
    OutputElement: InOutElementPainter(),
    AndElement: AndElementPainter(),
    OrElement: OrElementPainter(),
    NotElement: NotElementPainter(),
    XorElement: XorElementPainter(),
}

default_painter = DefaultElementPainter()

def get_render_strategy_for(element):
    return painter_registry.get(type(element), default_painter)