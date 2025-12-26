import re

from .core import EndNode
from .generators.generators import *
from .merge.blend import BlendNode
from .merge.mask import MaskNode
from .logic.logic import RandomOutNode, ConditionalNode
from .effects.buffered import DropShadowNode, StrokeNode, GaussianBlurNode
from .effects.inplace import RoundedCornersNode, VignetteNode
from .filters.inplace import SepiaNode, InvertNode, ThresholdNode, SolarizeNode
from .filters.buffered import SharpenNode, SobelNode, EmbossNode
from .adjust.adjust import BrightnessNode, ContrastNode, SaturationNode, GammaNode, OpacityNode
from .node_split import NodeSplit
from .transform.transform import ResizeNode, FlipNode, RotateNode, CropNode, ScaleNode, AspectResizeNode


def node_class_to_name(node_class) -> str:
    name = node_class.__name__
    if name.endswith('Node'):
        name = name[:-4]
    elif name.startswith('Node'):
        name = name[4:]
    name = re.sub(r'([A-Z])', r' \1', name).strip()
    return name


def create_node(node_class, name, preview_callback=None):
    if node_class == EndNode:
        return node_class(name=name, finish_callback=preview_callback)
    return node_class(name=name)

def get_all_node_classes() -> list[type]:
    generators = [
        ImageNode,
        TextNode,
        ColorNode,
        GradientNode,
        StripesNode,
        CheckerboardNode,
        GridNode,
        DotsNode,
        CircleNode,
        NoiseNode,
        PerlinNode,
        NgonNode,
        DynamicTextNode,
    ]
    
    effects = [
        RoundedCornersNode,
        DropShadowNode,
        StrokeNode,
        VignetteNode,
    ]
    
    filters = [
        GaussianBlurNode,
        SharpenNode,
        SepiaNode,
        InvertNode,
        ThresholdNode,
        SolarizeNode,
        SobelNode,
        EmbossNode,
    ]

    adjust = [
        BrightnessNode,
        ContrastNode,
        SaturationNode,
        GammaNode,
        OpacityNode,
    ]

    transform = [
        ResizeNode,
        AspectResizeNode,
        ScaleNode,
        FlipNode,
        RotateNode,
        CropNode,
    ]
    
    merge = [
        BlendNode,
        MaskNode,
    ]

    logic = [
        RandomOutNode,
        ConditionalNode,
    ]
    
    split = [
        NodeSplit,
    ]

    return [generators, effects, filters, adjust, transform, merge, logic, split]

def get_node_menu_structure():
    generators, effects, filters, adjust, transform, merge, logic, split = get_all_node_classes()    
    return {
        "Generators": {node_class_to_name(nc): nc for nc in generators},
        "Effects": {node_class_to_name(nc): nc for nc in effects},
        "Filters": {node_class_to_name(nc): nc for nc in filters},
        "Adjust": {node_class_to_name(nc): nc for nc in adjust},
        "Transform": {node_class_to_name(nc): nc for nc in transform},
        "Logic": {node_class_to_name(nc): nc for nc in logic},
        "Merge": {node_class_to_name(nc): nc for nc in merge},
        "Split": {node_class_to_name(nc): nc for nc in split},
    }