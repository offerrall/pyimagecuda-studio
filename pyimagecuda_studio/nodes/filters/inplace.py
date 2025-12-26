from dataclasses import dataclass
from typing import Annotated

from pyimagecuda import Image, Filter

from ..constraints import FLOAT
from ..node_in_out import NodeInputOutput


@dataclass
class SepiaNode(NodeInputOutput):
    intensity: Annotated[float, FLOAT(min_value=0.0, max_value=1.0)] = 1.0
    
    def apply_process(self, input_image: Image) -> Image:
        print(f"[SEPIA] {self.name} applying sepia (intensity={self.intensity})")
        Filter.sepia(input_image, self.intensity)
        return input_image


@dataclass
class InvertNode(NodeInputOutput):
    
    def apply_process(self, input_image: Image) -> Image:
        print(f"[INVERT] {self.name} inverting colors")
        Filter.invert(input_image)
        return input_image


@dataclass
class ThresholdNode(NodeInputOutput):
    value: Annotated[float, FLOAT(min_value=0.0, max_value=1.0)] = 0.5
    
    def apply_process(self, input_image: Image) -> Image:
        print(f"[THRESHOLD] {self.name} applying threshold (value={self.value})")
        Filter.threshold(input_image, self.value)
        return input_image


@dataclass
class SolarizeNode(NodeInputOutput):
    threshold: Annotated[float, FLOAT(min_value=0.0, max_value=1.0)] = 0.5
    
    def apply_process(self, input_image: Image) -> Image:
        print(f"[SOLARIZE] {self.name} applying solarize (threshold={self.threshold})")
        Filter.solarize(input_image, self.threshold)
        return input_image