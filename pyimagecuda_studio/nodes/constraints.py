from dataclasses import dataclass
from dataclasses import fields, is_dataclass
from typing import get_origin, get_args, Annotated, Any

@dataclass
class PARAM:
    pass

@dataclass
class INT(PARAM):
    max_value: int = 3_000
    min_value: int = -3_000

@dataclass
class FLOAT(PARAM):
    max_value: float = 3_000.0
    min_value: float = -3_000.0

@dataclass
class STR(PARAM):
    max_length: int = 255
    min_length: int = 0

@dataclass
class DROPDOWN(PARAM):
    options: list[str]

@dataclass
class CHECKBOX(PARAM):
    pass

@dataclass
class COLOR(PARAM):
    pass

@dataclass
class SIZE(PARAM):
    max_width: int = 7680
    min_width: int = 1
    max_height: int = 7680
    min_height: int = 1

@dataclass
class IMAGE_PATH(PARAM):
    format_options: list[str] = ("png", "jpg", "jpeg", "bmp", "tiff", "webp", "gif", "avi")

@dataclass
class FONT(PARAM):
    pass

@dataclass
class TEXT(PARAM):
    pass

TYPE_MAP = {
    "Integer": INT,
    "Float": FLOAT,
    "Normal Text": STR,
    "Dropdown": DROPDOWN,
    "Checkbox": CHECKBOX,
    "Color": COLOR,
    "Size": SIZE,
    "Image Path": IMAGE_PATH,
    "Font": FONT,
    "Multiline Text": TEXT
}

CLASS_NAME_TO_TYPE = {
    "INT": INT,
    "FLOAT": FLOAT,
    "STR": STR,
    "DROPDOWN": DROPDOWN,
    "CHECKBOX": CHECKBOX,
    "COLOR": COLOR,
    "SIZE": SIZE,
    "IMAGE_PATH": IMAGE_PATH,
    "FONT": FONT,
    "TEXT": TEXT
}

def class_to_type_map(cls: PARAM) -> str:
    for type_name, type_cls in TYPE_MAP.items():
        if type_cls == cls:
            return type_name
    return "Unknown"

class ParamInfo:
    def __init__(self, name: str, value: Any, param_type: type, constraint: Any):
        self.name = name
        self.value = value
        self.param_type = param_type
        self.constraint = constraint
    
    def __repr__(self):
        return f"ParamInfo(name={self.name}, value={self.value}, type={self.param_type.__name__}, constraint={self.constraint})"


def get_annotated_params(node_instance) -> list[ParamInfo]:

    if not is_dataclass(node_instance):
        return []
    
    result = []
    
    for field in fields(node_instance):
        annotation = field.type

        if get_origin(annotation) is Annotated:
            args = get_args(annotation)

            param_type = args[0]
            constraint = args[1] if len(args) > 1 else None

            current_value = getattr(node_instance, field.name)
            
            result.append(ParamInfo(
                name=field.name,
                value=current_value,
                param_type=param_type,
                constraint=constraint
            ))
    
    return result