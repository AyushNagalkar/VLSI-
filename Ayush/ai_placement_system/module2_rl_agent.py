"""
Module 2: Reinforcement Learning Agent
======================================
PPO (Proximal Policy Optimization) for Macro Placement

This module implements:
- Actor-Critic networks
- PPO training algorithm
- Experience buffer
- Policy optimization
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Categorical
import numpy as np
from typing import Dict, List, Tuple
from collections import deque
import random

# ============================================================================
# ACTOR-CRITIC NETWORK
# ============================================================================

class PlacementActor(nn.Module):
    """
    Actor network: outputs placement action distribution
    
    Given circuit graph embedding and current state, predicts best grid position
    """
    
    def __init__(self, graph_embed_dim: int, grid_size: int, hidden_dim: int = 512):
        super().__init__()
        
        self.grid_size = grid_size
        
        # Process graph embedding
        self.graph_encoder = nn.Sequential(
            nn.Linear(graph_embed_dim, hidden_dim),
            nn.ReLU(),
            nn.LayerNorm(hidden_dim),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )
        
        # Process grid state (CNN)
        self.grid_encoder = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=5, stride=2, padding=2),
            nn.ReLU(),
            nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(128, hidden_dim)
        )
        
        # Macro features encoder
        self.macro_encoder = nn.Sequential(
            nn.Linear(4, hidden_dim // 2),  # [width, height, area, aspect_ratio]
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, hidden_dim)
        )
        
        # Fusion layer
        self.fusion = nn.Sequential(
            nn.Linear(hidden_dim * 3, hidden_dim * 2),
            nn.ReLU(),
            nn.LayerNorm(hidden_dim * 2),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU()
        )
        
        # Policy heads (separate for x and y to reduce action space)
        self.policy_x = nn.Linear(hidden_dim, grid_size)
        self.policy_y = nn.Linear(hidden_dim, grid_size)
        
    def forward(self, graph_embed: torch.Tensor, grid_state: torch.Tensor, 
                macro_features: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass
        
        Args:
            graph_embed: [batch, graph_embed_dim]
            grid_state: [batch, 1, grid_size, grid_size]
            macro_features: [batch, 4]
        
        Returns:
            (x_logits, y_logits): Policy distributions for x and y coordinates
        """
        # Encode inputs
        graph_h = self.graph_encoder(graph_embed)
        grid_h = self.grid_encoder(grid_state)
        macro_h = self.macro_encoder(macro_features)
        
        # Fuse features
        combined = torch.cat([graph_h, grid_h, macro_h], dim=1)
        fused = self.fusion(combined)
        
        # Policy outputs
        x_logits = self.policy_x(fused)
        y_logits = self.policy_y(fused)
        
        return x_logits, y_logits
    
    def get_action(self, graph_embed: torch.Tensor, grid_state: torch.Tensor,
                   macro_features: torch.Tensor, deterministic: bool = False) -> Tuple:
        """
        Sample action from policy
        
        Returns:
            (action, log_prob, entropy)
        """
        x_logits, y_logits = self.forward(graph_embed, grid_state, macro_features)
        
        # Create distributions
        x_dist = Categorical(logits=x_logits)
        y_dist = Categorical(logits=y_logits)
        
        if deterministic:
            x_action = torch.argmax(x_logits, dim=1)
            y_action = torch.argmax(y_logits, dim=1)
        else:
            x_action = x_dist.sample()
            y_action = y_dist.sample()
        
        # Log probabilities
        x_log_prob = x_dist.log_prob(x_action)
        y_log_prob = y_dist.log_prob(y_action)
        log_prob = x_log_prob + y_log_prob
        
        # Entropy (for exploration bonus)
        entropy = x_dist.entropy() + y_dist.entropy()
        
        return (x_action, y_action), log_prob, entropy


class PlacementCritic(nn.Module):
    """
    Critic network: estimates value function V(s)
    
    Predicts expected cumulative reward from current state
    """
    
    def __init__(self, graph_embed_dim: int, grid_size: int, hidden_dim: int = 512):
        super().__init__()
        
        # Similar encoders as Actor
        self.graph_encoder = nn.Sequential(
            nn.Linear(graph_embed_dim, hidden_dim),
            nn.ReLU(),
            nn.LayerNorm(hidden_dim)
        )
        
        self.grid_encoder = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=5, stride=2, padding=2),
            nn.ReLU(),
            nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(128, hidden_dim)
        )
        
        self.macro_encoder = nn.Sequential(
            nn.Linear(4, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, hidden_dim)
        )
        
        # Fusion and value head
        self.value_head = nn.Sequential(
            nn.Linear(hidden_dim * 3, hidden_dim * 2),
            nn.ReLU(),
            nn.LayerNorm(hidden_dim * 2),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )
        
    def forward(self, graph_embed: torch.Tensor, grid_state: torch.Tensor,
                macro_features: torch.Tensor) -> torch.Tensor:
        """
        Forward pass
        
        Returns:
            value: [batch, 1] - estimated state value
        """
        graph_h = self.graph_encoder(graph_embed)
        grid_h = self.grid_encoder(grid_state)
        macro_h = self.macro_encoder(macro_features)
        
        combined = torch.cat([graph_h, grid_h, macro_h], dim=1)
        value = self.value_head(combined)
        
        return value


# ============================================================================
# EXPERIENCE BUFFER
# ============================================================================

class ExperienceBuffer:
    """Stores experiences for PPO training"""
    
    def __init__(self, capacity: int = 10000):
        self.capacity = capacity
        self.buffer = deque(maxlen=capacity)
        
    def add(self, experience: Dict):
        """Add experience tuple"""
        self.buffer.append(experience)
        
    def sample(self, batch_size: int) -> List[Dict]:
        """Sample random batch"""
        return random.sample(self.buffer, min(batch_size, len(self.buffer)))
    
    def get_all(self) -> List[Dict]:
        """Get all experiences (for on-policy PPO)"""
        return list(self.buffer)
    
    def clear(self):
        """Clear buffer"""
        self.buffer.clear()
    
    def __len__(self):
        return len(self.buffer)


# ============================================================================
# PPO AGENT
# ============================================================================

class PPOAgent:
    """
    Proximal Policy Optimization Agent
    
    Implements PPO algorithm for macro placement learning
    """
    
    def __init__(self, graph_embed_dim: int, grid_size: int, config):
        self.config = config
        self.device = config.DEVICE
        
        # Networks
        self.actor = PlacementActor(graph_embed_dim, grid_size).to(self.device)
        self.critic = PlacementCritic(graph_embed_dim, grid_size).to(self.device)
        
        # Optimizers
        self.actor_optimizer = torch.optim.Adam(
            self.actor.parameters(), lr=config.RL_LEARNING_RATE
        )
        self.critic_optimizer = torch.optim.Adam(
            self.critic.parameters(), lr=config.RL_LEARNING_RATE
        )
        
        # Experience buffer
        self.buffer = ExperienceBuffer(capacity=10000)
        
        # Training stats
        self.stats = {
            'actor_loss': [],
            'critic_loss': [],
            'total_reward': [],
            'episode_length': []
        }
        
    def select_action(self, graph_embed: np.ndarray, grid_state: np.ndarray,
                     macro_features: np.ndarray, deterministic: bool = False):
        """
        Select action from policy
        
        Args:
            graph_embed: Graph embedding from GNN
            grid_state: Current placement grid
            macro_features: Current macro features
            deterministic: If True, select best action (no sampling)
        
        Returns:
            action, log_prob, value
        """
        self.actor.eval()
        self.critic.eval()
        
        with torch.no_grad():
            # Convert to tensors
            graph_embed_t = torch.FloatTensor(graph_embed).unsqueeze(0).to(self.device)
            grid_state_t = torch.FloatTensor(grid_state).unsqueeze(0).unsqueeze(0).to(self.device)
            macro_features_t = torch.FloatTensor(macro_features).unsqueeze(0).to(self.device)
            
            # Get action
            (x_action, y_action), log_prob, entropy = self.actor.get_action(
                graph_embed_t, grid_state_t, macro_features_t, deterministic
            )
            
            # Get value estimate
            value = self.critic(graph_embed_t, grid_state_t, macro_features_t)
            
            action = (x_action.item(), y_action.item())
            log_prob = log_prob.item()
            value = value.item()
            
        self.actor.train()
        self.critic.train()
        
        return action, log_prob, value
    
    def store_experience(self, experience: Dict):
        """Store experience in buffer"""
        self.buffer.add(experience)
    
    def compute_gae(self, rewards: List[float], values: List[float], 
                    next_values: List[float], dones: List[bool]) -> Tuple:
        """
        Compute Generalized Advantage Estimation (GAE)
        
        GAE balances bias-variance tradeoff in advantage estimation
        """
        advantages = []
        gae = 0
        
        gamma = self.config.RL_GAMMA
        lambda_gae = self.config.RL_GAE_LAMBDA
        
        for t in reversed(range(len(rewards))):
            delta = rewards[t] + gamma * next_values[t] * (1 - dones[t]) - values[t]
            gae = delta + gamma * lambda_gae * (1 - dones[t]) * gae
            advantages.insert(0, gae)
        
        # Returns = advantages + values
        returns = [adv + val for adv, val in zip(advantages, values)]
        
        return advantages, returns
    
    def update(self, num_epochs: int = 4):
        """
        PPO update step
        
        Args:
            num_epochs: Number of epochs to train on collected experiences
        """
        if len(self.buffer) < self.config.BATCH_SIZE:
            return
        
        experiences = self.buffer.get_all()
        
        # Extract tensors
        graph_embeds = torch.FloatTensor([e['graph_embed'] for e in experiences]).to(self.device)
        grid_states = torch.FloatTensor([e['grid_state'] for e in experiences]).unsqueeze(1).to(self.device)
        macro_features = torch.FloatTensor([e['macro_features'] for e in experiences]).to(self.device)
        actions_x = torch.LongTensor([e['action'][0] for e in experiences]).to(self.device)
        actions_y = torch.LongTensor([e['action'][1] for e in experiences]).to(self.device)
        old_log_probs = torch.FloatTensor([e['log_prob'] for e in experiences]).to(self.device)
        rewards = [e['reward'] for e in experiences]
        values = [e['value'] for e in experiences]
        next_values = [e['next_value'] for e in experiences]
        dones = [e['done'] for e in experiences]
        
        # Compute advantages
        advantages, returns = self.compute_gae(rewards, values, next_values, dones)
        advantages_t = torch.FloatTensor(advantages).to(self.device)
        returns_t = torch.FloatTensor(returns).to(self.device)
        
        # Normalize advantages
        advantages_t = (advantages_t - advantages_t.mean()) / (advantages_t.std() + 1e-8)
        
        # PPO epochs
        for epoch in range(num_epochs):
            # Get current policy
            x_logits, y_logits = self.actor(graph_embeds, grid_states, macro_features)
            x_dist = Categorical(logits=x_logits)
            y_dist = Categorical(logits=y_logits)
            
            new_log_probs = x_dist.log_prob(actions_x) + y_dist.log_prob(actions_y)
            entropy = x_dist.entropy() + y_dist.entropy()
            
            # Policy ratio
            ratio = torch.exp(new_log_probs - old_log_probs)
            
            # Clipped surrogate objective
            surr1 = ratio * advantages_t
            surr2 = torch.clamp(ratio, 1 - self.config.RL_CLIP_EPSILON, 
                               1 + self.config.RL_CLIP_EPSILON) * advantages_t
            actor_loss = -torch.min(surr1, surr2).mean()
            
            # Entropy bonus for exploration
            actor_loss = actor_loss - self.config.RL_ENTROPY_COEFF * entropy.mean()
            
            # Update actor
            self.actor_optimizer.zero_grad()
            actor_loss.backward()
            torch.nn.utils.clip_grad_norm_(self.actor.parameters(), 0.5)
            self.actor_optimizer.step()
            
            # Critic loss (value function)
            values_pred = self.critic(graph_embeds, grid_states, macro_features).squeeze()
            critic_loss = F.mse_loss(values_pred, returns_t)
            
            # Update critic
            self.critic_optimizer.zero_grad()
            critic_loss.backward()
            torch.nn.utils.clip_grad_norm_(self.critic.parameters(), 0.5)
            self.critic_optimizer.step()
        
        # Store stats
        self.stats['actor_loss'].append(actor_loss.item())
        self.stats['critic_loss'].append(critic_loss.item())
        
        # Clear buffer (on-policy)
        self.buffer.clear()
    
    def save(self, path: str):
        """Save model checkpoints"""
        torch.save({
            'actor_state_dict': self.actor.state_dict(),
            'critic_state_dict': self.critic.state_dict(),
            'actor_optimizer': self.actor_optimizer.state_dict(),
            'critic_optimizer': self.critic_optimizer.state_dict(),
            'stats': self.stats
        }, path)
        print(f"  💾 Model saved to {path}")
    
    def load(self, path: str):
        """Load model checkpoints"""
        checkpoint = torch.load(path, map_location=self.device)
        self.actor.load_state_dict(checkpoint['actor_state_dict'])
        self.critic.load_state_dict(checkpoint['critic_state_dict'])
        self.actor_optimizer.load_state_dict(checkpoint['actor_optimizer'])
        self.critic_optimizer.load_state_dict(checkpoint['critic_optimizer'])
        self.stats = checkpoint['stats']
        print(f"  📂 Model loaded from {path}")

print("✓ Module 2 loaded: RL Agent (PPO)")
