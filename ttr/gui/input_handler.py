"""Mouse click → game action translation for human play mode."""

from __future__ import annotations

import pygame

from ttr.game.engine import GameState
from ttr.game.types import Action, ActionType, CardColor, Phase
from ttr.game.constants import ROUTES, CITY_NAMES, NUM_ROUTES
from .map_data import CITY_POSITIONS
from .renderer import Renderer, CITY_RADIUS


def find_clicked_city(pos: tuple[int, int]) -> int | None:
    """Return city ID if click is near a city, else None."""
    mx, my = pos
    for city_id, (cx, cy) in enumerate(CITY_POSITIONS):
        dist_sq = (mx - cx) ** 2 + (my - cy) ** 2
        if dist_sq <= (CITY_RADIUS + 6) ** 2:
            return city_id
    return None


def find_clicked_route(pos: tuple[int, int]) -> int | None:
    """Return route ID if click is near a route segment, else None."""
    mx, my = pos
    best_route = None
    best_dist = 15  # max click distance from route line

    for route in ROUTES:
        ax, ay = CITY_POSITIONS[route.city_a]
        bx, by = CITY_POSITIONS[route.city_b]

        # Point-to-line-segment distance
        dx, dy = bx - ax, by - ay
        length_sq = dx * dx + dy * dy
        if length_sq == 0:
            continue
        t = max(0, min(1, ((mx - ax) * dx + (my - ay) * dy) / length_sq))
        px, py = ax + t * dx, ay + t * dy
        dist = ((mx - px) ** 2 + (my - py) ** 2) ** 0.5

        if dist < best_dist:
            best_dist = dist
            best_route = route.id

    return best_route


class InputHandler:
    """Translates mouse/keyboard input into game actions."""

    def __init__(self, renderer: Renderer) -> None:
        self.renderer = renderer
        self._selected_route: int | None = None
        self._dest_selection: set[int] = set()  # indices of selected pending dests
        # Color picker state: list of Action options for a clicked route/city
        self._color_choices: list[Action] = []

    def handle_click(
        self, pos: tuple[int, int], game: GameState, valid_actions: list[Action]
    ) -> Action | None:
        """Process a mouse click and return a matching valid action, or None."""

        # If color picker is open, check if a color was clicked
        if self._color_choices:
            rects = self.renderer.get_color_picker_rects(len(self._color_choices))
            for i, rect in enumerate(rects):
                if rect.collidepoint(pos):
                    action = self._color_choices[i]
                    self._color_choices = []
                    return action
            # Clicked elsewhere — dismiss the picker
            self._color_choices = []
            return None

        if game.phase == Phase.KEEP_DESTINATIONS:
            return None  # Handled by keyboard

        # Check face-up card clicks
        face_up_rects = self.renderer.get_face_up_rects()
        for i, rect in enumerate(face_up_rects):
            if rect.collidepoint(pos):
                action = Action(type=ActionType.DRAW_FACE_UP, face_up_slot=i)
                if action in valid_actions:
                    return action
                # Maybe it's valid with a different slot check
                for va in valid_actions:
                    if va.type == ActionType.DRAW_FACE_UP and va.face_up_slot == i:
                        return va
                return None

        # Check deck click
        deck_rect = self.renderer.get_deck_rect()
        if deck_rect.collidepoint(pos):
            for va in valid_actions:
                if va.type == ActionType.DRAW_DECK:
                    return va
            return None

        # Check draw tickets button click
        tickets_rect = self.renderer.get_tickets_rect()
        if tickets_rect.collidepoint(pos):
            for va in valid_actions:
                if va.type == ActionType.DRAW_DESTINATIONS:
                    return va
            return None

        # Check route click
        route_id = find_clicked_route(pos)
        if route_id is not None:
            # Collect all valid claim actions for this route (and parallel)
            choices = [
                va for va in valid_actions
                if va.type == ActionType.CLAIM_ROUTE and va.route_id == route_id
            ]
            # Also check parallel route
            route = ROUTES[route_id]
            if route.parallel_id is not None and not choices:
                choices = [
                    va for va in valid_actions
                    if va.type == ActionType.CLAIM_ROUTE and va.route_id == route.parallel_id
                ]

            if len(choices) == 1:
                return choices[0]
            elif len(choices) > 1:
                self._color_choices = choices
                return None  # Wait for color picker click
            return None

        # Check city click for station placement
        city_id = find_clicked_city(pos)
        if city_id is not None:
            choices = [
                va for va in valid_actions
                if va.type == ActionType.PLACE_STATION and va.city_id == city_id
            ]
            if len(choices) == 1:
                return choices[0]
            elif len(choices) > 1:
                self._color_choices = choices
                return None
            return None

        return None

    def get_color_choices(self) -> list[Action]:
        """Current color picker choices (for rendering)."""
        return self._color_choices

    def handle_key(
        self, key: int, game: GameState, valid_actions: list[Action]
    ) -> Action | None:
        """Process a keypress. Used for destination selection and draw destinations."""

        if game.phase == Phase.KEEP_DESTINATIONS:
            n = len(game.pending_destinations)
            # Toggle destination with number keys 1-3
            if pygame.K_1 <= key <= pygame.K_3:
                idx = key - pygame.K_1
                if idx < n:
                    if idx in self._dest_selection:
                        self._dest_selection.discard(idx)
                    else:
                        self._dest_selection.add(idx)
                return None

            # Confirm with Enter
            if key == pygame.K_RETURN and self._dest_selection:
                mask = 0
                for idx in self._dest_selection:
                    mask |= (1 << idx)
                action = Action(type=ActionType.KEEP_DESTINATIONS, dest_mask=mask)
                if action in valid_actions:
                    self._dest_selection.clear()
                    return action
                return None

        # 'd' key to draw destinations
        if key == pygame.K_d:
            for va in valid_actions:
                if va.type == ActionType.DRAW_DESTINATIONS:
                    return va

        return None

    def get_dest_selection(self) -> set[int]:
        """Current destination selection state (for rendering highlights)."""
        return self._dest_selection
