from dataclasses import dataclass
from PySide6.QtWidgets import QMessageBox, QFileDialog
import os
import json

from .code_approval_dialog import CodeApprovalDialog
from ...nodes.serialization import (
    serialize_nodes, 
    deserialize_nodes, 
    check_executable_code,
    InvalidLinkError,
)
from ..config import get_config_value, set_config_value
from ...nodes.global_variables import clear_all_variables


class ProjectLoadCancelled(Exception):
    pass


@dataclass
class ProjectConfig:
    program_name: str = "Untitled"
    project_extension: str = "ext"
    current_path: str | None = None


config = ProjectConfig()


def set_program_name(name: str):
    config.program_name = name


def set_project_extension(extension: str):
    config.project_extension = extension


def get_current_path():
    return config.current_path


def set_no_project_name(parent):
    config.current_path = None
    parent.setWindowTitle(f"{config.program_name} - New Project")


def _get_file_filter():
    ext = config.project_extension
    ext_upper = ext.upper()
    return f"{ext_upper} Project Files (*.{ext})"


def new_project(parent, editor, preview_widget):
    reply = QMessageBox.question(
        parent, 
        "New Project", 
        "Create new project? Unsaved changes will be lost.", 
        QMessageBox.Yes | QMessageBox.No, 
        QMessageBox.No
    )
    
    if reply != QMessageBox.Yes:
        return
    
    print("[GUI-PROJECT] Creating new project")
    editor.clear_all()
    preview_widget.clear_preview()
    clear_all_variables()
    set_no_project_name(parent)
    print("[GUI-PROJECT] New project created")


def save_project_dialog(parent, editor):
    if config.current_path:
        save_to_file(parent, editor, config.current_path)
    else:
        save_project_as_dialog(parent, editor)


def save_project_as_dialog(parent, editor):
    last_save_dir = get_config_value("last_save_dir", "")
    
    filepath, _ = QFileDialog.getSaveFileName(
        parent,
        "Save Project",
        last_save_dir,
        _get_file_filter()
    )
    
    if not filepath:
        return
    
    if not filepath.endswith(f".{config.project_extension}"):
        filepath += f".{config.project_extension}"
    
    if save_to_file(parent, editor, filepath):
        config.current_path = filepath
        set_config_value("last_save_dir", os.path.dirname(filepath))


def save_to_file(parent, editor, filepath):
    try:
        print(f"[SAVE] Saving project to {filepath}")
        
        data = serialize_nodes(editor.nodes)
        
        for node_data in data["nodes"]:
            node_id = node_data["id"]
            widget = editor.node_widgets.get(node_id)
            if widget:
                pos = widget.pos()
                node_data["position"] = {"x": pos.x(), "y": pos.y()}
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        num_global_vars = len(data.get("global_variables", {}).get("variables", []))
        print(f"[SAVE] Project saved: {len(data['nodes'])} nodes, {len(data['connections'])} connections, {num_global_vars} global variables")
        
        parent.setWindowTitle(f"{config.program_name} - {filepath}")
        print(f"[GUI-PROJECT] Project saved: {filepath}")
        QMessageBox.about(parent, "Save Successful", "Project saved successfully.")
        return True
    except Exception as e:
        QMessageBox.critical(parent, "Save Failed", f"Failed to save project:\n{str(e)}")
        print(f"[GUI-PROJECT] Save error: {e}")
        return False


def _load_or_import_project(parent, editor, preview_widget, execute_callback, global_variables_widget, is_import=False):
    last_load_dir = get_config_value("last_load_dir", "")
    
    title = "Import Nodes" if is_import else "Load Project"
    filepath, _ = QFileDialog.getOpenFileName(parent, title, last_load_dir, _get_file_filter())
    
    if not filepath:
        return
    
    try:
        operation = "IMPORT" if is_import else "LOAD"
        print(f"[{operation}] {'Importing from' if is_import else 'Loading'} {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        executable_nodes = check_executable_code(data)
        for node_name, node_type, code in executable_nodes:
            approved = CodeApprovalDialog.request_approval(node_name, code, parent)
            if not approved:
                print(f"[{operation}] User rejected executable code - CANCELLING")
                raise ProjectLoadCancelled(
                    f"{'Import' if is_import else 'Load'} cancelled: User did not approve executable code in node '{node_name}'"
                )
        
        node_extra_params = {}
        if preview_widget and not is_import:
            node_extra_params["EndNode"] = {"finish_callback": preview_widget.update_preview}
        
        existing_names = {n.name for n in editor.nodes} if is_import else set()
        
        nodes, var_name_mapping, id_mapping = deserialize_nodes(
            data, 
            node_extra_params,
            skip_output=is_import,
            clear_variables=not is_import,
            existing_node_names=existing_names
        )
        
        positions = {}
        offset = (300, 300) if is_import else (0, 0)
        
        for node_data in data["nodes"]:
            if is_import and node_data["type"] == "EndNode":
                continue
            
            if "position" in node_data:
                old_id = node_data["id"]
                new_id = id_mapping.get(old_id)
                
                if new_id:
                    pos = node_data["position"]
                    positions[new_id] = (pos["x"] + offset[0], pos["y"] + offset[1])
        
        print(f"[{operation}] Processed {len(nodes)} nodes")
        
        if is_import:
            for node in nodes:
                editor.nodes.append(node)
                pos = positions.get(node.id, (100, 100))
                editor.add_node(node, pos[0], pos[1])
        else:
            editor.clear_all(create_output_node=False)
            editor.nodes = nodes
            for node in nodes:
                pos = positions.get(node.id, (0, 0))
                editor.add_node(node, pos[0], pos[1])
        
        editor.rebuild_cables()
        
        if global_variables_widget:
            global_variables_widget.refresh()
            print(f"[{operation}] Refreshed global variables widget")
        
        set_config_value("last_load_dir", os.path.dirname(filepath))
        
        if is_import:
            print(f"[IMPORT] Import completed: {len(nodes)} nodes")
        else:
            config.current_path = filepath
            parent.setWindowTitle(f"{config.program_name} - {filepath}")
            print(f"[LOAD] Project loaded: {filepath}")
        
        execute_callback()
        
    except ProjectLoadCancelled as e:
        operation = "IMPORT" if is_import else "LOAD"
        print(f"[{operation}] Operation cancelled: {e}")
        title = "Import Cancelled" if is_import else "Load Cancelled"
        msg = "Import was cancelled." if is_import else "Project loading was cancelled."
        QMessageBox.information(parent, title, msg)
    except InvalidLinkError as e:
        operation = "IMPORT" if is_import else "LOAD"
        print(f"[{operation}] Invalid link detected: {e}")
        QMessageBox.critical(parent, "Security Error", f"Invalid variable link detected:\n\n{str(e)}")
    except Exception as e:
        operation = "import nodes" if is_import else "load project"
        title = "Import Failed" if is_import else "Load Failed"
        QMessageBox.critical(parent, title, f"Failed to {operation}:\n{str(e)}")
        print(f"[{'IMPORT' if is_import else 'LOAD'}] Error: {e}")


def load_project_dialog(parent, editor, preview_widget, execute_callback, global_variables_widget=None):
    _load_or_import_project(parent, editor, preview_widget, execute_callback, global_variables_widget, is_import=False)


def import_nodes_dialog(parent, editor, preview_widget, execute_callback, global_variables_widget=None):
    _load_or_import_project(parent, editor, preview_widget, execute_callback, global_variables_widget, is_import=True)