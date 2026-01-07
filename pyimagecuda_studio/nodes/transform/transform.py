from dataclasses import dataclass
from typing import Annotated
import math

from pyimagecuda import Image, Transform

from ..constraints import INT, DROPDOWN, CHECKBOX, FLOAT, SIZE
from ..node_in_out import NodeInputOutput
from ..buffers import ensure_buffer
from ..utils import resize_methods, get_resize_function


@dataclass
class ResizeNode(NodeInputOutput):
    size: Annotated[tuple[int, int], SIZE(min_width=1, min_height=1)] = (1920, 1080)
    method: resize_methods = 'Lanczos'
    
    def __post_init__(self):
        self.dst_buffer = None
    
    def apply_process(self, input_image: Image) -> Image:
        method = get_resize_function(self.method)
        self.dst_buffer = ensure_buffer(self.dst_buffer, self.size[0], self.size[1], self.name)
        
        print(f"[RESIZE] {self.name} resizing to {self.size[0]}x{self.size[1]} using {self.method}")
        method(
            input_image,
            width=self.size[0],
            height=self.size[1],
            dst_buffer=self.dst_buffer
        )
        
        return self.dst_buffer


@dataclass
class FlipNode(NodeInputOutput):
    direction: Annotated[str, DROPDOWN(options=['Horizontal', 'Vertical', 'Both'])] = 'Horizontal'
    
    def __post_init__(self):
        self.dst_buffer = None
    
    def apply_process(self, input_image: Image) -> Image:
        self.dst_buffer = ensure_buffer(self.dst_buffer, input_image.width, input_image.height, self.name)
        
        print(f"[FLIP] {self.name} flipping {self.direction.lower()}")
        Transform.flip(input_image, direction=self.direction.lower(), dst_buffer=self.dst_buffer)
        
        return self.dst_buffer

@dataclass
class RotateNode(NodeInputOutput):
    angle: Annotated[float, FLOAT(min_value=0.0, max_value=360.0)] = 0.0
    expand: Annotated[bool, CHECKBOX()] = True
    method: resize_methods = 'Bilinear'
    
    def __post_init__(self):
        self.dst_buffer = None
        self.last_angle = None
        self.last_expand = None
        self.last_input_size = None
    
    def apply_process(self, input_image: Image) -> Image:
        
        norm_angle = self.angle % 360
        if norm_angle < 0:
            norm_angle += 360
        
        if abs(norm_angle - 0) < 0.01 or abs(norm_angle - 180) < 0.01:
            rot_w, rot_h = input_image.width, input_image.height
        elif abs(norm_angle - 90) < 0.01 or abs(norm_angle - 270) < 0.01:
            rot_w, rot_h = input_image.height, input_image.width
        else:
            rads = math.radians(self.angle)
            sin_a = abs(math.sin(rads))
            cos_a = abs(math.cos(rads))
            rot_w = int(input_image.width * cos_a + input_image.height * sin_a)
            rot_h = int(input_image.width * sin_a + input_image.height * cos_a)
        
        if self.expand:
            final_w, final_h = rot_w, rot_h
        else:
            final_w, final_h = input_image.width, input_image.height
        
        self.dst_buffer = ensure_buffer(self.dst_buffer, final_w, final_h, self.name)
        
        interpolation = self.method.lower()
        
        print(f"[ROTATE] {self.name} rotating {self.angle}° (expand={self.expand}, output={final_w}x{final_h}, method={self.method})")
        Transform.rotate(
            input_image, 
            angle=self.angle, 
            expand=self.expand, 
            interpolation=interpolation,
            dst_buffer=self.dst_buffer
        )
        
        return self.dst_buffer


@dataclass
class CropNode(NodeInputOutput):
    x: Annotated[int, INT(min_value=-10000, max_value=10000)] = 0
    y: Annotated[int, INT(min_value=-10000, max_value=10000)] = 0
    width: Annotated[int, INT(min_value=1, max_value=7680)] = 1920
    height: Annotated[int, INT(min_value=1, max_value=7680)] = 1080
    
    def __post_init__(self):
        self.dst_buffer = None
    
    def apply_process(self, input_image: Image) -> Image:
        self.dst_buffer = ensure_buffer(self.dst_buffer, self.width, self.height, self.name)
        
        print(f"[CROP] {self.name} cropping region (x={self.x}, y={self.y}, w={self.width}, h={self.height})")
        Transform.crop(input_image, x=self.x, y=self.y, width=self.width, height=self.height, dst_buffer=self.dst_buffer)
        
        return self.dst_buffer


@dataclass
class ScaleNode(NodeInputOutput):
    scale: Annotated[float, FLOAT(min_value=0.01, max_value=10.0)] = 1.0
    method: resize_methods = 'Lanczos'
    
    def __post_init__(self):
        self.dst_buffer = None
    
    def apply_process(self, input_image: Image) -> Image:
        new_width = int(input_image.width * self.scale)
        new_height = int(input_image.height * self.scale)
        
        new_width = max(1, new_width)
        new_height = max(1, new_height)
        
        method = get_resize_function(self.method)
        self.dst_buffer = ensure_buffer(self.dst_buffer, new_width, new_height, self.name)
        
        print(f"[SCALE] {self.name} scaling by {self.scale}x ({input_image.width}x{input_image.height} → {new_width}x{new_height}) using {self.method}")
        method(
            input_image,
            width=new_width,
            height=new_height,
            dst_buffer=self.dst_buffer
        )
        
        return self.dst_buffer

@dataclass
class ZoomNode(NodeInputOutput):
    zoom_factor: Annotated[float, FLOAT(min_value=0.1, max_value=100.0)] = 2.0
    offset_x: Annotated[int, INT(min_value=-10000, max_value=10000)] = 0
    offset_y: Annotated[int, INT(min_value=-10000, max_value=10000)] = 0
    method: resize_methods = 'Bilinear'
    
    def __post_init__(self):
        self.dst_buffer = None
    
    def apply_process(self, input_image: Image) -> Image:
        self.dst_buffer = ensure_buffer(self.dst_buffer, input_image.width, input_image.height, self.name)
        
        interpolation = self.method.lower()

        center_x = (input_image.width / 2.0) + self.offset_x
        center_y = (input_image.height / 2.0) + self.offset_y
        
        print(f"[ZOOM] {self.name} zooming by {self.zoom_factor}x at center+offset ({center_x:.1f}, {center_y:.1f}) using {self.method}")
        Transform.zoom(
            input_image,
            zoom_factor=self.zoom_factor,
            center_x=center_x,
            center_y=center_y,
            interpolation=interpolation,
            dst_buffer=self.dst_buffer
        )
        
        return self.dst_buffer

@dataclass
class AspectResizeNode(NodeInputOutput):
    mode: Annotated[str, DROPDOWN(options=['Width', 'Height', 'Max', 'Min'])] = 'Width'
    value: Annotated[int, INT(min_value=1, max_value=7680)] = 1920
    method: resize_methods = 'Lanczos'
    
    def __post_init__(self):
        self.dst_buffer = None
    
    def apply_process(self, input_image: Image) -> Image:
        aspect_ratio = input_image.width / input_image.height
        
        if self.mode == 'Width':
            new_width = self.value
            new_height = int(self.value / aspect_ratio)
        elif self.mode == 'Height':
            new_height = self.value
            new_width = int(self.value * aspect_ratio)
        elif self.mode == 'Max':
            if input_image.width >= input_image.height:
                new_width = self.value
                new_height = int(self.value / aspect_ratio)
            else:
                new_height = self.value
                new_width = int(self.value * aspect_ratio)
        else:
            if input_image.width <= input_image.height:
                new_width = self.value
                new_height = int(self.value / aspect_ratio)
            else:
                new_height = self.value
                new_width = int(self.value * aspect_ratio)
        
        new_width = max(1, new_width)
        new_height = max(1, new_height)
        
        method = get_resize_function(self.method)
        self.dst_buffer = ensure_buffer(self.dst_buffer, new_width, new_height, self.name)
        
        print(f"[ASPECT-RESIZE] {self.name} resizing mode={self.mode}, value={self.value} "
              f"({input_image.width}x{input_image.height} → {new_width}x{new_height}) "
              f"using {self.method}")
        
        method(
            input_image,
            width=new_width,
            height=new_height,
            dst_buffer=self.dst_buffer
        )
        
        return self.dst_buffer