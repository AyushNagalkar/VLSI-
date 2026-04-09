# QUICK START GUIDE 🚀

## Get Started in 3 Minutes!

### Step 1: Install Dependencies (1 minute)

```bash
cd ai_placement_system
pip install -r requirements.txt

# Install DGL (choose one based on your hardware)
# For CPU only:
pip install dgl -f https://data.dgl.ai/wheels/repo.html

# For NVIDIA GPU with CUDA 11.8:
pip install dgl -f https://data.dgl.ai/wheels/cu118/repo.html
```

### Step 2: Run Demo (2 minutes)

```bash
python main.py --mode demo
```

This will:
✓ Load CircuitNet data  
✓ Train for 100 episodes (~2 minutes)  
✓ Generate placement visualization  
✓ Export DEF file for Cadence Innovus  

### Step 3: Check Results

Look in the `placement_results/` folder:

1. **placement_design0.png** - Visualization of macro placement
2. **macro_placement_design0.def** - DEF file for Cadence Innovus
3. **macro_placement_design0.json** - JSON format placement data
4. **training_curves.png** - Training progress

---

## What You'll See

### Console Output:
```
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║          AI-POWERED MACRO PLACEMENT SYSTEM                        ║
║                                                                   ║
║     🤖 GNN + Reinforcement Learning for Chip Design               ║
║     📊 Trained on CircuitNet Dataset                              ║
║     🎯 Optimized for Cadence Innovus Integration                  ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝

🔧 Initializing CircuitNet Data Loader...
  Loading design: RISCY-a-1-c20
    ✓ RISCY-a-1-c20: 15 macros
    
  Building GNN model...
    Input dimension: 42
    Hidden dimension: 256
    Number of layers: 4
    
  Building RL Agent (PPO)...

✅ System initialized successfully!
  Total parameters: 2,145,678

🎯 STARTING TRAINING
Training: 100%|████████████| 100/100 [02:15<00:00,  1.35s/it]

📊 Episode 50/100
  Avg Reward (last 50): 245.67
  Avg Overlaps: 1.2
  Avg Utilization: 0.7234
  Best Reward: 389.45

✅ Training completed!
💾 Model saved to trained_models/best_model.pt
📊 Visualization saved to placement_results/placement_design0.png
💾 Innovus DEF exported to placement_results/macro_placement_design0.def
```

### Visualization:
You'll see a plot showing:
- Chip boundary (black rectangle)
- Placed macros (colored rectangles)
- Labels for each macro
- Coordinates in microns

---

## Next Steps

### 1. Full Training (Better Results)

```bash
python main.py --mode train --episodes 1000
```

This takes ~20 minutes but produces better placements.

### 2. Evaluate on Different Design

```bash
python main.py --mode eval --design 0
```

Try different design indices (0-9).

### 3. Use in Cadence Innovus

```tcl
# In Innovus Tcl console:
read_def placement_results/macro_placement_design0.def

# Continue with standard placement and routing:
place_opt_design
route_design
```

---

## Understanding the Output

### Training Curves (training_curves.png)

**Top Left - Training Reward:**
- Should increase over time
- Occasional dips are normal (exploration)
- Convergence around episode 500-800

**Top Right - Overlap Count:**
- Should decrease toward zero
- Overlaps = bad placement
- < 1 overlap = excellent

**Bottom Left - Utilization:**
- Fraction of chip area used
- 60-80% is typical
- Higher = denser (but may hurt timing)

**Bottom Right - Loss:**
- Actor and critic training losses
- Should stabilize after ~200 episodes

### Placement Visualization (placement_design0.png)

- Each colored rectangle = one macro
- Macros should NOT overlap
- Central placement often better (shorter wires)
- Grid lines show coordinate system

### DEF File Format

Standard format for Cadence Innovus:
```def
COMPONENTS 15 ;
  - MACRO_0 MACRO_TYPE
    + PLACED ( 125400 98600 ) N ;
```

Each line = one macro with (x, y) coordinates in DEF units (1 unit = 0.0005 microns).

---

## Troubleshooting

### "CUDA out of memory"
**Solution:** Edit `module1_data_env.py`, change:
```python
BATCH_SIZE = 16  # or 8
```

### "No module named 'dgl'"
**Solution:** Install DGL:
```bash
pip install dgl -f https://data.dgl.ai/wheels/repo.html
```

### "No valid designs loaded"
**Solution:** Make sure you're running from the CircuitNet folder:
```bash
cd h:/Labs/Generative\ Ai/Ayush1/Ayush/CircuitNet
python ai_placement_system/main.py --mode demo
```

### Training is very slow
**Solutions:**
1. Use GPU if available
2. Reduce number of designs loaded (edit config)
3. Use smaller grid (e.g., 128x128)

---

## Performance Tips

### For Faster Training:
```python
# In module1_data_env.py Config class:
GRID_SIZE = 128           # Smaller grid (default: 256)
BATCH_SIZE = 16           # Smaller batches
GNN_NUM_LAYERS = 3        # Fewer layers (default: 4)
```

### For Better Quality:
```python
GRID_SIZE = 512           # Larger grid for precision
NUM_EPOCHS = 200          # More training
RL_LEARNING_RATE = 1e-4   # Slower learning
```

### For GPU Training:
```python
# Automatically uses GPU if available
# To force CPU:
DEVICE = torch.device('cpu')
```

---

## Example Python Script

```python
# custom_training.py
from ai_placement_system import Config, MacroPlacementTrainer

# Create config
config = Config()
config.NUM_EPOCHS = 500
config.BATCH_SIZE = 32

# Create trainer
trainer = MacroPlacementTrainer(config)

# Initialize
trainer.initialize()

# Train
trainer.train(num_episodes=500)

# Evaluate
for design_idx in range(3):
    print(f"\nEvaluating design {design_idx}...")
    trainer.evaluate(design_idx, visualize=True)
```

Run with:
```bash
python custom_training.py
```

---

## System Requirements

**Minimum:**
- CPU: 4 cores
- RAM: 8 GB
- Disk: 5 GB
- Python: 3.8+

**Recommended:**
- CPU: 8+ cores
- RAM: 16 GB
- GPU: NVIDIA with 6GB+ VRAM (GTX 1060 or better)
- Disk: 10 GB SSD
- Python: 3.10+

**Training Time:**
- CPU only: ~5 minutes for 100 episodes
- GPU (GTX 1080): ~2 minutes for 100 episodes
- GPU (RTX 3090): ~1 minute for 100 episodes

---

## FAQ

**Q: What's a macro?**  
A: Large blocks like RAM, ROM, PLLs. Typically > 1000 μm².

**Q: Why only macros?**  
A: Macros are placed first. Standard cells are handled by Innovus.

**Q: Can I use this for real chips?**  
A: Yes! The DEF output works with Cadence tools. However, you should validate timing/power.

**Q: How does it compare to manual placement?**  
A: After training, it's much faster (seconds vs days) with comparable quality.

**Q: Can I customize the reward function?**  
A: Yes! Edit `_calculate_reward()` in `module1_data_env.py`.

**Q: Does it handle standard cells?**  
A: No, use Cadence Innovus for standard cell placement.

---

## Getting Help

1. **Check README.md** - Comprehensive documentation
2. **Run info mode** - `python main.py --mode info`
3. **Check code comments** - Each module has detailed docstrings
4. **GitHub Issues** - Report bugs or ask questions

---

**Happy Placing! 🎉**
