import os
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QComboBox, QSlider, QPushButton, QFileDialog)
from PySide6.QtCore import Qt

from .config import get_config_value, set_config_value


class ExportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Export Image")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        self.format = get_config_value("export_format", "PNG")
        self.quality = get_config_value("export_quality", 95)
        self.filepath = get_config_value("export_filepath", None)
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "JPEG", "WebP", "TIFF"])
        
        self.format_combo.setCurrentText(self.format)
        
        self.format_combo.currentTextChanged.connect(self.on_format_changed)
        format_layout.addWidget(self.format_combo)
        layout.addLayout(format_layout)
        
        self.quality_widget = QVBoxLayout()
        
        quality_label_layout = QHBoxLayout()
        quality_label_layout.addWidget(QLabel("Quality:"))
        self.quality_value_label = QLabel(str(self.quality))
        quality_label_layout.addWidget(self.quality_value_label)
        quality_label_layout.addStretch()
        self.quality_widget.addLayout(quality_label_layout)
        
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setMinimum(1)
        self.quality_slider.setMaximum(100)
        self.quality_slider.setValue(self.quality)
        self.quality_slider.valueChanged.connect(self.on_quality_changed)
        self.quality_widget.addWidget(self.quality_slider)
        
        quality_hint = QLabel("Higher = Better quality, Larger file size")
        quality_hint.setStyleSheet("color: gray; font-size: 10px;")
        self.quality_widget.addWidget(quality_hint)
        
        layout.addLayout(self.quality_widget)
        
        filepath_layout = QHBoxLayout()
        filepath_layout.addWidget(QLabel("Save to:"))
        self.filepath_button = QPushButton("Choose location...")
        self.filepath_button.clicked.connect(self.choose_filepath)
        filepath_layout.addWidget(self.filepath_button)
        layout.addLayout(filepath_layout)
        
        display_path = self.filepath if self.filepath else "No location selected"
        self.filepath_label = QLabel(display_path)
        self.filepath_label.setStyleSheet("color: gray; font-size: 10px;")
        self.filepath_label.setWordWrap(True)
        layout.addWidget(self.filepath_label)
        
        layout.addStretch()
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        self.export_btn = QPushButton("Export")
        self.export_btn.setEnabled(bool(self.filepath))
        self.export_btn.clicked.connect(self.accept)
        self.export_btn.setDefault(True)
        button_layout.addWidget(self.export_btn)
        
        layout.addLayout(button_layout)
        
        self.on_format_changed(self.format)

    def accept(self):
        set_config_value("export_format", self.format)
        set_config_value("export_quality", self.quality)
        set_config_value("export_filepath", self.filepath)
        
        super().accept()
    
    def on_format_changed(self, format_name):
        self.format = format_name
        
        supports_quality = format_name in ["JPEG", "WebP"]
        
        for i in range(self.quality_widget.count()):
            item = self.quality_widget.itemAt(i)
            if item.widget():
                item.widget().setVisible(supports_quality)
            elif item.layout():
                for j in range(item.layout().count()):
                    widget = item.layout().itemAt(j).widget()
                    if widget:
                        widget.setVisible(supports_quality)
        
        if self.filepath:
            base = self.filepath.rsplit('.', 1)[0]
            ext = self.get_extension()
            self.filepath = f"{base}.{ext}"
            self.filepath_label.setText(self.filepath)
    
    def on_quality_changed(self, value):
        self.quality = value
        self.quality_value_label.setText(str(value))
    
    def get_extension(self):
        ext_map = {
            "PNG": "png",
            "JPEG": "jpg",
            "WebP": "webp",
            "TIFF": "tiff",
        }
        return ext_map.get(self.format, "png")
    
    def get_filter(self):
        filter_map = {
            "PNG": "PNG Image (*.png)",
            "JPEG": "JPEG Image (*.jpg *.jpeg)",
            "WebP": "WebP Image (*.webp)",
            "TIFF": "TIFF Image (*.tiff *.tif)",
        }
        return filter_map.get(self.format, "PNG Image (*.png)")
    
    def choose_filepath(self):
        start_dir = ""
        if self.filepath:
            start_dir = os.path.dirname(self.filepath)

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Image",
            start_dir,
            self.get_filter()
        )
        
        if filepath:
            self.filepath = filepath
            self.filepath_label.setText(filepath)
            self.export_btn.setEnabled(True)
    
    def get_export_settings(self):
        if self.exec() == QDialog.Accepted and self.filepath:
            if self.format in ["JPEG", "WebP"]:
                return self.filepath, self.quality
            else:
                return self.filepath, None
        return None, None