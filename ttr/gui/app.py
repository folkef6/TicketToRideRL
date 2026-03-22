"""Main GUI application for Ticket to Ride Europe.

Two modes:
  - Spectator: watch agent vs agent (or random vs random)
  - Human play: play as one player against an AI/random opponent
"""

from __future__ import annotations

import sys
import random
import time
import argparse

import pygame

from ttr.game.engine import GameState
from ttr.game.types import Action, Phase
from .renderer import Renderer, WINDOW_W, WINDOW_H
from .input_handler import InputHandler


def random_policy(game: GameState, actions: list[Action]) -> Action:
    return random.choice(actions)


def make_model_policy(model_path: str, player_id: int = 0):
    """Create a policy function from a trained MaskablePPO model."""
    from sb3_contrib import MaskablePPO
    from ttr.env.observations import build_observation
    from ttr.env.actions import compute_action_mask, decode_action

    model = MaskablePPO.load(model_path)

    def policy(game: GameState, actions: list[Action]) -> Action:
        obs = build_observation(game, player_id=player_id)
        mask = compute_action_mask(game)
        action_idx, _ = model.predict(obs, action_masks=mask, deterministic=False)
        return decode_action(int(action_idx), game)

    return policy


def run_spectator(
    speed: float = 0.3,
    seed: int | None = None,
    policy_0=None,
    policy_1=None,
) -> None:
    """Watch two agents play a full game."""
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("Ticket to Ride Europe — Spectator")
    clock = pygame.time.Clock()

    policy_0 = policy_0 or random_policy
    policy_1 = policy_1 or random_policy
    policies = [policy_0, policy_1]

    game = GameState(seed=seed)
    renderer = Renderer(screen)

    paused = False
    step_one = False

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return
                if event.key == pygame.K_SPACE:
                    paused = not paused
                if event.key == pygame.K_RIGHT:
                    step_one = True
                if event.key == pygame.K_r:
                    game = GameState(seed=seed)
                if event.key == pygame.K_UP:
                    renderer.scroll_log(1)
                if event.key == pygame.K_DOWN:
                    renderer.scroll_log(-1)
            if event.type == pygame.MOUSEWHEEL:
                renderer.scroll_log(-event.y)

        renderer.draw(game)
        pygame.display.flip()

        if game.game_over:
            clock.tick(10)
            continue

        if paused and not step_one:
            clock.tick(30)
            continue
        step_one = False

        # Execute one action
        actions = game.get_valid_actions()
        if actions:
            policy = policies[game.current_player]
            action = policy(game, actions)
            game.step(action)

        time.sleep(speed)
        clock.tick(60)


def run_human(
    human_player: int = 0,
    seed: int | None = None,
    opponent_policy=None,
) -> None:
    """Play as a human against an AI/random opponent."""
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("Ticket to Ride Europe — Human Play")
    clock = pygame.time.Clock()

    opponent_policy = opponent_policy or random_policy
    game = GameState(seed=seed)
    renderer = Renderer(screen)
    input_handler = InputHandler(renderer)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return
                if event.key == pygame.K_r:
                    game = GameState(seed=seed)
                    continue
                if event.key == pygame.K_UP:
                    renderer.scroll_log(1)
                if event.key == pygame.K_DOWN:
                    renderer.scroll_log(-1)

                if not game.game_over and game.current_player == human_player:
                    valid = game.get_valid_actions()
                    action = input_handler.handle_key(event.key, game, valid)
                    if action is not None:
                        game.step(action)
            if event.type == pygame.MOUSEWHEEL:
                renderer.scroll_log(-event.y)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not game.game_over and game.current_player == human_player:
                    valid = game.get_valid_actions()
                    action = input_handler.handle_click(event.pos, game, valid)
                    if action is not None:
                        game.step(action)

        # Opponent's turn
        while (
            not game.game_over
            and game.current_player != human_player
        ):
            actions = game.get_valid_actions()
            if not actions:
                break
            action = opponent_policy(game, actions)
            game.step(action)

        renderer.draw(game, human_player=human_player)

        # Show color picker if active
        color_choices = input_handler.get_color_choices()
        if color_choices:
            renderer.draw_color_picker(color_choices)

        # Show destination selection UI
        if game.phase == Phase.KEEP_DESTINATIONS and game.current_player == human_player:
            selected = input_handler.get_dest_selection()
            y = WINDOW_H - 140
            font = renderer.font_small
            for i, ticket in enumerate(game.pending_destinations):
                from ttr.game.constants import CITY_NAMES
                a = CITY_NAMES[ticket.city_a]
                b = CITY_NAMES[ticket.city_b]
                marker = "[X]" if i in selected else "[ ]"
                color = (50, 150, 50) if i in selected else (30, 30, 30)
                label = font.render(f"  {marker} {i+1}: {a} - {b} ({ticket.points}pts)", True, color)
                screen.blit(label, (20, y))
                y += 16
            hint = font.render("  Press 1-3 to toggle, Enter to confirm", True, (120, 120, 120))
            screen.blit(hint, (20, y))

        pygame.display.flip()
        clock.tick(30)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ticket to Ride Europe GUI")
    parser.add_argument("--mode", choices=["spectator", "human"], default="spectator")
    parser.add_argument("--speed", type=float, default=0.3, help="Spectator delay between actions (seconds)")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--player", type=int, default=0, choices=[0, 1], help="Human player index")
    parser.add_argument("--model", type=str, default=None, help="Path to trained model .zip")
    args = parser.parse_args()

    if args.mode == "spectator":
        if args.model:
            p0 = make_model_policy(args.model, player_id=0)
            p1 = make_model_policy(args.model, player_id=1)
        else:
            p0, p1 = None, None
        run_spectator(speed=args.speed, seed=args.seed, policy_0=p0, policy_1=p1)
    else:
        opponent = make_model_policy(args.model, player_id=1) if args.model else None
        run_human(human_player=args.player, seed=args.seed, opponent_policy=opponent)


if __name__ == "__main__":
    main()
