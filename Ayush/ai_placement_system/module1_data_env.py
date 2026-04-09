"""
AI-Powered Macro Placement System
==================================
Using GNN + Reinforcement Learning on CircuitNet Data

Author: AI System Generator
Date: March 2026
Technology: PyTorch + DGL (Deep Graph Library)

System Overview:
- Load CircuitNet netlist and placement data
- Train GNN to encode circuit structure
- Use PPO (Proximal Policy Optimization) RL to learn placement
- Output macro coordinates for Cadence Innovus
"""

import os
os.environ['DGLBACKEND'] = 'pytorch'  # Set DGL backend before importing

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

# Try importing DGL, skip graphbolt if issues
try:
    import dgl
    import dgl.nn
except Exception as e:
    print(f"Warning: DGL import issue (will use workaround): {e}")
    import dgl
    import dgl.nn

from pathlib import Path
import json
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
import pickle

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    """System configuration"""
    
    # Paths (go up one level from ai_placement_system folder)
    DATA_PATH = Path("..").resolve()
    GRAPH_FEATURES_PATH = DATA_PATH / "graph_features/graph_information"
    GCELL_PLACEMENT_PATH = DATA_PATH / "instance_placement_gcell-001/instance_placement_gcell"
    MICRON_PLACEMENT_PATH = DATA_PATH / "instance_placement_micron-002/instance_placement_micron"
    
    # Model parameters
    GNN_HIDDEN_DIM = 256
    GNN_NUM_LAYERS = 4
    GNN_HEADS = 4  # For GAT (Graph Attention)
    
    # RL parameters
    RL_LEARNING_RATE = 3e-4
    RL_GAMMA = 0.99  # Discount factor
    RL_GAE_LAMBDA = 0.95
    RL_CLIP_EPSILON = 0.2
    RL_ENTROPY_COEFF = 0.01
    
    # Training
    BATCH_SIZE = 32
    NUM_EPOCHS = 100
    VALIDATION_SPLIT = 0.1
    
    # Placement
    MACRO_SIZE_THRESHOLD = 1000  # microns^2 - defines what's a macro
    GRID_SIZE = 256  # Placement grid resolution
    
    # Hardware
    DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    # Output
    OUTPUT_DIR = Path("./placement_results")
    MODEL_SAVE_DIR = Path("./trained_models")

# ============================================================================
# DATA LOADER
# ============================================================================

class CircuitNetDataLoader:
    """Load and process CircuitNet dataset"""
    
    def __init__(self, config: Config):
        self.config = config
        self.global_cell_types = None  # Will store all unique cell types across dataset
        self.cell_type_to_idx = None   # Mapping from cell type to index
        print("🔧 Initializing CircuitNet Data Loader...")
        
    def load_design(self, design_file: str) -> Dict:
        """Load a single design with all its data"""
        print(f"  Loading design: {design_file}")
        
        design_data = {}
        
        # Load graph features
        net_attr_path = self.config.GRAPH_FEATURES_PATH / "net_attr" / f"{design_file}_net_attr.npy"
        node_attr_path = self.config.GRAPH_FEATURES_PATH / "node_attr" / f"{design_file}_node_attr.npy"
        pin_attr_path = self.config.GRAPH_FEATURES_PATH / "pin_attr" / f"{design_file}_pin_attr.npy"
        
        if net_attr_path.exists():
            design_data['nets'] = np.load(str(net_attr_path), allow_pickle=True)
            design_data['nodes'] = np.load(str(node_attr_path), allow_pickle=True)
            design_data['pins'] = np.load(str(pin_attr_path), allow_pickle=True)
        
        # Load placement data (find matching files)
        micron_files = list(self.config.MICRON_PLACEMENT_PATH.glob(f"*{design_file}*.npy"))
        if micron_files:
            placement = np.load(str(micron_files[0]), allow_pickle=True).item()
            design_data['placement'] = placement
            design_data['placement_file'] = micron_files[0].name
        
        return design_data
    
    def extract_macros(self, placement: Dict) -> Dict:
        """Extract macro cells from placement"""
        macros = {}
        for cell_name, coords in placement.items():
            x1, y1, x2, y2 = coords
            area = (x2 - x1) * (y2 - y1)
            
            if area > self.config.MACRO_SIZE_THRESHOLD:
                macros[cell_name] = {
                    'coords': coords,
                    'area': area,
                    'width': x2 - x1,
                    'height': y2 - y1
                }
        
        return macros
    
    def build_netlist_graph(self, design_data: Dict) -> dgl.DGLGraph:
        """Convert netlist to DGL graph for GNN"""
        
        nodes = design_data['nodes']
        instance_names = nodes[0]  # Cell names
        cell_types = nodes[1]      # Cell types
        
        # Create node features
        num_nodes = len(instance_names)
        
        # Use consistent cell type encoding across all designs
        if self.cell_type_to_idx is None:
            # Fallback: create local encoding (shouldn't happen after load_all_designs)
            unique_types = sorted(set(cell_types))
            self.cell_type_to_idx = {t: i for i, t in enumerate(unique_types)}
        
        # Create one-hot encoding using global cell type vocabulary
        node_features = torch.zeros(num_nodes, len(self.cell_type_to_idx))
        for i, cell_type in enumerate(cell_types):
            if cell_type in self.cell_type_to_idx:
                node_features[i, self.cell_type_to_idx[cell_type]] = 1.0
            else:
                # Unknown cell type - use zeros (rare case)
                pass
        
        # Build edges from netlist connectivity
        # For simplicity, we'll create edges based on nets
        # (In production, you'd extract full netlist connectivity)
        edge_src = []
        edge_dst = []
        
        # Create random connectivity for demonstration
        # In real system, parse actual netlist connections
        for i in range(num_nodes):
            # Connect to a few random neighbors
            neighbors = np.random.choice(num_nodes, size=min(5, num_nodes), replace=False)
            for j in neighbors:
                if i != j:
                    edge_src.append(i)
                    edge_dst.append(j)
        
        # Create DGL graph
        g = dgl.graph((edge_src, edge_dst), num_nodes=num_nodes)
        
        # Add self-loops to handle 0-in-degree nodes
        g = dgl.add_self_loop(g)
        
        g.ndata['feat'] = node_features
        
        return g
    
    def load_all_designs(self) -> List[Dict]:
        """Load all available designs"""
        print("\n📚 Loading CircuitNet Dataset...")
        
        # Find all unique designs
        net_files = list(self.config.GRAPH_FEATURES_PATH.glob("net_attr/*.npy"))
        designs = [f.stem.replace('_net_attr', '') for f in net_files]
        
        print(f"  Found {len(designs)} designs")
        
        # First pass: collect all unique cell types across all designs
        print("  Pass 1: Collecting global cell type vocabulary...")
        all_cell_types = set()
        valid_design_names = []
        
        for design_name in designs[:10]:  # Load first 10 for faster training
            try:
                node_attr_path = self.config.GRAPH_FEATURES_PATH / "node_attr" / f"{design_name}_node_attr.npy"
                if node_attr_path.exists():
                    nodes = np.load(str(node_attr_path), allow_pickle=True)
                    cell_types = nodes[1]  # Cell types
                    all_cell_types.update(cell_types)
                    valid_design_names.append(design_name)
            except Exception as e:
                pass
        
        # Create global cell type mapping (sorted for consistency)
        self.global_cell_types = sorted(all_cell_types)
        self.cell_type_to_idx = {t: i for i, t in enumerate(self.global_cell_types)}
        print(f"  Global vocabulary: {len(self.global_cell_types)} unique cell types")
        
        # Second pass: load designs with consistent encoding
        print("  Pass 2: Loading designs with consistent encoding...")
        dataset = []
        for design_name in valid_design_names:
            try:
                design_data = self.load_design(design_name)
                if 'placement' in design_data:
                    macros = self.extract_macros(design_data['placement'])
                    if len(macros) > 0:
                        design_data['macros'] = macros
                        design_data['graph'] = self.build_netlist_graph(design_data)
                        dataset.append(design_data)
                        print(f"    ✓ {design_name}: {len(macros)} macros")
            except Exception as e:
                print(f"    ✗ {design_name}: {e}")
        
        print(f"\n  Successfully loaded {len(dataset)} designs with macros")
        print(f"  Feature dimension: {len(self.global_cell_types)}")
        return dataset

# ============================================================================
# GNN MODEL
# ============================================================================

class CircuitGNN(nn.Module):
    """Graph Neural Network for circuit netlist encoding"""
    
    def __init__(self, input_dim: int, hidden_dim: int, num_layers: int):
        super().__init__()
        
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        
        # Input projection
        self.input_proj = nn.Linear(input_dim, hidden_dim)
        
        # Graph convolution layers (using GAT - Graph Attention)
        self.conv_layers = nn.ModuleList()
        for _ in range(num_layers):
            self.conv_layers.append(
                dgl.nn.GATConv(hidden_dim, hidden_dim // 4, num_heads=4, allow_zero_in_degree=True)
            )
        
        # Output projection
        self.output_proj = nn.Linear(hidden_dim, hidden_dim)
        
        # Layer normalization
        self.layer_norms = nn.ModuleList([
            nn.LayerNorm(hidden_dim) for _ in range(num_layers)
        ])
        
    def forward(self, g: dgl.DGLGraph, node_features: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through GNN
        
        Args:
            g: DGL graph
            node_features: Node feature tensor [num_nodes, input_dim]
        
        Returns:
            Node embeddings [num_nodes, hidden_dim]
        """
        h = self.input_proj(node_features)
        
        for i, conv in enumerate(self.conv_layers):
            # Graph attention convolution
            h_new = conv(g, h)
            
            # Reshape from [num_nodes, num_heads, hidden_dim//num_heads]
            h_new = h_new.flatten(1)
            
            # Residual connection + layer norm
            h = self.layer_norms[i](h + h_new)
            h = F.relu(h)
        
        # Output projection
        h = self.output_proj(h)
        
        return h

# ============================================================================
# PLACEMENT ENVIRONMENT
# ============================================================================

class MacroPlacementEnv:
    """RL Environment for macro placement"""
    
    def __init__(self, design_data: Dict, config: Config):
        self.design_data = design_data
        self.config = config
        self.macros = design_data['macros']
        self.macro_list = list(self.macros.keys())
        
        # Get chip dimensions
        placement = design_data['placement']
        all_coords = []
        for coords in placement.values():
            all_coords.extend(coords)
        
        self.chip_width = max(all_coords)
        self.chip_height = max(all_coords)
        
        # Grid
        self.grid_size = config.GRID_SIZE
        self.grid = np.zeros((self.grid_size, self.grid_size))
        
        # State
        self.current_macro_idx = 0
        self.placed_macros = {}
        
    def reset(self) -> Dict:
        """Reset environment"""
        self.current_macro_idx = 0
        self.placed_macros = {}
        self.grid = np.zeros((self.grid_size, self.grid_size))
        
        return self._get_state()
    
    def _get_state(self) -> Dict:
        """Get current state"""
        if self.current_macro_idx >= len(self.macro_list):
            return None
        
        current_macro_name = self.macro_list[self.current_macro_idx]
        current_macro = self.macros[current_macro_name]
        
        return {
            'grid': self.grid.copy(),
            'current_macro': current_macro,
            'macro_name': current_macro_name,
            'num_placed': len(self.placed_macros),
            'total_macros': len(self.macro_list)
        }
    
    def step(self, action: Tuple[int, int]) -> Tuple[Dict, float, bool]:
        """
        Take action (place macro at grid position)
        
        Args:
            action: (grid_x, grid_y) position
        
        Returns:
            (next_state, reward, done)
        """
        grid_x, grid_y = action
        
        # Convert grid to real coordinates
        x = (grid_x / self.grid_size) * self.chip_width
        y = (grid_y / self.grid_size) * self.chip_height
        
        current_macro_name = self.macro_list[self.current_macro_idx]
        macro = self.macros[current_macro_name]
        
        # Place macro
        width = macro['width']
        height = macro['height']
        
        coords = [x, y, x + width, y + height]
        self.placed_macros[current_macro_name] = coords
        
        # Update grid
        grid_x1 = int((x / self.chip_width) * self.grid_size)
        grid_y1 = int((y / self.chip_height) * self.grid_size)
        grid_x2 = int(((x + width) / self.chip_width) * self.grid_size)
        grid_y2 = int(((y + height) / self.chip_height) * self.grid_size)
        
        grid_x2 = min(grid_x2, self.grid_size - 1)
        grid_y2 = min(grid_y2, self.grid_size - 1)
        
        self.grid[grid_y1:grid_y2, grid_x1:grid_x2] = 1.0
        
        # Calculate reward
        reward = self._calculate_reward(coords, macro)
        
        # Move to next macro
        self.current_macro_idx += 1
        done = self.current_macro_idx >= len(self.macro_list)
        
        next_state = self._get_state()
        
        return next_state, reward, done
    
    def _calculate_reward(self, coords: List[float], macro: Dict) -> float:
        """
        Calculate placement reward
        
        Reward components:
        - Overlap penalty (negative)
        - Boundary proximity bonus
        - Utilization bonus
        - Wirelength proxy (center distance)
        """
        reward = 0.0
        
        x1, y1, x2, y2 = coords
        
        # Check overlap with placed macros
        overlap_penalty = 0.0
        for other_name, other_coords in self.placed_macros.items():
            if other_name == self.macro_list[self.current_macro_idx]:
                continue
            
            ox1, oy1, ox2, oy2 = other_coords
            
            # Check intersection
            if not (x2 < ox1 or x1 > ox2 or y2 < oy1 or y1 > oy2):
                # Calculate overlap area
                overlap_w = min(x2, ox2) - max(x1, ox1)
                overlap_h = min(y2, oy2) - max(y1, oy1)
                overlap_area = overlap_w * overlap_h
                overlap_penalty += overlap_area * 0.01  # Heavy penalty
        
        reward -= overlap_penalty
        
        # Out of bounds penalty
        if x1 < 0 or y1 < 0 or x2 > self.chip_width or y2 > self.chip_height:
            reward -= 1000.0
        
        # Center proximity bonus (macros near center often better)
        center_x = self.chip_width / 2
        center_y = self.chip_height / 2
        macro_center_x = (x1 + x2) / 2
        macro_center_y = (y1 + y2) / 2
        
        distance_to_center = np.sqrt((macro_center_x - center_x)**2 + 
                                     (macro_center_y - center_y)**2)
        normalized_dist = distance_to_center / (self.chip_width / 2)
        
        reward += (1.0 - normalized_dist) * 10.0  # Bonus for being central
        
        # Utilization bonus
        utilization = np.sum(self.grid) / (self.grid_size * self.grid_size)
        reward += utilization * 5.0
        
        return reward

print("✓ Module 1 loaded: Data Loading & Environment")
