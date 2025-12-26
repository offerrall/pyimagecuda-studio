from dataclasses import dataclass
from typing import Annotated

from pyimagecuda import Image, Adjust

from ..constraints import FLOAT
from ..node_in_out import NodeInputOutput


@dataclass
class BrightnessNode(NodeInputOutput):
    factor: Annotated[float, FLOAT(min_value=-1.0, max_value=1.0)] = 0.0
    
    def apply_process(self, input_image: Image) -> Image:
        print(f"[BRIGHTNESS] {self.name} adjusting brightness (factor={self.factor})")
        Adjust.brightness(input_image, self.factor)
        return input_image


@dataclass
class ContrastNode(NodeInputOutput):
    factor: Annotated[float, FLOAT(min_value=0.0, max_value=3.0)] = 1.0
    
    def apply_process(self, input_image: Image) -> Image:
        print(f"[CONTRAST] {self.name} adjusting contrast (factor={self.factor})")
        Adjust.contrast(input_image, self.factor)
        return input_image


@dataclass
class SaturationNode(NodeInputOutput):
    factor: Annotated[float, FLOAT(min_value=0.0, max_value=3.0)] = 1.0
    
    def apply_process(self, input_image: Image) -> Image:
        print(f"[SATURATION] {self.name} adjusting saturation (factor={self.factor})")
        Adjust.saturation(input_image, self.factor)
        return input_image


@dataclass
class GammaNode(NodeInputOutput):
    gamma: Annotated[float, FLOAT(min_value=0.1, max_value=3.0)] = 1.0
    
    def apply_process(self, input_image: Image) -> Image:
        print(f"[GAMMA] {self.name} adjusting gamma (gamma={self.gamma})")
        Adjust.gamma(input_image, self.gamma)
        return input_image


@dataclass
class OpacityNode(NodeInputOutput):
    factor: Annotated[float, FLOAT(min_value=0.0, max_value=1.0)] = 1.0
    
    def apply_process(self, input_image: Image) -> Image:
        print(f"[OPACITY] {self.name} adjusting opacity (factor={self.factor})")
        Adjust.opacity(input_image, self.factor)
        return input_image