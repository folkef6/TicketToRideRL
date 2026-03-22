"""Tests for the TTR game engine."""

import random
import pytest
from ttr.game.engine import GameState
from ttr.game.types import Phase, ActionType, CardColor, Action
from ttr.game.constants import ROUTES, INITIAL_TRAINS, INITIAL_STATIONS


class TestGameInit:
    def test_initial_state(self):
        gs = GameState(seed=0)
        assert gs.current_player == 0
        assert gs.phase == Phase.KEEP_DESTINATIONS
        assert not gs.game_over
        assert gs.is_initial_dest_selection
        for p in gs.players:
            assert p.total_cards() == 4
            assert p.trains_remaining == INITIAL_TRAINS
            assert p.stations_remaining == INITIAL_STATIONS

    def test_initial_dest_selection(self):
        gs = GameState(seed=0)
        assert gs.phase == Phase.KEEP_DESTINATIONS
        actions = gs.get_valid_actions()
        # Should have keep-destination actions for player 0
        assert all(a.type == ActionType.KEEP_DESTINATIONS for a in actions)
        # Must keep at least 2 out of 3
        for a in actions:
            assert bin(a.dest_mask).count('1') >= 2


class TestDrawCards:
    def test_draw_from_deck(self):
        gs = GameState(seed=1)
        # Complete initial dest selection
        _complete_dest_selection(gs)
        assert gs.phase == Phase.MAIN
        player = gs.players[gs.current_player]
        initial_cards = player.total_cards()
        gs.step(Action(type=ActionType.DRAW_DECK))
        assert player.total_cards() == initial_cards + 1
        assert gs.phase == Phase.DRAW_SECOND_CARD

    def test_draw_face_up(self):
        gs = GameState(seed=2)
        _complete_dest_selection(gs)
        player = gs.players[gs.current_player]
        initial_cards = player.total_cards()
        card = gs.cards.face_up[0]
        gs.step(Action(type=ActionType.DRAW_FACE_UP, face_up_slot=0))
        assert player.total_cards() == initial_cards + 1
        assert player.hand[card] >= 1

    def test_face_up_loco_ends_turn(self):
        gs = GameState(seed=3)
        _complete_dest_selection(gs)
        # Find a face-up loco or skip
        loco_slot = None
        for i, c in enumerate(gs.cards.face_up):
            if c == CardColor.LOCOMOTIVE:
                loco_slot = i
                break
        if loco_slot is not None:
            current = gs.current_player
            gs.step(Action(type=ActionType.DRAW_FACE_UP, face_up_slot=loco_slot))
            assert gs.current_player != current  # turn ended


class TestClaimRoute:
    def test_claim_simple_route(self):
        gs = GameState(seed=10)
        _complete_dest_selection(gs)
        # Give player enough cards
        player = gs.players[gs.current_player]
        player.hand[:] = 0
        player.hand[CardColor.RED] = 6
        player.hand[CardColor.LOCOMOTIVE] = 4
        # Find a short red route
        for route in ROUTES:
            if route.color == CardColor.RED and route.length <= 3 and not route.is_tunnel:
                if gs.board.can_claim(route.id, gs.current_player):
                    gs.step(Action(type=ActionType.CLAIM_ROUTE, route_id=route.id, color=CardColor.RED))
                    assert route.id in player.claimed_routes
                    assert gs.board.route_owner[route.id] == 0 or gs.board.route_owner[route.id] == 1
                    return
        pytest.skip("No suitable red route found")

    def test_double_route_2p_rule(self):
        gs = GameState(seed=5)
        _complete_dest_selection(gs)
        # Find a parallel pair
        from ttr.game.constants import _PARALLEL_PAIRS
        pair = _PARALLEL_PAIRS[0]
        route_a = ROUTES[pair[0]]
        # Claim route A as player 0
        gs.players[0].hand[:] = 0
        gs.players[0].hand[route_a.color or 0] = route_a.length
        gs.players[0].hand[CardColor.LOCOMOTIVE] = route_a.ferry_locomotives
        gs.board.claim(route_a.id, 0)
        gs.players[0].claimed_routes.append(route_a.id)
        # Route B should not be claimable
        assert not gs.board.can_claim(pair[1], 1)


class TestEndGame:
    def test_end_triggers_on_low_trains(self):
        gs = GameState(seed=20)
        _complete_dest_selection(gs)
        gs.players[0].trains_remaining = 3
        # Claim a length-1 route
        for route in ROUTES:
            if route.length == 1 and gs.board.can_claim(route.id, 0):
                color = route.color if route.color is not None else CardColor.RED
                gs.players[0].hand[color] = 5
                gs.step(Action(type=ActionType.CLAIM_ROUTE, route_id=route.id, color=color))
                assert gs.end_triggered
                return
        pytest.skip("No length-1 route available")


class TestRandomGames:
    @pytest.mark.parametrize("seed", range(20))
    def test_random_game_completes(self, seed):
        gs = GameState(seed=seed)
        steps = 0
        while not gs.is_terminal() and steps < 1000:
            actions = gs.get_valid_actions()
            assert len(actions) > 0, f"No valid actions at step {steps}"
            action = random.choice(actions)
            gs.step(action)
            steps += 1
        assert gs.game_over
        assert steps < 1000


def _complete_dest_selection(gs: GameState) -> None:
    """Helper: complete initial destination selection for both players."""
    while gs.phase == Phase.KEEP_DESTINATIONS:
        actions = gs.get_valid_actions()
        # Keep all destinations
        best = max(actions, key=lambda a: bin(a.dest_mask).count('1'))
        gs.step(best)
