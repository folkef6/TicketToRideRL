"""Core game engine for Ticket to Ride Europe (2 players)."""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from numpy.random import Generator, default_rng

from .types import CardColor, Phase, ActionType, Action, Route, DestTicket
from .constants import (
    ROUTES, DEST_TICKETS, LONG_DEST_TICKETS, NUM_ROUTES, NUM_DEST_TICKETS,
    ROUTE_POINTS, CITY_NAMES,
    INITIAL_HAND_SIZE, INITIAL_DEST_DRAW, DEST_DRAW_COUNT,
    DEST_KEEP_MIN_INITIAL, DEST_KEEP_MIN,
    FACE_UP_COUNT, END_GAME_TRAIN_THRESHOLD,
)
from .cards import CardSupply
from .player import PlayerState
from .board import Board


class GameState:
    """Full game state and rules engine for 2-player Ticket to Ride Europe."""

    def __init__(self, seed: int | None = None) -> None:
        self.rng: Generator = default_rng(seed)
        self.num_players = 2
        self.cards = CardSupply(self.rng)
        self.board = Board()
        self.players = [PlayerState(i) for i in range(2)]
        self.station_cities: list[list[int]] = [[], []]  # cities where stations are placed

        self.current_player = 0
        self.phase = Phase.KEEP_DESTINATIONS  # start with destination selection
        self.turn_number = 0

        # End-game tracking
        self.end_triggered = False
        self.end_trigger_player: int | None = None
        self.final_turn_count = 0  # how many players have had their final turn
        self.game_over = False

        # Action log: list of (player_id, description_string)
        self.log: list[tuple[int, str]] = []

        # Pending destinations (for KEEP_DESTINATIONS phase)
        self.pending_destinations: list[DestTicket] = []
        self.is_initial_dest_selection = True  # True for game-start selection

        # Destination ticket draw pile
        self.dest_draw_pile: list[DestTicket] = list(DEST_TICKETS)
        self.rng.shuffle(self.dest_draw_pile)

        # Deal initial hands
        for p in self.players:
            for _ in range(INITIAL_HAND_SIZE):
                card = self.cards.draw_from_deck()
                if card is not None:
                    p.add_card(card)

        # Deal one long destination ticket to each player (mandatory, must keep)
        long_pile = list(LONG_DEST_TICKETS)
        self.rng.shuffle(long_pile)
        for p in self.players:
            ticket = long_pile.pop()
            p.dest_tickets.append(ticket)
            self.log.append((p.player_id, f"Received long ticket: {CITY_NAMES[ticket.city_a]}-{CITY_NAMES[ticket.city_b]} ({ticket.points}pts)"))

        # Deal initial destinations to player 0
        self._deal_destinations(INITIAL_DEST_DRAW)

    def _deal_destinations(self, count: int) -> None:
        """Deal destination tickets to current player."""
        drawn: list[DestTicket] = []
        for _ in range(count):
            if self.dest_draw_pile:
                drawn.append(self.dest_draw_pile.pop())
        self.pending_destinations = drawn
        self.phase = Phase.KEEP_DESTINATIONS

    def get_current_player(self) -> int:
        return self.current_player

    def is_terminal(self) -> bool:
        return self.game_over

    def get_scores(self) -> list[int]:
        """Get current scores (route points only until game end)."""
        return [p.points for p in self.players]

    def get_final_scores(self) -> list[int]:
        """Compute full final scores including destinations, stations, longest route."""
        from .scoring import compute_final_scores
        return compute_final_scores(self.players, self.board, self.station_cities)

    def get_valid_actions(self) -> list[Action]:
        """Return all valid actions for the current player."""
        if self.game_over:
            return []

        player = self.players[self.current_player]
        actions: list[Action] = []

        if self.phase == Phase.KEEP_DESTINATIONS:
            actions.extend(self._valid_keep_destinations())
        elif self.phase == Phase.DRAW_FIRST_CARD:
            actions.extend(self._valid_draw_card(first=True))
        elif self.phase == Phase.DRAW_SECOND_CARD:
            actions.extend(self._valid_draw_card(first=False))
        elif self.phase == Phase.MAIN:
            actions.extend(self._valid_draw_card(first=True))
            actions.extend(self._valid_claim_route())
            actions.extend(self._valid_place_station())
            actions.extend(self._valid_draw_destinations())

        return actions

    def _valid_keep_destinations(self) -> list[Action]:
        """Generate all valid destination-keeping bitmasks."""
        n = len(self.pending_destinations)
        if n == 0:
            return []

        min_keep = DEST_KEEP_MIN_INITIAL if self.is_initial_dest_selection else DEST_KEEP_MIN
        actions = []
        for mask in range(1, 1 << n):
            if bin(mask).count('1') >= min_keep:
                actions.append(Action(type=ActionType.KEEP_DESTINATIONS, dest_mask=mask))
        return actions

    def _valid_draw_card(self, first: bool) -> list[Action]:
        """Valid card draw actions."""
        actions = []
        # Face-up cards
        for i, card in enumerate(self.cards.face_up):
            if not first and card == CardColor.LOCOMOTIVE:
                continue  # Can't take face-up loco as second draw
            actions.append(Action(type=ActionType.DRAW_FACE_UP, face_up_slot=i))
        # Draw from deck
        if self.cards._cards_available():
            actions.append(Action(type=ActionType.DRAW_DECK))
        return actions

    def _valid_claim_route(self) -> list[Action]:
        """Valid route claiming actions."""
        player = self.players[self.current_player]
        actions = []

        for route in ROUTES:
            if not self.board.can_claim(route.id, self.current_player):
                continue
            if player.trains_remaining < route.length:
                continue

            # Determine which colors can pay for this route
            if route.color is not None:
                # Colored route: must use that color (+ locos)
                colors_to_try = [route.color]
            else:
                # Gray route: can use any single color (+ locos)
                colors_to_try = list(range(8))

            for color in colors_to_try:
                if route.color is None and player.hand[color] == 0:
                    continue
                can_pay, _, _ = player.can_pay(color, route.length, route.ferry_locomotives)
                if can_pay:
                    actions.append(Action(
                        type=ActionType.CLAIM_ROUTE,
                        route_id=route.id,
                        color=CardColor(color),
                    ))

            # Can also pay entirely with locomotives
            can_pay_loco, _, _ = player.can_pay(
                CardColor.LOCOMOTIVE, route.length, route.ferry_locomotives
            )
            if can_pay_loco and route.color is None:
                # Only add loco-only for gray routes (colored routes already try color+loco)
                actions.append(Action(
                    type=ActionType.CLAIM_ROUTE,
                    route_id=route.id,
                    color=CardColor.LOCOMOTIVE,
                ))

        return actions

    def _valid_place_station(self) -> list[Action]:
        """Valid station placement actions."""
        player = self.players[self.current_player]
        if not player.can_place_station():
            return []

        actions = []
        cost = player.station_cost()

        # Find cities where stations can be placed (cities with at least one opponent route)
        # Actually stations can be placed at any city not already having a station
        used_cities = set()
        for sc_list in self.station_cities:
            used_cities.update(sc_list)

        for city_id in range(len(ROUTES)):
            pass  # wrong iteration

        from .constants import NUM_CITIES
        for city_id in range(NUM_CITIES):
            if city_id in used_cities:
                continue
            # Check if player can pay with any color
            for c in range(9):
                if c == CardColor.LOCOMOTIVE:
                    if player.hand[c] >= cost:
                        actions.append(Action(
                            type=ActionType.PLACE_STATION,
                            city_id=city_id,
                            color=CardColor.LOCOMOTIVE,
                        ))
                else:
                    color_avail = int(player.hand[c])
                    loco_avail = int(player.hand[CardColor.LOCOMOTIVE])
                    if color_avail + loco_avail >= cost and (color_avail >= 1 or cost <= loco_avail):
                        actions.append(Action(
                            type=ActionType.PLACE_STATION,
                            city_id=city_id,
                            color=CardColor(c),
                        ))
        return actions

    def _valid_draw_destinations(self) -> list[Action]:
        if self.dest_draw_pile:
            return [Action(type=ActionType.DRAW_DESTINATIONS)]
        return []

    def step(self, action: Action) -> None:
        """Execute an action, advancing the game state."""
        assert not self.game_over, "Game is already over"

        if action.type == ActionType.KEEP_DESTINATIONS:
            self._do_keep_destinations(action)
        elif action.type == ActionType.DRAW_FACE_UP:
            self._do_draw_face_up(action)
        elif action.type == ActionType.DRAW_DECK:
            self._do_draw_deck(action)
        elif action.type == ActionType.CLAIM_ROUTE:
            self._do_claim_route(action)
        elif action.type == ActionType.PLACE_STATION:
            self._do_place_station(action)
        elif action.type == ActionType.DRAW_DESTINATIONS:
            self._do_draw_destinations(action)
        else:
            raise ValueError(f"Unknown action type: {action.type}")

    def _do_keep_destinations(self, action: Action) -> None:
        player = self.players[self.current_player]
        mask = action.dest_mask
        kept = []
        for i, ticket in enumerate(self.pending_destinations):
            if mask & (1 << i):
                player.dest_tickets.append(ticket)
                kept.append(f"{CITY_NAMES[ticket.city_a]}-{CITY_NAMES[ticket.city_b]}")
            else:
                self.dest_draw_pile.insert(0, ticket)
        self.log.append((self.current_player, f"Kept {len(kept)} tickets: {', '.join(kept)}"))
        self.pending_destinations = []

        if self.is_initial_dest_selection:
            if self.current_player == 0:
                # Player 1 needs to do initial selection too
                self.current_player = 1
                self._deal_destinations(INITIAL_DEST_DRAW)
                return
            else:
                # Both players done with initial selection
                self.is_initial_dest_selection = False
                self.current_player = 0
                self.phase = Phase.MAIN
                return

        # Normal destination draw during game
        self.phase = Phase.MAIN
        self._end_turn()

    def _do_draw_face_up(self, action: Action) -> None:
        player = self.players[self.current_player]
        slot = action.face_up_slot
        is_loco = self.cards.face_up_has_loco(slot)
        card = self.cards.draw_face_up(slot)
        if card is None:
            return

        player.add_card(card)
        self.log.append((self.current_player, f"Drew face-up {CardColor(card).name}"))

        if self.phase == Phase.MAIN or self.phase == Phase.DRAW_FIRST_CARD:
            if is_loco:
                # Taking a face-up locomotive uses entire turn
                self._end_turn()
            else:
                self.phase = Phase.DRAW_SECOND_CARD
        elif self.phase == Phase.DRAW_SECOND_CARD:
            self._end_turn()

    def _do_draw_deck(self, action: Action) -> None:
        player = self.players[self.current_player]
        card = self.cards.draw_from_deck()
        if card is not None:
            player.add_card(card)
            self.log.append((self.current_player, f"Drew from deck"))

        if self.phase == Phase.MAIN or self.phase == Phase.DRAW_FIRST_CARD:
            self.phase = Phase.DRAW_SECOND_CARD
        elif self.phase == Phase.DRAW_SECOND_CARD:
            self._end_turn()

    def _do_claim_route(self, action: Action) -> None:
        player = self.players[self.current_player]
        route = ROUTES[action.route_id]
        color = action.color

        can_pay, color_used, loco_used = player.can_pay(color, route.length, route.ferry_locomotives)
        assert can_pay, f"Player cannot pay for route {route.id} with {color}"

        # Handle tunnel: reveal 3 cards, check for extra cost
        extra_cost = 0
        if route.is_tunnel:
            extra_cost = self._resolve_tunnel(color, route)
            if extra_cost > 0:
                # Check if player can pay the extra
                remaining_color = int(player.hand[color]) - color_used
                remaining_loco = int(player.hand[CardColor.LOCOMOTIVE]) - loco_used
                extra_color = min(remaining_color, extra_cost)
                extra_loco = extra_cost - extra_color
                if extra_loco > remaining_loco:
                    # Can't pay extra — tunnel attempt fails, turn ends
                    ca, cb = CITY_NAMES[route.city_a], CITY_NAMES[route.city_b]
                    self.log.append((self.current_player, f"Tunnel failed: {ca}-{cb} (+{extra_cost} extra)"))
                    self._end_turn()
                    return
                color_used += extra_color
                loco_used += extra_loco

        # Pay cards
        if color == CardColor.LOCOMOTIVE:
            discarded = player.pay_cards(CardColor.LOCOMOTIVE, 0, color_used + loco_used)
        else:
            discarded = player.pay_cards(color, color_used, loco_used)
        self.cards.add_to_discard(discarded)

        # Claim route
        self.board.claim(route.id, self.current_player)
        player.claimed_routes.append(route.id)
        player.trains_remaining -= route.length
        pts = ROUTE_POINTS.get(route.length, 0)
        player.points += pts
        ca, cb = CITY_NAMES[route.city_a], CITY_NAMES[route.city_b]
        self.log.append((self.current_player, f"Claimed {ca}-{cb} (len {route.length}, +{pts}pts)"))

        # Check end-game trigger
        if player.trains_remaining <= END_GAME_TRAIN_THRESHOLD and not self.end_triggered:
            self.end_triggered = True
            self.end_trigger_player = self.current_player

        self._end_turn()

    def _resolve_tunnel(self, color: CardColor, route: Route) -> int:
        """Reveal 3 cards for tunnel. Returns extra cards needed."""
        extra = 0
        revealed: list[int] = []
        for _ in range(3):
            card = self.cards.draw_from_deck()
            if card is None:
                break
            revealed.append(card)
            if card == CardColor.LOCOMOTIVE or card == color:
                extra += 1
        self.cards.add_to_discard(revealed)
        return extra

    def _do_place_station(self, action: Action) -> None:
        player = self.players[self.current_player]
        discarded = player.pay_station(action.color)
        self.cards.add_to_discard(discarded)
        self.station_cities[self.current_player].append(action.city_id)
        self.log.append((self.current_player, f"Placed station at {CITY_NAMES[action.city_id]}"))
        self._end_turn()

    def _do_draw_destinations(self, action: Action) -> None:
        self.log.append((self.current_player, "Drew destination tickets"))
        self._deal_destinations(DEST_DRAW_COUNT)

    def _end_turn(self) -> None:
        """End current player's turn, advance to next player."""
        if self.end_triggered:
            self.final_turn_count += 1
            # Each player gets one more turn after trigger
            if self.final_turn_count >= self.num_players:
                self.game_over = True
                return

        self.current_player = 1 - self.current_player
        self.phase = Phase.MAIN
        self.turn_number += 1

        # Check if current player has any valid actions at all
        # (edge case: no cards to draw, no routes to claim)
        if not self.get_valid_actions():
            # Player must pass — skip their turn
            self._end_turn()

    def copy(self) -> GameState:
        """Create a deep copy of the game state."""
        import copy
        return copy.deepcopy(self)
