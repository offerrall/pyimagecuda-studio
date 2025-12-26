from PySide6.QtWidgets import QToolBar, QWidget, QSizePolicy
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import QSize, Qt, QPoint
from functools import partial

from ..qt_helpers import get_layout
from .node_graph import NodeGraphicsView
from ..config import *
from ...nodes.node_factory import get_node_menu_structure

class NodeEditor(QWidget):
    def __init__(self):
        super().__init__()

        self.view = NodeGraphicsView()
        self.toolbar = self.create_toolbar()

        self.setLayout(get_layout('hbox', [self.toolbar, self.view]))

    def create_toolbar(self):

        def add_spacer(toolbar: QToolBar):
            spacer = QWidget()
            spacer.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
            toolbar.addWidget(spacer)

        def show_all_nodes_menu():
            widget = toolbar.widgetForAction(self.others_action)
            self.view.show_context_menu(widget.mapToGlobal(QPoint(widget.width(), 0)))

        def add_node_center(node_class, node_name):
            center = self.view.mapToScene(self.view.viewport().rect().center())
            self.view.create_node_at_position(node_class, node_name, center)

        toolbar = QToolBar()
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setOrientation(Qt.Vertical)
        add_spacer(toolbar)
        menu_structure = get_node_menu_structure()

        common_nodes = [
            ("Image", menu_structure["Generators"], IMAGE_NODE_PATH),
            ("Text", menu_structure["Generators"], TEXT_NODE_PATH),
            ("Color", menu_structure["Generators"], COLOR_NODE_PATH),
            ("Blend", menu_structure["Merge"], BLEND_NODE_PATH),
            ("Split", menu_structure["Split"], SPLIT_NODE_PATH),
            ("Mask", menu_structure["Merge"], MASK_NODE_PATH),
            ("Scale", menu_structure["Transform"], SCALE_NODE_PATH),
            ("Resize", menu_structure["Transform"], RESIZE_NODE_PATH),
        ]

        for node_name, category, icon_path in common_nodes:
            node_class = category.get(node_name) if isinstance(category, dict) else category
            action = QAction(QIcon(icon_path), node_name, self)
            action.triggered.connect(partial(add_node_center, node_class, node_name))
            toolbar.addAction(action)

        toolbar.addSeparator()
        self.others_action = QAction(QIcon(OTHERS_NODE_PATH), "Others", self)
        self.others_action.triggered.connect(show_all_nodes_menu)
        toolbar.addAction(self.others_action)
        add_spacer(toolbar)

        return toolbar