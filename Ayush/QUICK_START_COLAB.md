# 🚀 Quick Start Guide: Running Your Notebook on Google Colab

## ✅ Files Created for You

1. **`VLSI_Design_Complete_Pipeline_COLAB.ipynb`** - Your Colab-ready notebook
2. **`COLAB_SETUP_GUIDE.md`** - Complete setup instructions
3. **`convert_to_colab.py`** - Converter script (for future use)

---

## 📝 Quick 5-Step Setup Process

### Step 1: Upload Notebook to Colab
1. Go to https://colab.research.google.com
2. Click **File** → **Upload notebook**
3. Select `VLSI_Design_Complete_Pipeline_COLAB.ipynb`

### Step 2: Enable GPU
1. In Colab: **Runtime** → **Change runtime type**
2. Select **Hardware accelerator**: **GPU**
3. Click **Save**

### Step 3: Upload Dataset to Google Drive
1. Go to https://drive.google.com
2. Create a folder named `CircuitNet` in "My Drive"
3. Upload your CircuitNet dataset to this folder

**Expected structure in Google Drive:**
```
MyDrive/
└── CircuitNet/
    ├── instance_placement_micron-002/
    │   └── instance_placement_micron/
    │       └── *.npy files
    └── graph_features/
        └── graph_information/
            ├── node_attr/
            └── net_attr/
```

### Step 4: Run the Setup Cells
1. Run the **first code cell** (Google Drive mount)
   - Click "Connect to Google Drive" when prompted
   - Allow access
2. Verify you see "✅ GOOGLE DRIVE MOUNTED SUCCESSFULLY"
3. Verify GPU is detected

### Step 5: Update Path (if needed)
If you uploaded CircuitNet to a different location:
- Find the cell with `CIRCUITNET_BASE = "/content/drive/MyDrive/CircuitNet"`
- Update the path to match your location
- Example: `CIRCUITNET_BASE = "/content/drive/MyDrive/MyFolder/CircuitNet"`

---

## 🔑 Key Path Changes Made

All Windows paths have been automatically converted:

| Original (Local)                          | New (Colab)                                    |
|-------------------------------------------|------------------------------------------------|
| `H:\Labs\Generative Ai\CircuitNet`       | `/content/drive/MyDrive/CircuitNet`            |
| `H:\Labs\Generative Ai\vlsi_*.pth`       | `/content/drive/MyDrive/vlsi_*.pth`            |
| `H:\Labs\Generative Ai\vlsi_results`     | `/content/drive/MyDrive/vlsi_results`          |

---

## 💡 Important Colab Features

### ✅ Resume Training Feature
Your notebook now includes **automatic training resume**:
- Model saves to Google Drive every epoch
- If Colab disconnects, just re-run the training cell
- It automatically loads the last checkpoint and continues training

### ✅ Results Saved to Drive
All outputs are saved to Google Drive:
- Model checkpoints: `/content/drive/MyDrive/vlsi_placement_model.pth`
- Results: `/content/drive/MyDrive/vlsi_results/`
- Plots and visualizations

### ⚡ GPU Monitoring
Monitor your GPU usage in Colab:
```python
# View GPU memory
!nvidia-smi
```

---

## 📊 Performance Expectations

| Resource      | Free Colab | Colab Pro  |
|---------------|------------|------------|
| GPU           | T4 (16GB)  | A100 (40GB)|
| RAM           | ~12GB      | ~32GB      |
| Session Time  | 12 hours   | 24 hours   |
| Max Samples   | ~200-300   | ~500-1000  |

---

## 🐛 Troubleshooting Quick Fixes

### "No module named torch_geometric"
```python
!pip install torch-geometric -q
!pip install pyg_lib torch_scatter torch_sparse -f https://data.pyg.org/whl/torch-2.7.0+cu118.html -q
```

### "Path not found"
- Verify Drive is mounted: `!ls /content/drive/MyDrive`
- Check CircuitNet folder exists: `!ls /content/drive/MyDrive/CircuitNet`
- Update `CIRCUITNET_BASE` path in configuration cell

### "CUDA out of memory"
- Reduce `MAX_SAMPLES = 100` (or lower)
- Restart runtime: **Runtime** → **Restart runtime**

### "Disconnected"
- Just re-run training cell - it will auto-resume from last checkpoint!

---

## 📥 How to Download Results

### Option 1: Already in Google Drive!
Results are automatically saved to your Drive at:
- `MyDrive/vlsi_results/`

### Option 2: Download from Colab
```python
from google.colab import files

# Download model
files.download('/content/drive/MyDrive/vlsi_placement_model.pth')

# Download results as ZIP
!zip -r /content/results.zip /content/drive/MyDrive/vlsi_results
files.download('/content/results.zip')
```

---

## ✨ Additional Features Added

The Colab version includes:

1. ✅ **Google Drive auto-mount** - First cell mounts your drive
2. ✅ **GPU verification** - Checks if GPU is enabled
3. ✅ **Path auto-configuration** - All paths updated for Colab
4. ✅ **Resume training** - Continue from last checkpoint
5. ✅ **Persistent storage** - Results saved to Drive

---

## 📚 Documentation Files

- **`COLAB_SETUP_GUIDE.md`** - Detailed setup instructions
- **`QUICK_START_COLAB.md`** - This quick reference (you are here!)

---

## 🎯 Ready to Start!

Your notebook is ready to run on Google Colab. Just:

1. ✅ Upload notebook to Colab
2. ✅ Enable GPU
3. ✅ Upload data to Drive
4. ✅ Run cells in order

**That's it! Happy training! 🚀**

---

## 📧 Need More Help?

Refer to the detailed guide: `COLAB_SETUP_GUIDE.md`

Common commands:
- Mount Drive: Already included in first cell
- Check GPU: `!nvidia-smi`
- View Drive contents: `!ls /content/drive/MyDrive`
- Install packages: Already included in setup cell
