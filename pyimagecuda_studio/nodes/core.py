from dataclasses import dataclass, field
from typing import Annotated, Callable, Literal
import uuid

from pyimagecuda import Image

from .constraints import STR
from .buffers import free_node


@dataclass
class Node:
    name: Annotated[str, STR(max_length=50, min_length=1)] = "Node"
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    properties_not_show: list[str] = field(default_factory=lambda: [])

    def process(self):
        raise NotImplementedError("Subclasses should implement this method.")

    def reset(self):
        pass

    def update_param(self, param_name: str, value) -> bool:
        current = getattr(self, param_name, None)
        if current == value:
            print(f"[UPDATE] {self.name}.{param_name} unchanged (value: {value})")
            return False

        self.update_param_child(param_name, value)
        print(f"[UPDATE] {self.name}.{param_name} = {value}")
        return True

    def update_param_child(self, param_name: str, value) -> None:
        setattr(self, param_name, value)

    def free(self):
        free_node(self)
        print(f"[FREE] Freed resources for node: {self.name}")

@dataclass
class EndNode(Node):
    finish_callback: Callable | None = None
    node_connected: Node | None = None
    is_called: bool = False

    def reset(self):
        self.is_called = False

    def process(self, input_image: Image):
        self.is_called = True
        if self.finish_callback:
            print(f"[CALLBACK] Executing finish callback for {self.name}")
            self.finish_callback(input_image)
        else:
            print(f"[CALLBACK] No callback defined for {self.name}")

def validate_connection(source: Node, target: Node, port: Literal[1, 2]) -> None:
    if source.id == target.id:
        error = f"Cannot connect node '{source.name}' to itself."
        print(f"[ERROR] {error}")
        raise ValueError(error)

    if not hasattr(target, 'node_connected') and not hasattr(target, 'node_connected_1'):
        error = f"Cannot connect to node '{target.name}'. It has no input ports."
        print(f"[ERROR] {error}")
        raise ValueError(error)

    if hasattr(target, 'apply_merge'):
        if port not in (1, 2):
            error = f"Merge node '{target.name}' port must be 1 or 2."
            print(f"[ERROR] {error}")
            raise ValueError(error)
        
        if port == 1 and target.node_connected_1 is not None:
            error = f"Merge '{target.name}' port 1 already has input from '{target.node_connected_1.name}'"
            print(f"[ERROR] {error}")
            raise ValueError(error)
        elif port == 2 and target.node_connected_2 is not None:
            error = f"Merge '{target.name}' port 2 already has input from '{target.node_connected_2.name}'"
            print(f"[ERROR] {error}")
            raise ValueError(error)
    else:
        if port != 1:
            error = f"Node '{target.name}' only accepts port 1."
            print(f"[ERROR] {error}")
            raise ValueError(error)

        if target.node_connected is not None:
            error = f"Node '{target.name}' already has input from '{target.node_connected.name}'"
            print(f"[ERROR] {error}")
            raise ValueError(error)

def connect_nodes(source: Node, target: Node, port: Literal[1, 2]) -> None:
    validate_connection(source, target, port)

    source.connect_to = target
    source.connect_to_port = port

    if hasattr(target, 'apply_merge'):
        if port == 1:
            target.node_connected_1 = source
        else:
            target.node_connected_2 = source
    else:
        target.node_connected = source
    
    print(f"[CONNECT] {source.name} -> {target.name} (port {port})")


def disconnect_nodes(source: Node, port: Literal[1, 2] | None = None) -> None:
    if hasattr(source, 'connect_to_1'):
        if port is None:
            error = f"Port must be specified when disconnecting from a split node '{source.name}'."
            print(f"[ERROR] {error}")
            raise ValueError(error)
        if port == 1:
            target = source.connect_to_1
            target_port = source.connect_to_1_port
            source.connect_to_1 = None
            source.connect_to_1_port = 1
        else:
            target = source.connect_to_2
            target_port = source.connect_to_2_port
            source.connect_to_2 = None
            source.connect_to_2_port = 1
    else:
        target = source.connect_to
        target_port = source.connect_to_port
        source.connect_to = None
        source.connect_to_port = 1

    if target:
        if hasattr(target, 'apply_merge'):
            if target_port == 1:
                target.node_connected_1 = None
            else:
                target.node_connected_2 = None
        else:
            target.node_connected = None
        
        print(f"[DISCONNECT] {source.name} -x- {target.name}")

def delete_node(node: Node) -> None:
    print(f"[DELETE] Deleting node: {node.name}")
    
    if hasattr(node, 'connect_to_1'):
        if node.connect_to_1: node.disconnect_node(port=1)
        if node.connect_to_2: node.disconnect_node(port=2)
    elif hasattr(node, 'connect_to') and node.connect_to:
        node.disconnect_node()
    
    parents = []
    
    if hasattr(node, 'node_connected') and node.node_connected:
        parents.append(node.node_connected)
    
    if hasattr(node, 'node_connected_1') and node.node_connected_1:
        parents.append(node.node_connected_1)
    
    if hasattr(node, 'node_connected_2') and node.node_connected_2:
        parents.append(node.node_connected_2)
    
    for parent in parents:
        if hasattr(parent, 'connect_to_1'):
            if parent.connect_to_1 == node:
                parent.disconnect_node(port=1)
            if parent.connect_to_2 == node:
                parent.disconnect_node(port=2)
        elif hasattr(parent, 'connect_to') and parent.connect_to == node:
            parent.disconnect_node()
    
    node.free()
    print(f"[DELETE] Node deleted: {node.name}")

def send_to_node(target: Node, image: Image, port: Literal[1, 2]) -> None:
    if hasattr(target, 'apply_merge'):
        target.process(image, port)
        return
    target.process(image)

def run_nodes(nodes: list[Node]) -> bool:
    from .global_variables import update_nodes_from_variables
    print("\n[EXECUTE] Starting execution")
    
    out_node = None

    for node in nodes:
        node.reset()

    update_nodes_from_variables(nodes)
    
    generators = []
    for node in nodes:
        if not hasattr(node, 'node_connected') and not hasattr(node, 'node_connected_1'):
            generators.append(node)
        if isinstance(node, EndNode):
            if not out_node is None:
                raise ValueError(f"[EXECUTE-ERROR] Multiple EndNodes found: '{out_node.name}' and '{node.name}'")
            out_node = node
    
    print(f"[EXECUTE] Found {len(generators)} generator(s): {', '.join(g.name for g in generators)}")
    
    for node in generators:
        print(f"[EXECUTE] Processing generator: {node.name}")
        node.process()
    
    print("[EXECUTE] Execution complete\n")
    if out_node and out_node.is_called:
        return True
    return False

def free_nodes(nodes: list[Node]):
    for node in nodes:
        node.free()