from dataclasses import dataclass
from typing import Annotated

from pyimagecuda import Image, Effect, Filter

from ..constraints import COLOR, INT, FLOAT, CHECKBOX, DROPDOWN
from ..node_in_out import NodeInputOutput
from ..buffers import ensure_buffer


@dataclass
class GaussianBlurNode(NodeInputOutput):
    radius: Annotated[int, INT(min_value=0, max_value=100)] = 20
    sigma: Annotated[float, FLOAT(min_value=0.0, max_value=50.0)] = 5.0
    
    def __post_init__(self):
        self.dst_buffer = None
        self.temp_buffer = None
    
    def apply_process(self, input_image: Image) -> Image:
        self.dst_buffer = ensure_buffer(self.dst_buffer, input_image.width, input_image.height, self.name)
        self.temp_buffer = ensure_buffer(self.temp_buffer, input_image.width, input_image.height, self.name)
        
        print(f"[GAUSSIAN_BLUR] {self.name} applying gaussian blur (radius={self.radius}, sigma={self.sigma})")
        Filter.gaussian_blur(
            input_image,
            radius=self.radius,
            sigma=self.sigma,
            dst_buffer=self.dst_buffer,
            temp_buffer=self.temp_buffer
        )
        
        return self.dst_buffer


@dataclass
class StrokeNode(NodeInputOutput):
    width: Annotated[int, INT(min_value=1, max_value=1000)] = 2
    color: Annotated[tuple[float, float, float, float], COLOR()] = (0.0, 0.0, 0.0, 1.0)
    position: Annotated[str, DROPDOWN(options=['Outside', 'Inside'])] = 'Outside'
    expand: Annotated[bool, CHECKBOX()] = False
    
    def __post_init__(self):
        self.dst_buffer = None
        self.distance_buffer = None
    
    def apply_process(self, input_image: Image) -> Image:
        if self.position == 'Outside' and self.expand:
            needed_w = input_image.width + self.width * 2
            needed_h = input_image.height + self.width * 2
        else:
            needed_w = input_image.width
            needed_h = input_image.height
        
        self.dst_buffer = ensure_buffer(self.dst_buffer, needed_w, needed_h, self.name)
        self.distance_buffer = ensure_buffer(self.distance_buffer, needed_w, needed_h, self.name)
        
        print(f"[STROKE] {self.name} applying stroke (width={self.width}, color={self.color}, position={self.position}, expand={self.expand})")
        Effect.stroke(
            input_image,
            width=self.width,
            color=self.color,
            position=self.position.lower(),
            expand=self.expand,
            dst_buffer=self.dst_buffer,
            distance_buffer=self.distance_buffer
        )
        
        return self.dst_buffer


@dataclass
class DropShadowNode(NodeInputOutput):
    offset_x: Annotated[int, INT(min_value=-200, max_value=200)] = 10
    offset_y: Annotated[int, INT(min_value=-200, max_value=200)] = 10
    blur: Annotated[int, INT(min_value=0, max_value=100)] = 20
    color: Annotated[tuple[float, float, float, float], COLOR()] = (0.0, 0.0, 0.0, 0.5)
    expand: Annotated[bool, CHECKBOX()] = True
    
    def __post_init__(self):
        self.dst_buffer = None
        self.shadow_buffer = None
        self.temp_buffer = None
    
    def apply_process(self, input_image: Image) -> Image:
        if self.expand:
            pad_l = self.blur + max(0, -self.offset_x)
            pad_r = self.blur + max(0, self.offset_x)
            pad_t = self.blur + max(0, -self.offset_y)
            pad_b = self.blur + max(0, self.offset_y)
            needed_w = input_image.width + pad_l + pad_r
            needed_h = input_image.height + pad_t + pad_b
        else:
            needed_w = input_image.width
            needed_h = input_image.height
        
        self.dst_buffer = ensure_buffer(self.dst_buffer, needed_w, needed_h, self.name)
        self.shadow_buffer = ensure_buffer(self.shadow_buffer, needed_w, needed_h, self.name)
        self.temp_buffer = ensure_buffer(self.temp_buffer, needed_w, needed_h, self.name)
        
        print(f"[DROP_SHADOW] {self.name} applying drop shadow (offset_x={self.offset_x}, offset_y={self.offset_y}, blur={self.blur}, color={self.color}, expand={self.expand})")
        Effect.drop_shadow(
            input_image,
            offset_x=self.offset_x,
            offset_y=self.offset_y,
            blur=self.blur,
            color=self.color,
            expand=self.expand,
            dst_buffer=self.dst_buffer,
            shadow_buffer=self.shadow_buffer,
            temp_buffer=self.temp_buffer
        )
        
        return self.dst_buffer