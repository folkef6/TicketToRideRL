"""Self-play training with opponent pool."""

from __future__ import annotations

import argparse
import os
import random
from pathlib import Path

import numpy as np
from sb3_contrib import MaskablePPO
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import SubprocVecEnv

from ttr.env import TTREnv
from ttr.game.engine import GameState
from ttr.game.types import Action
from ttr.env.actions import decode_action, compute_action_mask
from ttr.env.observations import build_observation
from .callbacks import WinRateCallback


class OpponentPool:
    """Pool of past model snapshots for self-play."""

    def __init__(self, latest_ratio: float = 0.8) -> None:
        self.snapshots: list[Path] = []
        self.latest_ratio = latest_ratio

    def add_snapshot(self, path: Path) -> None:
        self.snapshots.append(path)

    def sample_opponent(self) -> Path | None:
        if not self.snapshots:
            return None
        if random.random() < self.latest_ratio or len(self.snapshots) == 1:
            return self.snapshots[-1]
        return random.choice(self.snapshots[:-1])


def make_model_opponent(model_path: Path):
    """Create an opponent function from a saved model."""
    model = MaskablePPO.load(str(model_path))

    def opponent_fn(game: GameState, actions: list[Action]) -> Action:
        obs = build_observation(game, player_id=1)
        mask = compute_action_mask(game)
        action_idx, _ = model.predict(obs, action_masks=mask, deterministic=False)
        return decode_action(int(action_idx), game)

    return opponent_fn


def _make_env(seed: int, opponent_model_path: str | None = None):
    """Factory that returns a no-arg callable for SubprocVecEnv."""
    def _init():
        opponent_fn = None
        if opponent_model_path is not None:
            opponent_fn = make_model_opponent(Path(opponent_model_path))
        return Monitor(TTREnv(seed=seed, opponent_fn=opponent_fn))
    return _init


def _make_vec_env(n_envs: int, seed: int, opponent_model_path: str | None = None) -> SubprocVecEnv:
    """Create a SubprocVecEnv with n_envs parallel environments."""
    env_fns = [_make_env(seed + i, opponent_model_path) for i in range(n_envs)]
    return SubprocVecEnv(env_fns)


def train_self_play(
    total_timesteps: int = 5_000_000,
    snapshot_freq: int = 100_000,
    save_dir: str = "models/self_play",
    log_dir: str = "logs/self_play",
    seed: int = 0,
    resume_model: str | None = None,
    n_envs: int | None = None,
) -> None:
    """Train with self-play opponent pool."""
    if n_envs is None:
        n_envs = min(os.cpu_count() or 1, 16)

    save_path = Path(save_dir)
    save_path.mkdir(parents=True, exist_ok=True)
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    pool = OpponentPool()

    # Track current opponent model path for env recreation
    current_opponent_path: str | None = None

    if resume_model:
        # Seed the pool with the resumed model as first opponent
        initial_snapshot = save_path / "snapshot_0"
        # Load temporarily to save the snapshot
        tmp_env = Monitor(TTREnv(seed=seed))
        tmp_model = MaskablePPO.load(resume_model, env=tmp_env)
        tmp_model.save(str(initial_snapshot))
        del tmp_model, tmp_env
        pool.add_snapshot(initial_snapshot)
        current_opponent_path = str(initial_snapshot)
        print(f"Resumed from {resume_model}, starting self-play")

    env = _make_vec_env(n_envs, seed, current_opponent_path)
    print(f"Using {n_envs} parallel environments")

    if resume_model:
        model = MaskablePPO.load(resume_model, env=env)
        model.tensorboard_log = str(log_path)
    else:
        model = MaskablePPO(
            "MlpPolicy",
            env,
            learning_rate=3e-4,
            n_steps=2048,
            batch_size=64,
            policy_kwargs=dict(net_arch=[256, 256]),
            verbose=1,
            tensorboard_log=str(log_path),
            seed=seed,
        )

    # Eval env always plays vs random to track absolute strength
    eval_env = TTREnv(seed=seed + 1000)
    win_rate_cb = WinRateCallback(eval_env, eval_freq=10_000, n_eval_episodes=50)

    checkpoint_cb = CheckpointCallback(
        save_freq=50_000,
        save_path=str(save_path),
        name_prefix="ttr_selfplay",
    )

    steps_done = 0
    while steps_done < total_timesteps:
        chunk = min(snapshot_freq, total_timesteps - steps_done)
        model.learn(
            total_timesteps=chunk,
            reset_num_timesteps=False,
            callback=[checkpoint_cb, win_rate_cb],
            progress_bar=True,
        )
        steps_done += chunk

        # Save snapshot and add to pool
        snapshot_path = save_path / f"snapshot_{steps_done}"
        model.save(str(snapshot_path))
        pool.add_snapshot(snapshot_path)

        # Swap opponent: close old env, create new one with updated opponent
        opp_path = pool.sample_opponent()
        if opp_path is not None:
            current_opponent_path = str(opp_path)
            env.close()
            env = _make_vec_env(n_envs, seed + steps_done, current_opponent_path)
            model.set_env(env)
            print(f"[{steps_done}/{total_timesteps}] Opponent updated → {opp_path.name} (pool size: {len(pool.snapshots)})")

    env.close()
    model.save(str(save_path / "final"))
    print(f"Training complete. Final model saved to {save_path / 'final'}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Self-play training for TTR")
    parser.add_argument("--timesteps", type=int, default=5_000_000)
    parser.add_argument("--snapshot-freq", type=int, default=100_000)
    parser.add_argument("--save-dir", type=str, default="models/self_play")
    parser.add_argument("--log-dir", type=str, default="logs/self_play")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--resume", type=str, default=None, help="Path to model .zip to resume from")
    parser.add_argument("--n-envs", type=int, default=None, help="Number of parallel environments (default: CPU count, max 16)")
    args = parser.parse_args()

    train_self_play(
        total_timesteps=args.timesteps,
        snapshot_freq=args.snapshot_freq,
        save_dir=args.save_dir,
        log_dir=args.log_dir,
        seed=args.seed,
        resume_model=args.resume,
        n_envs=args.n_envs,
    )


if __name__ == "__main__":
    main()
