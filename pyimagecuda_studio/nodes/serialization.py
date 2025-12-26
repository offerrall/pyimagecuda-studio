import json
from pathlib import Path
from typing import Any, get_origin, get_args, Annotated
from dataclasses import is_dataclass, fields

from .constraints import CLASS_NAME_TO_TYPE
from .core import Node, EndNode
from .node_factory import get_node_menu_structure
from .constraints import get_annotated_params, TEXT
from .global_variables import (
    clear_all_variables, add_variable, set_variable_value, 
    link_to_node, get_all_variables
)


VERSION = "1.0"
EXECUTABLE_CODE_NODES = ["ConditionalNode", "DynamicTextNode"]


class CodeRejectionError(Exception):
    pass


class InvalidLinkError(Exception):
    pass


def create_node_factory() -> dict:
    menu_structure = get_node_menu_structure()
    factory = {"EndNode": EndNode}
    
    for category, items in menu_structure.items():
        if isinstance(items, dict):
            for node_class in items.values():
                factory[node_class.__name__] = node_class
        else:
            factory[items.__name__] = items
    
    return factory


def serialize_value(value: Any) -> Any:
    if isinstance(value, tuple):
        return list(value)
    elif isinstance(value, Path):
        return str(value)
    elif is_dataclass(value):
        return {f.name: serialize_value(getattr(value, f.name)) for f in fields(value)}
    return value


def deserialize_value(value: Any, target_type: type) -> Any:
    if target_type == tuple and isinstance(value, list):
        return tuple(value)
    if isinstance(value, list) and len(value) > 0 and isinstance(value[0], list):
        return tuple(tuple(item) if isinstance(item, list) else item for item in value)
    return value


def get_unique_name(base_name: str, existing_names: set[str]) -> str:
    if base_name not in existing_names:
        return base_name
    
    counter = 2
    while f"{base_name} ({counter})" in existing_names:
        counter += 1
    
    return f"{base_name} ({counter})"


def serialize_node(node: Node) -> dict:
    params = get_annotated_params(node)
    
    parameters = {}
    for param in params:
        if param.name in ['id', 'name']:
            continue
        value = getattr(node, param.name)
        parameters[param.name] = serialize_value(value)
    
    if hasattr(node, 'hide_node'):
        parameters['hide_node'] = node.hide_node
    
    return {
        "id": node.id,
        "type": type(node).__name__,
        "name": node.name,
        "parameters": parameters
    }


def serialize_connections(nodes: list[Node]) -> list[dict]:
    connections = []
    
    for node in nodes:
        if hasattr(node, 'connect_to') and node.connect_to:
            connections.append({
                "source_id": node.id,
                "target_id": node.connect_to.id,
                "source_port": 1,
                "target_port": node.connect_to_port
            })
        
        if hasattr(node, 'connect_to_1') and node.connect_to_1:
            connections.append({
                "source_id": node.id,
                "target_id": node.connect_to_1.id,
                "source_port": 1,
                "target_port": node.connect_to_1_port
            })
        
        if hasattr(node, 'connect_to_2') and node.connect_to_2:
            connections.append({
                "source_id": node.id,
                "target_id": node.connect_to_2.id,
                "source_port": 2,
                "target_port": node.connect_to_2_port
            })
    
    return connections


def serialize_global_variables() -> dict:
    variables = get_all_variables()
    
    vars_data = []
    for var in variables:
        var_data = {
            "name": var.name,
            "type": type(var.type).__name__,
            "value": serialize_value(var.value),
            "links": [
                {"node_id": link.node_id, "param_name": link.param_name}
                for link in var.links
            ]
        }
        vars_data.append(var_data)
    
    return {"variables": vars_data}


def serialize_nodes(nodes: list[Node]) -> dict:
    print(f"[SERIALIZATION] Serializing {len(nodes)} nodes")
    
    nodes_data = [serialize_node(node) for node in nodes]
    connections = serialize_connections(nodes)
    global_vars = serialize_global_variables()
    
    print(f"[SERIALIZATION] Serialized {len(connections)} connections")
    print(f"[SERIALIZATION] Serialized {len(global_vars['variables'])} global variables")
    
    return {
        "version": VERSION,
        "nodes": nodes_data,
        "connections": connections,
        "global_variables": global_vars
    }

def deserialize_node(node_data: dict, node_factory: dict, generate_new_id: bool, 
                     existing_names: set[str], **extra_params) -> Node:
    node_type = node_data["type"]
    node_class = node_factory.get(node_type)
    if not node_class:
        raise ValueError(f"Unknown node type: {node_type}")
    
    original_name = node_data["name"]
    unique_name = get_unique_name(original_name, existing_names)
    
    init_params = {
        "name": unique_name
    }
    
    if not generate_new_id:
        init_params["id"] = node_data["id"]
    
    init_params.update(extra_params)
    
    if is_dataclass(node_class):
        for field_info in fields(node_class):
            annotation = field_info.type
            if get_origin(annotation) is Annotated:
                param_name = field_info.name
                if param_name in node_data["parameters"]:
                    args = get_args(annotation)
                    param_type = args[0]
                    value = node_data["parameters"][param_name]
                    init_params[param_name] = deserialize_value(value, param_type)
    
    node = node_class(**init_params)
    
    if unique_name != original_name:
        print(f"[DESERIALIZATION] Created: {node.name} ({node_type}) ID={node.id} (renamed from '{original_name}')")
    else:
        print(f"[DESERIALIZATION] Created: {node.name} ({node_type}) ID={node.id}")
    
    existing_names.add(unique_name)
    
    return node


def connect_deserialized_nodes(nodes_dict: dict, connections_data: list[dict], skipped_node_ids: set[str], id_mapping: dict[str, str]) -> None:
    print(f"[DESERIALIZATION] Connecting {len(connections_data)} connections")
    
    for conn in connections_data:
        old_source_id = conn["source_id"]
        old_target_id = conn["target_id"]
        
        if old_source_id in skipped_node_ids or old_target_id in skipped_node_ids:
            print(f"[DESERIALIZATION] Skipping connection to/from skipped node")
            continue
        
        source_id = id_mapping.get(old_source_id, old_source_id)
        target_id = id_mapping.get(old_target_id, old_target_id)
        
        source = nodes_dict.get(source_id)
        target = nodes_dict.get(target_id)
        
        if not source or not target:
            print(f"[DESERIALIZATION] Warning: Connection skipped (nodes not found)")
            continue
        
        source_port = conn["source_port"]
        target_port = conn["target_port"]
        
        try:
            if hasattr(source, 'connect_to_1'):
                source.connect_to_node(target, port=source_port, target_port=target_port)
            else:
                source.connect_to_node(target, port=target_port)
        except Exception as e:
            print(f"[DESERIALIZATION] Connection error: {e}")


def deserialize_global_variables(global_vars_data: dict, nodes_dict: dict, 
                                 clear_variables: bool, skipped_node_ids: set[str], id_mapping: dict[str, str]) -> dict[str, str]:
    var_name_mapping = {}
    existing_var_names = set()
    
    if clear_variables:
        clear_all_variables()
    else:
        existing_var_names = {v.name for v in get_all_variables()}
    
    if not global_vars_data or "variables" not in global_vars_data:
        print("[DESERIALIZATION] No global variables to restore")
        return var_name_mapping
    
    variables_data = global_vars_data["variables"]
    print(f"[DESERIALIZATION] Restoring {len(variables_data)} global variables")
    
    for var_data in variables_data:
        old_var_name = var_data["name"]
        var_type_name = var_data["type"]
        var_value = var_data["value"]
        var_links = var_data.get("links", [])
        
        var_type = CLASS_NAME_TO_TYPE.get(var_type_name)
        if not var_type:
            print(f"[DESERIALIZATION] Warning: Unknown variable type '{var_type_name}', skipping")
            continue
        
        new_var_name = old_var_name
        if not clear_variables and old_var_name in existing_var_names:
            new_var_name = get_unique_name(old_var_name, existing_var_names)
            print(f"[DESERIALIZATION] Variable '{old_var_name}' renamed to '{new_var_name}' (duplicate)")
        
        var_name_mapping[old_var_name] = new_var_name
        existing_var_names.add(new_var_name)
        
        add_variable(new_var_name, var_type)
        set_variable_value(new_var_name, deserialize_value(var_value, type(var_value)))
        
        for link in var_links:
            old_node_id = link["node_id"]
            param_name = link["param_name"]
            
            if old_node_id in skipped_node_ids:
                print(f"[DESERIALIZATION] Skipping link to skipped node {old_node_id}")
                continue
            
            node_id = id_mapping.get(old_node_id, old_node_id)
            node = nodes_dict.get(node_id)
            
            if not node:
                print(f"[DESERIALIZATION] Warning: Node {node_id} not found for variable link, skipping")
                continue
            
            node_type = type(node).__name__
            if node_type in EXECUTABLE_CODE_NODES:
                params = get_annotated_params(node)
                param = next((p for p in params if p.name == param_name), None)
                
                if param and isinstance(param.constraint, TEXT):
                    error_msg = (
                        f"SECURITY: Detected attempt to link variable '{new_var_name}' to executable code parameter "
                        f"'{param_name}' in node '{node.name}' ({node_type}). This is not allowed."
                    )
                    print(f"[DESERIALIZATION] {error_msg}")
                    raise InvalidLinkError(error_msg)
            
            link_to_node(new_var_name, node_id, param_name)
            print(f"[DESERIALIZATION] Linked variable '{new_var_name}' to {node_id}.{param_name}")
    
    return var_name_mapping


def deserialize_nodes(data: dict, node_extra_params: dict = None,
                     skip_output: bool = False, clear_variables: bool = True, 
                     existing_node_names: set[str] = None) -> tuple[list[Node], dict[str, str], dict[str, str]]:
    version = data.get("version", "1.0")
    print(f"[DESERIALIZATION] Project version: {version}")
    
    node_factory = create_node_factory()
    
    nodes = []
    nodes_dict = {}
    skipped_node_ids = set()
    id_mapping = {}
    generate_new_ids = skip_output
    
    if existing_node_names is None:
        existing_node_names = set()
    else:
        existing_node_names = existing_node_names.copy()
    
    for node_data in data["nodes"]:
        if skip_output and node_data["type"] == "EndNode":
            skipped_node_ids.add(node_data["id"])
            print(f"[DESERIALIZATION] Skipping Output node (import mode)")
            continue
        
        extra = {}
        if node_extra_params and node_data["type"] in node_extra_params:
            extra = node_extra_params[node_data["type"]]
        
        try:
            old_id = node_data["id"]
            node = deserialize_node(node_data, node_factory, generate_new_ids, existing_node_names, **extra)
            nodes.append(node)
            nodes_dict[node.id] = node
            
            if generate_new_ids:
                id_mapping[old_id] = node.id
                print(f"[DESERIALIZATION] ID remapped: {old_id} -> {node.id}")
            else:
                id_mapping[old_id] = old_id
            
        except Exception as e:
            print(f"[DESERIALIZATION] Error creating node: {e}")
            continue
    
    connect_deserialized_nodes(nodes_dict, data["connections"], skipped_node_ids, id_mapping)
    
    global_vars_data = data.get("global_variables", {})
    var_name_mapping = deserialize_global_variables(global_vars_data, nodes_dict, clear_variables, skipped_node_ids, id_mapping)
    
    print(f"[DESERIALIZATION] Loaded {len(nodes)} nodes")
    return nodes, var_name_mapping, id_mapping


def check_executable_code(data: dict) -> list[tuple[str, str, str]]:
    executable_nodes = []
    
    for node_data in data["nodes"]:
        node_type = node_data["type"]
        
        if node_type in EXECUTABLE_CODE_NODES:
            code = node_data["parameters"].get("code", "")
            node_name = node_data["name"]
            executable_nodes.append((node_name, node_type, code))
    
    return executable_nodes