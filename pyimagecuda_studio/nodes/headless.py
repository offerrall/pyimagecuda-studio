from typing import Any
import json

from .core import Node, run_nodes, EndNode, free_nodes
from .serialization import deserialize_nodes, CodeRejectionError, check_executable_code
from .global_variables import get_all_variables, set_variable_value as _set_var
from .constraints import INT, FLOAT, STR, DROPDOWN, COLOR, SIZE, TEXT, FONT, IMAGE_PATH, CHECKBOX, get_annotated_params
from .buffers import resize_buffers
from pyimagecuda import save, ImageU8, Image

_nodes: list[Node] = []
_out_cache: ImageU8 = None

class LoadProject:
    """
    Context manager for loading PyImageCUDA Studio projects.
    
    Automatically handles resource cleanup when exiting the context,
    ensuring proper memory management by calling free_nodes().
    
    Args:
        filepath: Path to the .pics project file
        trust_code: If True, allows loading projects with executable code nodes.
                   Default is False for security.
    
    Raises:
        CodeRejectionError: If project contains executable code and trust_code=False
        FileNotFoundError: If project file doesn't exist
        json.JSONDecodeError: If project file is not valid JSON
    
    Example:
        >>> with LoadProject("my_project.pics") as project:
        ...     set_node_parameter("Text", "text", "Hello")
        ...     run("output.png")
    """
    
    def __init__(self, filepath: str, trust_code: bool = False):
        self.filepath = filepath
        self.trust_code = trust_code
    
    def __enter__(self):
        global _nodes
        
        _nodes.clear()
        
        with open(self.filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        executable_nodes = check_executable_code(data)
        if executable_nodes and not self.trust_code:
            raise CodeRejectionError(
                f"Project contains {len(executable_nodes)} executable code nodes. "
                f"Set trust_code=True to load anyway."
            )
        
        _nodes, _, _ = deserialize_nodes(data, skip_output=False, clear_variables=True)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        global _nodes
        free_nodes(_nodes)
        _nodes.clear()
        return False


def run(output_path: str, quality: int | None = None):
    """
    Execute the loaded project and save the output image.
    
    Runs all nodes in the project graph and saves the final output to the specified path.
    The image format is determined by the file extension (.png, .jpg, .jpeg, .webp).
    
    Args:
        output_path: Path where the output image will be saved
        quality: Compression quality for lossy formats (1-100). 
                None uses format defaults. Only applies to JPEG and WebP.
    
    Raises:
        ValueError: If no Output node is found in the project
        RuntimeError: If the output node was not called during execution
    
    Example:
        >>> with LoadProject("project.pics"):
        ...     run("output.png")
        ...     run("output.jpg", quality=95)
    """
    global _out_cache

    def save_image_callback(img: Image):
        global _out_cache
        _out_cache = resize_buffers([_out_cache], (img.width, img.height))[0]
        save(img, output_path, quality=quality, u8_buffer=_out_cache)

    if not _out_cache:
        _out_cache = ImageU8(1920, 1080)
        print(f"[RUN] Created output cache buffer: 1920x1080")

    out_node = None
    for node in _nodes:
        if isinstance(node, EndNode):
            out_node = node
            break
    if not out_node:
        raise ValueError("[RUN-ERROR] No Output found in project")
    
    out_node.finish_callback = lambda img: save_image_callback(img)

    success = run_nodes(_nodes)
    if not success:
        raise RuntimeError("[RUN-ERROR] Output was not called during execution")
    
    print(f"[RUN] Saving output image to: {output_path}")


def get_variables() -> list[str]:
    """
    Get a list of all variable names in the loaded project.
    
    Variables are global parameters that can be modified across the project.
    
    Returns:
        List of variable names as strings
    
    Example:
        >>> with LoadProject("project.pics"):
        ...     vars = get_variables()
        ...     print(vars)
    """
    return [var.name for var in get_all_variables()]

def set_variable(name: str, value: Any):
    """
    Set the value of a project variable.
    
    Variables are validated according to their type constraints defined in the project.
    
    Args:
        name: Name of the variable to set
        value: New value for the variable. Type depends on variable constraint:
            - INT: int within min/max range
            - FLOAT: float/int within min/max range
            - STR: str within min/max length
            - TEXT: str (no length limit)
            - DROPDOWN: str (must be one of the allowed options)
            - COLOR: tuple/list of 4 floats (r, g, b, a) in range [0, 1]
            - SIZE: tuple/list of 2 ints (width, height) within min/max ranges
            - CHECKBOX: bool
            - IMAGE_PATH: str (file path)
            - FONT: str (font name)
    
    Raises:
        KeyError: If variable with the given name doesn't exist
        TypeError: If value type doesn't match the variable's expected type
        ValueError: If value is outside the allowed range or not in dropdown options
    
    Example:
        >>> with LoadProject("project.pics"):
        ...     set_variable("opacity", 0.75)
        ...     set_variable("text_color", (1.0, 0.0, 0.0, 1.0))
        ...     set_variable("mode", "dark")
        ...     run("output.png")
    """
    for var in get_all_variables():
        if var.name == name:
            constraint = var.type
            
            if isinstance(constraint, INT):
                if not isinstance(value, int):
                    raise TypeError(f"Variable '{name}' expects int")
                if value < constraint.min_value or value > constraint.max_value:
                    raise ValueError(f"Variable '{name}' outside range [{constraint.min_value}, {constraint.max_value}]")
            
            elif isinstance(constraint, FLOAT):
                if not isinstance(value, (int, float)):
                    raise TypeError(f"Variable '{name}' expects float")
                value = float(value)
                if value < constraint.min_value or value > constraint.max_value:
                    raise ValueError(f"Variable '{name}' outside range [{constraint.min_value}, {constraint.max_value}]")
            
            elif isinstance(constraint, STR):
                if not isinstance(value, str):
                    raise TypeError(f"Variable '{name}' expects str")
                if len(value) < constraint.min_length:
                    raise ValueError(f"Variable '{name}' below min length {constraint.min_length}")
                if len(value) > constraint.max_length:
                    raise ValueError(f"Variable '{name}' exceeds max length {constraint.max_length}")
            
            elif isinstance(constraint, TEXT):
                if not isinstance(value, str):
                    raise TypeError(f"Variable '{name}' expects str")
            
            elif isinstance(constraint, DROPDOWN):
                if not isinstance(value, str):
                    raise TypeError(f"Variable '{name}' expects str")
                if value not in constraint.options:
                    raise ValueError(f"Variable '{name}' not in options: {constraint.options}")
            
            elif isinstance(constraint, COLOR):
                if not isinstance(value, (tuple, list)) or len(value) != 4:
                    raise TypeError(f"Variable '{name}' expects (r, g, b, a) tuple/list")
                if not all(isinstance(v, (int, float)) for v in value):
                    raise TypeError(f"Variable '{name}' color components must be numbers")
                if not all(0 <= v <= 1 for v in value):
                    raise ValueError(f"Variable '{name}' color values must be in [0, 1]")
                value = tuple(value)
            
            elif isinstance(constraint, SIZE):
                if not isinstance(value, (tuple, list)) or len(value) != 2:
                    raise TypeError(f"Variable '{name}' expects (width, height) tuple/list")
                if not all(isinstance(v, int) for v in value):
                    raise TypeError(f"Variable '{name}' width and height must be int")
                w, h = value
                if w < constraint.min_width or w > constraint.max_width:
                    raise ValueError(f"Width {w} outside range [{constraint.min_width}, {constraint.max_width}]")
                if h < constraint.min_height or h > constraint.max_height:
                    raise ValueError(f"Height {h} outside range [{constraint.min_height}, {constraint.max_height}]")
                value = tuple(value)
            
            elif isinstance(constraint, CHECKBOX):
                if not isinstance(value, bool):
                    raise TypeError(f"Variable '{name}' expects bool")
            
            elif isinstance(constraint, IMAGE_PATH):
                if not isinstance(value, str):
                    raise TypeError(f"Variable '{name}' expects str (file path)")
            
            elif isinstance(constraint, FONT):
                if not isinstance(value, str):
                    raise TypeError(f"Variable '{name}' expects str (font name)")
            
            _set_var(name, value)
            return
    
    raise KeyError(f"Variable '{name}' not found")

def get_nodes() -> list[str]:
    """
    Get a list of all node names in the loaded project.
    
    Returns:
        List of node names as strings
    
    Example:
        >>> with LoadProject("project.pics"):
        ...     nodes = get_nodes()
        ...     print(nodes)
    """
    return [node.name for node in _nodes]

def get_node_parameters(node_name: str) -> dict[str, Any]:
    """
    Get all parameters and their current values for a specific node.
    
    Args:
        node_name: Name of the node to query
    
    Returns:
        Dictionary mapping parameter names to their current values
    
    Raises:
        KeyError: If no node with the given name exists
    
    Note:
        If multiple nodes share the same name, returns parameters from the first match
        and prints a warning.
    
    Example:
        >>> with LoadProject("project.pics"):
        ...     params = get_node_parameters("Text")
        ...     print(params)
    """
    matches = [node for node in _nodes if node.name == node_name]
    
    if not matches:
        raise KeyError(f"Node '{node_name}' not found")
    
    if len(matches) > 1:
        print(f"[WARNING] Found {len(matches)} nodes with name '{node_name}', returning first one")
    
    node = matches[0]
    params = get_annotated_params(node)
    
    return {param.name: param.value for param in params}

def set_node_parameter(node_name: str, param_name: str, value: Any):
    """
    Set a specific parameter value for a node.
    
    Parameters are validated according to their type constraints.
    
    Args:
        node_name: Name of the node to modify
        param_name: Name of the parameter to set
        value: New value for the parameter. Type depends on parameter constraint:
            - INT: int within min/max range
            - FLOAT: float/int within min/max range
            - STR: str within min/max length
            - TEXT: str (no length limit)
            - DROPDOWN: str (must be one of the allowed options)
            - COLOR: tuple/list of 4 floats (r, g, b, a) in range [0, 1]
            - SIZE: tuple/list of 2 ints (width, height) within min/max ranges
            - CHECKBOX: bool
            - IMAGE_PATH: str (file path)
            - FONT: str (font name)
    
    Raises:
        KeyError: If node or parameter with the given name doesn't exist
        TypeError: If value type doesn't match the parameter's expected type
        ValueError: If value is outside the allowed range or not in dropdown options
    
    Note:
        If multiple nodes share the same name, modifies the first match
        and prints a warning.
    
    Example:
        >>> with LoadProject("project.pics"):
        ...     set_node_parameter("Text", "text", "Hello World")
        ...     set_node_parameter("Blur", "radius", 5.0)
        ...     set_node_parameter("Background", "color", (0.5, 0.5, 0.5, 1.0))
        ...     run("output.png")
    """
    matches = [node for node in _nodes if node.name == node_name]
    
    if not matches:
        raise KeyError(f"Node '{node_name}' not found")
    
    if len(matches) > 1:
        print(f"[WARNING] Found {len(matches)} nodes with name '{node_name}', updating first one")
    
    node = matches[0]
    params = get_annotated_params(node)
    param_info = None
    
    for p in params:
        if p.name == param_name:
            param_info = p
            break
    
    if not param_info:
        raise KeyError(f"Parameter '{param_name}' not found in node '{node_name}'")
    
    constraint = param_info.constraint
    
    if isinstance(constraint, INT):
        if not isinstance(value, int):
            raise TypeError(f"Parameter '{param_name}' expects int")
        if value < constraint.min_value or value > constraint.max_value:
            raise ValueError(f"Parameter '{param_name}' outside range [{constraint.min_value}, {constraint.max_value}]")
    
    elif isinstance(constraint, FLOAT):
        if not isinstance(value, (int, float)):
            raise TypeError(f"Parameter '{param_name}' expects float")
        value = float(value)
        if value < constraint.min_value or value > constraint.max_value:
            raise ValueError(f"Parameter '{param_name}' outside range [{constraint.min_value}, {constraint.max_value}]")
    
    elif isinstance(constraint, STR):
        if not isinstance(value, str):
            raise TypeError(f"Parameter '{param_name}' expects str")
        if len(value) < constraint.min_length:
            raise ValueError(f"Parameter '{param_name}' below min length {constraint.min_length}")
        if len(value) > constraint.max_length:
            raise ValueError(f"Parameter '{param_name}' exceeds max length {constraint.max_length}")
    
    elif isinstance(constraint, TEXT):
        if not isinstance(value, str):
            raise TypeError(f"Parameter '{param_name}' expects str")
    
    elif isinstance(constraint, DROPDOWN):
        if not isinstance(value, str):
            raise TypeError(f"Parameter '{param_name}' expects str")
        if value not in constraint.options:
            raise ValueError(f"Parameter '{param_name}' not in options: {constraint.options}")
    
    elif isinstance(constraint, COLOR):
        if not isinstance(value, (tuple, list)) or len(value) != 4:
            raise TypeError(f"Parameter '{param_name}' expects (r, g, b, a) tuple/list")
        if not all(isinstance(v, (int, float)) for v in value):
            raise TypeError(f"Parameter '{param_name}' color components must be numbers")
        if not all(0 <= v <= 1 for v in value):
            raise ValueError(f"Parameter '{param_name}' color values must be in [0, 1]")
        value = tuple(value)
    
    elif isinstance(constraint, SIZE):
        if not isinstance(value, (tuple, list)) or len(value) != 2:
            raise TypeError(f"Parameter '{param_name}' expects (width, height) tuple/list")
        if not all(isinstance(v, int) for v in value):
            raise TypeError(f"Parameter '{param_name}' width and height must be int")
        w, h = value
        if w < constraint.min_width or w > constraint.max_width:
            raise ValueError(f"Width {w} outside range [{constraint.min_width}, {constraint.max_width}]")
        if h < constraint.min_height or h > constraint.max_height:
            raise ValueError(f"Height {h} outside range [{constraint.min_height}, {constraint.max_height}]")
        value = tuple(value)
    
    elif isinstance(constraint, CHECKBOX):
        if not isinstance(value, bool):
            raise TypeError(f"Parameter '{param_name}' expects bool")
    
    elif isinstance(constraint, IMAGE_PATH):
        if not isinstance(value, str):
            raise TypeError(f"Parameter '{param_name}' expects str (file path)")
    
    elif isinstance(constraint, FONT):
        if not isinstance(value, str):
            raise TypeError(f"Parameter '{param_name}' expects str (font name)")
    
    node.update_param(param_name, value)