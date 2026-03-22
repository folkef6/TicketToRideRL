"""Gymnasium environment for Ticket to Ride Europe (2-player)."""

from __future__ import annotations

import random
from typing import Any

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from ttr.game.engine import GameState
from ttr.game.types import Phase
from .actions import (
    ACTION_SPACE_SIZE, encode_action, decode_action, compute_action_mask,
)
from .observations import build_observation, observation_size


class TTREnv(gym.Env):
    """Ticket to Ride Europe environment.

    The agent always plays as Player 0. The opponent (Player 1) is controlled
    by an opponent policy passed at construction.

    Supports action masking via the `action_masks()` method for MaskablePPO.
    """

    metadata = {"render_modes": ["human"]}

    def __init__(
        self,
        opponent_fn: callable | None = None,
        seed: int | None = None,
        render_mode: str | None = None,
    ) -> None:
        super().__init__()

        self.obs_size = observation_size()
        self.observation_space = spaces.Box(
            low=-1.0, high=2.0, shape=(self.obs_size,), dtype=np.float32
        )
        self.action_space = spaces.Discrete(ACTION_SPACE_SIZE)

        self.opponent_fn = opponent_fn or self._random_opponent
        self.render_mode = render_mode
        self._seed = seed
        self._seed_counter = seed or 0

        self.game: GameState | None = None

    def reset(
        self, *, seed: int | None = None, options: dict | None = None
    ) -> tuple[np.ndarray, dict[str, Any]]:
        super().reset(seed=seed)

        if seed is not None:
            self._seed_counter = seed
        self.game = GameState(seed=self._seed_counter)
        self._seed_counter += 1

        # Let opponent complete their initial destination selection if they go first
        self._run_opponent_turns()

        obs = build_observation(self.game, player_id=0)
        info = {"action_mask": self.action_masks()}
        return obs, info

    def step(self, action: int) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        assert self.game is not None, "Call reset() first"
        assert not self.game.is_terminal(), "Game is over"

        # Validate action against mask
        mask = self.action_masks()
        if mask[action] == 0:
            # Invalid action — return current state with penalty
            obs = build_observation(self.game, player_id=0)
            return obs, -0.1, False, False, {"action_mask": mask}

        # Decode and execute agent's action
        game_action = decode_action(action, self.game)
        prev_points = self.game.players[0].points
        self.game.step(game_action)
        new_points = self.game.players[0].points

        # Reward shaping: route points gained
        reward = (new_points - prev_points) / 100.0

        # Check for destination completion
        # (simplified: check after route claims)
        reward += self._check_dest_completion_reward()

        # Let opponent play until it's our turn or game ends
        if not self.game.is_terminal():
            self._run_opponent_turns()

        terminated = self.game.is_terminal()
        truncated = False

        if terminated:
            final_scores = self.game.get_final_scores()
            if final_scores[0] > final_scores[1]:
                reward += 1.0
            elif final_scores[0] < final_scores[1]:
                reward -= 1.0
            # Tie: no additional reward

        obs = build_observation(self.game, player_id=0)
        info = {"action_mask": self.action_masks()}
        if terminated:
            info["final_scores"] = self.game.get_final_scores()

        return obs, reward, terminated, truncated, info

    def action_masks(self) -> np.ndarray:
        """Return valid action mask for MaskablePPO."""
        if self.game is None or self.game.is_terminal() or self.game.current_player != 0:
            # Return a dummy mask with one valid action to avoid Simplex errors
            # in PPO training when terminal masks get stored in the rollout buffer
            mask = np.zeros(ACTION_SPACE_SIZE, dtype=np.int8)
            mask[0] = 1
            return mask

        return compute_action_mask(self.game)

    def _run_opponent_turns(self) -> None:
        """Execute opponent moves until it's player 0's turn or game ends."""
        while (
            not self.game.is_terminal()
            and self.game.current_player == 1
        ):
            actions = self.game.get_valid_actions()
            if not actions:
                break
            opp_action = self.opponent_fn(self.game, actions)
            self.game.step(opp_action)

    def _random_opponent(self, game: GameState, actions: list) -> Any:
        """Random opponent policy."""
        return random.choice(actions)

    def _check_dest_completion_reward(self) -> float:
        """Small reward bonus when a destination ticket becomes completed."""
        # For now, skip this — full check is expensive and mainly matters at end
        return 0.0
