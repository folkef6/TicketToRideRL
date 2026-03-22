"""Tests for scoring logic."""

import pytest
from ttr.game.scoring import (
    cities_connected,
    compute_longest_route,
    compute_final_scores,
    build_adjacency,
)
from ttr.game.board import Board
from ttr.game.player import PlayerState
from ttr.game.constants import ROUTES, ROUTE_POINTS
from ttr.game.engine import GameState
import random


class TestConnectivity:
    def test_directly_connected(self):
        board = Board()
        route = ROUTES[0]  # Edinburgh - London
        board.claim(route.id, 0)
        adj = build_adjacency(0, board)
        assert cities_connected(route.city_a, route.city_b, adj)

    def test_not_connected(self):
        board = Board()
        adj = build_adjacency(0, board)
        assert not cities_connected(0, 22, adj)  # Edinburgh - Athina

    def test_transitive_connection(self):
        board = Board()
        # Claim Edinburgh-London and London-Dieppe
        board.claim(0, 0)  # Edinburgh-London
        board.claim(2, 0)  # London-Dieppe
        adj = build_adjacency(0, board)
        assert cities_connected(
            ROUTES[0].city_a,
            ROUTES[2].city_b,
            adj,
        )


class TestLongestRoute:
    def test_empty(self):
        board = Board()
        assert compute_longest_route(0, board) == 0

    def test_single_route(self):
        board = Board()
        board.claim(0, 0)  # Edinburgh-London, length 4
        assert compute_longest_route(0, board) == 4

    def test_chain(self):
        board = Board()
        # Claim a chain: Edinburgh-London (4) + London-Dieppe (2)
        board.claim(0, 0)
        board.claim(2, 0)
        longest = compute_longest_route(0, board)
        assert longest == 6  # 4 + 2


class TestRoutePoints:
    def test_scoring_table(self):
        for length, points in ROUTE_POINTS.items():
            assert points > 0


class TestFullGame:
    def test_final_scores_computed(self):
        gs = GameState(seed=42)
        steps = 0
        while not gs.is_terminal() and steps < 500:
            actions = gs.get_valid_actions()
            gs.step(random.choice(actions))
            steps += 1
        assert gs.game_over
        scores = gs.get_final_scores()
        assert len(scores) == 2
