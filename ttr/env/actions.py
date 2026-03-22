"""Action encoding/decoding and mask computation for the TTR environment.

Action space layout — Discrete(969):
  0–4:     Draw face-up card at slot i (5)
  5:       Draw from deck (1)
  6–914:   Claim route: route_id * 9 + color (101 * 9 = 909)
  915–960: Place station at city i (46)
  961:     Draw destination tickets (1)
  962–968: Keep destination subset, bitmask 1–7 (7)
"""

from __future__ import annotations

import numpy as np

from ttr.game.types import CardColor, Phase, ActionType, Action
from ttr.game.constants import NUM_ROUTES, NUM_CITIES
from ttr.game.engine import GameState

# Action space constants
FACE_UP_START = 0
FACE_UP_END = 5
DRAW_DECK = 5
CLAIM_ROUTE_START = 6
CLAIM_ROUTE_END = 6 + NUM_ROUTES * 9  # 6 + 846 = 852... wait NUM_ROUTES is 94

STATION_START = CLAIM_ROUTE_END
STATION_END = STATION_START + NUM_CITIES
DRAW_DEST = STATION_END
KEEP_DEST_START = DRAW_DEST + 1
KEEP_DEST_END = KEEP_DEST_START + 7

ACTION_SPACE_SIZE = KEEP_DEST_END


def encode_action(action: Action) -> int:
    """Convert a game Action to an integer action index."""
    if action.type == ActionType.DRAW_FACE_UP:
        return FACE_UP_START + action.face_up_slot
    elif action.type == ActionType.DRAW_DECK:
        return DRAW_DECK
    elif action.type == ActionType.CLAIM_ROUTE:
        return CLAIM_ROUTE_START + action.route_id * 9 + int(action.color)
    elif action.type == ActionType.PLACE_STATION:
        return STATION_START + action.city_id
    elif action.type == ActionType.DRAW_DESTINATIONS:
        return DRAW_DEST
    elif action.type == ActionType.KEEP_DESTINATIONS:
        return KEEP_DEST_START + action.dest_mask - 1  # mask 1-7 → index 0-6
    else:
        raise ValueError(f"Unknown action type: {action.type}")


def decode_action(action_idx: int, game: GameState) -> Action:
    """Convert an integer action index back to a game Action."""
    if FACE_UP_START <= action_idx < FACE_UP_END:
        return Action(type=ActionType.DRAW_FACE_UP, face_up_slot=action_idx - FACE_UP_START)
    elif action_idx == DRAW_DECK:
        return Action(type=ActionType.DRAW_DECK)
    elif CLAIM_ROUTE_START <= action_idx < CLAIM_ROUTE_END:
        offset = action_idx - CLAIM_ROUTE_START
        route_id = offset // 9
        color = CardColor(offset % 9)
        return Action(type=ActionType.CLAIM_ROUTE, route_id=route_id, color=color)
    elif STATION_START <= action_idx < STATION_END:
        city_id = action_idx - STATION_START
        # Determine the color to pay with — find a valid one
        player = game.players[game.current_player]
        cost = player.station_cost()
        pay_color = CardColor.LOCOMOTIVE  # default
        for c in range(8):
            avail = int(player.hand[c])
            loco = int(player.hand[CardColor.LOCOMOTIVE])
            if avail + loco >= cost and avail >= 1:
                pay_color = CardColor(c)
                break
        else:
            if player.hand[CardColor.LOCOMOTIVE] >= cost:
                pay_color = CardColor.LOCOMOTIVE
        return Action(type=ActionType.PLACE_STATION, city_id=city_id, color=pay_color)
    elif action_idx == DRAW_DEST:
        return Action(type=ActionType.DRAW_DESTINATIONS)
    elif KEEP_DEST_START <= action_idx < KEEP_DEST_END:
        mask = action_idx - KEEP_DEST_START + 1  # index 0-6 → mask 1-7
        return Action(type=ActionType.KEEP_DESTINATIONS, dest_mask=mask)
    else:
        raise ValueError(f"Invalid action index: {action_idx}")


def compute_action_mask(game: GameState) -> np.ndarray:
    """Compute a boolean mask over the action space for valid actions."""
    mask = np.zeros(ACTION_SPACE_SIZE, dtype=np.int8)
    for action in game.get_valid_actions():
        idx = encode_action(action)
        mask[idx] = 1
    return mask
