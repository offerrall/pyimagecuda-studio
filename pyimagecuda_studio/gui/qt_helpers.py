from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout
from PySide6.QtCore import QObject, QEvent
from PySide6.QtWidgets import QDockWidget
from PySide6.QtCore import Qt

from typing import Literal

def get_layout(type: Literal['hbox', 'vbox'], widgets: list[QWidget] | None = None) -> QHBoxLayout | QVBoxLayout:
    lay_type = QHBoxLayout if type == 'hbox' else QVBoxLayout
    layout = lay_type()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    if widgets:
        for widget in widgets:
            layout.addWidget(widget)
    return layout

class PopupCloseFilter(QObject):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Hide:
            self.callback()
        return False

def create_dock(parent, title: str, widget: QWidget, area: Qt.DockWidgetArea, min_width: int = 300, min_height: int = 300) -> QDockWidget:
    dock = QDockWidget(title)
    dock.setWidget(widget)
    dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
    parent.addDockWidget(area, dock)
    dock.setMinimumWidth(min_width)
    dock.setMinimumHeight(min_height)
    return dock