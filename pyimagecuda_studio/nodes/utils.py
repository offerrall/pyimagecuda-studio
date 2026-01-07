from typing import Annotated
from typing import Literal
from pyimagecuda import Resize

from .constraints import DROPDOWN

resize_methods = Annotated[str, DROPDOWN(options=['Nearest', 'Bilinear', 'Bicubic', 'Lanczos'])]

def get_resize_function(method: Literal['Nearest', 'Bilinear', 'Bicubic', 'Lanczos']):
    """
    Returns the appropriate resize function from pyimagecuda.
    
    Args:
        method: Resize method name ('Nearest', 'Bilinear', 'Bicubic', 'Lanczos')
    
    Returns:
        Corresponding Resize function
    """
    resize_methods = {
        'Nearest': Resize.nearest,
        'Bilinear': Resize.bilinear,
        'Bicubic': Resize.bicubic,
        'Lanczos': Resize.lanczos
    }
    return resize_methods.get(method, Resize.lanczos)