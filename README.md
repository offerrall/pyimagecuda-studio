# PyImageCUDA Studio 0.1.7 Beta

[![PyPI version](https://img.shields.io/pypi/v/pyimagecuda-studio.svg)](https://pypi.org/project/pyimagecuda-studio/)
[![Version](https://img.shields.io/badge/version-0.1.0%20beta-blue.svg)](https://github.com/offerrall/pyimagecuda-studio)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![CUDA](https://img.shields.io/badge/NVIDIA-CUDA-76B900.svg?logo=nvidia)](https://developer.nvidia.com/cuda-zone)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-lightgrey.svg)](https://github.com/offerrall/pyimagecuda-studio)

**Design image pipelines visually. Automate with Python.**

Node-based GPU compositor with real-time preview and headless batch processing.

Core is [PyImageCUDA](https://github.com/offerrall/pyimagecuda), my custom CUDA library with native kernels for all operations.

Dependencies only for UI (PySide6), I/O (PyVips), and preview (PyOpenGL), no CUDA Toolkit required (just NVIDIA drivers).

https://github.com/user-attachments/assets/6a0ab3da-d961-4587-a67c-7d290a008017

https://github.com/user-attachments/assets/f5c6a81d-5741-40e0-ad55-86a171a8aaa4

---

## Key Features

### Visual Node Editor
- **40+ GPU-accelerated nodes**: Generators, effects, filters, transforms, blend modes (see full list below)
- **Real-time preview**: CUDA-OpenGL interop for instant visual feedback on every change
- **Global variables**: Link any parameter across multiple nodes for template reuse
- **Flexible controls**: Numeric inputs with optional sliders for precise adjustments
- **Intuitive workflow**: Right-click to add nodes, drag to connect, see results instantly

### Headless Automation
- **Simple Python API**: Load `.pics` projects and modify parameters programmatically
- **Batch processing**: Generate thousands of variations in seconds
- **Type-safe validation**: All parameters validated (colors, sizes, text, ranges, etc.)

```python
from pyimagecuda_studio import LoadProject, run, set_node_parameter

with LoadProject("sign.pics"):
    for i in range(1, 11):
        set_node_parameter("Text", "text", f"Test {i}")
        run(f"output_{i:02d}.png")
```

### Performance
- **10-350x faster**: than CPU alternatives for complex operations, see [PyImageCUDA benchmarks](https://offerrall.github.io/pyimagecuda/benchmarks/)
- **5-15ms rendering** — Typical 1080p pipelines (RTX 3070, varies by GPU)
- **Memory efficient**: GPU buffers created on-demand and reused intelligently

---

## Installation

### Requirements
- **Python 3.10+**
- **NVIDIA GPU** (GTX 900 series or newer)
- **OS**: Windows 10/11 or [Linux](https://github.com/offerrall/pyimagecuda?tab=readme-ov-file#linux-compatibility--troubleshooting)

### Install via pip
```bash
pip install pyimagecuda-studio
```

### Launch GUI
```bash
pyimagecuda-studio
# or shorter alias:
pics
```

---

## Available Nodes

### Generators (13 nodes)
- **Image** — Load from file with resize options
- **Text** — Rich text rendering (font, size, color, alignment, spacing)
- **Dynamic Text** — Python-generated text (API calls, calculations, etc.)
- **Color** — Solid fill
- **Gradient** — Linear/radial/diagonal gradients
- **Stripes** — Angled stripe patterns
- **Checkerboard** — Classic checker pattern
- **Grid** — Customizable grid lines
- **Dots** — Polka dot patterns
- **Circle** — Perfect circle
- **Ngon** — Regular polygons (3-20 sides)
- **Noise** — White noise (RGB or monochrome)
- **Perlin** — Organic noise textures

### Effects (5 nodes)
- **Rounded Corners** — Smooth corner radius
- **Drop Shadow** — Blur, offset, color control
- **Stroke** — Inside/outside outline
- **Vignette** — Edge darkening
- **Chroma Key** — Background removal by color

### Filters (8 nodes)
- **Gaussian Blur** — Fast separable blur
- **Sharpen** — Unsharp mask
- **Sepia** — Vintage tone
- **Invert** — Color negative
- **Threshold** — Binary conversion
- **Solarize** — Partial inversion
- **Sobel** — Edge detection
- **Emboss** — 3D relief

### Adjust (7 nodes)
- **Brightness** — Linear adjustment
- **Contrast** — Midpoint scaling
- **Saturation** — Color intensity
- **Hue** — Color rotation
- **Gamma** — Non-linear correction
- **Opacity** — Alpha blending
- **Vibrance** — Smart saturation boost

### Transform (7 nodes)
- **Resize** — Scale to exact dimensions (Nearest/Bilinear/Bicubic/Lanczos)
- **Aspect Resize** — Maintain ratio while resizing
- **Scale** — Percentage-based scaling
- **Flip** — Horizontal/vertical/both
- **Rotate** — Arbitrary angles with optional expand
- **Crop** — Extract rectangular region
- **Zoom** — Zoom in/out with offset

### Merge (2 nodes)
- **Blend** — Composite two images with Photoshop-style blend modes
  - **Modes:** Normal, Multiply, Screen, Add, Overlay, Soft Light, Hard Light
  - **Positioning:** 9 anchor points (top-left, center, bottom-right, etc.) + pixel offset
  - **Control:** Opacity slider (0.0-1.0)
- **Mask** — Use image brightness or alpha as transparency mask
  - **Modes:** Luminance (brightness) or Alpha channel
  - **Positioning:** Same anchor + offset system as Blend

### Logic (2 nodes)
- **Random Out** — Randomly select between inputs
- **Conditional** — Python-based routing logic

### Utility (1 node)
- **Split** — Duplicate to 2 outputs

## Headless Mode

Design templates in the GUI, automate generation with Python.

### Basic Example
```python
from pyimagecuda_studio import LoadProject, set_node_parameter, run

with LoadProject("template.pics"):
    set_node_parameter("Text", "text", "Hello World")
    run("output.png")
```

### Batch Processing
```python
from pyimagecuda_studio import LoadProject, set_node_parameter, run

with LoadProject("certificate.pics"):
    for name in ["Alice", "Bob", "Charlie"]:
        set_node_parameter("Text", "text", f"Certificate for {name}")
        run(f"certs/{name}.png")
```

### Global Variables

Control multiple parameters at once:
```python
from pyimagecuda_studio import LoadProject, set_variable, run

with LoadProject("banner.pics"):
    set_variable("primary_color", (0.2, 0.4, 0.8, 1.0))
    set_variable("title", "Summer Sale")
    run("output.png")
```

### Real-World: CSV Data
```python
import csv
from pyimagecuda_studio import LoadProject, set_variable, run

with LoadProject("product_card.pics"):
    with open('products.csv') as f:
        for row in csv.DictReader(f):
            set_variable("product_name", row['name'])
            set_variable("price", f"${row['price']}")
            set_node_parameter("Image", "path", row['image_path'])
            run(f"cards/{row['id']}.png")
```

### API Functions
```python
# Load project (context manager handles cleanup)
with LoadProject(filepath, trust_code=False):
    
    # Modify nodes directly
    set_node_parameter(node_name, param_name, value)
    
    # Modify global variables
    set_variable(name, value)
    
    # Generate output
    run(output_path, quality=None)
    
    # Query project
    get_nodes()           # -> list[str]
    get_variables()       # -> list[str]
    get_node_parameters(node_name)  # -> dict
```

### Security Note

Projects with **Dynamic Text** or **Conditional** nodes execute Python code. Set `trust_code=True` only for projects you trust:
```python
with LoadProject("untrusted.pics", trust_code=True):  # ⚠️ Only if you trust the source
    run("output.png")
```
---

## Roadmap to v1.0

### Current: v0.1.0 Beta
Core functionality complete and stable.

### Path to v1.0 Stable
- [ ] **Bug fixes** — Address issues reported by community
- [ ] **Undo/redo** — Full history system for GUI operations
- [ ] **Memory pooling** — Intelligent VRAM reuse to reduce memory footprint
- [ ] **Expanded library** — More nodes, effects, and generators

**Timeline:** v1.0 release when all critical features are stable and well-tested.

---

## Contributing

**Beta Release** — Contributions, feedback, and collaborators welcome!

I'm very open to:
- **Code contributions** — Pull requests for bug fixes, features, or optimizations
- **Ideas and suggestions** — Feature requests and use case proposals
- **Use case adaptations** — I'm happy to adapt the program for personal workflows if they have general applicability

All contributions, questions, and feature requests go through [GitHub Issues](https://github.com/offerrall/pyimagecuda-studio/issues).

I'll respond as quickly as I can.

**When reporting bugs, include:**
- OS and GPU model
- Python version
- Error message or unexpected behavior
- `.pics` project file (if applicable)

---

## License

MIT License

Copyright (c) 2025 Beltrán Offerrall Selma

See [LICENSE](LICENSE) file for details.

---
