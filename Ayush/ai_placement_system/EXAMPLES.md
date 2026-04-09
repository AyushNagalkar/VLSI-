# Usage Examples & Configuration

## Basic Usage

### 1. Quick Demo
```bash
# Run 100 episode demo
python main.py --mode demo

# Outputs:
# - placement_results/placement_design0.png
# - placement_results/macro_placement_design0.def
# - placement_results/training_curves.png
```

### 2. Full Training
```bash
# Train for 1000 episodes
python main.py --mode train --episodes 1000

# With custom episodes
python main.py --mode train --episodes 2000
```

### 3. Evaluation
```bash
# Evaluate on design 0
python main.py --mode eval --design 0

# Evaluate on different designs
python main.py --mode eval --design 1
python main.py --mode eval --design 2
```

### 4. System Info
```bash
# Show configuration and system details
python main.py --mode info
```

---

## Advanced Python Usage

### Example 1: Custom Training Loop

```python
# custom_train.py
from module1_data_env import Config
from module3_training import MacroPlacementTrainer

# Create custom config
config = Config()
config.NUM_EPOCHS = 500
config.BATCH_SIZE = 32
config.GRID_SIZE = 512  # Higher resolution

# Initialize trainer
trainer = MacroPlacementTrainer(config)
trainer.initialize()

# Train
trainer.train(num_episodes=1000)

# Evaluate multiple designs
for i in range(5):
    metrics = trainer.evaluate(design_idx=i, visualize=True)
    print(f"Design {i}: Reward={metrics['total_reward']:.2f}")
```

### Example 2: Custom Reward Function

```python
# In module1_data_env.py, modify MacroPlacementEnv._calculate_reward()

def _calculate_reward(self, coords: List[float], macro: Dict) -> float:
    """Custom reward with wirelength proxy"""
    reward = 0.0
    
    x1, y1, x2, y2 = coords
    
    # 1. Overlap penalty (existing)
    for other_name, other_coords in self.placed_macros.items():
        # ... overlap calculation ...
        reward -= overlap_area * 0.01
    
    # 2. Out of bounds (existing)
    if x1 < 0 or y1 < 0 or x2 > self.chip_width or y2 > self.chip_height:
        reward -= 1000.0
    
    # 3. NEW: Wirelength proxy
    # Encourage macros to be placed near chip center
    center_x = self.chip_width / 2
    center_y = self.chip_height / 2
    macro_center_x = (x1 + x2) / 2
    macro_center_y = (y1 + y2) / 2
    
    distance = np.sqrt((macro_center_x - center_x)**2 + 
                      (macro_center_y - center_y)**2)
    max_distance = np.sqrt((self.chip_width/2)**2 + (self.chip_height/2)**2)
    normalized_distance = distance / max_distance
    
    # Bonus for being near center (reduces average wirelength)
    reward += (1.0 - normalized_distance) * 20.0
    
    # 4. NEW: Aspect ratio consideration
    # Penalize very elongated placements
    width = x2 - x1
    height = y2 - y1
    aspect_ratio = max(width, height) / min(width, height)
    if aspect_ratio > 3.0:
        reward -= (aspect_ratio - 3.0) * 5.0
    
    # 5. NEW: Boundary preference
    # Slight bonus for edge placement (reduces routing congestion)
    margin = 50.0  # microns
    is_near_edge = (x1 < margin or y1 < margin or 
                    x2 > self.chip_width - margin or 
                    y2 > self.chip_height - margin)
    if is_near_edge:
        reward += 5.0
    
    return reward
```

### Example 3: Custom GNN Architecture

```python
# In module1_data_env.py, modify CircuitGNN to use GraphSAGE

import dgl.nn as dglnn

class CircuitGNNSAGE(nn.Module):
    """Circuit GNN using GraphSAGE instead of GAT"""
    
    def __init__(self, input_dim: int, hidden_dim: int, num_layers: int):
        super().__init__()
        
        self.input_proj = nn.Linear(input_dim, hidden_dim)
        
        # Use GraphSAGE instead of GAT
        self.conv_layers = nn.ModuleList()
        for _ in range(num_layers):
            self.conv_layers.append(
                dglnn.SAGEConv(hidden_dim, hidden_dim, 'mean')
            )
        
        self.layer_norms = nn.ModuleList([
            nn.LayerNorm(hidden_dim) for _ in range(num_layers)
        ])
        
        self.output_proj = nn.Linear(hidden_dim, hidden_dim)
    
    def forward(self, g, node_features):
        h = self.input_proj(node_features)
        
        for conv, norm in zip(self.conv_layers, self.layer_norms):
            h_new = conv(g, h)
            h = norm(h + h_new)
            h = F.relu(h)
        
        return self.output_proj(h)

# Then use it in training:
trainer.gnn_model = CircuitGNNSAGE(input_dim, hidden_dim, num_layers)
```

### Example 4: Multi-Design Batch Training

```python
# batch_train.py
from module3_training import MacroPlacementTrainer
from module1_data_env import Config
import numpy as np

config = Config()
trainer = MacroPlacementTrainer(config)
trainer.initialize()

# Train on multiple designs in rotation
for epoch in range(100):
    for design_idx in range(len(trainer.dataset)):
        design = trainer.dataset[design_idx]
        
        # Train one episode
        metrics = trainer.train_episode(design)
        
        # Update agent
        if len(trainer.agent.buffer) >= config.BATCH_SIZE:
            trainer.agent.update()
        
        if epoch % 10 == 0 and design_idx == 0:
            print(f"Epoch {epoch}, Design {design_idx}: "
                  f"Reward={metrics['total_reward']:.2f}")
    
    # Save checkpoint
    if epoch % 20 == 0:
        trainer.agent.save(f"checkpoint_epoch{epoch}.pt")
```

### Example 5: Transfer Learning

```python
# transfer_learn.py
from module3_training import MacroPlacementTrainer
from module1_data_env import Config

# Load pre-trained model
config = Config()
trainer = MacroPlacementTrainer(config)
trainer.initialize()

# Load checkpoint
trainer.agent.load("trained_models/best_model.pt")
print("Loaded pre-trained model")

# Fine-tune on specific design type
# (e.g., only RISCY designs)
filtered_dataset = [d for d in trainer.dataset 
                   if 'RISCY' in d['nodes'][0][0]]

for episode in range(200):
    design = np.random.choice(filtered_dataset)
    metrics = trainer.train_episode(design)
    
    if len(trainer.agent.buffer) >= config.BATCH_SIZE:
        trainer.agent.update()
    
    if episode % 50 == 0:
        print(f"Episode {episode}: Reward={metrics['total_reward']:.2f}")

trainer.agent.save("finetuned_riscy.pt")
```

---

## Configuration Options

### In module1_data_env.py - Config class:

```python
class Config:
    # === DATA PATHS ===
    DATA_PATH = Path(".")
    GRAPH_FEATURES_PATH = DATA_PATH / "graph_features/graph_information"
    
    # === GNN PARAMETERS ===
    GNN_HIDDEN_DIM = 256        # Embedding dimension (128, 256, 512)
    GNN_NUM_LAYERS = 4          # Number of layers (2, 3, 4, 5)
    GNN_HEADS = 4               # Attention heads for GAT (2, 4, 8)
    
    # === RL PARAMETERS ===
    RL_LEARNING_RATE = 3e-4     # Learning rate (1e-4, 3e-4, 1e-3)
    RL_GAMMA = 0.99             # Discount factor (0.95, 0.99, 0.995)
    RL_GAE_LAMBDA = 0.95        # GAE lambda (0.9, 0.95, 0.99)
    RL_CLIP_EPSILON = 0.2       # PPO clipping (0.1, 0.2, 0.3)
    RL_ENTROPY_COEFF = 0.01     # Exploration bonus (0.001, 0.01, 0.1)
    
    # === TRAINING ===
    BATCH_SIZE = 32             # Batch size (16, 32, 64)
    NUM_EPOCHS = 100            # Training epochs (50, 100, 200)
    VALIDATION_SPLIT = 0.1      # Validation split (0.1, 0.2)
    
    # === PLACEMENT ===
    MACRO_SIZE_THRESHOLD = 1000 # Macro threshold in μm² (500, 1000, 2000)
    GRID_SIZE = 256             # Grid resolution (64, 128, 256, 512)
    
    # === HARDWARE ===
    DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
```

### Recommended Configurations:

**Fast Training (CPU):**
```python
GNN_HIDDEN_DIM = 128
GNN_NUM_LAYERS = 3
BATCH_SIZE = 16
GRID_SIZE = 128
```

**Balanced (GPU):**
```python
GNN_HIDDEN_DIM = 256
GNN_NUM_LAYERS = 4
BATCH_SIZE = 32
GRID_SIZE = 256
```

**High Quality (Powerful GPU):**
```python
GNN_HIDDEN_DIM = 512
GNN_NUM_LAYERS = 5
BATCH_SIZE = 64
GRID_SIZE = 512
```

---

## Innovus Integration

### 1. Export from our system:
```bash
python main.py --mode eval --design 0
# Generates: placement_results/macro_placement_design0.def
```

### 2. Import to Cadence Innovus:
```tcl
# In Innovus Tcl console:

# Read LEF (technology files)
read_lef /path/to/technology.lef
read_lef /path/to/macro_library.lef

# Read netlist
read_verilog design.v

# Read our macro placement
read_def placement_results/macro_placement_design0.def

# Floorplan
floorplan -site core -r 1.0 0.7 10 10 10 10

# Place standard cells
place_opt_design

# Route
route_design

# Timing analysis
report_timing

# Export final GDS
write_gds final_design.gds
```

### 3. Verify placement:
```tcl
# Check macro placement
report_placement -macros

# Visualize
gui_show

# Check DRC
verify_drc
```

---

## Performance Tuning

### Improve Training Speed:

1. **Use GPU:**
   ```python
   # Automatically uses GPU if available
   # Check: python -c "import torch; print(torch.cuda.is_available())"
   ```

2. **Reduce model size:**
   ```python
   GNN_HIDDEN_DIM = 128  # Default: 256
   GNN_NUM_LAYERS = 3    # Default: 4
   ```

3. **Smaller grid:**
   ```python
   GRID_SIZE = 128  # Default: 256
   ```

4. **Larger batch:**
   ```python
   BATCH_SIZE = 64  # Default: 32 (requires more RAM)
   ```

### Improve Placement Quality:

1. **More training:**
   ```bash
   python main.py --mode train --episodes 2000
   ```

2. **Larger grid:**
   ```python
   GRID_SIZE = 512  # Higher precision
   ```

3. **Tune rewards:**
   - Increase overlap penalty
   - Add timing-aware components
   - Use actual wirelength calculation

4. **Better GNN:**
   ```python
   GNN_HIDDEN_DIM = 512
   GNN_NUM_LAYERS = 5
   ```

### Reduce Memory Usage:

1. **Smaller batch:**
   ```python
   BATCH_SIZE = 16  # or 8
   ```

2. **Load fewer designs:**
   ```python
   # In load_all_designs()
   for design_name in designs[:5]:  # Load only 5 designs
   ```

3. **Use CPU:**
   ```python
   DEVICE = torch.device('cpu')
   ```

---

## Troubleshooting Common Issues

### Issue: "CUDA out of memory"
**Solutions:**
- Reduce BATCH_SIZE to 16 or 8
- Reduce GNN_HIDDEN_DIM to 128
- Use CPU mode
- Close other GPU applications

### Issue: "No valid designs loaded"
**Solutions:**
- Check data paths in Config
- Ensure .npy files exist
- Run from correct directory

### Issue: "DGL import error"
**Solutions:**
- Reinstall: `pip install dgl -f https://data.dgl.ai/wheels/repo.html`
- Check CUDA compatibility
- Try CPU version first

### Issue: "Training diverges (NaN loss)"
**Solutions:**
- Reduce learning rate: `RL_LEARNING_RATE = 1e-4`
- Add gradient clipping (already included)
- Check reward function for infinity values
- Increase batch size

### Issue: "Too many overlaps"
**Solutions:**
- Increase overlap penalty in reward function
- Train longer
- Use larger grid for precision
- Add hard overlap constraints

---

## Tips & Best Practices

1. **Start Small**: Begin with demo mode, then scale up
2. **Monitor Training**: Watch training curves for convergence
3. **Save Checkpoints**: Training randomly fails sometimes
4. **Validate Often**: Evaluate on validation set regularly
5. **Tune Gradually**: Change one parameter at a time
6. **Use Version Control**: Git track your modifications
7. **Document Changes**: Note what worked and what didn't
8. **Compare Baselines**: Keep reference results
9. **Visualize Everything**: Plots help debug issues
10. **Test on Real Designs**: Validate with actual chip flows

---

## Next Steps

After mastering basic usage:

1. **Add Timing Constraints**: Integrate STA (Static Timing Analysis)
2. **Congestion-Aware**: Predict routing congestion
3. **Power Optimization**: Add power-aware placement
4. **Hierarchical Placement**: Handle very large designs
5. **Multi-Objective**: Optimize multiple metrics simultaneously
6. **Standard Cell Integration**: Joint macro + standard cell placement
7. **Routing-Aware**: Predict routability
8. **Foundation Models**: Pre-train on large corpus

---

**Happy Experimenting! 🚀**
