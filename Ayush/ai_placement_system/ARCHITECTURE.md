# System Architecture Diagram

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                                                                               │
│                   AI-POWERED MACRO PLACEMENT SYSTEM                           │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘

                                    INPUT
                                      ↓
                    ┌─────────────────────────────────┐
                    │     CircuitNet Dataset          │
                    │  • 54 designs                   │
                    │  • 10,242 placement configs     │
                    │  • Net/Node/Pin attributes      │
                    └──────────────┬──────────────────┘
                                   ↓
                    ┌─────────────────────────────────┐
                    │  CircuitNetDataLoader           │
                    │  • Load .npy files              │
                    │  • Extract macros (>1000μm²)    │
                    │  • Build netlist graph          │
                    └──────────────┬──────────────────┘
                                   ↓
                            ┌──────┴──────┐
                            │             │
                    ┌───────▼─────┐  ┌───▼─────────────┐
                    │  Netlist    │  │  Placement      │
                    │  Graph      │  │  Data           │
                    │  (DGL)      │  │  (Microns)      │
                    └───────┬─────┘  └───┬─────────────┘
                            │            │
                            └──────┬─────┘
                                   ↓
                    ┌─────────────────────────────────┐
                    │     Circuit GNN (GAT)           │
                    │  • 4 attention layers           │
                    │  • 256-dim embeddings           │
                    │  • Graph encoding               │
                    └──────────────┬──────────────────┘
                                   ↓
                         Graph Embedding (256-dim)
                                   ↓
                    ┌─────────────────────────────────┐
                    │  MacroPlacementEnv (RL Env)     │
                    │  • State: grid + macro features │
                    │  • Action: (x,y) position       │
                    │  • Reward: overlap + util       │
                    └──┬──────────────────────────┬───┘
                       │                          │
                ┌──────▼──────┐           ┌──────▼──────┐
                │   Actor     │           │   Critic    │
                │  (Policy)   │           │   (Value)   │
                │             │           │             │
                │  Graph ─┐   │           │  Graph ─┐   │
                │  Grid  ─┤→ Fusion      │  Grid  ─┤→ Fusion
                │  Macro ─┘   │           │  Macro ─┘   │
                │      ↓      │           │      ↓      │
                │  Policy     │           │   Value     │
                │  (x,y)      │           │   V(s)      │
                └──────┬──────┘           └──────┬──────┘
                       │                          │
                       └──────────┬───────────────┘
                                  ↓
                    ┌─────────────────────────────────┐
                    │     PPO Training Loop           │
                    │  1. Collect experiences         │
                    │  2. Compute GAE advantages      │
                    │  3. Update actor (clipped)      │
                    │  4. Update critic (MSE)         │
                    └──────────────┬──────────────────┘
                                   ↓
                         Training Iteration
                                   ↓
                    ┌─────────────────────────────────┐
                    │     Episodes & Checkpoints      │
                    │  • Save best model              │
                    │  • Track metrics                │
                    │  • Generate curves              │
                    └──────────────┬──────────────────┘
                                   ↓
                                 OUTPUT
                                   ↓
                ┌──────────────────┼───────────────────┐
                │                  │                   │
        ┌───────▼──────┐   ┌──────▼──────┐   ┌───────▼──────┐
        │  Trained     │   │ Placement   │   │  Cadence     │
        │  Models      │   │ Visualize   │   │  Innovus DEF │
        │  (.pt)       │   │ (.png)      │   │  (.def)      │
        └──────────────┘   └─────────────┘   └──────────────┘


═════════════════════════════════════════════════════════════════════════

DATA FLOW DETAIL:

1. LOADING PHASE:
   netlist.npy → {nets, nodes, pins} → DGL Graph
   placement.npy → {macro: [x1,y1,x2,y2]} → Environment

2. ENCODING PHASE:
   DGL Graph → GNN(GAT) → Graph Embedding [256]
   Current State → {grid[256,256], macro[4]} → State Features

3. DECISION PHASE:
   State + Graph Embed → Actor → Policy Distribution
   State + Graph Embed → Critic → Value Estimate
   Sample Action → (x, y) position

4. EXECUTION PHASE:
   Action + Environment → Update Grid
   Calculate Reward → {overlap, bounds, center, util}
   Store Experience → Buffer

5. LEARNING PHASE:
   Batch Experiences → Compute Advantages (GAE)
   Update Actor → PPO Clipped Objective
   Update Critic → MSE Loss

6. EXPORT PHASE:
   Final Placement → Visualize (matplotlib)
   Final Placement → DEF Format (Innovus)
   Final Placement → JSON (parsing)

═════════════════════════════════════════════════════════════════════════

REWARD FUNCTION:

   R = 0
   R -= overlap_penalty * 0.01        # Heavy penalty
   R -= out_of_bounds * 1000          # Very heavy
   R += center_proximity * 20         # Wirelength proxy
   R += utilization * 5               # Space efficiency
   
   Goal: Maximize R → Better placement

═════════════════════════════════════════════════════════════════════════

NEURAL NETWORK ARCHITECTURE:

┌─────────────────────────────────────────────────────────────────────────┐
│                          CIRCUIT GNN (GAT)                              │
├─────────────────────────────────────────────────────────────────────────┤
│  Input: Node Features [N, F_in]                                        │
│    ↓                                                                    │
│  Linear Projection [N, 256]                                            │
│    ↓                                                                    │
│  GAT Layer 1 (4 heads) [N, 256]                                        │
│    ↓ + residual                                                         │
│  LayerNorm + ReLU                                                       │
│    ↓                                                                    │
│  GAT Layer 2 (4 heads) [N, 256]                                        │
│    ↓ + residual                                                         │
│  LayerNorm + ReLU                                                       │
│    ↓                                                                    │
│  GAT Layer 3 (4 heads) [N, 256]                                        │
│    ↓ + residual                                                         │
│  LayerNorm + ReLU                                                       │
│    ↓                                                                    │
│  GAT Layer 4 (4 heads) [N, 256]                                        │
│    ↓ + residual                                                         │
│  LayerNorm + ReLU                                                       │
│    ↓                                                                    │
│  Mean Pooling [256]                                                     │
│    ↓                                                                    │
│  Output: Graph Embedding [256]                                          │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                            ACTOR NETWORK                                │
├─────────────────────────────────────────────────────────────────────────┤
│  Inputs:                                                                │
│    • Graph Embed [256]                                                  │
│    • Grid State [1, 256, 256]                                           │
│    • Macro Features [4]                                                 │
│                                                                          │
│  Graph Encoder:                                                          │
│    Linear(256→512) → ReLU → LayerNorm → Linear(512→512) → ReLU         │
│                                                                          │
│  Grid Encoder (CNN):                                                     │
│    Conv2d(1→32, k=5, s=2) → ReLU                                         │
│    Conv2d(32→64, k=3, s=2) → ReLU                                        │
│    Conv2d(64→128, k=3, s=2) → ReLU                                       │
│    AdaptiveAvgPool2d(1) → Flatten → Linear(128→512)                     │
│                                                                          │
│  Macro Encoder:                                                          │
│    Linear(4→256) → ReLU → Linear(256→512)                               │
│                                                                          │
│  Fusion:                                                                 │
│    Concat(512+512+512=1536)                                             │
│    Linear(1536→1024) → ReLU → LayerNorm → Dropout(0.1)                 │
│    Linear(1024→512) → ReLU                                              │
│                                                                          │
│  Policy Heads:                                                           │
│    X: Linear(512→256)  → Categorical Distribution                       │
│    Y: Linear(512→256)  → Categorical Distribution                       │
│                                                                          │
│  Output: Action (x, y), Log Prob, Entropy                               │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                           CRITIC NETWORK                                │
├─────────────────────────────────────────────────────────────────────────┤
│  Same encoders as Actor                                                  │
│                                                                          │
│  Value Head:                                                             │
│    Concat(512+512+512=1536)                                             │
│    Linear(1536→1024) → ReLU → LayerNorm → Dropout(0.1)                 │
│    Linear(1024→512) → ReLU                                              │
│    Linear(512→1)                                                        │
│                                                                          │
│  Output: Value V(s)                                                      │
└─────────────────────────────────────────────────────────────────────────┘

═════════════════════════════════════════════════════════════════════════

TRAINING ALGORITHM (PPO):

for episode in episodes:
    # Collect experiences
    state = env.reset()
    while not done:
        action, log_prob, value = agent.select_action(state)
        next_state, reward, done = env.step(action)
        store_experience(state, action, reward, value...)
        state = next_state
    
    # Update policy
    if len(buffer) >= batch_size:
        # Compute advantages with GAE
        advantages, returns = compute_gae(rewards, values, gamma, lambda)
        
        # PPO updates
        for _ in range(ppo_epochs):
            # Get current policy
            new_log_probs = actor(states, ...)
            
            # Ratio
            ratio = exp(new_log_probs - old_log_probs)
            
            # Clipped objective
            surr1 = ratio * advantages
            surr2 = clip(ratio, 1-ε, 1+ε) * advantages
            actor_loss = -min(surr1, surr2) - β * entropy
            
            # Value loss
            critic_loss = MSE(critic(states), returns)
            
            # Update
            actor_loss.backward()
            critic_loss.backward()

═════════════════════════════════════════════════════════════════════════

KEY HYPERPARAMETERS:

GNN:
  - Hidden Dim: 256
  - Num Layers: 4
  - Attention Heads: 4
  - Dropout: 0.0

RL:
  - Learning Rate: 3e-4
  - Gamma (discount): 0.99
  - GAE Lambda: 0.95
  - Clip Epsilon: 0.2
  - Entropy Coeff: 0.01
  - Batch Size: 32

Environment:
  - Grid Size: 256×256
  - Macro Threshold: 1000 μm²
  - Chip Size: ~554×554 μm

Training:
  - Episodes: 100-1000
  - Update Freq: Every batch
  - Save Freq: Every 200 episodes

═════════════════════════════════════════════════════════════════════════
```
