from dataclasses import dataclass
from typing import Annotated, Literal

from pyimagecuda import Image, copy, Fill

from .constraints import SIZE
from .buffers import resize_buffers
from .core import connect_nodes, send_to_node, Node, disconnect_nodes

@dataclass
class NodeGenerator(Node):
    size: Annotated[tuple[int, int], SIZE(min_width=1, min_height=1)] = (1920, 1080)
    connect_to: Node | None = None
    connect_to_port: Literal[1, 2] = 1
    hide_node: bool = False

    def __post_init__(self):
        self.image = Image(width=self.size[0], height=self.size[1])
        self.cache_image = Image(width=self.size[0], height=self.size[1])
        print(f"[GENERATOR] Created buffers for {self.name}: {self.size[0]}x{self.size[1]}")

    def connect_to_node(self, node: Node, port: Literal[1, 2] = 1):
        if self.connect_to is not None:
            raise ValueError(f"Node '{self.name}' is already connected to another node.")
        
        connect_nodes(self, node, port)

    def disconnect_node(self):
        disconnect_nodes(self)

    def process(self):
        if not self.connect_to:
            print(f"[GENERATOR] {self.name} has no output, skipping")
            return
        
        if self.hide_node:
            print(f"[GENERATOR] {self.name} is hidden, passing a transparent image to connected node")
            Fill.color(self.cache_image, (0, 0, 0, 0))
            send_to_node(self.connect_to, self.cache_image, self.connect_to_port)
            return
        
        print(f"[GENERATOR] {self.name} copying image {self.image.width}x{self.image.height} to cached image and sending to connected node")
        copy(self.cache_image, self.image)
        send_to_node(self.connect_to, self.cache_image, self.connect_to_port)

    def generate_image(self):
        raise NotImplementedError("Subclasses should implement this method.")

    def update_param_child(self, param_name, value):
        if param_name == "size":
            current = getattr(self, param_name, None)
            print(f"[GENERATOR] Resizing {self.name} buffers: {current} -> {value}")
            self.image, self.cache_image = resize_buffers(
                [self.image, self.cache_image], value
            )
        setattr(self, param_name, value)
        if param_name == "name":
            return
        self.generate_image()