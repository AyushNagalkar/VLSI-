"""
Module 3: Training Pipeline & System Integration
=================================================
Complete training loop with evaluation and Innovus export
"""

import torch
import numpy as np
from pathlib import Path
import json
from datetime import datetime
from tqdm import tqdm
import matplotlib.pyplot as plt
from typing import Dict, List

from Ayush.ai_placement_system.module1_data_env import Config, CircuitNetDataLoader, MacroPlacementEnv, CircuitGNN
from Ayush.ai_placement_system.module2_rl_agent import PPOAgent

# ============================================================================
# TRAINING PIPELINE
# ============================================================================

class MacroPlacementTrainer:
    """Complete training pipeline for macro placement"""
    
    def __init__(self, config: Config):
        self.config = config
        config.OUTPUT_DIR.mkdir(exist_ok=True)
        config.MODEL_SAVE_DIR.mkdir(exist_ok=True)
        
        print("\n" + "="*80)
        print("🚀 AI-POWERED MACRO PLACEMENT SYSTEM")
        print("="*80)
        print(f"Device: {config.DEVICE}")
        print(f"GNN Hidden Dim: {config.GNN_HIDDEN_DIM}")
        print(f"Grid Size: {config.GRID_SIZE} x {config.GRID_SIZE}")
        print(f"RL Algorithm: PPO (Proximal Policy Optimization)")
        print("="*80 + "\n")
        
        # Initialize components
        self.data_loader = CircuitNetDataLoader(config)
        self.dataset = None
        self.gnn_model = None
        self.agent = None
        
        # Training metrics
        self.training_history = {
            'episodes': [],
            'avg_reward': [],
            'avg_overlap': [],
            'avg_utilization': [],
            'best_reward': float('-inf')
        }
        
    def initialize(self):
        """Load data and initialize models"""
        print("⚙️  Initializing system...")
        
        # Load dataset
        self.dataset = self.data_loader.load_all_designs()
        
        if len(self.dataset) == 0:
            raise ValueError("No valid designs loaded!")
        
        # Get input dimension from global cell type vocabulary
        input_dim = len(self.data_loader.global_cell_types)
        
        print(f"\n  Building GNN model...")
        print(f"    Input dimension: {input_dim}")
        print(f"    Hidden dimension: {self.config.GNN_HIDDEN_DIM}")
        print(f"    Number of layers: {self.config.GNN_NUM_LAYERS}")
        
        self.gnn_model = CircuitGNN(
            input_dim=input_dim,
            hidden_dim=self.config.GNN_HIDDEN_DIM,
            num_layers=self.config.GNN_NUM_LAYERS
        ).to(self.config.DEVICE)
        
        # Initialize RL agent
        print(f"\n  Building RL Agent (PPO)...")
        self.agent = PPOAgent(
            graph_embed_dim=self.config.GNN_HIDDEN_DIM,
            grid_size=self.config.GRID_SIZE,
            config=self.config
        )
        
        print("\n✅ System initialized successfully!")
        print(f"  Total parameters: {self._count_parameters():,}")
        
    def _count_parameters(self) -> int:
        """Count total trainable parameters"""
        total = 0
        total += sum(p.numel() for p in self.gnn_model.parameters() if p.requires_grad)
        total += sum(p.numel() for p in self.agent.actor.parameters() if p.requires_grad)
        total += sum(p.numel() for p in self.agent.critic.parameters() if p.requires_grad)
        return total
    
    def encode_graph(self, graph) -> np.ndarray:
        """Encode circuit graph using GNN"""
        self.gnn_model.eval()
        with torch.no_grad():
            graph = graph.to(self.config.DEVICE)
            node_features = graph.ndata['feat'].to(self.config.DEVICE)
            
            # Get node embeddings
            node_embeds = self.gnn_model(graph, node_features)
            
            # Graph-level embedding (mean pooling)
            graph_embed = torch.mean(node_embeds, dim=0)
            
            return graph_embed.cpu().numpy()
    
    def train_episode(self, design_data: Dict) -> Dict:
        """Train one episode on a design"""
        
        # Create environment
        env = MacroPlacementEnv(design_data, self.config)
        
        # Encode graph
        graph_embed = self.encode_graph(design_data['graph'])
        
        # Reset environment
        state = env.reset()
        
        episode_reward = 0
        episode_length = 0
        experiences = []
        
        done = False
        while not done:
            # Extract state features
            grid_state = state['grid']
            macro = state['current_macro']
            macro_features = np.array([
                macro['width'],
                macro['height'],
                macro['area'],
                macro['width'] / macro['height']  # aspect ratio
            ])
            
            # Select action
            action, log_prob, value = self.agent.select_action(
                graph_embed, grid_state, macro_features
            )
            
            # Take action in environment
            next_state, reward, done = env.step(action)
            
            # Get next value
            if next_state is not None:
                next_grid = next_state['grid']
                next_macro = next_state['current_macro']
                next_macro_features = np.array([
                    next_macro['width'],
                    next_macro['height'],
                    next_macro['area'],
                    next_macro['width'] / next_macro['height']
                ])
                _, _, next_value = self.agent.select_action(
                    graph_embed, next_grid, next_macro_features
                )
            else:
                next_value = 0.0
            
            # Store experience
            experience = {
                'graph_embed': graph_embed,
                'grid_state': grid_state,
                'macro_features': macro_features,
                'action': action,
                'log_prob': log_prob,
                'value': value,
                'reward': reward,
                'next_value': next_value,
                'done': done
            }
            self.agent.store_experience(experience)
            
            episode_reward += reward
            episode_length += 1
            
            state = next_state
        
        # Calculate metrics
        metrics = {
            'total_reward': episode_reward,
            'episode_length': episode_length,
            'avg_reward_per_step': episode_reward / episode_length if episode_length > 0 else 0,
            'overlap_count': self._count_overlaps(env.placed_macros),
            'utilization': np.sum(env.grid) / (env.grid.size)
        }
        
        return metrics
    
    def _count_overlaps(self, placed_macros: Dict) -> int:
        """Count number of overlapping macro pairs"""
        overlaps = 0
        macro_list = list(placed_macros.items())
        
        for i in range(len(macro_list)):
            name1, coords1 = macro_list[i]
            x1_1, y1_1, x2_1, y2_1 = coords1
            
            for j in range(i + 1, len(macro_list)):
                name2, coords2 = macro_list[j]
                x1_2, y1_2, x2_2, y2_2 = coords2
                
                # Check intersection
                if not (x2_1 < x1_2 or x1_1 > x2_2 or y2_1 < y1_2 or y1_1 > y2_2):
                    overlaps += 1
        
        return overlaps
    
    def train(self, num_episodes: int = 1000):
        """
        Main training loop
        
        Args:
            num_episodes: Number of training episodes
        """
        print("\n" + "="*80)
        print("🎯 STARTING TRAINING")
        print("="*80)
        print(f"Episodes: {num_episodes}")
        print(f"Batch size: {self.config.BATCH_SIZE}")
        print(f"Designs: {len(self.dataset)}")
        print("="*80 + "\n")
        
        best_reward = float('-inf')
        
        for episode in tqdm(range(num_episodes), desc="Training"):
            # Sample random design
            design_data = np.random.choice(self.dataset)
            
            # Train episode
            metrics = self.train_episode(design_data)
            
            # Update agent
            if len(self.agent.buffer) >= self.config.BATCH_SIZE:
                self.agent.update(num_epochs=4)
            
            # Log metrics
            self.training_history['episodes'].append(episode)
            self.training_history['avg_reward'].append(metrics['total_reward'])
            self.training_history['avg_overlap'].append(metrics['overlap_count'])
            self.training_history['avg_utilization'].append(metrics['utilization'])
            
            # Save best model
            if metrics['total_reward'] > best_reward:
                best_reward = metrics['total_reward']
                self.training_history['best_reward'] = best_reward
                self.agent.save(self.config.MODEL_SAVE_DIR / "best_model.pt")
            
            # Periodic logging
            if (episode + 1) % 50 == 0:
                recent_rewards = self.training_history['avg_reward'][-50:]
                recent_overlaps = self.training_history['avg_overlap'][-50:]
                recent_util = self.training_history['avg_utilization'][-50:]
                
                print(f"\n📊 Episode {episode + 1}/{num_episodes}")
                print(f"  Avg Reward (last 50): {np.mean(recent_rewards):.2f}")
                print(f"  Avg Overlaps: {np.mean(recent_overlaps):.2f}")
                print(f"  Avg Utilization: {np.mean(recent_util):.4f}")
                print(f"  Best Reward: {best_reward:.2f}")
            
            # Save checkpoint
            if (episode + 1) % 200 == 0:
                checkpoint_path = self.config.MODEL_SAVE_DIR / f"checkpoint_ep{episode+1}.pt"
                self.agent.save(checkpoint_path)
                self.save_training_history()
        
        print("\n✅ Training completed!")
        self.save_training_history()
        self.plot_training_curves()
    
    def evaluate(self, design_idx: int = 0, visualize: bool = True) -> Dict:
        """
        Evaluate on a specific design
        
        Args:
            design_idx: Index of design in dataset
            visualize: Whether to create visualization
        
        Returns:
            Evaluation metrics and placement results
        """
        print(f"\n🔍 Evaluating on design {design_idx}...")
        
        design_data = self.dataset[design_idx]
        env = MacroPlacementEnv(design_data, self.config)
        
        # Encode graph
        graph_embed = self.encode_graph(design_data['graph'])
        
        # Run deterministic policy
        state = env.reset()
        done = False
        total_reward = 0
        
        while not done:
            grid_state = state['grid']
            macro = state['current_macro']
            macro_features = np.array([
                macro['width'],
                macro['height'],
                macro['area'],
                macro['width'] / macro['height']
            ])
            
            # Deterministic action
            action, _, _ = self.agent.select_action(
                graph_embed, grid_state, macro_features, deterministic=True
            )
            
            next_state, reward, done = env.step(action)
            total_reward += reward
            state = next_state
        
        # Metrics
        metrics = {
            'total_reward': total_reward,
            'num_macros': len(env.placed_macros),
            'overlaps': self._count_overlaps(env.placed_macros),
            'utilization': np.sum(env.grid) / env.grid.size,
            'chip_width': env.chip_width,
            'chip_height': env.chip_height
        }
        
        print(f"\n  Total Reward: {metrics['total_reward']:.2f}")
        print(f"  Macros Placed: {metrics['num_macros']}")
        print(f"  Overlaps: {metrics['overlaps']}")
        print(f"  Utilization: {metrics['utilization']:.4f}")
        
        # Visualize
        if visualize:
            self.visualize_placement(env.placed_macros, env.chip_width, env.chip_height,
                                    save_path=self.config.OUTPUT_DIR / f"placement_design{design_idx}.png")
        
        # Export for Innovus
        self.export_to_innovus(env.placed_macros, design_idx)
        
        return metrics
    
    def visualize_placement(self, placed_macros: Dict, chip_width: float, 
                           chip_height: float, save_path: Path):
        """Visualize macro placement"""
        fig, ax = plt.subplots(figsize=(12, 12))
        
        # Draw chip boundary
        ax.add_patch(plt.Rectangle((0, 0), chip_width, chip_height,
                                   fill=False, edgecolor='black', linewidth=2))
        
        # Draw macros
        colors = plt.cm.Set3(np.linspace(0, 1, len(placed_macros)))
        
        for i, (name, coords) in enumerate(placed_macros.items()):
            x1, y1, x2, y2 = coords
            width = x2 - x1
            height = y2 - y1
            
            ax.add_patch(plt.Rectangle((x1, y1), width, height,
                                      facecolor=colors[i], edgecolor='black',
                                      linewidth=1, alpha=0.7))
            
            # Label
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            ax.text(cx, cy, f"M{i}", ha='center', va='center',
                   fontsize=8, fontweight='bold')
        
        ax.set_xlim(0, chip_width)
        ax.set_ylim(0, chip_height)
        ax.set_aspect('equal')
        ax.set_xlabel('X (microns)', fontsize=12)
        ax.set_ylabel('Y (microns)', fontsize=12)
        ax.set_title('AI-Generated Macro Placement', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"  📊 Visualization saved to {save_path}")
    
    def export_to_innovus(self, placed_macros: Dict, design_idx: int):
        """
        Export placement to Cadence Innovus DEF format
        
        DEF (Design Exchange Format) is standard for physical design
        """
        output_file = self.config.OUTPUT_DIR / f"macro_placement_design{design_idx}.def"
        
        with open(output_file, 'w') as f:
            f.write("# Macro Placement for Cadence Innovus\n")
            f.write(f"# Generated by AI Placement System\n")
            f.write(f"# Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Design: design_{design_idx}\n\n")
            
            f.write("VERSION 5.8 ;\n")
            f.write("DIVIDERCHAR \"/\" ;\n")
            f.write("BUSBITCHARS \"[]\" ;\n\n")
            
            f.write("DESIGN macro_placement ;\n\n")
            
            # Components section
            f.write(f"COMPONENTS {len(placed_macros)} ;\n")
            for name, coords in placed_macros.items():
                x1, y1, x2, y2 = coords
                # Convert microns to DEF units (typically 2000 units = 1 micron)
                def_x = int(x1 * 2000)
                def_y = int(y1 * 2000)
                
                f.write(f"  - {name} MACRO_TYPE\n")
                f.write(f"    + PLACED ( {def_x} {def_y} ) N ;\n")
            f.write("END COMPONENTS\n\n")
            
            f.write("END DESIGN\n")
        
        # Also save as JSON for easy parsing
        json_file = self.config.OUTPUT_DIR / f"macro_placement_design{design_idx}.json"
        placement_dict = {
            name: {
                'x1': float(coords[0]),
                'y1': float(coords[1]),
                'x2': float(coords[2]),
                'y2': float(coords[3]),
                'width': float(coords[2] - coords[0]),
                'height': float(coords[3] - coords[1])
            }
            for name, coords in placed_macros.items()
        }
        
        with open(json_file, 'w') as f:
            json.dump(placement_dict, f, indent=2)
        
        print(f"  💾 Innovus DEF exported to {output_file}")
        print(f"  💾 JSON format saved to {json_file}")
    
    def save_training_history(self):
        """Save training metrics"""
        history_file = self.config.OUTPUT_DIR / "training_history.json"
        with open(history_file, 'w') as f:
            json.dump(self.training_history, f, indent=2)
        print(f"  💾 Training history saved to {history_file}")
    
    def plot_training_curves(self):
        """Plot training curves"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # Reward curve
        axes[0, 0].plot(self.training_history['episodes'], 
                       self.training_history['avg_reward'])
        axes[0, 0].set_xlabel('Episode')
        axes[0, 0].set_ylabel('Total Reward')
        axes[0, 0].set_title('Training Reward')
        axes[0, 0].grid(True, alpha=0.3)
        
        # Overlap curve
        axes[0, 1].plot(self.training_history['episodes'],
                       self.training_history['avg_overlap'])
        axes[0, 1].set_xlabel('Episode')
        axes[0, 1].set_ylabel('Number of Overlaps')
        axes[0, 1].set_title('Macro Overlaps')
        axes[0, 1].grid(True, alpha=0.3)
        
        # Utilization curve
        axes[1, 0].plot(self.training_history['episodes'],
                       self.training_history['avg_utilization'])
        axes[1, 0].set_xlabel('Episode')
        axes[1, 0].set_ylabel('Utilization')
        axes[1, 0].set_title('Grid Utilization')
        axes[1, 0].grid(True, alpha=0.3)
        
        # Actor/Critic loss
        if len(self.agent.stats['actor_loss']) > 0:
            axes[1, 1].plot(self.agent.stats['actor_loss'], label='Actor Loss')
            axes[1, 1].plot(self.agent.stats['critic_loss'], label='Critic Loss')
            axes[1, 1].set_xlabel('Update Step')
            axes[1, 1].set_ylabel('Loss')
            axes[1, 1].set_title('RL Losses')
            axes[1, 1].legend()
            axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plot_file = self.config.OUTPUT_DIR / "training_curves.png"
        plt.savefig(plot_file, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"  📈 Training curves saved to {plot_file}")

print("✓ Module 3 loaded: Training Pipeline")
