from PySide6.QtWidgets import (QLabel, QWidget, QVBoxLayout, QFormLayout, QFrame, 
                               QHBoxLayout, QPushButton, QMenu)
from PySide6.QtCore import Qt, QTimer, Signal

from .properties_factory import create_widget_from_param
from ...nodes.core import Node
from ...nodes.constraints import get_annotated_params, class_to_type_map, IMAGE_PATH, INT, FLOAT, TEXT
from ...nodes.global_variables import link_to_node, unlink_from_node, get_linked_variable, get_all_variables
from ...nodes.serialization import EXECUTABLE_CODE_NODES


class ParamRowWidget(QWidget):
    link_changed = Signal(str, str, str)
    
    def __init__(self, node_id: str, param_name: str, param_type: type, parent=None):
        super().__init__(parent)
        self.node_id = node_id
        self.param_name = param_name
        self.param_type = param_type
        
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(5)
        
        self.link_indicator = QLabel("🔗")
        self.link_indicator.setToolTip("Linked to global variable")
        self.link_indicator.setStyleSheet("color: #4CAF50; font-size: 14px;")
        self.link_indicator.setVisible(False)
        self.main_layout.addWidget(self.link_indicator)
        
        self.widget_container = QWidget()
        self.widget_layout = QHBoxLayout(self.widget_container)
        self.widget_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.widget_container, 1)
        
        self.menu_button = QPushButton("⋮")
        self.menu_button.setFixedSize(20, 20)
        self.menu_button.setStyleSheet("QPushButton { padding: 0px; }")
        self.menu_button.clicked.connect(self.show_context_menu)
        self.main_layout.addWidget(self.menu_button)
        
        self.param_widget = None
        self.draggable_label = None
        self.normal_label = None
        self.linked_var_name = None
        self.update_link_status()
    
    def set_param_widget(self, widget: QWidget, draggable_label=None, normal_label=None):
        self.param_widget = widget
        self.draggable_label = draggable_label
        self.normal_label = normal_label
        self.widget_layout.addWidget(widget)
        self.update_widget_state()
    
    def update_link_status(self):
        self.linked_var_name = get_linked_variable(self.node_id, self.param_name)
        self.link_indicator.setVisible(self.linked_var_name is not None)
        
        if self.linked_var_name:
            self.link_indicator.setToolTip(f"Linked to: {self.linked_var_name}")
            self.setStyleSheet("ParamRowWidget { background-color: rgba(76, 175, 80, 0.1); border-radius: 3px; }")
        else:
            self.setStyleSheet("")
        
        self.update_widget_state()
    
    def update_widget_state(self):
        is_linked = self.linked_var_name is not None
        
        if self.param_widget:
            self.param_widget.setEnabled(not is_linked)
        
        if self.draggable_label:
            self.draggable_label.setEnabled(not is_linked)
            if is_linked:
                self.draggable_label.setStyleSheet("QLabel { color: #888; }")
            else:
                self.draggable_label.setStyleSheet("QLabel:hover { color: #4A9EFF; }")
        
        if self.normal_label:
            if is_linked:
                self.normal_label.setStyleSheet("QLabel { color: #888; }")
            else:
                self.normal_label.setStyleSheet("")
    
    def show_context_menu(self):
        menu = QMenu(self)
        
        if self.linked_var_name:
            unlink_action = menu.addAction(f"Unlink from '{self.linked_var_name}'")
            unlink_action.triggered.connect(self.unlink_variable)
        else:
            variables = get_all_variables()
            compatible_vars = []
            for v in variables:
                var_type = type(v.type)
                param_type = self.param_type
                
                if var_type == param_type:
                    compatible_vars.append(v)
                elif (var_type == INT and param_type == FLOAT) or (var_type == FLOAT and param_type == INT):
                    compatible_vars.append(v)
            
            if compatible_vars:
                link_menu = menu.addMenu("🔗 Link to variable")
                for var in compatible_vars:
                    action = link_menu.addAction(f"{var.name}")
                    action.triggered.connect(lambda checked=False, v=var.name: self.link_variable(v))
            else:
                if self.param_type == INT or self.param_type == FLOAT:
                    no_vars_action = menu.addAction(f"No variables of type int or float")
                else:
                    param_type_name = class_to_type_map(self.param_type)
                    no_vars_action = menu.addAction(f"No variables of type {param_type_name}")
                no_vars_action.setEnabled(False)
        
        menu.exec_(self.menu_button.mapToGlobal(self.menu_button.rect().bottomLeft()))
    
    def link_variable(self, var_name: str):
        link_to_node(var_name, self.node_id, self.param_name)
        self.update_link_status()
        self.link_changed.emit(self.node_id, self.param_name, var_name)
    
    def unlink_variable(self):
        if self.linked_var_name:
            unlink_from_node(self.linked_var_name, self.node_id, self.param_name)
            self.update_link_status()
            self.link_changed.emit(self.node_id, self.param_name, None)


class NodePropertiesWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        self.execute_callback = None
        self.node_updated_callback = None
        self.global_var_linked_callback = None
        
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        
        self.title_label = QLabel("No node selected")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.title_label)
        self.main_layout.addWidget(separator)
        
        self.form_container = QWidget()
        self.form_layout = QFormLayout(self.form_container)
        self.main_layout.addWidget(self.form_container)
        
        self.main_layout.addStretch()
        
        self.current_selected_id = None
        self.current_node = None
        self.param_rows = {}
    
    def on_param_changed(self, param_name, value):
        if not self.current_node:
            return

        linked_var = get_linked_variable(self.current_node.id, param_name)
        if linked_var:
            return

        current_value = getattr(self.current_node, param_name)
        if current_value == value:
            return

        if param_name == "name":
            if value == "":
                value = "Node"
            self.current_node.update_param(param_name, value)
            self.title_label.setText(f"Node: {self.current_node.name}")
            if self.node_updated_callback:
                self.node_updated_callback(self.current_node.id)
        else:
            self.current_node.update_param(param_name, value)

        if self.execute_callback and param_name != "name":
            self.execute_callback()

            params = get_annotated_params(self.current_node)
            param = next((p for p in params if p.name == param_name), None)
            if param and isinstance(param.constraint, IMAGE_PATH):
                QTimer.singleShot(500, self.refresh_current_properties)
    
    def on_link_changed(self, node_id, param_name, var_name):
        if self.global_var_linked_callback:
            self.global_var_linked_callback()
    
    def refresh_current_properties(self):
        if self.current_selected_id and self.current_node:
            self.update_properties([self.current_selected_id], [self.current_node])

    def update_properties(self, selected_node_ids: list[str], nodes: list[Node]):
        self.clear_form()
        self.param_rows.clear()
        
        if not selected_node_ids:
            self.current_selected_id = None
            self.current_node = None
            self.title_label.setText("No node selected")
        else:
            self.current_selected_id = selected_node_ids[0]
            node = next((n for n in nodes if n.id == self.current_selected_id), None)
            if node:
                self.current_node = node
                self.title_label.setText(f"Node: {node.name}")

                if node.name == "Output":
                    return
                
                hidden_props = node.properties_not_show
                is_executable_code_node = type(node).__name__ in EXECUTABLE_CODE_NODES

                params = get_annotated_params(node)
                for param in params:
                    if param.name in hidden_props:
                        continue

                    widget, draggable_label, display_name = create_widget_from_param(
                        param,
                        on_change_callback=self.on_param_changed,
                        parent=self
                    )

                    is_code_field = is_executable_code_node and isinstance(param.constraint, TEXT)
                    
                    if param.name == "name" or is_code_field:
                        if display_name is None:
                            self.form_layout.addRow(widget)
                        elif draggable_label:
                            self.form_layout.addRow(draggable_label, widget)
                        else:
                            label = QLabel(f"{display_name}:")
                            self.form_layout.addRow(label, widget)
                    else:
                        param_row = ParamRowWidget(
                            node.id, 
                            param.name, 
                            type(param.constraint),
                            self
                        )
                        
                        if display_name is None:
                            param_row.set_param_widget(widget, draggable_label, None)
                            param_row.link_changed.connect(self.on_link_changed)
                            self.param_rows[param.name] = param_row
                            self.form_layout.addRow(param_row)
                        elif draggable_label:
                            param_row.set_param_widget(widget, draggable_label, None)
                            param_row.link_changed.connect(self.on_link_changed)
                            self.param_rows[param.name] = param_row
                            self.form_layout.addRow(draggable_label, param_row)
                        else:
                            label = QLabel(f"{display_name}:")
                            param_row.set_param_widget(widget, None, label)
                            param_row.link_changed.connect(self.on_link_changed)
                            self.param_rows[param.name] = param_row
                            self.form_layout.addRow(label, param_row)
            else:
                self.current_node = None
                self.title_label.setText("Node not found")
    
    def update_link_indicators(self):
        for param_row in self.param_rows.values():
            param_row.update_link_status()
    
    def clear_form(self):
        while self.form_layout.count():
            item = self.form_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def check_deleted_nodes(self, deleted_node_ids):
        if self.current_selected_id and self.current_selected_id in deleted_node_ids:
            self.current_selected_id = None
            self.current_node = None
            self.title_label.setText("No node selected")
            self.clear_form()
            self.param_rows.clear()