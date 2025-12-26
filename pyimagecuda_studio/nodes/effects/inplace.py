from dataclasses import dataclass
from typing import Annotated

from pyimagecuda import Image, Effect

from ..constraints import FLOAT, COLOR
from ..node_in_out import NodeInputOutput

@dataclass
class RoundedCornersNode(NodeInputOutput):
    radius: Annotated[float, FLOAT(min_value=0.0)] = 50.0
    
    def apply_process(self, input_image: Image) -> Image:
        print(f"[ROUNDED_CORNERS] {self.name} applying rounded corners (radius={self.radius})")
        Effect.rounded_corners(input_image, self.radius)
        return input_image

@dataclass
class VignetteNode(NodeInputOutput):
    radius: Annotated[float, FLOAT(min_value=0.0, max_value=2.0)] = 0.9
    softness: Annotated[float, FLOAT(min_value=0.0, max_value=5.0)] = 1.0
    color: Annotated[tuple[float, float, float, float], COLOR()] = (0.0, 0.0, 0.0, 1.0)
    
    def apply_process(self, input_image: Image) -> Image:
        print(f"[VIGNETTE] {self.name} applying vignette (radius={self.radius}, softness={self.softness}, color={self.color})")
        Effect.vignette(input_image, self.radius, self.softness, self.color)
        return input_image