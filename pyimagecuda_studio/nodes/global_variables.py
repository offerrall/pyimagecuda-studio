from dataclasses import dataclass, field, fields
from typing import Annotated, get_origin, get_args
from typing import Any

from .node_factory import get_all_node_classes
from .constraints import get_annotated_params, PARAM, INT, FLOAT, STR, DROPDOWN, COLOR, SIZE, TEXT, CHECKBOX, IMAGE_PATH, FONT


@dataclass
class LinkInfo:
    node_id: str
    param_name: str


@dataclass
class GlobalVariable:
    name: str
    value: Any
    type: PARAM
    links: list[LinkInfo] = field(default_factory=list)


_global_variables: list[GlobalVariable] = []


def add_variable(name: str, var_type: type[PARAM]) -> None:
    all_dropdown_options = []

    for node_class_list in get_all_node_classes():
        for node_class in node_class_list:
            for field_info in fields(node_class):
                annotation = field_info.type
                if not get_origin(annotation) is Annotated:
                    continue

                args = get_args(annotation)
                constraint = args[1] if len(args) > 1 else None
                
                if isinstance(constraint, DROPDOWN):
                    all_dropdown_options.extend(constraint.options)

    all_dropdown_options = list(dict.fromkeys(all_dropdown_options))

    if var_type is INT or var_type == INT:
        constraint = INT()
        value = 0
    elif var_type is FLOAT or var_type == FLOAT:
        constraint = FLOAT()
        value = 0
    elif var_type is STR or var_type == STR:
        constraint = STR()
        value = ""
    elif var_type is DROPDOWN or var_type == DROPDOWN:
        constraint = DROPDOWN(options=all_dropdown_options)
        value = all_dropdown_options[0] if all_dropdown_options else ""
    elif var_type is COLOR or var_type == COLOR:
        constraint = COLOR()
        value = (0.0, 0.0, 0.0, 1.0)
    elif var_type is SIZE or var_type == SIZE:
        constraint = SIZE()
        value = (1920, 1080)
    elif var_type is TEXT or var_type == TEXT:
        constraint = TEXT()
        value = ""
    elif var_type is CHECKBOX or var_type == CHECKBOX:
        constraint = CHECKBOX()
        value = False
    elif var_type is IMAGE_PATH or var_type == IMAGE_PATH:
        constraint = IMAGE_PATH()
        value = ""
    elif var_type is FONT or var_type == FONT:
        constraint = FONT()
        value = "Arial"
    else:
        raise ValueError(f"Unsupported variable type: {var_type}")
    
    _global_variables.append(GlobalVariable(name, value, constraint, []))
    print(f"[GLOBAL_VAR] Added '{name}' = {value}")


def remove_variable(name: str) -> None:
    global _global_variables
    _global_variables = [v for v in _global_variables if v.name != name]
    print(f"[GLOBAL_VAR] Removed '{name}'")


def set_variable_value(name: str, value: Any) -> None:
    for var in _global_variables:
        if var.name == name:
            var.value = value
            print(f"[GLOBAL_VAR] Set '{name}' = {value}")
            return


def get_variable_value(name: str) -> Any:
    for var in _global_variables:
        if var.name == name:
            return var.value
    return None


def link_to_node(var_name: str, node_id: str, param_name: str) -> None:
    for var in _global_variables:
        if var.name == var_name:
            link = LinkInfo(node_id, param_name)
            if link not in var.links:
                var.links.append(link)
                print(f"[GLOBAL_VAR] Linked '{var_name}' -> {node_id}.{param_name}")
            else:
                print(f"[GLOBAL_VAR] '{var_name}' already linked to {node_id}.{param_name}")
            return


def unlink_from_node(var_name: str, node_id: str, param_name: str) -> None:
    for var in _global_variables:
        if var.name == var_name:
            var.links = [l for l in var.links if not (l.node_id == node_id and l.param_name == param_name)]
            print(f"[GLOBAL_VAR] Unlinked '{var_name}' -x- {node_id}.{param_name}")
            return


def get_linked_variable(node_id: str, param_name: str) -> str | None:
    for var in _global_variables:
        for link in var.links:
            if link.node_id == node_id and link.param_name == param_name:
                return var.name
    return None


def get_all_variables() -> list[GlobalVariable]:
    return _global_variables.copy()


def clear_all_variables() -> None:
    _global_variables.clear()

def unlink_deleted_nodes(deleted_node_ids: list[str]) -> None:
    for var in _global_variables:
        original_count = len(var.links)
        var.links = [l for l in var.links if l.node_id not in deleted_node_ids]
        
        removed_count = original_count - len(var.links)
        if removed_count > 0:
            print(f"[GLOBAL_VAR] Removed {removed_count} link(s) from '{var.name}' due to node deletion")

def update_nodes_from_variables(nodes: list) -> None:
    if not _global_variables:
        return
    
    nodes_dict = {n.id: n for n in nodes}
    
    for var in _global_variables:
        for link in var.links:
            node = nodes_dict.get(link.node_id)
            if not node:
                continue
            
            value = var.value
            
            params = get_annotated_params(node)
            for param in params:
                if param.name == link.param_name and param.constraint:
                    if isinstance(param.constraint, INT):
                        value = max(param.constraint.min_value, min(param.constraint.max_value, int(value)))
                    elif isinstance(param.constraint, FLOAT):
                        value = max(param.constraint.min_value, min(param.constraint.max_value, float(value)))
                    elif isinstance(param.constraint, STR):
                        value = str(value)[:param.constraint.max_length]
                    elif isinstance(param.constraint, DROPDOWN):
                        if value not in param.constraint.options:
                            print(f"[GLOBAL_VAR] Warning: Value '{value}' not in dropdown options for {node.name}.{param.name}, defaulting to '{param.constraint.options[0]}'")
                            value = param.constraint.options[0]
                    elif isinstance(param.constraint, COLOR):
                        if isinstance(value, (list, tuple)) and len(value) == 4:
                            value = tuple(max(0.0, min(1.0, float(c))) for c in value)
                    elif isinstance(param.constraint, SIZE):
                        if isinstance(value, (list, tuple)) and len(value) == 2:
                            w = max(param.constraint.min_width, min(param.constraint.max_width, int(value[0])))
                            h = max(param.constraint.min_height, min(param.constraint.max_height, int(value[1])))
                            value = (w, h)
                    break

            if node.update_param(link.param_name, value):
                print(f"[GLOBAL_VAR] Applied '{var.name}' to {node.name}.{link.param_name}")