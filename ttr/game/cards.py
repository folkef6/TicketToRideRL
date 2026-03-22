"""Train card deck management: draw pile, discard, face-up display."""

from __future__ import annotations

import numpy as np
from numpy.random import Generator

from .types import CardColor
from .constants import CARDS_PER_COLOR, LOCOMOTIVE_COUNT, FACE_UP_COUNT


def make_deck(rng: Generator) -> list[int]:
    """Create and shuffle a full 110-card deck. Cards represented as CardColor ints."""
    deck: list[int] = []
    for color in range(8):  # 8 normal colors
        deck.extend([color] * CARDS_PER_COLOR)
    deck.extend([CardColor.LOCOMOTIVE] * LOCOMOTIVE_COUNT)
    rng.shuffle(deck)
    return deck


class CardSupply:
    """Manages the draw pile, discard pile, and 5 face-up cards."""

    def __init__(self, rng: Generator) -> None:
        self.rng = rng
        self.draw_pile: list[int] = make_deck(rng)
        self.discard: list[int] = []
        self.face_up: list[int] = []
        self._fill_face_up()

    def _fill_face_up(self) -> None:
        """Fill face-up slots to 5 (or as many as available), enforcing 3-loco rule."""
        while len(self.face_up) < FACE_UP_COUNT and self._cards_available():
            self.face_up.append(self._draw_one_raw())
        self._check_three_loco_rule()

    def _check_three_loco_rule(self) -> None:
        """If 3+ locos in face-up, discard all and redraw (repeat until ok or no cards)."""
        max_attempts = 3
        attempts = 0
        while (
            self.face_up.count(CardColor.LOCOMOTIVE) >= 3
            and self._cards_available()
            and attempts < max_attempts
        ):
            attempts += 1
            self.discard.extend(self.face_up)
            self.face_up.clear()
            while len(self.face_up) < FACE_UP_COUNT and self._cards_available():
                self.face_up.append(self._draw_one_raw())
        # If still 3+ locos after max attempts, leave them — remaining cards are mostly locos

    def _cards_available(self) -> bool:
        return len(self.draw_pile) > 0 or len(self.discard) > 0

    def _reshuffle_if_needed(self) -> None:
        if len(self.draw_pile) == 0 and len(self.discard) > 0:
            self.draw_pile = self.discard
            self.discard = []
            self.rng.shuffle(self.draw_pile)

    def _draw_one_raw(self) -> int:
        """Draw one card from draw pile, reshuffling discard if needed."""
        self._reshuffle_if_needed()
        if len(self.draw_pile) == 0:
            raise RuntimeError("No cards available to draw")
        return self.draw_pile.pop()

    def draw_from_deck(self) -> int | None:
        """Draw a card from the deck. Returns None if no cards available."""
        if not self._cards_available():
            return None
        card = self._draw_one_raw()
        return card

    def draw_face_up(self, slot: int) -> int | None:
        """Take a face-up card at given slot. Replaces it and checks 3-loco rule.
        Returns the card color, or None if slot is empty/invalid."""
        if slot < 0 or slot >= len(self.face_up):
            return None
        card = self.face_up[slot]
        # Replace the card
        if self._cards_available():
            self.face_up[slot] = self._draw_one_raw()
        else:
            self.face_up.pop(slot)
        self._check_three_loco_rule()
        return card

    def add_to_discard(self, cards: list[int]) -> None:
        self.discard.extend(cards)

    def deck_size(self) -> int:
        return len(self.draw_pile) + len(self.discard)

    def face_up_has_loco(self, slot: int) -> bool:
        return 0 <= slot < len(self.face_up) and self.face_up[slot] == CardColor.LOCOMOTIVE

    def can_draw(self) -> bool:
        return self._cards_available() or len(self.face_up) > 0

    def face_up_counts(self) -> np.ndarray:
        """Return a 9-element array of face-up card counts per color."""
        counts = np.zeros(9, dtype=np.int32)
        for c in self.face_up:
            counts[c] += 1
        return counts
