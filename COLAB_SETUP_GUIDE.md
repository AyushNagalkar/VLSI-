# Google Colab Setup Guide for VLSI Design Pipeline

## 📋 Quick Start Checklist

- [ ] Enable GPU runtime in Colab
- [ ] Upload CircuitNet dataset to Google Drive
- [ ] Mount Google Drive in Colab
- [ ] Update file paths in the notebook
- [ ] Run the notebook cells

---

## 🚀 Step-by-Step Setup Instructions

### 1. Enable GPU in Google Colab

1. Open your notebook in Google Colab
2. Click **Runtime** → **Change runtime type**
3. Under **Hardware accelerator**, select **GPU** (T4 or A100)
4. Click **Save**

### 2. Upload CircuitNet Dataset to Google Drive

#### Option A: Upload via Google Drive Website (Recommended for large datasets)

1. Go to https://drive.google.com
2. Create a new folder called `CircuitNet` (or any name you prefer)
3. Upload your CircuitNet dataset folder structure:
   ```
   MyDrive/
   └── CircuitNet/
       ├── instance_placement_micron-002/
       │   └── instance_placement_micron/
       │       ├── 1-RISCY-a-1-c2-u0.7-m1-p1-f0.npy
       │       ├── 10-RISCY-a-1-c2-u0.7-m2-p2-f0.npy
       │       └── ... (more .npy files)
       └── graph_features/
           └── graph_information/
               ├── node_attr/
               │   ├── zero-riscy-a-1-c20_node_attr.npy
               │   └── ... (more files)
               ├── net_attr/
               └── pin_attr/
   ```

4. Wait for upload to complete (this may take a while for large datasets!)

#### Option B: Upload ZIP and Extract in Colab

If you have the dataset as a ZIP file:

```python
# Upload ZIP file
from google.colab import files
uploaded = files.upload()  # Select your CircuitNet.zip

# Extract
!unzip -q CircuitNet.zip -d /content/drive/MyDrive/
print("✅ Data extracted to Google Drive")
```

#### Option C: Download Directly from URL (If available)

```python
# Download and extract
!wget -O /content/circuitnet.zip "YOUR_DATASET_URL"
!unzip -q /content/circuitnet.zip -d /content/drive/MyDrive/
```

### 3. Key Path Changes for Colab

Replace these paths in the original notebook:

| Original (Local Windows)                         | Colab (Google Drive)                                  |
|--------------------------------------------------|-------------------------------------------------------|
| `H:\Labs\Generative Ai\CircuitNet`              | `/content/drive/MyDrive/CircuitNet`                   |
| `H:\Labs\Generative Ai\vlsi_placement_model.pth`| `/content/drive/MyDrive/vlsi_placement_model.pth`     |
| `H:\Labs\Generative Ai\vlsi_results`            | `/content/drive/MyDrive/vlsi_results`                 |

### 4. Add Google Drive Mount Cell at the Beginning

Add this as the **FIRST CODE CELL** in your notebook:

```python
# Mount Google Drive
from google.colab import drive
drive.mount('/content/drive')

print("\n" + "="*80)
print("GOOGLE DRIVE MOUNTED SUCCESSFULLY")
print("="*80)

# Verify GPU
import torch
if torch.cuda.is_available():
    print(f"\n✅ GPU Available: {torch.cuda.get_device_name(0)}")
    print(f"   GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
else:
    print("\n⚠️  WARNING: No GPU detected!")
    print("   Go to: Runtime → Change runtime type → GPU")
```

### 5. Update Path Configuration Cell

Change the path configuration cell to:

```python
# ============================================
# CONFIGURE YOUR CIRCUITNET PATHS HERE
# ============================================

# UPDATE THIS PATH to match your Google Drive location!
CIRCUITNET_BASE = "/content/drive/MyDrive/CircuitNet"

# Data paths
PLACEMENT_PATH = os.path.join(CIRCUITNET_BASE, "instance_placement_micron-002", "instance_placement_micron")
NODE_ATTR_PATH = os.path.join(CIRCUITNET_BASE, "graph_features", "graph_information", "node_attr")
NET_ATTR_PATH = os.path.join(CIRCUITNET_BASE, "graph_features", "graph_information", "net_attr")
CONGESTION_PATH = os.path.join(CIRCUITNET_BASE, "congestion")

# Model save path (also on Google Drive to persist across sessions)
MODEL_SAVE_PATH = "/content/drive/MyDrive/vlsi_placement_model.pth"
OUTPUT_DIR = "/content/drive/MyDrive/vlsi_results"

# Verify paths exist
print("Verifying dataset paths...\n")

paths_to_check = {
    "Base Directory": CIRCUITNET_BASE,
    "Placement Data": PLACEMENT_PATH,
    "Node Attributes": NODE_ATTR_PATH,
    "Net Attributes": NET_ATTR_PATH,
}

all_exist = True
for name, path in paths_to_check.items():
    exists = os.path.exists(path)
    status = "✅ [OK]" if exists else "❌ [MISSING]"
    print(f"{status} {name}")
    if not exists:
        all_exist = False

if all_exist:
    print("\n✅ All paths verified! Ready to load data.")
else:
    print("\n❌ Some paths missing. Check your Google Drive upload.")
```

### 6. Update Model Save Path in Training Cell

Find the line:
```python
model_save_path = r"H:\Labs\Generative Ai\vlsi_placement_model.pth"
```

Replace with:
```python
model_save_path = "/content/drive/MyDrive/vlsi_placement_model.pth"
```

### 7. Update Results Export Path

Find the line:
```python
output_dir = r"H:\Labs\Generative Ai\vlsi_results"
```

Replace with:
```python
output_dir = "/content/drive/MyDrive/vlsi_results"
```

---

## 🔧 Complete Path Replacement Script

Run this cell after mounting Google Drive to automatically fix all paths:

```python
# Define path mappings
OLD_BASE = r"H:\Labs\Generative Ai"
NEW_BASE = "/content/drive/MyDrive"

# This will be used for MODEL_SAVE_PATH and OUTPUT_DIR variables
# Just manually update CIRCUITNET_BASE in your path configuration cell
print("Path Configuration:")
print(f"   Old base: {OLD_BASE}")
print(f"   New base: {NEW_BASE}")
print(f"\nUpdate these paths in your notebook:")
print(f"   CIRCUITNET_BASE = '{NEW_BASE}/CircuitNet'")
print(f"   MODEL_SAVE_PATH = '{NEW_BASE}/vlsi_placement_model.pth'")
print(f"   OUTPUT_DIR = '{NEW_BASE}/vlsi_results'")
```

---

## 📊 Expected File Structure in Google Drive

After setup, your Google Drive should look like:

```
MyDrive/
├── CircuitNet/                          # Your dataset
│   ├── instance_placement_micron-002/
│   └── graph_features/
├── vlsi_placement_model.pth             # Saved model (created after training)
├── vlsi_results/                        # Output directory (created automatically)
│   ├── model_metrics.json
│   ├── training_history.csv
│   └── ... (other outputs)
└── VLSI_Design_Complete_Pipeline_Colab.ipynb  # Your notebook
```

---

## ⚡ Performance Tips for Google Colab

### 1. Use GPU Runtime
- Always use GPU for training (Runtime → Change runtime type → GPU)
- Free tier provides T4 GPU (16GB VRAM)
- Colab Pro offers A100 GPU (40GB VRAM)

### 2. Manage Session Time
- Free Colab sessions timeout after 12 hours
- Save model checkpoints frequently to Google Drive
- Use the resume training feature to continue after disconnects

### 3. Optimize Memory Usage
```python
# Reduce batch size if out of memory
BATCH_SIZE = 1  # Already optimal for large graphs

# Reduce number of samples if RAM limited
MAX_SAMPLES = 100  # Start small, increase gradually
```

### 4. Monitor Resources
```python
# Check RAM usage
import psutil
process = psutil.Process()
memory_mb = process.memory_info().rss / 1024 / 1024
print(f"RAM Usage: {memory_mb:.2f} MB")

# Check GPU memory
if torch.cuda.is_available():
    print(f"GPU Memory: {torch.cuda.memory_allocated()/1e9:.2f} GB")
```

---

## 🐛 Common Issues and Solutions

### Issue 1: "No module named 'torch_geometric'"

**Solution:** Reinstall PyTorch Geometric

```python
!pip uninstall torch-geometric -y
!pip install torch-geometric -q
!pip install pyg_lib torch_scatter torch_sparse torch_cluster torch_spline_conv -f https://data.pyg.org/whl/torch-2.7.0+cu118.html -q
```

### Issue 2: "Path not found" errors

**Solution:** 
1. Verify Google Drive is mounted: `!ls /content/drive/MyDrive`
2. Check if CircuitNet folder exists in Drive
3. Update `CIRCUITNET_BASE` path in the configuration cell

### Issue 3: "CUDA out of memory"

**Solution:**
- Reduce `MAX_SAMPLES` to load fewer circuits
- Restart runtime to clear GPU memory
- Upgrade to Colab Pro for more VRAM

### Issue 4: Session timeout during training

**Solution:**
- Model auto-saves to Google Drive every epoch
- Re-run the training cell - it will automatically resume from last checkpoint
- Keep browser tab active to prevent disconnection

### Issue 5: Slow data loading from Google Drive

**Solution:**
- First time loading is slower (Google Drive latency)
- Subsequent epochs are faster (data cached in RAM)
- Alternatively, copy data to local Colab storage:

```python
# One-time copy to local storage (faster access)
!cp -r /content/drive/MyDrive/CircuitNet /content/
CIRCUITNET_BASE = "/content/CircuitNet"  # Update path
```

⚠️ **Warning:** Local storage is cleared when runtime disconnects!

---

## 💾 Downloading Results from Colab

### Method 1: Download Individual Files
```python
from google.colab import files
files.download('/content/drive/MyDrive/vlsi_placement_model.pth')
```

### Method 2: Download as ZIP
```python
!zip -r /content/vlsi_results.zip /content/drive/MyDrive/vlsi_results
files.download('/content/vlsi_results.zip')
```

### Method 3: Keep in Google Drive
Results are already saved to Google Drive and accessible anytime!

---

## 📝 Summary Checklist

Before running the notebook:

- [ ] GPU runtime enabled
- [ ] Google Drive mounted
- [ ] CircuitNet uploaded to Drive
- [ ] All paths updated (CIRCUITNET_BASE, MODEL_SAVE_PATH, OUTPUT_DIR)
- [ ] Path verification cell shows all ✅ OK

Then proceed with:

1. ✅ Run installation cell
2. ✅ Run import libraries cell
3. ✅ Run path configuration cell (verify all paths OK)
4. ✅ Run data loading cells
5. ✅ Run model definition cell
6. ✅ Run training cell
7. ✅ Run evaluation and visualization cells

---

## 🆘 Need Help?

If you encounter issues:

1. Check the error message carefully
2. Verify all paths are correct
3. Ensure GPU is enabled
4. Restart runtime and try again
5. Check CircuitNet dataset integrity

---

**Happy Training! 🚀**
