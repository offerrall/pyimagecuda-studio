from dataclasses import dataclass
from typing import Literal
from pyimagecuda import Image, copy

from .core import Node, validate_connection, send_to_node, disconnect_nodes
from .buffers import ensure_buffer


@dataclass
class NodeSplit(Node):
    connect_to_1: Node | None = None
    connect_to_2: Node | None = None
    connect_to_1_port: Literal[1, 2] = 1
    connect_to_2_port: Literal[1, 2] = 1
    node_connected: Node | None = None

    def __post_init__(self):
        self.cache_image = None

    def connect_to_node(self, node: Node, port: Literal[1, 2], target_port: Literal[1, 2] = 1):
        validate_connection(self, node, target_port)
        
        if port == 1:
            if self.connect_to_1 is not None:
                raise ValueError(f"Node '{self.name}' port 1 is already connected.")
            self.connect_to_1 = node
            self.connect_to_1_port = target_port
            print(f"[SPLIT] {self.name} port 1 -> {node.name} (port {target_port})")
        else:
            if self.connect_to_2 is not None:
                raise ValueError(f"Node '{self.name}' port 2 is already connected.")
            self.connect_to_2 = node
            self.connect_to_2_port = target_port
            print(f"[SPLIT] {self.name} port 2 -> {node.name} (port {target_port})")

        if hasattr(node, 'apply_merge'):
            if target_port == 1:
                node.node_connected_1 = self
            else:
                node.node_connected_2 = self
        else:
            node.node_connected = self

    def disconnect_node(self, port: Literal[1, 2]):
        disconnect_nodes(self, port)

    def process(self, input_image: Image):
        if self.connect_to_1 is None and self.connect_to_2 is None:
            print(f"[SPLIT] {self.name} has no outputs, skipping")
            return

        self.cache_image = ensure_buffer(self.cache_image, input_image.width, input_image.height, self.name)
        copy(self.cache_image, input_image)

        outputs = []
        if self.connect_to_1:
            outputs.append(f"{self.connect_to_1.name}")
            send_to_node(self.connect_to_1, input_image, self.connect_to_1_port)

        if self.connect_to_2:
            outputs.append(f"{self.connect_to_2.name}")
            send_to_node(self.connect_to_2, self.cache_image, self.connect_to_2_port)
        
        print(f"[SPLIT] {self.name} splitting to: {', '.join(outputs)}")