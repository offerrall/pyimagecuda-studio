from PySide6.QtWidgets import QWidget, QLabel
from PySide6.QtCore import Qt

from pyimagecuda import ImageU8, convert_float_to_u8, Image
from .gl_preview import GLPreviewWidget
from ..qt_helpers import get_layout


class PreviewWidget(QWidget):
    def __init__(self):
        super().__init__()

        self._gl_widget = GLPreviewWidget()
        self.u8_buffer = None
        
        self.info_label = QLabel("No preview", self._gl_widget)
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("""
            QLabel {
                background-color: rgba(40, 40, 40, 180);
                color: white;
                padding: 4px 8px;
                border-radius: 3px;
                font-size: 11px;
            }
        """)
        self.info_label.setFixedHeight(20)
        self.info_label.adjustSize()

        self.alloc_preview_buffer(GLPreviewWidget.INITIAL_ALLOCATION_SIZE, GLPreviewWidget.INITIAL_ALLOCATION_SIZE)
        self.setLayout(get_layout('vbox', [self._gl_widget]))
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_info_label()
    
    def _position_info_label(self):
        self.info_label.adjustSize()
        gl_width = self._gl_widget.width()
        gl_height = self._gl_widget.height()
        label_width = self.info_label.width()
        
        x = (gl_width - label_width) // 2
        y = gl_height - self.info_label.height() - 10
        
        self.info_label.move(x, y)

    def update_preview(self, image: Image) -> None:
        max_w, max_h = self.u8_buffer.get_max_capacity()

        if image.width > max_h or image.height > max_h:
            self.alloc_preview_buffer(image.width, image.height)

        convert_float_to_u8(self.u8_buffer, image)
        self._gl_widget.display(self.u8_buffer)
        
        self.info_label.setText(f"{image.width} × {image.height}")
        self._position_info_label()

    def alloc_preview_buffer(self, width: int, height: int) -> None:
        if self.u8_buffer:
            print(f"[GUI] Freeing U8 buffer ({self.u8_buffer.width}x{self.u8_buffer.height}) for preview")
            self.u8_buffer.free()

        self.u8_buffer = ImageU8(width, height)
        print(f"[GUI] Allocated U8 buffer: {width}x{height} for preview")

    def has_preview(self):
        return self._gl_widget._current_image_width != 0

    def clear_preview(self):
        self._gl_widget.clear()
        self.info_label.setText("No preview")
        self._position_info_label()

    def cleanup(self):
        if self.u8_buffer is not None:
            self.u8_buffer.free()
            self.u8_buffer = None
        self._gl_widget.cleanup()

    def __del__(self):
        self.cleanup()