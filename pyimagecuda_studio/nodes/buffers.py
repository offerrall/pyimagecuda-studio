from pyimagecuda import Image
from pyimagecuda.image import ImageBase

def ensure_buffer(buffer: Image | None, width: int, height: int, node_name: str = "Node") -> Image:
    if buffer is None:
        print(f"[BUFFER] Creating buffer for {node_name}: {width}x{height}")
        return Image(width, height)
    
    max_pixels = buffer.get_max_capacity()
    
    if width * height <= max_pixels:
        buffer.resize(width, height)
        return buffer

    print(f"[BUFFER] Recreating buffer for {node_name}: {width}x{height} (exceeded capacity {max_pixels} pixels)")
    buffer.free()
    return Image(width, height)


def resize_buffers(buffers: list[ImageBase], new_size: tuple[int, int]) -> list[ImageBase]:
    new_width, new_height = new_size
    
    if not buffers:
        return buffers
    
    max_pixels = buffers[0].get_max_capacity()
    
    if new_width * new_height <= max_pixels:
        print(f"[BUFFER] Reusing buffers, resizing to {new_width}x{new_height}")
        for buffer in buffers:
            buffer.resize(new_width, new_height)
        return buffers
    else:
        print(f"[BUFFER] Creating new buffers {new_width}x{new_height} (exceeded capacity {max_pixels} pixels)")
        new_buffers = []
        for buffer in buffers:
            BufferClass = type(buffer)
            old_size = (buffer.width, buffer.height)
            buffer.free()
            print(f"[BUFFER] Freed old buffer of type {BufferClass.__name__} with size {old_size}")
            new_buffers.append(BufferClass(width=new_width, height=new_height))
        return new_buffers


def free_node(node) -> None:
    for attr_name in dir(node):
        if attr_name.startswith('_'):
            continue
        
        try:
            attr_value = getattr(node, attr_name)
            
            if isinstance(attr_value, ImageBase):
                print(f"[BUFFER] Freeing {node.name}.{attr_name}")
                attr_value.free()
                setattr(node, attr_name, None)
            
            elif isinstance(attr_value, list):
                for i, item in enumerate(attr_value):
                    if isinstance(item, ImageBase):
                        print(f"[BUFFER] Freeing {node.name}.{attr_name}[{i}]")
                        item.free()
                attr_value.clear()
        
        except (AttributeError, TypeError):
            print(f"[BUFFER] Could not free attribute {attr_name} of node {node.name}")