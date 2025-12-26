import sys
import json
from pathlib import Path
from importlib import resources

def get_icon_path(icon_name):
    """Get path to icon file from package resources"""
    return str(resources.files('pyimagecuda_studio.icons').joinpath(icon_name))

def get_config_path():
    """Get config file path in user's app data directory"""
    if sys.platform == 'win32':
        config_dir = Path.home() / 'AppData' / 'Local' / 'pyimagecuda_studio'
    else:
        config_dir = Path.home() / '.config' / 'pyimagecuda_studio'
    
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / 'config.json'

def _load_config_data():
    config = get_config_path()
    if not config.exists():
        return {}
    with open(config, 'r', encoding='utf-8') as f:
        return json.load(f)

def _save_config_data(data):
    with open(get_config_path(), 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def get_config_value(key, default=None):
    return _load_config_data().get(key, default)

def set_config_value(key, value):
    data = _load_config_data()
    data[key] = value
    _save_config_data(data)

# Icon paths
EYE_OPEN_PATH = get_icon_path('eye_open.svg')
EYE_CLOSED_PATH = get_icon_path('eye_closed.svg')
TEXT_NODE_PATH = get_icon_path('text_node.svg')
IMAGE_NODE_PATH = get_icon_path('image_node.svg')
COLOR_NODE_PATH = get_icon_path('color_node.svg')
BLEND_NODE_PATH = get_icon_path('blend_node.svg')
MASK_NODE_PATH = get_icon_path('mask_node.svg')
SPLIT_NODE_PATH = get_icon_path('split_node.svg')
RESIZE_NODE_PATH = get_icon_path('resize_node.svg')
SCALE_NODE_PATH = get_icon_path('scale_node.svg')
OTHERS_NODE_PATH = get_icon_path('others_node.svg')