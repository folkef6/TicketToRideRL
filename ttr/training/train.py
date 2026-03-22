"""Training entry point for MaskablePPO."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from sb3_contrib import MaskablePPO
from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import SubprocVecEnv

from ttr.env import TTREnv
from ttr.training.self_play import make_model_opponent
from .callbacks import WinRateCallback


def _make_env(seed: int = 0, opponent_model: str | None = None):
    """Factory that returns a no-arg callable for SubprocVecEnv."""
    def _init():
        opponent_fn = None
        if opponent_model:
            opponent_fn = make_model_opponent(Path(opponent_model))
        return Monitor(TTREnv(seed=seed, opponent_fn=opponent_fn))
    return _init


def train(
    total_timesteps: int = 1_000_000,
    lr: float = 3e-4,
    n_steps: int = 2048,
    batch_size: int = 64,
    save_dir: str = "models",
    log_dir: str = "logs",
    seed: int = 0,
    opponent_model: str | None = None,
    resume_model: str | None = None,
    n_envs: int | None = None,
) -> MaskablePPO:
    if n_envs is None:
        n_envs = min(os.cpu_count() or 1, 16)

    save_path = Path(save_dir)
    save_path.mkdir(parents=True, exist_ok=True)
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    env_fns = [_make_env(seed + i, opponent_model) for i in range(n_envs)]
    env = SubprocVecEnv(env_fns)
    print(f"Using {n_envs} parallel environments")

    if resume_model:
        model = MaskablePPO.load(resume_model, env=env)
        model.tensorboard_log = str(log_path)
    else:
        model = MaskablePPO(
            "MlpPolicy",
            env,
            learning_rate=lr,
            n_steps=n_steps,
            batch_size=batch_size,
            policy_kwargs=dict(net_arch=[256, 256]),
            verbose=1,
            tensorboard_log=str(log_path),
            seed=seed,
        )

    checkpoint_cb = CheckpointCallback(
        save_freq=50_000,
        save_path=str(save_path),
        name_prefix="ttr_ppo",
    )

    eval_env = TTREnv(seed=seed + 1000)
    win_rate_cb = WinRateCallback(eval_env, eval_freq=10_000, n_eval_episodes=50)

    model.learn(
        total_timesteps=total_timesteps,
        callback=[checkpoint_cb, win_rate_cb],
        progress_bar=True,
    )

    env.close()
    model.save(str(save_path / "ttr_ppo_final"))
    return model


def main() -> None:
    parser = argparse.ArgumentParser(description="Train TTR agent with MaskablePPO")
    parser.add_argument("--timesteps", type=int, default=1_000_000)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--n-steps", type=int, default=2048)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--save-dir", type=str, default="models")
    parser.add_argument("--log-dir", type=str, default="logs")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--opponent", type=str, default=None, help="Path to opponent model .zip")
    parser.add_argument("--resume", type=str, default=None, help="Path to model .zip to resume training from")
    parser.add_argument("--n-envs", type=int, default=None, help="Number of parallel environments (default: CPU count, max 16)")
    args = parser.parse_args()

    train(
        total_timesteps=args.timesteps,
        lr=args.lr,
        n_steps=args.n_steps,
        batch_size=args.batch_size,
        save_dir=args.save_dir,
        log_dir=args.log_dir,
        seed=args.seed,
        opponent_model=args.opponent,
        resume_model=args.resume,
        n_envs=args.n_envs,
    )


if __name__ == "__main__":
    main()
