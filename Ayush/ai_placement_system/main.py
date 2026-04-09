"""
AI-POWERED MACRO PLACEMENT SYSTEM
==================================
Main Entry Point

Usage:
    python main.py --mode train --episodes 1000
    python main.py --mode eval --design 0
    python main.py --mode demo

Author: AI System
Date: March 2026
"""

import argparse
import sys
import torch
import numpy as np
from pathlib import Path

# Import our modules
from Ayush.ai_placement_system.module1_data_env import Config
from Ayush.ai_placement_system.module3_training import MacroPlacementTrainer

def print_banner():
    """Print system banner"""
    banner = """
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║          AI-POWERED MACRO PLACEMENT SYSTEM                        ║
    ║                                                                   ║
    ║     🤖 GNN + Reinforcement Learning for Chip Design               ║
    ║     📊 Trained on CircuitNet Dataset                              ║
    ║     🎯 Optimized for Cadence Innovus Integration                  ║
    ║                                                                   ║
    ║     Technology: PyTorch + DGL + PPO                               ║
    ║     Dataset: CircuitNet (54 designs, 10K+ configs)                ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """
    print(banner)

def train_mode(args):
    """Training mode"""
    print("\n🎓 TRAINING MODE\n")
    
    config = Config()
    trainer = MacroPlacementTrainer(config)
    
    # Initialize system
    trainer.initialize()
    
    # Train
    trainer.train(num_episodes=args.episodes)
    
    # Evaluate on first design
    print("\n" + "="*80)
    print("📊 POST-TRAINING EVALUATION")
    print("="*80)
    trainer.evaluate(design_idx=0, visualize=True)

def eval_mode(args):
    """Evaluation mode"""
    print("\n🔍 EVALUATION MODE\n")
    
    config = Config()
    trainer = MacroPlacementTrainer(config)
    
    # Initialize
    trainer.initialize()
    
    # Load trained model
    model_path = config.MODEL_SAVE_DIR / "best_model.pt"
    if model_path.exists():
        trainer.agent.load(str(model_path))
        print("✅ Loaded trained model")
    else:
        print("⚠️  No trained model found! Using random policy.")
    
    # Evaluate
    trainer.evaluate(design_idx=args.design, visualize=True)

def demo_mode(args):
    """Demo mode - quick demonstration"""
    print("\n🎬 DEMO MODE\n")
    print("Running quick demonstration with 100 training episodes...\n")
    
    config = Config()
    config.BATCH_SIZE = 16  # Smaller batch for demo
    
    trainer = MacroPlacementTrainer(config)
    
    # Initialize
    trainer.initialize()
    
    # Quick training
    print("\n🏃 Quick training (100 episodes)...")
    trainer.train(num_episodes=100)
    
    # Evaluate
    print("\n📊 Evaluation...")
    trainer.evaluate(design_idx=0, visualize=True)
    
    print("\n" + "="*80)
    print("✅ DEMO COMPLETED!")
    print("="*80)
    print("\nGenerated files:")
    print(f"  📁 Models: {config.MODEL_SAVE_DIR}")
    print(f"  📁 Results: {config.OUTPUT_DIR}")
    print(f"\nKey outputs:")
    print(f"  • Training curves: {config.OUTPUT_DIR / 'training_curves.png'}")
    print(f"  • Placement visualization: {config.OUTPUT_DIR / 'placement_design0.png'}")
    print(f"  • Innovus DEF file: {config.OUTPUT_DIR / 'macro_placement_design0.def'}")
    print(f"  • JSON placement: {config.OUTPUT_DIR / 'macro_placement_design0.json'}")

def info_mode():
    """Show system information"""
    print("\n📋 SYSTEM INFORMATION\n")
    
    config = Config()
    
    print("Configuration:")
    print(f"  Device: {config.DEVICE}")
    print(f"  GNN Hidden Dim: {config.GNN_HIDDEN_DIM}")
    print(f"  GNN Layers: {config.GNN_NUM_LAYERS}")
    print(f"  Grid Size: {config.GRID_SIZE}x{config.GRID_SIZE}")
    print(f"  RL Algorithm: PPO")
    print(f"  Learning Rate: {config.RL_LEARNING_RATE}")
    print(f"  Batch Size: {config.BATCH_SIZE}")
    
    print("\nData Paths:")
    print(f"  Dataset: {config.DATA_PATH}")
    print(f"  Graph Features: {config.GRAPH_FEATURES_PATH}")
    print(f"  Placements: {config.MICRON_PLACEMENT_PATH}")
    
    print("\nOutput Paths:")
    print(f"  Models: {config.MODEL_SAVE_DIR}")
    print(f"  Results: {config.OUTPUT_DIR}")
    
    print("\nAlgorithm Details:")
    print("  • GNN: Graph Attention Network (GAT)")
    print("  • Policy: Actor-Critic with PPO")
    print("  • Advantage: Generalized Advantage Estimation (GAE)")
    print("  • Exploration: Entropy regularization")
    
    print("\nReward Components:")
    print("  • Overlap penalty (negative)")
    print("  • Out-of-bounds penalty (negative)")
    print("  • Center proximity bonus")
    print("  • Utilization bonus")
    
    print("\nExport Formats:")
    print("  • DEF (Design Exchange Format) for Cadence Innovus")
    print("  • JSON for easy parsing and visualization")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="AI-Powered Macro Placement System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Train from scratch
  python main.py --mode train --episodes 1000
  
  # Evaluate trained model
  python main.py --mode eval --design 0
  
  # Quick demo (100 episodes)
  python main.py --mode demo
  
  # Show system info
  python main.py --mode info
        """
    )
    
    parser.add_argument('--mode', type=str, required=True,
                       choices=['train', 'eval', 'demo', 'info'],
                       help='Operation mode')
    parser.add_argument('--episodes', type=int, default=1000,
                       help='Number of training episodes (train mode)')
    parser.add_argument('--design', type=int, default=0,
                       help='Design index to evaluate (eval mode)')
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    # Check PyTorch
    print(f"\n✓ PyTorch version: {torch.__version__}")
    print(f"✓ CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"✓ CUDA device: {torch.cuda.get_device_name(0)}")
    
    # Run mode
    try:
        if args.mode == 'train':
            train_mode(args)
        elif args.mode == 'eval':
            eval_mode(args)
        elif args.mode == 'demo':
            demo_mode(args)
        elif args.mode == 'info':
            info_mode()
        
        print("\n✅ Completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
