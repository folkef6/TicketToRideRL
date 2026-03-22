"""Custom SB3 callbacks for TTR training."""

from __future__ import annotations

import numpy as np
from stable_baselines3.common.callbacks import BaseCallback


class WinRateCallback(BaseCallback):
    """Periodically evaluate the agent's win rate against the environment's opponent."""

    def __init__(
        self,
        eval_env,
        eval_freq: int = 10_000,
        n_eval_episodes: int = 50,
        verbose: int = 1,
    ):
        super().__init__(verbose)
        self.eval_env = eval_env
        self.eval_freq = eval_freq
        self.n_eval_episodes = n_eval_episodes

    def _on_step(self) -> bool:
        if self.n_calls % self.eval_freq != 0:
            return True

        wins = 0
        max_steps_per_episode = 500
        for _ in range(self.n_eval_episodes):
            obs, info = self.eval_env.reset()
            done = False
            steps = 0
            while not done and steps < max_steps_per_episode:
                mask = info.get("action_mask", None)
                if mask is None or not mask.any():
                    break
                action, _ = self.model.predict(obs, action_masks=mask, deterministic=True)
                obs, _, terminated, truncated, info = self.eval_env.step(action)
                done = terminated or truncated
                steps += 1
            final = info.get("final_scores", [0, 0])
            if final[0] > final[1]:
                wins += 1

        win_rate = wins / self.n_eval_episodes
        self.logger.record("eval/win_rate", win_rate)
        if self.verbose:
            print(f"  Win rate: {win_rate:.1%} ({wins}/{self.n_eval_episodes})")
        return True
