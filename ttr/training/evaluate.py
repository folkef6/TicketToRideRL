"""Evaluation scripts for trained agents."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from sb3_contrib import MaskablePPO

from ttr.env import TTREnv


def evaluate(
    model_path: str,
    n_episodes: int = 100,
    seed: int = 0,
) -> dict:
    """Evaluate a trained model against a random opponent."""
    model = MaskablePPO.load(model_path)
    env = TTREnv(seed=seed)

    wins = 0
    total_score_diff = 0
    all_scores = []

    for ep in range(n_episodes):
        obs, info = env.reset()
        done = False
        while not done:
            mask = info.get("action_mask", None)
            action, _ = model.predict(obs, action_masks=mask, deterministic=True)
            obs, _, terminated, truncated, info = env.step(action)
            done = terminated or truncated

        final = info.get("final_scores", [0, 0])
        all_scores.append(final)
        if final[0] > final[1]:
            wins += 1
        total_score_diff += final[0] - final[1]

    results = {
        "win_rate": wins / n_episodes,
        "avg_score_diff": total_score_diff / n_episodes,
        "avg_score_p0": np.mean([s[0] for s in all_scores]),
        "avg_score_p1": np.mean([s[1] for s in all_scores]),
    }
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate TTR agent")
    parser.add_argument("model", type=str, help="Path to saved model")
    parser.add_argument("--episodes", type=int, default=100)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    results = evaluate(args.model, n_episodes=args.episodes, seed=args.seed)
    print(f"Win rate: {results['win_rate']:.1%}")
    print(f"Avg score diff: {results['avg_score_diff']:.1f}")
    print(f"Avg P0 score: {results['avg_score_p0']:.1f}")
    print(f"Avg P1 score: {results['avg_score_p1']:.1f}")


if __name__ == "__main__":
    main()
