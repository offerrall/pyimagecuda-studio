from dataclasses import dataclass
from typing import Annotated

from pyimagecuda import Image, Blend

from ..constraints import INT, DROPDOWN
from ..node_merge import NodeMerge


@dataclass
class MaskNode(NodeMerge):
    anchor: Annotated[str, DROPDOWN(options=[
        "Top-Left", "Top-Center", "Top-Right",
        "Center-Left", "Center", "Center-Right",
        "Bottom-Left", "Bottom-Center", "Bottom-Right"
    ])] = "Center"
    offset_x: Annotated[int, INT(min_value=-5000, max_value=5000)] = 0
    offset_y: Annotated[int, INT(min_value=-5000, max_value=5000)] = 0
    mode: Annotated[str, DROPDOWN(options=["Alpha", "Luminance"])] = "Luminance"
    
    def apply_merge(self, input_1: Image, input_2: Image) -> Image:
        print(f"[MASK] {self.name} applying mask (mode={self.mode}, anchor={self.anchor}, offset_x={self.offset_x}, offset_y={self.offset_y})")

        Blend.mask(
            input_2,
            input_1,
            anchor=self.anchor.lower(),
            offset_x=self.offset_x,
            offset_y=self.offset_y,
            mode=self.mode.lower()
        )
        
        return input_2