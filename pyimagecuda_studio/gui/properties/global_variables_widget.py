from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QScrollArea, QFrame, QLineEdit, QComboBox, QPushButton, QMessageBox, QFormLayout)
from PySide6.QtCore import Qt

from .properties_factory import create_widget_from_param
from ...nodes.global_variables import get_all_variables, add_variable, set_variable_value, remove_variable
from ...nodes.constraints import TYPE_MAP, ParamInfo

class GlobalVariablesWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.variable_added_callback = None
        self.variable_deleted_callback = None
        self.variable_value_changed_callback = None
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        title_label = QLabel("Global Variables")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)

        add_widget = QWidget()
        add_layout = QFormLayout(add_widget)
        add_layout.setContentsMargins(0, 0, 0, 0)
        add_layout.setSpacing(3)

        self.name_input = QLineEdit()
        add_layout.addRow("Name:", self.name_input)

        self.type_combo = QComboBox()
        self.type_combo.addItems(TYPE_MAP.keys())
        add_layout.addRow("Type:", self.type_combo)

        self.add_button = QPushButton("Add Variable")
        self.add_button.clicked.connect(self.on_add_variable)
        add_layout.addRow(self.add_button)
        
        main_layout.addWidget(add_widget)
        
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator2)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(2)
        self.content_layout.setAlignment(Qt.AlignTop)
        
        scroll.setWidget(self.content_widget)
        main_layout.addWidget(scroll)
        
        self.refresh()
    
    def on_add_variable(self):
        name = self.name_input.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Invalid Name", "Variable name cannot be empty.")
            return

        existing_vars = get_all_variables()
        if any(v.name == name for v in existing_vars):
            QMessageBox.warning(self, "Duplicate Name", f"Variable '{name}' already exists.")
            return
        
        selected_type = self.type_combo.currentText()
        var_type = TYPE_MAP[selected_type]

        add_variable(name, var_type)
        self.name_input.clear()
        self.refresh()
        print(f"[GUI] Added global variable: {name} ({selected_type})")
        if self.variable_added_callback:
            self.variable_added_callback()
    
    def on_variable_changed(self, var_name, param_name, value):
        set_variable_value(var_name, value)
        print(f"[GUI] Updated global variable: {var_name} = {value}")
        
        variables = get_all_variables()
        var = next((v for v in variables if v.name == var_name), None)
        
        if var and len(var.links) > 0:
            if self.variable_value_changed_callback:
                self.variable_value_changed_callback()
        else:
            print(f"[GUI] Variable '{var_name}' has no links, skipping execution")
    
    def on_delete_variable(self, var_name):
        reply = QMessageBox.question(
            self,
            "Delete Variable",
            f"Are you sure you want to delete '{var_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                remove_variable(var_name)
                self.refresh()
                print(f"[GUI] Deleted global variable: {var_name}")
                if self.variable_deleted_callback:
                    self.variable_deleted_callback()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete variable:\n{str(e)}")
    
    def refresh(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        variables = get_all_variables()
        
        if not variables:
            no_vars_label = QLabel("No variables defined")
            self.content_layout.addWidget(no_vars_label)
            return
        
        for var in variables:
            var_widget = self._create_variable_widget(var)
            self.content_layout.addWidget(var_widget)
    
    def _create_variable_widget(self, var):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        header_layout = QHBoxLayout()
        name_label = QLabel(f"<b>{var.name}</b>")
        header_layout.addWidget(name_label)
        
        type_name = type(var.type).__name__
        type_label = QLabel(f"({type_name})")
        type_label.setStyleSheet("color: #888;")
        header_layout.addWidget(type_label)
        header_layout.addStretch()
        
        delete_button = QPushButton("Delete")
        delete_button.setFixedWidth(60)
        delete_button.clicked.connect(lambda: self.on_delete_variable(var.name))
        header_layout.addWidget(delete_button)
        
        layout.addLayout(header_layout)
        
        if var.links:
            links_label = QLabel(f"Linked to {len(var.links)} parameter(s)")
            links_label.setStyleSheet("color: #666; font-size: 10px;")
            layout.addWidget(links_label)
        
        param_info = ParamInfo("value", var.value, type(var.value), var.type)
        
        editor_widget, draggable_label, display_name = create_widget_from_param(
            param_info,
            on_change_callback=lambda pname, value, vname=var.name: self.on_variable_changed(vname, pname, value),
            parent=self
        )
        
        value_layout = QHBoxLayout()
        value_layout.setSpacing(5)
        
        if draggable_label:
            value_layout.addWidget(draggable_label)
        else:
            value_label = QLabel("Value:")
            value_layout.addWidget(value_label)
        
        value_layout.addWidget(editor_widget, 1)
        layout.addLayout(value_layout)
        
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        
        return widget