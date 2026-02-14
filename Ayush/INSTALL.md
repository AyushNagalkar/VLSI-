# Installation Instructions for VLSI Physical Design Notebook

## Prerequisites
- Python 3.8 or higher
- 16GB+ RAM (32GB recommended)
- GPU with 8GB+ VRAM (optional but recommended for faster training)
- CUDA 11.8 (if using GPU)

## Installation Steps

### Option 1: Quick Install (CPU Only)
```bash
pip install -r requirements.txt
```

### Option 2: GPU Install (CUDA 11.8)

1. **Install PyTorch with CUDA support:**
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

2. **Install PyTorch Geometric:**
```bash
pip install torch-geometric
```

3. **Install PyTorch Geometric extensions (pre-built wheels):**
```bash
pip install pyg_lib torch_scatter torch_sparse torch_cluster torch_spline_conv -f https://data.pyg.org/whl/torch-2.0.0+cu118.html
```

4. **Install remaining dependencies:**
```bash
pip install matplotlib numpy scipy pandas psutil
```

5. **(Optional) Install Jupyter support:**
```bash
pip install jupyter ipykernel ipywidgets
```

### Option 3: For Different CUDA Versions

If you have a different CUDA version, visit:
- PyTorch: https://pytorch.org/get-started/locally/
- PyG Wheels: https://data.pyg.org/whl/

Replace `cu118` with your CUDA version (e.g., `cu117`, `cu121`)

## Verify Installation

Run this in Python to verify everything is installed correctly:

```python
import torch
import torch_geometric
print(f"PyTorch: {torch.__version__}")
print(f"PyG: {torch_geometric.__version__}")
print(f"CUDA Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
```

## Dataset Download

Download the CircuitNet dataset from:
https://drive.google.com/drive/folders/1GjW-1LBx1563bg3pHQGvhcEyK2A9sYUB

Extract it to: `H:\Labs\Generative Ai\Ayush1\Ayush\CircuitNet\`

## Troubleshooting

**Issue: CUDA out of memory**
- Reduce batch size in training
- Reduce `max_samples` when loading data
- Use CPU by setting `device = torch.device('cpu')`

**Issue: PyG installation fails**
- Try installing without the `-f` flag
- Build from source: https://github.com/pyg-team/pytorch_geometric

**Issue: Import errors**
- Make sure all dependencies are installed
- Check Python version (3.8+ required)
- Try creating a fresh virtual environment

## Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```
