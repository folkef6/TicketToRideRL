"""Board state: route ownership and double-route rules."""

from __future__ import annotations

import numpy as np

from .constants import NUM_ROUTES, ROUTES


class Board:
    """Tracks which routes are claimed and by whom."""

    def __init__(self) -> None:
        # -1 = unclaimed, 0 = player 0, 1 = player 1
        self.route_owner = np.full(NUM_ROUTES, -1, dtype=np.int8)

    def is_claimed(self, route_id: int) -> bool:
        return self.route_owner[route_id] != -1

    def claim(self, route_id: int, player_id: int) -> None:
        self.route_owner[route_id] = player_id

    def can_claim(self, route_id: int, player_id: int) -> bool:
        """Check if a route can be claimed (not already taken, double-route 2p rule)."""
        if self.is_claimed(route_id):
            return False
        route = ROUTES[route_id]
        # 2-player double-route rule: only one of a parallel pair can be claimed total
        if route.parallel_id is not None:
            if self.is_claimed(route.parallel_id):
                return False
        return True

    def player_routes(self, player_id: int) -> list[int]:
        """Return list of route IDs owned by the given player."""
        return [i for i in range(NUM_ROUTES) if self.route_owner[i] == player_id]

    def ownership_vector(self, perspective: int) -> np.ndarray:
        """Return route ownership from a player's perspective.
        0=unclaimed, 1=mine, 2=theirs."""
        result = np.zeros(NUM_ROUTES, dtype=np.float32)
        for i in range(NUM_ROUTES):
            if self.route_owner[i] == perspective:
                result[i] = 1.0
            elif self.route_owner[i] != -1:
                result[i] = 2.0
        return result
