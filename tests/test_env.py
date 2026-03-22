"""Tests for the Gymnasium environment."""

import pytest
import numpy as np
from ttr.env import TTREnv
from ttr.env.actions import ACTION_SPACE_SIZE
from ttr.env.observations import observation_size


class TestEnvBasic:
    def test_reset(self):
        env = TTREnv(seed=0)
        obs, info = env.reset()
        assert obs.shape == (observation_size(),)
        assert "action_mask" in info
        assert len(info["action_mask"]) == ACTION_SPACE_SIZE

    def test_step_valid_action(self):
        env = TTREnv(seed=0)
        obs, info = env.reset()
        mask = info["action_mask"]
        valid = np.where(mask > 0)[0]
        assert len(valid) > 0
        obs2, reward, term, trunc, info2 = env.step(valid[0])
        assert obs2.shape == obs.shape

    def test_invalid_action_penalty(self):
        env = TTREnv(seed=0)
        obs, info = env.reset()
        mask = info["action_mask"]
        invalid = np.where(mask == 0)[0]
        if len(invalid) > 0:
            obs2, reward, term, trunc, info2 = env.step(invalid[0])
            assert reward == -0.1
            assert not term

    def test_gymnasium_check_env(self):
        from gymnasium.utils.env_checker import check_env
        env = TTREnv(seed=42)
        check_env(env, skip_render_check=True)


class TestRandomEpisodes:
    @pytest.mark.parametrize("seed", range(20))
    def test_episode_completes(self, seed):
        env = TTREnv(seed=seed)
        obs, info = env.reset()
        steps = 0
        while steps < 500:
            mask = info["action_mask"]
            valid = np.where(mask > 0)[0]
            assert len(valid) > 0, f"No valid actions at step {steps}"
            action = np.random.choice(valid)
            obs, reward, term, trunc, info = env.step(action)
            steps += 1
            if term or trunc:
                break
        assert steps < 500
