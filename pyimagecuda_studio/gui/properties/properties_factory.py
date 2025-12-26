import os
from PySide6.QtWidgets import (QLabel, QWidget, QVBoxLayout, QHBoxLayout,
                               QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox,
                               QComboBox, QPushButton, QColorDialog, QFileDialog, 
                               QFontComboBox, QPlainTextEdit)
from PySide6.QtGui import QColor, QFont

from .custom_properties import DraggableLabel, ToggleButton
from ..qt_helpers import PopupCloseFilter
from ..config import get_config_value, set_config_value
from ...nodes.constraints import INT, FLOAT, STR, DROPDOWN, CHECKBOX, COLOR, SIZE, IMAGE_PATH, FONT, TEXT


def format_param_name(name):
    return name.replace('_', ' ').title()

def create_widget_from_param(param, on_change_callback=None, parent=None):
    constraint = param.constraint
    display_name = format_param_name(param.name)
    
    def notify_change(value):
        if on_change_callback:
            on_change_callback(param.name, value)

    if isinstance(constraint, STR):
        widget = QLineEdit()
        widget.setText(str(param.value))
        widget.setMaxLength(constraint.max_length)
        widget.editingFinished.connect(lambda: notify_change(widget.text()))
        return widget, None, display_name

    elif isinstance(constraint, TEXT):
        widget = QPlainTextEdit()
        widget.setPlainText(str(param.value))
        widget.setMinimumHeight(100)
        widget.textChanged.connect(lambda: notify_change(widget.toPlainText()))
        return widget, None, display_name

    elif isinstance(constraint, INT):
        widget = QSpinBox()
        widget.setMinimum(constraint.min_value)
        widget.setMaximum(constraint.max_value)
        widget.setValue(param.value)
        widget.valueChanged.connect(lambda: notify_change(widget.value()))
        
        draggable_label = DraggableLabel(
            f"{display_name}:",
            widget,
            constraint,
            lambda: notify_change(widget.value())
        )
        return widget, draggable_label, display_name

    elif isinstance(constraint, FLOAT):
        widget = QDoubleSpinBox()
        widget.setMinimum(constraint.min_value)
        widget.setMaximum(constraint.max_value)
        widget.setValue(param.value)
        widget.setDecimals(2)
        widget.setSingleStep(0.1)
        widget.valueChanged.connect(lambda: notify_change(widget.value()))
        
        draggable_label = DraggableLabel(
            f"{display_name}:",
            widget,
            constraint,
            lambda: notify_change(widget.value())
        )
        return widget, draggable_label, display_name

    elif isinstance(constraint, DROPDOWN):
        widget = QComboBox()
        widget.addItems(constraint.options)
        if param.value in constraint.options:
            widget.setCurrentText(param.value)
        widget.currentTextChanged.connect(lambda text: notify_change(text))
        return widget, None, display_name

    elif isinstance(constraint, CHECKBOX):
        widget = ToggleButton()
        widget.setChecked(bool(param.value))
        widget.clicked.connect(lambda: notify_change(widget.isChecked()))
        return widget, None, display_name

    elif isinstance(constraint, FONT):
        widget = QFontComboBox()
        widget.setFontFilters(QFontComboBox.AllFonts)

        if param.value:
            widget.setCurrentFont(QFont(str(param.value)))
        
        widget.confirmed_font = param.value if param.value else "Sans Serif"

        widget.highlighted.connect(lambda index: notify_change(widget.itemText(index)))
        
        def on_font_activated(index):
            widget.confirmed_font = widget.itemText(index)
            notify_change(widget.confirmed_font)
        
        widget.activated.connect(on_font_activated)

        def on_popup_close():
            notify_change(str(widget.confirmed_font))

        widget._close_filter = PopupCloseFilter(on_popup_close)
        widget.view().installEventFilter(widget._close_filter)

        return widget, None, display_name

    elif isinstance(constraint, COLOR):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        color_button = QPushButton()
        r, g, b, a = param.value
        color_button.setStyleSheet(f"background-color: rgba({int(r*255)}, {int(g*255)}, {int(b*255)}, {a})")
        color_button.color_value = param.value
        
        def pick_color():
            current_value = color_button.color_value
            r, g, b, a = current_value
            
            initial_color = QColor(int(r * 255), int(g * 255), int(b * 255), int(a * 255))
            
            color = QColorDialog.getColor(
                initial_color,
                parent,
                "Choose Color",
                QColorDialog.ShowAlphaChannel
            )
            
            if color.isValid():
                color_button.setStyleSheet(f"background-color: {color.name(QColor.HexArgb)}")
                color_button.color_value = (color.redF(), color.greenF(), color.blueF(), color.alphaF())
                notify_change(color_button.color_value)
        
        color_button.clicked.connect(pick_color)
        layout.addWidget(color_button)

        container.get_value = lambda: color_button.color_value
        
        return container, None, display_name

    elif isinstance(constraint, SIZE):
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(3)
        
        size_row = QWidget()
        h_layout = QHBoxLayout(size_row)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(8)
        
        w_label = QLabel("W:")
        width_spin = QSpinBox()
        width_spin.setMinimum(constraint.min_width)
        width_spin.setMaximum(constraint.max_width)
        width_spin.setValue(param.value[0])
        
        aspect_checkbox = QCheckBox()
        aspect_checkbox.setChecked(True)
        aspect_checkbox.setToolTip("Maintain Aspect Ratio")
        aspect_checkbox.setFixedWidth(20)
        
        h_label = QLabel("H:")
        height_spin = QSpinBox()
        height_spin.setMinimum(constraint.min_height)
        height_spin.setMaximum(constraint.max_height)
        height_spin.setValue(param.value[1])
        
        h_layout.addWidget(w_label)
        h_layout.addWidget(width_spin)
        h_layout.addSpacing(5)
        h_layout.addWidget(aspect_checkbox)
        h_layout.addSpacing(5)
        h_layout.addWidget(h_label)
        h_layout.addWidget(height_spin)
        
        main_layout.addWidget(size_row)
        
        container.width_spin = width_spin
        container.height_spin = height_spin
        container.aspect_checkbox = aspect_checkbox
        container.aspect_ratio = param.value[0] / param.value[1] if param.value[1] != 0 else 1.0
        
        def on_width_changed():
            if aspect_checkbox.isChecked():
                new_height = int(width_spin.value() / container.aspect_ratio)
                height_spin.blockSignals(True)
                height_spin.setValue(new_height)
                height_spin.blockSignals(False)
        
        def on_height_changed():
            if aspect_checkbox.isChecked():
                new_width = int(height_spin.value() * container.aspect_ratio)
                width_spin.blockSignals(True)
                width_spin.setValue(new_width)
                width_spin.blockSignals(False)
        
        def update_aspect_ratio():
            if width_spin.value() != 0 and height_spin.value() != 0:
                container.aspect_ratio = width_spin.value() / height_spin.value()
        
        def on_size_editing_finished():
            update_aspect_ratio()
            notify_change((width_spin.value(), height_spin.value()))
        
        width_spin.valueChanged.connect(on_width_changed)
        height_spin.valueChanged.connect(on_height_changed)
        width_spin.editingFinished.connect(on_size_editing_finished)
        height_spin.editingFinished.connect(on_size_editing_finished)

        container.get_value = lambda: (width_spin.value(), height_spin.value())

        return container, None, None

    elif isinstance(constraint, IMAGE_PATH):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        full_path_str = str(param.value) if param.value else ""
        container.full_path = full_path_str

        def get_display_text(path):
            if not path:
                return "None"
            if len(path) > 15:
                return "..." + path[-15:]
            return path

        path_label = QLabel(get_display_text(full_path_str))
        path_label.setToolTip(full_path_str)
        path_label.setStyleSheet("color: #AAA;")

        browse_button = QPushButton("Browse")
        browse_button.setFixedWidth(70)
        
        def browse_file():
            formats = constraint.format_options
            filter_string = "Images (" + " ".join([f"*.{fmt}" for fmt in formats]) + ")"
            
            last_dir = get_config_value("last_open_image_path", os.path.expanduser("~"))
            
            file_path, _ = QFileDialog.getOpenFileName(
                parent,
                "Select Image",
                last_dir,
                filter_string
            )
            
            if file_path:
                directory = os.path.dirname(file_path)
                set_config_value("last_open_image_path", directory)
                
                container.full_path = file_path
                path_label.setText(get_display_text(file_path))
                path_label.setToolTip(file_path)
                
                notify_change(file_path)
        
        browse_button.clicked.connect(browse_file)
        
        layout.addWidget(path_label)
        layout.addWidget(browse_button)

        container.get_value = lambda: container.full_path
        
        return container, None, display_name

    else:
        label = QLabel(str(param.value))
        return label, None, display_name


def get_widget_value(widget, constraint):

    if isinstance(constraint, STR):
        return widget.text()
    elif isinstance(constraint, TEXT):
        return widget.toPlainText()
    elif isinstance(constraint, INT):
        return widget.value()
    elif isinstance(constraint, FLOAT):
        return widget.value()
    elif isinstance(constraint, DROPDOWN):
        return widget.currentText()
    elif isinstance(constraint, CHECKBOX):
        return widget.isChecked()
    elif isinstance(constraint, FONT):
        return widget.currentFont().family()
    elif isinstance(constraint, COLOR):
        if hasattr(widget, 'get_value'):
            return widget.get_value()
        color_button = widget.findChild(QPushButton)
        if color_button and hasattr(color_button, 'color_value'):
            return color_button.color_value
    elif isinstance(constraint, SIZE):
        if hasattr(widget, 'get_value'):
            return widget.get_value()
        return (widget.width_spin.value(), widget.height_spin.value())
    elif isinstance(constraint, IMAGE_PATH):
        if hasattr(widget, 'get_value'):
            return widget.get_value()
        if hasattr(widget, 'full_path'):
            return widget.full_path
    
    return None