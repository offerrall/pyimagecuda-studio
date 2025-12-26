from dataclasses import dataclass
from typing import Annotated

from pyimagecuda import Image, Filter

from ..constraints import FLOAT
from ..node_in_out import NodeInputOutput
from ..buffers import ensure_buffer


@dataclass
class SharpenNode(NodeInputOutput):
    strength: Annotated[float, FLOAT(min_value=0.0, max_value=10.0)] = 1.0
    
    def __post_init__(self):
        self.dst_buffer = None
    
    def apply_process(self, input_image: Image) -> Image:
        self.dst_buffer = ensure_buffer(self.dst_buffer, input_image.width, input_image.height, self.name)
        
        print(f"[SHARPEN] {self.name} applying sharpen (strength={self.strength})")
        Filter.sharpen(input_image, strength=self.strength, dst_buffer=self.dst_buffer)
        
        return self.dst_buffer


@dataclass
class SobelNode(NodeInputOutput):
    
    def __post_init__(self):
        self.dst_buffer = None
    
    def apply_process(self, input_image: Image) -> Image:
        self.dst_buffer = ensure_buffer(self.dst_buffer, input_image.width, input_image.height, self.name)
        
        print(f"[SOBEL] {self.name} applying sobel edge detection")
        Filter.sobel(input_image, dst_buffer=self.dst_buffer)
        
        return self.dst_buffer


@dataclass
class EmbossNode(NodeInputOutput):
    strength: Annotated[float, FLOAT(min_value=0.0, max_value=10.0)] = 1.0
    
    def __post_init__(self):
        self.dst_buffer = None
    
    def apply_process(self, input_image: Image) -> Image:
        self.dst_buffer = ensure_buffer(self.dst_buffer, input_image.width, input_image.height, self.name)
        
        print(f"[EMBOSS] {self.name} applying emboss (strength={self.strength})")
        Filter.emboss(input_image, strength=self.strength, dst_buffer=self.dst_buffer)
        
        return self.dst_buffer