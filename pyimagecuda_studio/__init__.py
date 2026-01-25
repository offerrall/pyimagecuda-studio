__version__ = "0.1.7"
__author__ = "Beltrán Offerrall Selma"
__license__ = "MIT"

VERSION_VERBOSE = f"PyImageCuda Studio v{__version__} beta"
DESCRIPTION = "Node-based image processing powered by CUDA."
DEPENDENCIES = ["PyImageCuda", "PySide6", "OpenGL", "PyVips"]
REPO_URL = "https://github.com/offerrall/pyimagecuda-studio"
LICENSE = __license__
PROJECT_EXTENSION = "pics"
AUTHOR_NAME = __author__

from .nodes.headless import (
    LoadProject,
    get_variables,
    set_variable,
    get_nodes,
    get_node_parameters,
    set_node_parameter,
    run,
)