"""Player state for Ticket to Ride Europe."""

from __future__ import annotations

import numpy as np

from .types import CardColor, DestTicket
from .constants import INITIAL_TRAINS, INITIAL_STATIONS


class PlayerState:
    """Tracks a single player's hand, trains, stations, tickets, and points."""

    def __init__(self, player_id: int) -> None:
        self.player_id = player_id
        self.hand = np.zeros(9, dtype=np.int32)  # card counts per CardColor
        self.trains_remaining = INITIAL_TRAINS
        self.stations_remaining = INITIAL_STATIONS
        self.stations_placed = 0  # 0, 1, 2, or 3
        self.dest_tickets: list[DestTicket] = []
        self.claimed_routes: list[int] = []  # route IDs
        self.points = 0

    def total_cards(self) -> int:
        return int(self.hand.sum())

    def add_card(self, color: int) -> None:
        self.hand[color] += 1

    def can_pay(self, color: CardColor | None, length: int, ferry_locos: int) -> tuple[bool, int, int]:
        """Check if player can pay for a route.

        For gray routes, color should be the chosen payment color.
        Returns (can_pay, color_cards_used, locos_used).
        Uses minimum locomotives possible.
        """
        if color is None:
            return False, 0, 0

        locos_available = int(self.hand[CardColor.LOCOMOTIVE])

        if color == CardColor.LOCOMOTIVE:
            # Paying entirely with locomotives
            if locos_available >= length:
                return True, 0, length
            return False, 0, 0

        color_available = int(self.hand[color])

        # Must use at least ferry_locos locomotives
        min_locos = ferry_locos

        # Remaining needed from color cards or additional locos
        remaining = length - min_locos
        color_used = min(color_available, remaining)
        extra_locos = remaining - color_used
        total_locos = min_locos + extra_locos

        if total_locos <= locos_available:
            return True, color_used, total_locos
        return False, 0, 0

    def pay_cards(self, color: int, color_count: int, loco_count: int) -> list[int]:
        """Remove cards from hand. Returns list of card ints for discard."""
        discarded: list[int] = []
        self.hand[color] -= color_count
        discarded.extend([color] * color_count)
        self.hand[CardColor.LOCOMOTIVE] -= loco_count
        discarded.extend([CardColor.LOCOMOTIVE] * loco_count)
        return discarded

    def station_cost(self) -> int:
        """Number of same-color cards needed for next station: 1, 2, or 3."""
        return self.stations_placed + 1

    def can_place_station(self) -> bool:
        """Check if the player can afford any station placement."""
        if self.stations_remaining <= 0:
            return False
        cost = self.station_cost()
        # Can pay with any single color (including locos)
        for c in range(9):
            if self.hand[c] >= cost:
                return True
        # Can also mix color + locos
        if cost > 1:
            for c in range(8):
                if self.hand[c] + self.hand[CardColor.LOCOMOTIVE] >= cost and self.hand[c] >= 1:
                    return True
            # All locos
            if self.hand[CardColor.LOCOMOTIVE] >= cost:
                return True
        return False

    def pay_station(self, color: int) -> list[int]:
        """Pay for a station with cards of the given color (+ locos if needed).
        Returns discarded cards."""
        cost = self.station_cost()
        color_available = int(self.hand[color]) if color != CardColor.LOCOMOTIVE else 0
        color_used = min(color_available, cost)
        loco_used = cost - color_used

        if color == CardColor.LOCOMOTIVE:
            color_used = 0
            loco_used = cost

        discarded = self.pay_cards(color, color_used, loco_used)
        self.stations_remaining -= 1
        self.stations_placed += 1
        return discarded
