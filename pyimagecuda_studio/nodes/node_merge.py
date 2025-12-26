from dataclasses import dataclass
from typing import Literal

from pyimagecuda import Image

from .core import connect_nodes, send_to_node, Node, disconnect_nodes


@dataclass
class NodeMerge(Node):
    connect_to: Node | None = None
    connect_to_port: Literal[1, 2] = 1
    node_connected_1: Node | None = None
    node_connected_2: Node | None = None

    def __post_init__(self):
        self.reset()

    def reset(self):
        self.input_1 = None
        self.input_2 = None

    def connect_to_node(self, node: Node, port: Literal[1, 2] = 1):
        if self.connect_to is not None:
            raise ValueError(f"Node '{self.name}' is already connected to another node.")
        
        connect_nodes(self, node, port)

    def disconnect_node(self):
        disconnect_nodes(self)

    def process(self, input_image: Image, port: Literal[1, 2]):
        if self.connect_to is None:
            print(f"[MERGE] {self.name} has no output, skipping")
            return

        if port == 1:
            self.input_1 = input_image
            print(f"[MERGE] {self.name} received input on port 1")
        else:
            self.input_2 = input_image
            print(f"[MERGE] {self.name} received input on port 2")

        if self.input_1 is not None and self.input_2 is not None:
            print(f"[MERGE] {self.name} merging both inputs and sending to {self.connect_to.name}")
            result = self.apply_merge(self.input_1, self.input_2)

            self.input_1 = None
            self.input_2 = None

            send_to_node(self.connect_to, result, self.connect_to_port)
        else:
            waiting = "port 2" if self.input_1 is not None else "port 1"
            print(f"[MERGE] {self.name} waiting for input on {waiting}")

    def apply_merge(self, input_1: Image, input_2: Image) -> Image:
        raise NotImplementedError("Subclasses should implement this method.")