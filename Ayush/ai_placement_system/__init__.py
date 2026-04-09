"""
AI-Powered Macro Placement System
==================================

A complete deep learning system for automated chip macro placement
using Graph Neural Networks (GNN) and Reinforcement Learning (RL).

Modules:
- module1_data_env: Data loading, environment, and GNN
- module2_rl_agent: PPO agent with actor-critic networks
- module3_training: Training pipeline and evaluation

Usage:
    from ai_placement_system import Config, MacroPlacementTrainer
    
    config = Config()
    trainer = MacroPlacementTrainer(config)
    trainer.initialize()
    trainer.train(num_episodes=1000)
"""

__version__ = "1.0.0"
__author__ = "AI Development Team"
__email__ = "support@ai-placement.com"

# Import main components for easy access
from Ayush.ai_placement_system.module1_data_env import (
    Config,
    CircuitNetDataLoader,
    MacroPlacementEnv,
    CircuitGNN
)

from Ayush.ai_placement_system.module2_rl_agent import (
    PlacementActor,
    PlacementCritic,
    PPOAgent,
    ExperienceBuffer
)

from Ayush.ai_placement_system.module3_training import (
    MacroPlacementTrainer
)

__all__ = [
    'Config',
    'CircuitNetDataLoader',
    'MacroPlacementEnv',
    'CircuitGNN',
    'PlacementActor',
    'PlacementCritic',
    'PPOAgent',
    'ExperienceBuffer',
    'MacroPlacementTrainer'
]
