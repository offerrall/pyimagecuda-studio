from dataclasses import dataclass
from typing import Literal

from pyimagecuda import Image

from .core import connect_nodes, send_to_node, Node, disconnect_nodes

@dataclass
class NodeInputOutput(Node):
    connect_to: Node | None = None
    connect_to_port: Literal[1, 2] = 1
    node_connected: Node | None = None
    hide_node: bool = False

    def connect_to_node(self, node: Node, port: Literal[1, 2] = 1):
        if self.connect_to is not None:
            raise ValueError(f"Node '{self.name}' is already connected to another node.")
        
        connect_nodes(self, node, port)

    def disconnect_node(self):
        disconnect_nodes(self)

    def process(self, input_image: Image):
        if self.connect_to is None:
            print(f"[PROCESS] {self.name} has no output, skipping")
            return
        
        if self.hide_node:
            print(f"[PROCESS] {self.name} is hidden, not processing")
            send_to_node(self.connect_to, input_image, self.connect_to_port)
            return

        print(f"[PROCESS] {self.name} processing and sending to {self.connect_to.name}")
        image = self.apply_process(input_image)
        send_to_node(self.connect_to, image, self.connect_to_port)

    def apply_process(self, input_image: Image) -> Image:
        raise NotImplementedError("Subclasses should implement this method.")