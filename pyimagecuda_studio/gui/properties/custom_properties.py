from PySide6.QtWidgets import QLabel, QPushButton
from PySide6.QtCore import Qt, QPoint

from ...nodes.constraints import INT, FLOAT

class ToggleButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._checked = False
        self.setCheckable(True)
        self.setFixedHeight(30)
        self.update_style()
        self.clicked.connect(self._on_clicked)
    
    def _on_clicked(self):
        self._checked = not self._checked
        self.update_style()
    
    def setChecked(self, checked):
        self._checked = checked
        super().setChecked(checked)
        self.update_style()
    
    def isChecked(self):
        return self._checked
    
    def update_style(self):
        if self._checked:
            self.setText("Active")
        else:
            self.setText("Inactive")

class DraggableLabel(QLabel):
    def __init__(self, text, widget, constraint, callback):
        super().__init__(text)
        self.widget = widget
        self.constraint = constraint
        self.callback = callback
        self.dragging = False
        self.last_pos = QPoint()
        self.setCursor(Qt.SizeHorCursor)
        self.setStyleSheet("QLabel:hover { color: #4A9EFF; }")
        
    def mousePressEvent(self, event):
        if not self.isEnabled():
            event.ignore()
            return
            
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.last_pos = event.globalPosition().toPoint()
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if not self.isEnabled():
            event.ignore()
            return
            
        if self.dragging:
            current_pos = event.globalPosition().toPoint()
            delta = current_pos.x() - self.last_pos.x()
            
            if isinstance(self.constraint, INT):
                sensitivity = 0.5
                new_value = self.widget.value() + int(delta * sensitivity)
                new_value = max(self.constraint.min_value, min(self.constraint.max_value, new_value))
                self.widget.setValue(new_value)
                
            elif isinstance(self.constraint, FLOAT):
                range_size = self.constraint.max_value - self.constraint.min_value
                sensitivity = range_size / 500.0
                
                modifiers = event.modifiers()
                if modifiers & Qt.ShiftModifier:
                    sensitivity *= 0.1
                elif modifiers & Qt.ControlModifier:
                    sensitivity *= 10.0
                
                new_value = self.widget.value() + (delta * sensitivity)
                new_value = max(self.constraint.min_value, min(self.constraint.max_value, new_value))
                self.widget.setValue(new_value)
            
            self.last_pos = current_pos
            self.callback()
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        if not self.isEnabled():
            event.ignore()
            return
            
        if event.button() == Qt.LeftButton:
            self.dragging = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        if not self.isEnabled():
            event.ignore()
            return
            
        if event.button() == Qt.LeftButton:
            self.widget.setFocus()
            self.widget.selectAll()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)