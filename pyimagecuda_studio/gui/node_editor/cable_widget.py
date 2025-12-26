from PySide6.QtWidgets import QGraphicsPathItem, QStyle
from PySide6.QtCore import QPointF
from PySide6.QtGui import QPen, QColor, QPainterPath


class CableWidget(QGraphicsPathItem):
    def __init__(self, source_node, target_node, source_port_num, target_port_num):
        super().__init__()
        self.source_node = source_node
        self.target_node = target_node
        self.source_port_num = source_port_num
        self.target_port_num = target_port_num
        self.source_port = None
        self.target_port = None
        
        self.normal_pen = QPen(QColor(100, 100, 100), 3)
        self.hover_pen = QPen(QColor(200, 200, 200), 4)
        self.selected_pen = QPen(QColor(255, 255, 255), 4)
        self.setPen(self.normal_pen)
        self.setZValue(0)
        
        self.setFlag(QGraphicsPathItem.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
    
    def set_ports(self, source_port, target_port):
        self.source_port = source_port
        self.target_port = target_port
        self.update_position()
    
    def update_position(self):
        if self.source_port and self.target_port:
            start = self.source_port.get_center()
            end = self.target_port.get_center()
            
            path = QPainterPath(start)
            dx = end.x() - start.x()
            ctrl_offset = abs(dx) * 0.5
            if ctrl_offset < 50:
                ctrl_offset = 50
            
            ctrl1 = QPointF(start.x() + ctrl_offset, start.y())
            ctrl2 = QPointF(end.x() - ctrl_offset, end.y())
            path.cubicTo(ctrl1, ctrl2, end)
            self.setPath(path)
    
    def paint(self, painter, option, widget=None):
        option.state &= ~QStyle.State_Selected
        super().paint(painter, option, widget)
    
    def hoverEnterEvent(self, event):
        if not self.isSelected():
            self.setPen(self.hover_pen)
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        if self.isSelected():
            self.setPen(self.selected_pen)
        else:
            self.setPen(self.normal_pen)
        super().hoverLeaveEvent(event)
    
    def itemChange(self, change, value):
        if change == QGraphicsPathItem.ItemSelectedChange:
            if value:
                self.setPen(self.selected_pen)
            else:
                self.setPen(self.normal_pen)
        return super().itemChange(change, value)