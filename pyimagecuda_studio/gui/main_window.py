from PySide6.QtWidgets import QMainWindow, QToolBar, QLabel, QWidget, QSizePolicy
from PySide6.QtGui import QAction, QKeySequence, QDesktopServices
from PySide6.QtCore import Qt, QUrl
from PySide6.QtWidgets import QMessageBox
import time

from .properties.node_properties import NodePropertiesWidget
from .properties.global_variables_widget import GlobalVariablesWidget
from .node_editor.node_editor import NodeEditor
from .preview.preview_dock import PreviewWidget
from .export import ExportDialog

from .qt_helpers import create_dock, get_layout
from .project import project_operations as proj
from ..nodes.core import run_nodes, free_nodes
from ..nodes.global_variables import unlink_deleted_nodes

from pyimagecuda import cuda_sync, save_u8

from .. import VERSION_VERBOSE, DESCRIPTION, DEPENDENCIES, LICENSE, PROJECT_EXTENSION, AUTHOR_NAME, REPO_URL


proj.set_program_name(VERSION_VERBOSE)
proj.set_project_extension(PROJECT_EXTENSION)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        proj.set_no_project_name(self)
        self.setGeometry(300, 50, 1400, 800)

        self.preview_widget = PreviewWidget()
        self.global_variables_widget = GlobalVariablesWidget()
        self.properties_widget = NodePropertiesWidget()
        editor = NodeEditor()
        self.editor = editor.view
        
        self.editor.preview_callback = self.preview_widget.update_preview
        self.editor.execute_callback = self.execute_nodes
        self.editor.selection_changed_callback = self.on_selection_changed
        self.editor.delete_callback = self.on_nodes_deleted
        
        self.properties_widget.execute_callback = self.execute_nodes
        self.properties_widget.node_updated_callback = self.editor.refresh_node_visual
        self.properties_widget.global_var_linked_callback = self.on_global_var_linked
        
        self.global_variables_widget.variable_added_callback = self.on_variable_added
        self.global_variables_widget.variable_deleted_callback = self.on_variable_deleted
        self.global_variables_widget.variable_value_changed_callback = self.on_variable_value_changed

        self.editor.create_init_output_node()

        preview_dock = create_dock(self, "Preview", self.preview_widget, Qt.RightDockWidgetArea)
        
        combined_widget = QWidget()
        combined_widget.setLayout(get_layout('vbox', [self.global_variables_widget, self.properties_widget]))
        
        properties_dock = create_dock(self, "Variables / Properties", combined_widget, Qt.LeftDockWidgetArea)

        self.setCentralWidget(editor)
        self.create_menu_bar()
        self.create_info_toolbar()
        self.resizeDocks([preview_dock, properties_dock], [300, 300], Qt.Horizontal)

        self.showMaximized()

    def create_menu_bar(self):
        def add_action(menu, text, shortcut, callback):
            action = QAction(text, self)
            action.setShortcut(QKeySequence(shortcut))
            action.triggered.connect(callback)
            menu.addAction(action)
        
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")
        add_action(file_menu, "New Project", "Ctrl+N", self.new_project)
        file_menu.addSeparator()
        add_action(file_menu, "Save Project", "Ctrl+S", 
                lambda: proj.save_project_dialog(self, self.editor))
        add_action(file_menu, "Save Project As...", "Ctrl+Shift+S", 
                lambda: proj.save_project_as_dialog(self, self.editor))
        add_action(file_menu, "Load Project...", "Ctrl+O", self.load_project)
        add_action(file_menu, "Import Nodes...", "Ctrl+I", self.import_nodes)
        file_menu.addSeparator()
        add_action(file_menu, "Export Image", "Ctrl+E", self.export_preview)
        file_menu.addSeparator()
        add_action(file_menu, "Exit", "Ctrl+Q", self.close)

        edit_menu = menubar.addMenu("Edit")
        add_action(edit_menu, "Execute Graph", "F5", self.execute_nodes)
        edit_menu.addSeparator()
        add_action(edit_menu, "Duplicate", "Ctrl+D", lambda: self.editor.duplicate_selected_nodes())
        add_action(edit_menu, "Delete", "Delete", lambda: self.editor.delete_selected_items())

        view_menu = menubar.addMenu("View")
        add_action(view_menu, "Zoom In", "Ctrl++", lambda: self.editor.scale(1.15, 1.15))
        add_action(view_menu, "Zoom Out", "Ctrl+-", lambda: self.editor.scale(1/1.15, 1/1.15))
        add_action(view_menu, "Reset Zoom", "Ctrl+0", lambda: self.editor.resetTransform())

        help_menu = menubar.addMenu("Help")
        #add_action(help_menu, "Documentation", "F1", lambda: QDesktopServices.openUrl(QUrl("WIP")))
        #add_action(help_menu, "Video Tutorials", "", lambda: QDesktopServices.openUrl(QUrl("WIP")))
        #help_menu.addSeparator()
        add_action(help_menu, "GitHub Repository", "", lambda: QDesktopServices.openUrl(QUrl(REPO_URL)))
        #add_action(help_menu, "Official Website", "", lambda: QDesktopServices.openUrl(QUrl("WIP")))
        help_menu.addSeparator()
        add_action(help_menu, "About", "", self.show_about)

    def show_about(self):
        QMessageBox.about(
            self,
            f"About {VERSION_VERBOSE}",
            f"""<h3>{VERSION_VERBOSE}</h3>
            <p>{DESCRIPTION}</p>
            <p><b>Built with:</b> {', '.join(DEPENDENCIES)}</p>
            <p><b>License:</b> {LICENSE}</p>
            <p>By {AUTHOR_NAME}</p>
            """
        )

    def modify_last_render_time(self, time_ms: float):
        msg = "    Last render time: "
        msg_tail = " - ms"
        if not time_ms == -1:
            msg_tail = f"{time_ms:.2f} ms"
            print(f"[GUI] Render time: {time_ms:.2f} ms")
        msg += msg_tail
        self.render_time_label.setText(msg)

    def create_info_toolbar(self):
        info_tool = "F5: Execute | Ctrl+S: Save | Ctrl+O: Load | Ctrl+I: Import | Ctrl+E: Export | Ctrl+D: Duplicate | Right-click: Add node | Delete: Remove | Middle-click: Pan | Scroll: Zoom    "

        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(Qt.BottomToolBarArea, toolbar)

        self.render_time_label = QLabel()
        self.modify_last_render_time(-1)
        toolbar.addWidget(self.render_time_label)
        
        self.selected_nodes_label = QLabel("")
        toolbar.addWidget(self.selected_nodes_label)
        
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)
        
        toolbar.addWidget(QLabel(info_tool))

    def new_project(self):
        proj.new_project(self, self.editor, self.preview_widget)
        self.global_variables_widget.refresh()

    def load_project(self):
        proj.load_project_dialog(self, self.editor, self.preview_widget, self.execute_nodes, self.global_variables_widget)

    def import_nodes(self):
        proj.import_nodes_dialog(self, self.editor, self.preview_widget, self.execute_nodes, self.global_variables_widget)

    def export_preview(self):
        if not self.preview_widget.has_preview():
            QMessageBox.warning(self, "No Preview", "No preview image available.")
            return
        
        dialog = ExportDialog(self)
        filepath, quality = dialog.get_export_settings()
        
        if not filepath:
            return

        print(f"[GUI-EXPORT] Saving preview to: {filepath}")
        if quality is not None:
            print(f"[GUI-EXPORT] Quality: {quality}")
            save_u8(self.preview_widget.u8_buffer, filepath, quality)
        else:
            print(f"[GUI-EXPORT] Lossless format")
            save_u8(self.preview_widget.u8_buffer, filepath)
        
        print(f"[GUI-EXPORT] Successfully saved: {filepath}")
    
    def on_selection_changed(self, selected_node_ids: list[str]):
        self.properties_widget.update_properties(selected_node_ids, self.editor.nodes)
        self.global_variables_widget.refresh()
        
        if selected_node_ids:
            self.selected_nodes_label.setText(f"    Selected nodes: {len(selected_node_ids)}")
            return

        self.selected_nodes_label.setText("")
    
    def on_nodes_deleted(self, deleted_node_ids: list[str]):
        unlink_deleted_nodes(deleted_node_ids)
        self.properties_widget.check_deleted_nodes(deleted_node_ids)
        self.global_variables_widget.refresh()
    
    def on_global_var_linked(self):
        self.execute_nodes()
        self.global_variables_widget.refresh()
        self.properties_widget.refresh_current_properties()
    
    def on_variable_added(self):
        self.properties_widget.update_link_indicators()
    
    def on_variable_deleted(self):
        self.properties_widget.refresh_current_properties()
    
    def on_variable_value_changed(self):
        self.execute_nodes()
        self.properties_widget.refresh_current_properties()
        
    def execute_nodes(self):
        start_time = time.perf_counter()
        self.preview_widget.clear_preview()
        
        if not run_nodes(self.editor.nodes):
            print("[GUI] Forcing cuda_sync() since preview was not called")
            cuda_sync()

        self.modify_last_render_time((time.perf_counter() - start_time) * 1000)

    def closeEvent(self, event):
        free_nodes(self.editor.nodes)
        self.preview_widget.cleanup()
        event.accept()