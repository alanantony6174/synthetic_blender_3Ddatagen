# 3D Synthetic Data Generation with Blender

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

A lightweight, extensible pipeline to wrap arbitrary 2D images onto 3D primitives (e.g., boxes, future cylinder support) using Blender, then auto-generate a complete Gazebo model (SDF + textures).

---

## Table of Contents

1. [Overview](#overview)  
2. [Features](#features)  
3. [Prerequisites](#prerequisites)  
4. [Installation](#installation)  
5. [Directory Structure](#directory-structure)  
6. [Usage](#usage)  
   - [Single Model Generation](#single-model-generation)  
   - [Batch Generation](#batch-generation)  
   - [Selecting a Different Primitive](#selecting-a-different-primitive)  
   - [Blender Path Configuration](#blender-path-configuration)  
7. [Configuration for New Primitives](#configuration-for-new-primitives)  
8. [Contributing](#contributing)  
9. [License](#license)

---

## Overview

This repository provides:

- A **Blender** script (`wrap_image_box.py`) to project 2D images onto the side face of a box primitive (with future support for other shapes).
- A **Python** tool (`generate_sdf_model.py`) that reads shape parameters or meshes and produces a valid Gazebo model folder (`model.sdf`, `model.config`, and `/meshes`).
- A **one‑stop launcher** (`main.py`) that runs both steps seamlessly, headlessly or interactively.

Together, they streamline synthetic 3D data creation for robotics, computer vision, and simulation.

---

## Features

- **Automatic aspect‑ratio detection** of input images  
- **Interactive prompts** for box dimensions (X, Z in cm)  
- **Consistent naming conventions**:  
  - Texture: `texture_<W>x<D>x<H>.<ext>`  
  - Model:   `<primitive>_<W>x<D>x<H>.dae`  
- **One‑stop pipeline** via `main.py`  
- **Headless / batch operation** for large datasets  
- **Extensible**: add new shapes by dropping in a primitive wrapper and config

---

## Prerequisites

- **Blender 4.2.1** (or newer)  
- **Python 3.7+**  
- Unix‑like shell (tested on Linux; Blender CLI required)

---

## Installation

1. **Clone the repository**  
   ```bash
   git clone https://github.com/alanantony6174/synthetic_blender_3Ddatagen.git
   cd synthetic_blender_3Ddatagen
   ```

2. **Download & extract Blender** (if not installed)  
   ```bash
   cd ~
   wget https://download.blender.org/release/Blender4.2/blender-4.2.1-linux-x64.tar.xz
   tar -xf blender-4.2.1-linux-x64.tar.xz
   ```

3. **Make scripts executable**  
   ```bash
   chmod +x wrap_image_box.py generate_sdf_model.py main.py
   ```

4. **(Optional) Add Blender to your PATH**  
   ```bash
   echo 'export BLENDER_PATH=~/blender-4.2.1-linux-x64/blender' >> ~/.bashrc
   source ~/.bashrc
   ```

---

## Directory Structure

```
project-root/
├── primitives/             # OOP wrappers for each shape
│   ├── __init__.py
│   ├── base.py
│   ├── box.py
│   └── cylinder.py         # stub for future
├── configs/                # (optional) shape‑based SDF templates
│   ├── box.yaml
│   └── cylinder.yaml
├── wrap_image_box.py       # Blender CLI entry point
├── generate_sdf_model.py   # Generic SDF model generator
├── main.py                 # One‑stop pipeline launcher
├── images/                 # Example input images
│   └── pics_crop/
├── output_tmp/             # Scratch folder (auto‑created)
└── README.md
```

---

## Usage

### Single Model Generation
Run main,py
```bash
python3 main.py
```
![Example Image](images/image.png)

### Batch Directory Generation

```bash
./main.py \
  --batch-dir ./images/ \
  --output    ~/.gazebo/models/
```

### Selecting a Different Primitive

Supported primitives: `box` (default), `cylinder` (stub).  

```bash
./main.py   --primitive cylinder   --image     ./images/stripes.png   --output    ~/.gazebo/models/striped_cylinder
```

### Blender Path Configuration

If `blender` is not on your `$PATH`, either:

```bash
./main.py --blender ~/blender-4.2.1-linux-x64/blender   --image ... --output ...
```

or add to your shell:

```bash
export BLENDER_PATH=~/blender-4.2.1-linux-x64/blender
```

---

## Configuration for New Primitives

1. **Add a wrapper** in `primitives/<shape>.py` subclassing `PrimitiveWrapper`.  
2. **Register** it in `primitives/__init__.py`.  
3. **(Optional)** Add a `configs/<shape>.yaml` with your SDF template.  
4. **Run** with `--primitive <shape>`.

_No changes to the core scripts needed._

---

## Contributing

1. Fork the repository.  
2. Create a feature branch (`git checkout -b feature/myshape`).  
3. Add your primitive wrapper and config.  
4. Submit a pull request.

Please follow existing code style and update tests if any.

---

## License

This project is licensed under the **MIT License** – see the [LICENSE](LICENSE) file for details.



