from dataclasses import dataclass
from typing import Annotated

from pyimagecuda import Image, Blend

from ..constraints import FLOAT, INT, DROPDOWN
from ..node_merge import NodeMerge

@dataclass
class BlendNode(NodeMerge):
    blend_mode: Annotated[str, DROPDOWN(options=[
        "Normal", "Multiply", "Screen", "Add", "Overlay", "Soft light", "Hard light"
    ])] = "Normal"
    anchor: Annotated[str, DROPDOWN(options=[
        "Top-Left", "Top-Center", "Top-Right",
        "Center-Left", "Center", "Center-Right",
        "Bottom-Left", "Bottom-Center", "Bottom-Right"
    ])] = "Center"
    offset_x: Annotated[int, INT(min_value=-5000, max_value=5000)] = 0
    offset_y: Annotated[int, INT(min_value=-5000, max_value=5000)] = 0
    opacity: Annotated[float, FLOAT(min_value=0.0, max_value=1.0)] = 1.0
    
    def apply_merge(self, input_1: Image, input_2: Image) -> Image:
        print(f"[BLEND] {self.name} blending (mode={self.blend_mode}, anchor={self.anchor}, offset_x={self.offset_x}, offset_y={self.offset_y}, opacity={self.opacity})")
        
        blend_func = {
            "Normal": Blend.normal,
            "Multiply": Blend.multiply,
            "Screen": Blend.screen,
            "Add": Blend.add,
            "Overlay": Blend.overlay,
            "Soft light": Blend.soft_light,
            "Hard light": Blend.hard_light
        }[self.blend_mode]
        
        blend_func(
            input_2,
            input_1,
            anchor=self.anchor.lower(),
            offset_x=self.offset_x,
            offset_y=self.offset_y,
            opacity=self.opacity
        )
        
        return input_2