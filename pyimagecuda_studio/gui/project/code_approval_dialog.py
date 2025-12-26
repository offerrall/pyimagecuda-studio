from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextEdit, QCheckBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class CodeApprovalDialog(QDialog):
    def __init__(self, node_name: str, code: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚠️ Code Execution Warning")
        self.setModal(True)
        self.resize(700, 500)
        
        layout = QVBoxLayout(self)
        
        warning_label = QLabel(
            f"<h3>⚠️ Security Warning</h3>"
            f"<p>The node <b>'{node_name}'</b> contains executable code.</p>"
            f"<p><b>Only approve if you trust the source of this project.</b></p>"
        )
        warning_label.setWordWrap(True)
        layout.addWidget(warning_label)
        
        code_label = QLabel("<b>Code to be executed:</b>")
        layout.addWidget(code_label)
        
        code_display = QTextEdit()
        code_display.setReadOnly(True)
        code_display.setPlainText(code)
        code_display.setFont(QFont("Courier New", 10))
        layout.addWidget(code_display)
        
        self.understand_checkbox = QCheckBox(
            "I understand the risks and trust this code"
        )
        layout.addWidget(self.understand_checkbox)
        
        button_layout = QHBoxLayout()
        
        self.approve_btn = QPushButton("✓ Approve and Load Project")
        self.approve_btn.setEnabled(False)
        self.approve_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("✗ Cancel Loading")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(self.approve_btn)
        
        layout.addLayout(button_layout)
        
        self.understand_checkbox.stateChanged.connect(self._on_checkbox_changed)
    
    def _on_checkbox_changed(self, state):
        self.approve_btn.setEnabled(state == Qt.CheckState.Checked.value)
    
    @staticmethod
    def request_approval(node_name: str, code: str, parent=None) -> bool:
        dialog = CodeApprovalDialog(node_name, code, parent)
        result = dialog.exec()
        return result == QDialog.DialogCode.Accepted