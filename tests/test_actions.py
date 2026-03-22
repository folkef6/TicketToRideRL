"""Tests for action encoding/decoding."""

import pytest
from ttr.env.actions import (
    encode_action, decode_action, compute_action_mask,
    ACTION_SPACE_SIZE, FACE_UP_START, DRAW_DECK,
    CLAIM_ROUTE_START, STATION_START, DRAW_DEST, KEEP_DEST_START,
)
from ttr.game.types import Action, ActionType, CardColor
from ttr.game.engine import GameState


class TestEncoding:
    def test_draw_face_up_roundtrip(self):
        game = GameState(seed=0)
        for slot in range(5):
            action = Action(type=ActionType.DRAW_FACE_UP, face_up_slot=slot)
            idx = encode_action(action)
            assert idx == FACE_UP_START + slot

    def test_draw_deck(self):
        action = Action(type=ActionType.DRAW_DECK)
        assert encode_action(action) == DRAW_DECK

    def test_claim_route_encoding(self):
        action = Action(type=ActionType.CLAIM_ROUTE, route_id=5, color=CardColor.RED)
        idx = encode_action(action)
        expected = CLAIM_ROUTE_START + 5 * 9 + int(CardColor.RED)
        assert idx == expected

    def test_keep_destinations_encoding(self):
        for mask in range(1, 8):
            action = Action(type=ActionType.KEEP_DESTINATIONS, dest_mask=mask)
            idx = encode_action(action)
            assert idx == KEEP_DEST_START + mask - 1


class TestMask:
    def test_mask_has_valid_actions(self):
        game = GameState(seed=0)
        mask = compute_action_mask(game)
        assert mask.sum() > 0
        # During initial dest selection, only keep-dest actions valid
        assert mask[:KEEP_DEST_START].sum() == 0

    def test_mask_size(self):
        game = GameState(seed=0)
        mask = compute_action_mask(game)
        assert len(mask) == ACTION_SPACE_SIZE
