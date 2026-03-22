"""Observation vector construction for the TTR environment."""

from __future__ import annotations

import numpy as np

from ttr.game.engine import GameState
from ttr.game.types import Phase
from ttr.game.constants import NUM_ROUTES, NUM_DEST_TICKETS, NUM_LONG_DEST_TICKETS, INITIAL_TRAINS, INITIAL_STATIONS, TOTAL_CARDS

TOTAL_DEST_TICKETS = NUM_DEST_TICKETS + NUM_LONG_DEST_TICKETS


def build_observation(game: GameState, player_id: int = 0) -> np.ndarray:
    """Build the observation vector for the given player.

    Layout (see plan for details):
      my_hand:              9
      face_up_cards:        9
      deck_size:            1
      route_ownership:      NUM_ROUTES
      my_trains:            1
      opp_trains:           1
      my_stations:          1
      opp_stations:         1
      my_dest_tickets:      NUM_DEST_TICKETS
      my_score:             1
      opp_score:            1
      phase:                4
      opp_hand_size:        1
      pending_destinations: NUM_DEST_TICKETS
      turns_to_end:         1
    """
    player = game.players[player_id]
    opponent = game.players[1 - player_id]

    parts: list[np.ndarray] = []

    # My hand (9 values, normalized)
    parts.append(player.hand.astype(np.float32) / 12.0)

    # Face-up cards (9 values, normalized)
    parts.append(game.cards.face_up_counts().astype(np.float32) / 5.0)

    # Deck size (normalized)
    parts.append(np.array([game.cards.deck_size() / TOTAL_CARDS], dtype=np.float32))

    # Route ownership from player's perspective
    parts.append(game.board.ownership_vector(player_id) / 2.0)

    # Train counts (normalized)
    parts.append(np.array([player.trains_remaining / INITIAL_TRAINS], dtype=np.float32))
    parts.append(np.array([opponent.trains_remaining / INITIAL_TRAINS], dtype=np.float32))

    # Station counts (normalized)
    parts.append(np.array([player.stations_remaining / INITIAL_STATIONS], dtype=np.float32))
    parts.append(np.array([opponent.stations_remaining / INITIAL_STATIONS], dtype=np.float32))

    # My destination tickets (binary vector)
    dest_vec = np.zeros(TOTAL_DEST_TICKETS, dtype=np.float32)
    for ticket in player.dest_tickets:
        dest_vec[ticket.id] = 1.0
    parts.append(dest_vec)

    # Scores (normalized roughly)
    parts.append(np.array([player.points / 100.0], dtype=np.float32))
    parts.append(np.array([opponent.points / 100.0], dtype=np.float32))

    # Phase (one-hot, 4 values)
    phase_vec = np.zeros(4, dtype=np.float32)
    phase_vec[int(game.phase)] = 1.0
    parts.append(phase_vec)

    # Opponent hand size
    parts.append(np.array([opponent.total_cards() / 40.0], dtype=np.float32))

    # Pending destinations (binary vector during keep-destinations phase)
    pending_vec = np.zeros(TOTAL_DEST_TICKETS, dtype=np.float32)
    if game.phase == Phase.KEEP_DESTINATIONS and game.current_player == player_id:
        for ticket in game.pending_destinations:
            pending_vec[ticket.id] = 1.0
    parts.append(pending_vec)

    # Turns to end (0 if not triggered, else decreasing)
    if game.end_triggered:
        parts.append(np.array([max(0, (game.num_players - game.final_turn_count)) / 2.0], dtype=np.float32))
    else:
        parts.append(np.array([1.0], dtype=np.float32))

    return np.concatenate(parts)


def observation_size() -> int:
    """Return the total observation vector size."""
    return (
        9          # my_hand
        + 9        # face_up_cards
        + 1        # deck_size
        + NUM_ROUTES  # route_ownership
        + 2        # trains
        + 2        # stations
        + TOTAL_DEST_TICKETS  # my_dest_tickets
        + 2        # scores
        + 4        # phase
        + 1        # opp_hand_size
        + TOTAL_DEST_TICKETS  # pending_destinations
        + 1        # turns_to_end
    )
