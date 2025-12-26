from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsTextItem, QGraphicsEllipseItem
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QBrush, QPen, QColor
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtSvgWidgets import QGraphicsSvgItem
import os

from ..config import EYE_OPEN_PATH, EYE_CLOSED_PATH


class PortWidget(QGraphicsEllipseItem):
    def __init__(self, node_widget, is_input=False, port_number=1):
        super().__init__(-6, -6, 12, 12)
        self.node_widget = node_widget
        self.is_input = is_input
        self.port_number = port_number

        if is_input:
            self.setBrush(QBrush(QColor(180, 100, 100)))
        else:
            self.setBrush(QBrush(QColor(100, 180, 100)))
        
        self.setPen(QPen(QColor(255, 255, 255), 2))
        self.setZValue(3)
        
    def get_center(self):
        return self.mapToScene(QPointF(0, 0))


class HideToggleWidget(QGraphicsSvgItem):
    def __init__(self, node_widget):
        super().__init__()
        self.node_widget = node_widget
        self.is_hidden = False
        
        self.setZValue(4)
        self.setCursor(Qt.PointingHandCursor)
        
        self.eye_open_renderer = QSvgRenderer(EYE_OPEN_PATH)
        self.eye_closed_renderer = QSvgRenderer(EYE_CLOSED_PATH)

        self.setSharedRenderer(self.eye_open_renderer)
        self.setScale(0.025)
        
    def update_state(self, is_hidden):
        self.is_hidden = is_hidden
        
        if is_hidden and self.eye_closed_renderer:
            self.setSharedRenderer(self.eye_closed_renderer)
        elif not is_hidden and self.eye_open_renderer:
            self.setSharedRenderer(self.eye_open_renderer)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            new_state = not self.is_hidden
            self.node_widget.toggle_hide_node(new_state)
            event.accept()
        else:
            super().mousePressEvent(event)


class NodeWidget(QGraphicsRectItem):
    def __init__(self, node, x, y, editor):
        super().__init__(0, 0, 150, 80)
        self.node = node
        self.editor = editor
        self.setPos(x, y)

        has_input = hasattr(node, 'node_connected') or hasattr(node, 'node_connected_1')
        has_output = hasattr(node, 'connect_to') or hasattr(node, 'connect_to_1')
        
        if has_output and not has_input:
            self.setBrush(QBrush(QColor(35, 35, 35)))
        elif has_input and not has_output:
            self.setBrush(QBrush(QColor(70, 70, 70)))
        else:
            self.setBrush(QBrush(QColor(50, 50, 50)))

        self.setPen(QPen(QColor(100, 100, 100), 2))
        self.setFlag(QGraphicsRectItem.ItemIsMovable)
        self.setFlag(QGraphicsRectItem.ItemIsSelectable)
        self.setFlag(QGraphicsRectItem.ItemSendsGeometryChanges)
        self.setZValue(1)

        self.text = QGraphicsTextItem(node.name, self)
        self.text.setDefaultTextColor(QColor(255, 255, 255))

        text_width = self.text.boundingRect().width()
        text_height = self.text.boundingRect().height()
        self.text.setPos(
            (150 - text_width) / 2,
            (80 - text_height) / 2
        )

        self.input_port = None
        self.output_port = None
        self.input_port_2 = None
        self.output_port_2 = None
        self.hide_toggle = None
        
        self._create_ports()
        self._create_hide_toggle()

    def _create_hide_toggle(self):
        if hasattr(self.node, 'hide_node'):
            self.hide_toggle = HideToggleWidget(self)
            self.hide_toggle.setParentItem(self)
            self.hide_toggle.setPos(125, 5)
            self.hide_toggle.update_state(self.node.hide_node)

    def toggle_hide_node(self, new_state):
        if hasattr(self.node, 'hide_node'):
            self.node.hide_node = new_state
            self.hide_toggle.update_state(new_state)
            
            if new_state:
                self.setOpacity(0.4)
            else:
                self.setOpacity(1.0)
            
            print(f"[HIDE_TOGGLE] {self.node.name}.hide_node = {new_state}")
            
            if self.editor:
                self.editor.auto_execute()

    def update_visuals(self):
        self.text.setPlainText(self.node.name)

        text_width = self.text.boundingRect().width()
        text_height = self.text.boundingRect().height()
        
        self.text.setPos(
            (150 - text_width) / 2,
            (80 - text_height) / 2
        )
        
        if self.hide_toggle and hasattr(self.node, 'hide_node'):
            self.hide_toggle.update_state(self.node.hide_node)
        
        self.update()

    def paint(self, painter, option, widget=None):
        painter.setBrush(self.brush())
        
        if self.isSelected():
            selection_pen = QPen(QColor(100, 100, 100), 2, Qt.DashLine)
            painter.setPen(selection_pen)
        else:
            painter.setPen(self.pen())
        
        painter.drawRoundedRect(self.rect(), 10, 10)
        
    def _create_ports(self):
        node = self.node
        
        input_count = 0
        output_count = 0
        
        if hasattr(node, 'node_connected'):
            input_count = 1
        if hasattr(node, 'node_connected_1'):
            input_count = 2
            
        if hasattr(node, 'connect_to'):
            output_count = 1
        if hasattr(node, 'connect_to_1'):
            output_count = 2

        node_height = 80
        
        if input_count == 1:
            input_y = node_height / 2
        elif input_count == 2:
            input_y_1 = node_height / 3
            input_y_2 = (node_height * 2) / 3
            
        if output_count == 1:
            output_y = node_height / 2
        elif output_count == 2:
            output_y_1 = node_height / 3
            output_y_2 = (node_height * 2) / 3

        if input_count >= 1:
            self.input_port = PortWidget(self, is_input=True, port_number=1)
            self.input_port.setParentItem(self)
            self.input_port.setPos(0, input_y if input_count == 1 else input_y_1)

        if input_count == 2:
            self.input_port_2 = PortWidget(self, is_input=True, port_number=2)
            self.input_port_2.setParentItem(self)
            self.input_port_2.setPos(0, input_y_2)

        if output_count >= 1:
            self.output_port = PortWidget(self, is_input=False, port_number=1)
            self.output_port.setParentItem(self)
            self.output_port.setPos(150, output_y if output_count == 1 else output_y_1)

        if output_count == 2:
            self.output_port_2 = PortWidget(self, is_input=False, port_number=2)
            self.output_port_2.setParentItem(self)
            self.output_port_2.setPos(150, output_y_2)
    
    def get_input_port(self, port_number=1):
        if port_number == 1:
            return self.input_port
        elif port_number == 2 and self.input_port_2:
            return self.input_port_2
        return None
    
    def get_output_port(self, port_number=1):
        if port_number == 1:
            return self.output_port
        elif port_number == 2 and self.output_port_2:
            return self.output_port_2
        return None
    
    def itemChange(self, change, value):
        if change == QGraphicsRectItem.ItemPositionChange:
            if self.editor:
                self.editor.update_cables()
        
        return super().itemChange(change, value)