# Ticket to Ride Europe RL — Implementation Plan

## Context

Build a reinforcement learning project where agents learn to play Ticket to Ride Europe (1v1). The project includes a full game engine, a Gymnasium-compatible RL environment, training with MaskablePPO (sb3-contrib), and a Pygame GUI for spectating agent games and playing against the agent.

## Project Structure

```
TicketToRideRL/
├── pyproject.toml
├── ttr/
│   ├── __init__.py
│   ├── game/                    # Pure game logic, no RL/GUI deps
│   │   ├── __init__.py
│   │   ├── constants.py         # Map data, routes, destination tickets, scoring table
│   │   ├── types.py             # Enums (CardColor, Phase, ActionType), dataclasses (Route, DestTicket)
│   │   ├── cards.py             # Train card deck, face-up display, discard, 3-loco rule
│   │   ├── player.py            # Player state (hand, trains, stations, tickets, points)
│   │   ├── board.py             # Route ownership, double-route 2p rule
│   │   ├── engine.py            # GameState + rules engine (action validation, turn flow)
│   │   └── scoring.py           # End-game scoring, destination BFS, longest route DFS
│   ├── env/                     # Gymnasium environment
│   │   ├── __init__.py
│   │   ├── actions.py           # Action encoding/decoding + mask computation
│   │   ├── observations.py      # Observation vector construction
│   │   └── ttr_env.py           # Gymnasium env (reset, step, action_masks)
│   ├── training/                # RL training pipeline
│   │   ├── __init__.py
│   │   ├── train.py             # Training entry point (MaskablePPO)
│   │   ├── self_play.py         # Opponent pool + periodic snapshots
│   │   ├── callbacks.py         # SB3 callbacks (eval, checkpoints)
│   │   └── evaluate.py          # Evaluation scripts (win rates, stats)
│   └── gui/                     # Pygame visualization
│       ├── __init__.py
│       ├── app.py               # Main loop (spectator + human-play modes)
│       ├── renderer.py          # Board/card/score rendering
│       ├── map_data.py          # City pixel coordinates
│       ├── input_handler.py     # Mouse click → game action translation
│       └── assets/              # Map image, card sprites, fonts
└── tests/
    ├── test_engine.py
    ├── test_scoring.py
    ├── test_actions.py
    └── test_env.py
```

## Dependencies

- `gymnasium>=1.0`, `numpy`, `stable-baselines3>=2.4`, `sb3-contrib>=2.4`, `pygame>=2.6`, `tensorboard`
- Note: verify Python 3.14 compat for SB3/PyTorch; fall back to 3.12 if needed.

---

## Phase 1: Game Engine (`ttr/game/`)

**Goal**: Fully functional, testable game engine with no RL or GUI dependencies.

### Key data (`constants.py`)
- 46 cities mapped to integer IDs
- ~101 route segments as frozen dataclasses: `Route(id, city_a, city_b, length, color, is_tunnel, ferry_locomotives, is_double, parallel_id)`
- ~46 destination tickets as `(city_a, city_b, points)` tuples
- Scoring table: `{1:1, 2:2, 3:4, 4:7, 5:10, 6:15, 8:21}`
- 110 train cards: 12 each of 8 colors + 14 locomotives

### Core rules to implement
- **Drawing cards**: 2 cards per turn; face-up locomotive = entire turn; 3+ locos in face-up → refresh all 5
- **Tunnels**: Reveal 3 cards, pay extra matching/loco cards or fail (auto-resolve: pay if able, else fail)
- **Ferries**: Require minimum locomotive count
- **Stations**: Cost 1/2/3 same-color cards for 1st/2nd/3rd; borrow one opponent route for connectivity
- **Double routes (2p)**: Only one of a parallel pair may be claimed total
- **Game end**: Triggered when a player has ≤2 trains; each player gets one final turn
- **Scoring**: Route points + destination completion/penalty + longest route (+10) + unplaced stations (+4 each)

### GameState core
- `route_owner[101]`, train/face-up/discard decks, per-player hands (9-element card counts), trains/stations remaining, destination tickets, points, current_player, phase
- Key methods: `get_valid_actions()`, `step(action)`, `is_terminal()`, `get_scores()`

**Milestone**: Run complete games with two random players via script.

---

## Phase 2: Gymnasium Environment (`ttr/env/`)

### Action space — `Discrete(969)` with masking

| Range     | Count | Description                            |
|-----------|-------|----------------------------------------|
| 0–4       | 5     | Draw face-up card at slot i            |
| 5         | 1     | Draw from deck                         |
| 6–914     | 909   | Claim route (101 routes × 9 colors)    |
| 915–960   | 46    | Place station at city i                |
| 961       | 1     | Draw destination tickets               |
| 962–968   | 7     | Keep destination subset (bitmask 1–7)  |

Design decisions:
- Locomotive split auto-resolved (use minimum locos) to keep action space manageable
- Most actions masked out at any given step

### Observation space — `Box(shape=(224,), float32)`

| Feature              | Size | Notes                                   |
|----------------------|------|-----------------------------------------|
| my_hand              | 9    | Card counts per color                   |
| face_up_cards        | 9    | Counts of each color in face-up display |
| deck_size            | 1    | Normalized                              |
| route_ownership      | 101  | 0=unclaimed, 1=mine, 2=theirs          |
| my/opp trains        | 2    | Normalized                              |
| my/opp stations      | 2    |                                         |
| my_dest_tickets      | 46   | Binary vector over all possible tickets |
| my/opp score         | 2    |                                         |
| phase                | 4    | One-hot                                 |
| opp_hand_size        | 1    |                                         |
| pending_destinations | 46   | Binary (during keep-destinations phase) |
| turns_to_end         | 1    |                                         |

### Reward shaping
- +route_points/100 on route claim
- +ticket_value/100 when a destination is completed
- Terminal: +1 win, -1 loss

### Opponent handling
- Environment always plays as Player 0
- Opponent steps automatically inside `env.step()`
- Opponent can be: random policy, fixed model, or self-play

**Milestone**: `gymnasium.utils.env_checker.check_env(env)` passes. 1000 random episodes without errors.

---

## Phase 3: Basic RL Training

- Train MaskablePPO vs random opponent
- MLP policy `[256, 256]`, lr=3e-4, n_steps=2048, batch_size=64
- Evaluation callback tracking win rate vs random
- Iterate on reward shaping if needed

**Milestone**: Agent achieves >80% win rate vs random.

---

## Phase 4: Self-Play Training

- Opponent pool with periodic model snapshots (every N steps)
- Sample opponent: 80% latest, 20% uniform from pool
- Train 5–10M steps
- Evaluate self-play agent vs Phase 3 agent

**Milestone**: Self-play agent consistently beats the random-trained agent.

---

## Phase 5: GUI (`ttr/gui/`)

- **Pygame** — lightweight, good for 2D board rendering
- GUI operates on `GameState` directly (not through Gymnasium env)
- Two modes: **spectator** (agent vs agent with configurable speed) and **human play** (click to act)
- Render: map background, cities, routes (colored lines, filled when claimed), cards, scores
- Input: click routes to claim, click face-up cards to draw, click deck, destination selection overlay

**Milestone**: Watch full agent-vs-agent game visually. Play a full human-vs-agent game.

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Python 3.14 compat (SB3/PyTorch) | Test early; fall back to 3.12 |
| Map data accuracy (101 routes) | Cross-reference sources; validation tests |
| Action mask correctness | Extensive unit tests; assertions in `step()` |
| Long episodes (~100+ steps) | Sufficient n_steps in PPO; shaped rewards |
| Sparse early rewards | Generous reward shaping; possible curriculum |

## Verification

- **Phase 1**: Run `pytest tests/test_engine.py tests/test_scoring.py` — all pass; random game script runs to completion
- **Phase 2**: Run `pytest tests/test_env.py` — check_env passes; 1000 random episodes complete
- **Phase 3**: Run training script; monitor TensorBoard; evaluate win rate >80% vs random
- **Phase 4**: Compare self-play agent vs Phase 3 agent; win rate should be significant
- **Phase 5**: Launch GUI; watch a game; play a game as human
