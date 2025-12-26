from dataclasses import dataclass
from typing import Annotated
from os.path import exists
from pyimagecuda import Fill, load, copy, Resize, Text, Image

from ..constraints import COLOR, FLOAT, INT, CHECKBOX, DROPDOWN, IMAGE_PATH, TEXT, FONT
from ..node_generator import NodeGenerator
from ..buffers import resize_buffers

@dataclass
class ImageNode(NodeGenerator):
    path: Annotated[str, IMAGE_PATH()] = ""
    resize_method: Annotated[str, DROPDOWN(options=['Nearest', 'Bilinear', 'Bicubic', 'Lanczos'])] = 'Lanczos'
    
    def __post_init__(self):
        super().__post_init__()
        self.original_image = None
        self.original_image_filepath = self.path
        
        if not exists(self.path):
            print(f"[LOAD_IMAGE] {self.name} filepath does not exist at init: {self.path}")
            self.path = ""
            self.original_image_filepath = ""

        self.generate_image()
    
    def generate_image(self):

        if not self.path:
            print(f"[LOAD_IMAGE] {self.name} no filepath provided, skipping load")
            Fill.checkerboard(self.image, size=10, color1=(1.0, 0.0, 1.0, 1.0), color2=(0.0, 0.0, 0.0, 1.0), offset_x=0, offset_y=0)
            return
        
        if self.original_image_filepath != self.path:
            print(f"[LOAD_IMAGE] {self.name} filepath changed from {self.original_image_filepath} to {self.path}")
            if self.original_image:
                last_size = (self.original_image.width, self.original_image.height)
                self.original_image.free()
                print(f"[LOAD_IMAGE] {self.name} freed previous original image of size {last_size}")
            self.original_image = None

        if not self.original_image:
            print(f"[LOAD_IMAGE] {self.name} loading image from {self.path}")
            self.original_image = load(self.path)
            self.original_image_filepath = self.path
            self.image, self.cache_image = resize_buffers([self.image, self.cache_image], (self.original_image.width, self.original_image.height))
            print(f"[LOAD_IMAGE] Created buffer for original image size ({self.original_image.width}x{self.original_image.height})")
            self.size = (self.original_image.width, self.original_image.height)
        
        if self.original_image.width == self.size[0] and self.original_image.height == self.size[1]:
            print(f"[LOAD_IMAGE] {self.name} original image size matches target size ({self.image.width}x{self.image.height}), no resize needed")
            copy(self.image, self.original_image)
            print(f"[LOAD_IMAGE] {self.name} copied original image to image buffer")
            return
        
        resize_methods = {
            'Nearest': Resize.nearest,
            'Bilinear': Resize.bilinear,
            'Bicubic': Resize.bicubic,
            'Lanczos': Resize.lanczos
        }
        method = resize_methods.get(self.resize_method, Resize.lanczos)
        print(f"[LOAD_IMAGE] {self.name} resizing original image to ({self.image.width}x{self.image.height}) using {self.resize_method} method")
        method(
            self.original_image,
            width=self.image.width,
            height=self.image.height,
            dst_buffer=self.image
        )

@dataclass
class ColorNode(NodeGenerator):
    color: Annotated[tuple[float, float, float, float], COLOR()] = (0.0, 0.0, 0.0, 1.0)
    
    def __post_init__(self):
        super().__post_init__()
        self.generate_image()
    
    def generate_image(self):
        print(f"[FILL_COLOR] {self.name} filling (color={self.color})")
        Fill.color(self.image, self.color)

@dataclass
class StripesNode(NodeGenerator):
    angle: Annotated[float, FLOAT(min_value=0.0, max_value=360.0)] = 45.0
    spacing: Annotated[int, INT(min_value=1, max_value=1000)] = 40
    width: Annotated[int, INT(min_value=1, max_value=1000)] = 20
    color1: Annotated[tuple[float, float, float, float], COLOR()] = (1.0, 1.0, 1.0, 1.0)
    color2: Annotated[tuple[float, float, float, float], COLOR()] = (0.0, 0.0, 0.0, 0.0)
    offset: Annotated[int, INT(min_value=0, max_value=10000)] = 0
    
    def __post_init__(self):
        super().__post_init__()
        self.generate_image()
    
    def generate_image(self):
        print(f"[STRIPES] {self.name} generating stripes (angle={self.angle}, spacing={self.spacing}, width={self.width}, color1={self.color1}, color2={self.color2}, offset={self.offset})")
        Fill.stripes(
            self.image,
            angle=self.angle,
            spacing=self.spacing,
            width=self.width,
            color1=self.color1,
            color2=self.color2,
            offset=self.offset
        )


@dataclass
class GradientNode(NodeGenerator):
    color_1: Annotated[tuple[float, float, float, float], COLOR()] = (0.0, 0.0, 0.0, 1.0)
    color_2: Annotated[tuple[float, float, float, float], COLOR()] = (1.0, 1.0, 1.0, 1.0)
    direction: Annotated[str, DROPDOWN(options=['Horizontal', 'Vertical', 'Diagonal', 'Radial'])] = 'Horizontal'
    seamless: Annotated[bool, CHECKBOX()] = False
    
    def __post_init__(self):
        super().__post_init__()
        self.generate_image()
    
    def generate_image(self):
        print(f"[GRADIENT] {self.name} generating gradient (color_1={self.color_1}, color_2={self.color_2}, direction={self.direction}, seamless={self.seamless})")
        direction = self.direction.lower()
        Fill.gradient(
            self.image,
            rgba1=self.color_1,
            rgba2=self.color_2,
            direction=direction,
            seamless=self.seamless
        )


@dataclass
class CheckerboardNode(NodeGenerator):
    cell_size: Annotated[int, INT(min_value=1, max_value=1000)] = 50
    color_1: Annotated[tuple[float, float, float, float], COLOR()] = (0.8, 0.8, 0.8, 1.0)
    color_2: Annotated[tuple[float, float, float, float], COLOR()] = (0.5, 0.5, 0.5, 1.0)
    offset_x: Annotated[int, INT(min_value=0, max_value=10000)] = 0
    offset_y: Annotated[int, INT(min_value=0, max_value=10000)] = 0
    
    def __post_init__(self):
        super().__post_init__()
        self.generate_image()
    
    def generate_image(self):
        print(f"[CHECKERBOARD] {self.name} generating checkerboard (size={self.cell_size}, color1={self.color_1}, color2={self.color_2}, offset_x={self.offset_x}, offset_y={self.offset_y})")
        Fill.checkerboard(
            self.image,
            size=self.cell_size,
            color1=self.color_1,
            color2=self.color_2,
            offset_x=self.offset_x,
            offset_y=self.offset_y
        )


@dataclass
class GridNode(NodeGenerator):
    spacing: Annotated[int, INT(min_value=1, max_value=1000)] = 50
    line_width: Annotated[int, INT(min_value=1, max_value=300)] = 10
    color: Annotated[tuple[float, float, float, float], COLOR()] = (0.5, 0.5, 0.5, 1.0)
    bg_color: Annotated[tuple[float, float, float, float], COLOR()] = (0.0, 0.0, 0.0, 0.0)
    offset_x: Annotated[int, INT(min_value=0, max_value=10000)] = 0
    offset_y: Annotated[int, INT(min_value=0, max_value=10000)] = 0
    
    def __post_init__(self):
        super().__post_init__()
        self.generate_image()
    
    def generate_image(self):
        print(f"[GRID] {self.name} generating grid (spacing={self.spacing}, line_width={self.line_width}, color={self.color}, bg_color={self.bg_color}, offset_x={self.offset_x}, offset_y={self.offset_y})")
        Fill.grid(
            self.image,
            spacing=self.spacing,
            line_width=self.line_width,
            color=self.color,
            bg_color=self.bg_color,
            offset_x=self.offset_x,
            offset_y=self.offset_y
        )


@dataclass
class DotsNode(NodeGenerator):
    spacing: Annotated[int, INT(min_value=1, max_value=1000)] = 40
    radius: Annotated[float, FLOAT(min_value=0.1, max_value=500.0)] = 10.0
    color: Annotated[tuple[float, float, float, float], COLOR()] = (1.0, 1.0, 1.0, 1.0)
    bg_color: Annotated[tuple[float, float, float, float], COLOR()] = (0.0, 0.0, 0.0, 0.0)
    offset_x: Annotated[int, INT(min_value=0, max_value=10000)] = 0
    offset_y: Annotated[int, INT(min_value=0, max_value=10000)] = 0
    softness: Annotated[float, FLOAT(min_value=0.0, max_value=1.0)] = 0.0
    
    def __post_init__(self):
        super().__post_init__()
        self.generate_image()
    
    def generate_image(self):
        print(f"[DOTS] {self.name} generating dots (spacing={self.spacing}, radius={self.radius}, color={self.color}, bg_color={self.bg_color}, offset_x={self.offset_x}, offset_y={self.offset_y}, softness={self.softness})")
        Fill.dots(
            self.image,
            spacing=self.spacing,
            radius=self.radius,
            color=self.color,
            bg_color=self.bg_color,
            offset_x=self.offset_x,
            offset_y=self.offset_y,
            softness=self.softness
        )


@dataclass
class CircleNode(NodeGenerator):
    color: Annotated[tuple[float, float, float, float], COLOR()] = (1.0, 1.0, 1.0, 1.0)
    bg_color: Annotated[tuple[float, float, float, float], COLOR()] = (0.0, 0.0, 0.0, 0.0)
    softness: Annotated[float, FLOAT(min_value=0.0, max_value=1.0)] = 0.0
    
    def __post_init__(self):
        super().__post_init__()
        self.generate_image()
    
    def generate_image(self):
        print(f"[CIRCLE] {self.name} generating circle (color={self.color}, bg_color={self.bg_color}, softness={self.softness})")
        Fill.circle(
            self.image,
            color=self.color,
            bg_color=self.bg_color,
            softness=self.softness
        )


@dataclass
class NoiseNode(NodeGenerator):
    seed: Annotated[float, FLOAT(min_value=0.0, max_value=10000.0)] = 0.0
    monochrome: Annotated[bool, CHECKBOX()] = True
    
    def __post_init__(self):
        super().__post_init__()
        self.generate_image()
    
    def generate_image(self):
        print(f"[NOISE] {self.name} generating noise (seed={self.seed}, monochrome={self.monochrome})")
        Fill.noise(
            self.image,
            seed=self.seed,
            monochrome=self.monochrome
        )


@dataclass
class PerlinNode(NodeGenerator):
    scale: Annotated[float, FLOAT(min_value=0.1, max_value=1000.0)] = 50.0
    seed: Annotated[float, FLOAT(min_value=0.0, max_value=10000.0)] = 0.0
    octaves: Annotated[int, INT(min_value=1, max_value=10)] = 1
    persistence: Annotated[float, FLOAT(min_value=0.0, max_value=1.0)] = 0.5
    lacunarity: Annotated[float, FLOAT(min_value=1.0, max_value=4.0)] = 2.0
    offset_x: Annotated[float, FLOAT(min_value=-10000.0, max_value=10000.0)] = 0.0
    offset_y: Annotated[float, FLOAT(min_value=-10000.0, max_value=10000.0)] = 0.0
    color1: Annotated[tuple[float, float, float, float], COLOR()] = (0.0, 0.0, 0.0, 1.0)
    color2: Annotated[tuple[float, float, float, float], COLOR()] = (1.0, 1.0, 1.0, 1.0)
    
    def __post_init__(self):
        super().__post_init__()
        self.generate_image()
    
    def generate_image(self):
        print(f"[PERLIN] {self.name} generating perlin noise (scale={self.scale}, seed={self.seed}, octaves={self.octaves}, persistence={self.persistence}, lacunarity={self.lacunarity}, offset_x={self.offset_x}, offset_y={self.offset_y}, color1={self.color1}, color2={self.color2})")
        Fill.perlin(
            self.image,
            scale=self.scale,
            seed=self.seed,
            octaves=self.octaves,
            persistence=self.persistence,
            lacunarity=self.lacunarity,
            offset_x=self.offset_x,
            offset_y=self.offset_y,
            color1=self.color1,
            color2=self.color2
        )


@dataclass
class NgonNode(NodeGenerator):
    sides: Annotated[int, INT(min_value=3, max_value=20)] = 3
    color: Annotated[tuple[float, float, float, float], COLOR()] = (1.0, 1.0, 1.0, 1.0)
    bg_color: Annotated[tuple[float, float, float, float], COLOR()] = (0.0, 0.0, 0.0, 0.0)
    rotation: Annotated[float, FLOAT(min_value=0.0, max_value=360.0)] = 0.0
    softness: Annotated[float, FLOAT(min_value=0.0, max_value=1.0)] = 0.0
    
    def __post_init__(self):
        super().__post_init__()
        self.generate_image()
    
    def generate_image(self):
        print(f"[NGON] {self.name} generating ngon (sides={self.sides}, color={self.color}, bg_color={self.bg_color}, rotation={self.rotation}, softness={self.softness})")
        Fill.ngon(
            self.image,
            sides=self.sides,
            color=self.color,
            bg_color=self.bg_color,
            rotation=self.rotation,
            softness=self.softness
        )

@dataclass
class TextNode(NodeGenerator):
    text: Annotated[str, TEXT()] = "Hello World"
    font: Annotated[str, FONT()] = "Arial"
    text_size: Annotated[float, FLOAT(min_value=1.0, max_value=2000.0)] = 50.0
    color: Annotated[tuple[float, float, float, float], COLOR()] = (0.0, 0.0, 0.0, 1.0)
    bg_color: Annotated[tuple[float, float, float, float], COLOR()] = (0.0, 0.0, 0.0, 0.0)
    align: Annotated[str, DROPDOWN(options=['Left', 'Centre', 'Right'])] = 'Left'
    spacing: Annotated[int, INT(min_value=-1500.0, max_value=1500)] = 0
    letter_spacing: Annotated[float, FLOAT(min_value=-500.0, max_value=500.0)] = 0.0

    def __post_init__(self):
        self.properties_not_show.append("size")
        self.image = None
        self.cache_image = None
        self.generate_image()

    def generate_image(self):
        print(f"[TEXT] {self.name} rendering text '{self.text}' (font={self.font}, size={self.size}, align={self.align})")
        
        if self.image:
            old_size = (self.image.width, self.image.height)
            self.image.free()
            self.cache_image.free()
            print(f"[TEXT] {self.name} freed previous text image of size {old_size}, 2 buffers freed")

        self.image = Text.create(
            text=self.text,
            font=self.font,
            size=self.text_size,
            color=self.color,
            bg_color=self.bg_color,
            align=self.align.lower(),
            justify=False,
            spacing=self.spacing,
            letter_spacing=self.letter_spacing,
        )

        self.cache_image = Image(self.image.width, self.image.height)
        self.size = (self.image.width, self.image.height)
        print(f"[TEXT] {self.name} 2 Buffers created for text image size ({self.image.width}x{self.image.height})")

    def update_param_child(self, param_name, value):
        setattr(self, param_name, value)
        if param_name == "name":
            return
        self.generate_image()

code_example = """
import requests

def get_text():
    try:
        response = requests.get('https://api.coinbase.com/v2/prices/BTC-USD/spot')
        price = response.json()['data']['amount']
        return f"Bitcoin: ${price}"
    except:
        return "Bitcoin: ERROR"
"""


@dataclass
class DynamicTextNode(TextNode):
    code: Annotated[str, TEXT()] = code_example

    def __post_init__(self):
        super().__post_init__()
        self.properties_not_show.append("text")

    def _execute_code(self) -> str:
        try:
            namespace = {'__builtins__': __builtins__}
            exec(self.code, namespace, namespace)
            
            if 'get_text' not in namespace:
                print(f"[DYNAMIC-TEXT] {self.name} error: Function 'get_text()' not found in code")
                raise ValueError("Function 'get_text()' not found in code")
            
            result = namespace['get_text']()
            
            if not isinstance(result, str):
                result = str(result)
            
            print(f"[DYNAMIC-TEXT] {self.name} executed get_text() → '{result}'")
            return result
            
        except Exception as e:
            error_msg = f"ERROR: {str(e)}"
            print(f"[DYNAMIC-TEXT] {self.name} execution error: {e}")
            return error_msg

    def process(self):
        if self.connect_to and not self.hide_node:
            self.text = self._execute_code()
        super().generate_image()
        super().process()

    def generate_image(self):
        self.text = self._execute_code()
        super().generate_image()