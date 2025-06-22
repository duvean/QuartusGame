from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QGraphicsView


class GameView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setMouseTracking(True)
        self._is_panning = False
        self._pan_start = QPoint()
        self._zoom = 1.0
        self._zoom_step = 1.15
        self._zoom_range = (0.1, 10.0)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._is_panning = True
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            self._pan_start = event.pos()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_panning:
            delta = event.pos() - self._pan_start
            self._pan_start = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            old_pos = self.mapToScene(event.position().toPoint())
            delta = event.angleDelta().y()

            if delta > 0:
                zoom_factor = self._zoom_step
            else:
                zoom_factor = 1 / self._zoom_step

            new_zoom = self._zoom * zoom_factor
            if not (self._zoom_range[0] <= new_zoom <= self._zoom_range[1]):
                return

            self._zoom = new_zoom
            self.scale(zoom_factor, zoom_factor)

            new_pos = self.mapToScene(event.position().toPoint())
            offset = new_pos - old_pos
            self.translate(offset.x(), offset.y())
        else:
            super().wheelEvent(event)