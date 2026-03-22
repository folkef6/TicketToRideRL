"""Pygame rendering for the TTR board, cards, and scores."""

from __future__ import annotations

import pygame
import numpy as np

from ttr.game.engine import GameState
from ttr.game.types import Action, CardColor, Phase
from ttr.game.constants import ROUTES, CITY_NAMES, NUM_ROUTES, ROUTE_POINTS
from .map_data import CITY_POSITIONS

# ── Color palette ───────────────────────────────────────────────
CARD_COLORS: dict[int, tuple[int, int, int]] = {
    CardColor.RED: (220, 50, 50),
    CardColor.ORANGE: (230, 150, 30),
    CardColor.YELLOW: (220, 210, 40),
    CardColor.GREEN: (40, 180, 60),
    CardColor.BLUE: (50, 100, 220),
    CardColor.PURPLE: (160, 50, 180),
    CardColor.BLACK: (40, 40, 40),
    CardColor.WHITE: (230, 230, 230),
    CardColor.LOCOMOTIVE: (140, 140, 140),
}

PLAYER_COLORS = [
    (30, 130, 230),   # Player 0 - blue
    (230, 70, 50),    # Player 1 - red
]

BG_COLOR = (245, 235, 220)
CITY_COLOR = (60, 60, 60)
CITY_RADIUS = 8
ROUTE_UNCLAIMED_COLOR = (180, 180, 170)
TEXT_COLOR = (30, 30, 30)
PANEL_BG = (235, 225, 210)

WINDOW_W = 1300
WINDOW_H = 800
MAP_W = 1000
PANEL_X = MAP_W + 10


class Renderer:
    """Draws the game state using Pygame."""

    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.font_small = pygame.font.SysFont("monospace", 13)
        self.font_med = pygame.font.SysFont("monospace", 16, bold=True)
        self.font_large = pygame.font.SysFont("monospace", 22, bold=True)
        self.log_scroll_offset = 0  # 0 = bottom (most recent)

    def draw(self, game: GameState, human_player: int | None = None) -> None:
        self.screen.fill(BG_COLOR)
        self._draw_routes(game)
        self._draw_cities(game)
        self._draw_panel(game, human_player)
        self._draw_face_up_cards(game)
        self._draw_game_log(game)

    def _draw_routes(self, game: GameState) -> None:
        for route in ROUTES:
            pos_a = CITY_POSITIONS[route.city_a]
            pos_b = CITY_POSITIONS[route.city_b]
            owner = int(game.board.route_owner[route.id])

            if owner >= 0:
                color = PLAYER_COLORS[owner]
                width = 5
            else:
                if route.color is not None:
                    color = CARD_COLORS[route.color]
                    # Make unclaimed colored routes slightly transparent
                    color = tuple(min(255, c + 80) for c in color)
                else:
                    color = ROUTE_UNCLAIMED_COLOR
                width = 2

            # Offset parallel routes slightly
            if route.parallel_id is not None and route.id > route.parallel_id:
                dx = pos_b[1] - pos_a[1]
                dy = -(pos_b[0] - pos_a[0])
                length = max(1, (dx * dx + dy * dy) ** 0.5)
                offset = 4
                ox, oy = int(dx / length * offset), int(dy / length * offset)
                pos_a = (pos_a[0] + ox, pos_a[1] + oy)
                pos_b = (pos_b[0] + ox, pos_b[1] + oy)

            pygame.draw.line(self.screen, color, pos_a, pos_b, width)

            # Draw tunnel markers (dashed appearance)
            if route.is_tunnel and owner < 0:
                mid_x = (pos_a[0] + pos_b[0]) // 2
                mid_y = (pos_a[1] + pos_b[1]) // 2
                pygame.draw.circle(self.screen, (200, 200, 180), (mid_x, mid_y), 3)

            # Draw ferry locomotive markers
            if route.ferry_locomotives > 0 and owner < 0:
                for f in range(route.ferry_locomotives):
                    t = (f + 1) / (route.ferry_locomotives + 1)
                    fx = int(pos_a[0] + t * (pos_b[0] - pos_a[0]))
                    fy = int(pos_a[1] + t * (pos_b[1] - pos_a[1]))
                    pygame.draw.circle(self.screen, (100, 100, 255), (fx, fy), 3)

            # Route length label at midpoint
            mid_x = (pos_a[0] + pos_b[0]) // 2
            mid_y = (pos_a[1] + pos_b[1]) // 2
            # Offset slightly so it doesn't sit right on the line
            label = self.font_small.render(str(route.length), True, (100, 70, 40))
            self.screen.blit(label, (mid_x - label.get_width() // 2, mid_y - label.get_height() // 2 - 6))

    def _draw_cities(self, game: GameState) -> None:
        for city_id, (x, y) in enumerate(CITY_POSITIONS):
            # Check if station is placed here
            station_owner = None
            for pid, cities in enumerate(game.station_cities):
                if city_id in cities:
                    station_owner = pid
                    break

            if station_owner is not None:
                pygame.draw.circle(self.screen, PLAYER_COLORS[station_owner], (x, y), CITY_RADIUS + 3, 3)

            pygame.draw.circle(self.screen, CITY_COLOR, (x, y), CITY_RADIUS)
            pygame.draw.circle(self.screen, (255, 255, 255), (x, y), CITY_RADIUS - 2)

            # City name
            label = self.font_small.render(CITY_NAMES[city_id], True, TEXT_COLOR)
            self.screen.blit(label, (x - label.get_width() // 2, y - CITY_RADIUS - 14))

    def _draw_panel(self, game: GameState, human_player: int | None) -> None:
        # Right panel background
        pygame.draw.rect(self.screen, PANEL_BG, (MAP_W, 0, WINDOW_W - MAP_W, WINDOW_H))

        y = 10

        # Phase info
        phase_names = {
            Phase.MAIN: "Main",
            Phase.DRAW_FIRST_CARD: "Draw 1st Card",
            Phase.DRAW_SECOND_CARD: "Draw 2nd Card",
            Phase.KEEP_DESTINATIONS: "Keep Destinations",
        }
        phase_text = f"Turn {game.turn_number} | P{game.current_player}"
        label = self.font_med.render(phase_text, True, TEXT_COLOR)
        self.screen.blit(label, (PANEL_X, y))
        y += 20
        label = self.font_small.render(f"Phase: {phase_names.get(game.phase, '?')}", True, TEXT_COLOR)
        self.screen.blit(label, (PANEL_X, y))
        y += 25

        # Player info
        for pid in range(2):
            p = game.players[pid]
            if human_player is not None and pid == human_player:
                player_label = f"Player {pid} (YOU)"
            else:
                player_label = f"Player {pid}"

            color = PLAYER_COLORS[pid]
            label = self.font_med.render(player_label, True, color)
            self.screen.blit(label, (PANEL_X, y))
            y += 18

            label = self.font_small.render(f"  Points: {p.points}", True, TEXT_COLOR)
            self.screen.blit(label, (PANEL_X, y))
            y += 15
            label = self.font_small.render(f"  Trains: {p.trains_remaining}  Stations: {p.stations_remaining}", True, TEXT_COLOR)
            self.screen.blit(label, (PANEL_X, y))
            y += 15
            label = self.font_small.render(f"  Cards: {p.total_cards()}  Tickets: {len(p.dest_tickets)}", True, TEXT_COLOR)
            self.screen.blit(label, (PANEL_X, y))
            y += 15

            # Show hand if human player or spectator mode
            if human_player is None or pid == human_player:
                hand_items = [
                    f"{CardColor(c).name[:3]}:{int(p.hand[c])}"
                    for c in range(9) if p.hand[c] > 0
                ]
                row1 = " ".join(hand_items[:5])
                row2 = " ".join(hand_items[5:])
                label = self.font_small.render(f"  {row1}", True, TEXT_COLOR)
                self.screen.blit(label, (PANEL_X, y))
                if row2:
                    y += 15
                    label = self.font_small.render(f"  {row2}", True, TEXT_COLOR)
                    self.screen.blit(label, (PANEL_X, y))
                y += 15

            y += 10

        # Destination tickets for human player
        if human_player is not None:
            p = game.players[human_player]
            y += 5
            label = self.font_med.render("Your Tickets:", True, TEXT_COLOR)
            self.screen.blit(label, (PANEL_X, y))
            y += 18
            for ticket in p.dest_tickets:
                a = CITY_NAMES[ticket.city_a][:8]
                b = CITY_NAMES[ticket.city_b][:8]
                label = self.font_small.render(f"  {a}-{b} ({ticket.points})", True, TEXT_COLOR)
                self.screen.blit(label, (PANEL_X, y))
                y += 14

        # Pending destinations (during keep phase)
        if game.phase == Phase.KEEP_DESTINATIONS:
            y += 10
            label = self.font_med.render("Pending Dests:", True, (180, 50, 50))
            self.screen.blit(label, (PANEL_X, y))
            y += 18
            for i, ticket in enumerate(game.pending_destinations):
                a = CITY_NAMES[ticket.city_a][:8]
                b = CITY_NAMES[ticket.city_b][:8]
                label = self.font_small.render(f"  [{i+1}] {a}-{b} ({ticket.points})", True, TEXT_COLOR)
                self.screen.blit(label, (PANEL_X, y))
                y += 14

        # End game indicator
        if game.end_triggered:
            y += 10
            label = self.font_med.render("LAST ROUND!", True, (200, 50, 50))
            self.screen.blit(label, (PANEL_X, y))

        # Game over
        if game.game_over:
            final = game.get_final_scores()
            y = WINDOW_H // 2 - 30
            label = self.font_large.render("GAME OVER", True, (200, 50, 50))
            self.screen.blit(label, (WINDOW_W // 2 - label.get_width() // 2, y))
            y += 30
            for pid in range(2):
                text = f"P{pid}: {final[pid]} pts"
                label = self.font_med.render(text, True, PLAYER_COLORS[pid])
                self.screen.blit(label, (WINDOW_W // 2 - label.get_width() // 2, y))
                y += 22
            winner = 0 if final[0] > final[1] else (1 if final[1] > final[0] else -1)
            if winner >= 0:
                text = f"Player {winner} wins!"
            else:
                text = "It's a tie!"
            label = self.font_large.render(text, True, TEXT_COLOR)
            self.screen.blit(label, (WINDOW_W // 2 - label.get_width() // 2, y))

    def _draw_face_up_cards(self, game: GameState) -> None:
        """Draw face-up cards at the bottom of the map area."""
        y_base = WINDOW_H - 60
        x_start = 20
        card_w = 55
        card_h = 40

        label = self.font_small.render("Face-up:", True, TEXT_COLOR)
        self.screen.blit(label, (x_start, y_base - 18))

        for i, card in enumerate(game.cards.face_up):
            x = x_start + i * (card_w + 8)
            color = CARD_COLORS.get(card, (128, 128, 128))
            pygame.draw.rect(self.screen, color, (x, y_base, card_w, card_h), border_radius=4)
            pygame.draw.rect(self.screen, (0, 0, 0), (x, y_base, card_w, card_h), 2, border_radius=4)
            name = CardColor(card).name[:4]
            label = self.font_small.render(name, True, (255, 255, 255) if card != CardColor.WHITE else (0, 0, 0))
            self.screen.blit(label, (x + 4, y_base + 12))

        # Draw deck indicator
        x_deck = x_start + 5 * (card_w + 8) + 20
        pygame.draw.rect(self.screen, (100, 80, 60), (x_deck, y_base, card_w, card_h), border_radius=4)
        pygame.draw.rect(self.screen, (0, 0, 0), (x_deck, y_base, card_w, card_h), 2, border_radius=4)
        deck_label = self.font_small.render(f"Deck", True, (255, 255, 255))
        self.screen.blit(deck_label, (x_deck + 8, y_base + 4))
        count_label = self.font_small.render(f"{game.cards.deck_size()}", True, (255, 255, 255))
        self.screen.blit(count_label, (x_deck + 14, y_base + 20))

        # Draw destination tickets button
        x_dest = x_deck + card_w + 15
        dest_w = 80
        pygame.draw.rect(self.screen, (120, 60, 30), (x_dest, y_base, dest_w, card_h), border_radius=4)
        pygame.draw.rect(self.screen, (0, 0, 0), (x_dest, y_base, dest_w, card_h), 2, border_radius=4)
        dest_label = self.font_small.render("Tickets", True, (255, 255, 255))
        self.screen.blit(dest_label, (x_dest + 10, y_base + 12))

    def _draw_game_log(self, game: GameState) -> None:
        """Draw a scrollable game log at the bottom-left of the map area."""
        log_x = 420
        log_y = WINDOW_H - 180
        log_w = MAP_W - log_x - 10
        log_h = 110
        line_h = 14

        # Background
        pygame.draw.rect(self.screen, (255, 250, 240), (log_x, log_y, log_w, log_h))
        pygame.draw.rect(self.screen, (160, 150, 130), (log_x, log_y, log_w, log_h), 1)

        header = self.font_small.render("Game Log (scroll: Up/Down)", True, (120, 110, 90))
        self.screen.blit(header, (log_x + 4, log_y - 15))

        if not game.log:
            return

        max_visible = log_h // line_h
        total = len(game.log)

        # Clamp scroll offset
        max_scroll = max(0, total - max_visible)
        self.log_scroll_offset = max(0, min(self.log_scroll_offset, max_scroll))

        # Determine visible range (show most recent at bottom)
        start = total - max_visible - self.log_scroll_offset
        if start < 0:
            start = 0
        end = min(start + max_visible, total)

        # Clip rendering to log area
        clip_rect = pygame.Rect(log_x, log_y, log_w, log_h)
        self.screen.set_clip(clip_rect)

        y = log_y + 2
        for i in range(start, end):
            pid, msg = game.log[i]
            color = PLAYER_COLORS[pid]
            prefix = f"P{pid}: "
            label = self.font_small.render(prefix + msg, True, color)
            self.screen.blit(label, (log_x + 4, y))
            y += line_h

        self.screen.set_clip(None)

        # Scroll indicators
        if self.log_scroll_offset < max_scroll:
            arrow = self.font_small.render("^", True, (100, 100, 100))
            self.screen.blit(arrow, (log_x + log_w - 14, log_y + 2))
        if self.log_scroll_offset > 0:
            arrow = self.font_small.render("v", True, (100, 100, 100))
            self.screen.blit(arrow, (log_x + log_w - 14, log_y + log_h - 14))

    def scroll_log(self, direction: int) -> None:
        """Scroll the game log. direction: +1 = older, -1 = newer."""
        self.log_scroll_offset += direction

    def get_face_up_rects(self) -> list[pygame.Rect]:
        """Return clickable rects for face-up cards."""
        y_base = WINDOW_H - 60
        x_start = 20
        card_w = 55
        card_h = 40
        rects = []
        for i in range(5):
            x = x_start + i * (card_w + 8)
            rects.append(pygame.Rect(x, y_base, card_w, card_h))
        return rects

    def get_deck_rect(self) -> pygame.Rect:
        y_base = WINDOW_H - 60
        x_start = 20
        card_w = 55
        card_h = 40
        x_deck = x_start + 5 * (card_w + 8) + 20
        return pygame.Rect(x_deck, y_base, card_w, card_h)

    def get_tickets_rect(self) -> pygame.Rect:
        """Return clickable rect for the Draw Tickets button."""
        y_base = WINDOW_H - 60
        x_start = 20
        card_w = 55
        card_h = 40
        x_deck = x_start + 5 * (card_w + 8) + 20
        x_dest = x_deck + card_w + 15
        return pygame.Rect(x_dest, y_base, 80, card_h)

    # ── Color picker ────────────────────────────────────────────────

    _PICKER_ITEM_W = 70
    _PICKER_ITEM_H = 30
    _PICKER_PAD = 4

    def get_color_picker_rects(self, count: int) -> list[pygame.Rect]:
        """Return clickable rects for color picker items, centered on screen."""
        total_w = count * self._PICKER_ITEM_W + (count - 1) * self._PICKER_PAD
        x_start = (MAP_W - total_w) // 2
        y = WINDOW_H // 2
        rects = []
        for i in range(count):
            x = x_start + i * (self._PICKER_ITEM_W + self._PICKER_PAD)
            rects.append(pygame.Rect(x, y, self._PICKER_ITEM_W, self._PICKER_ITEM_H))
        return rects

    def draw_color_picker(self, choices: list[Action]) -> None:
        """Draw a color picker overlay for route/station color selection."""
        if not choices:
            return
        count = len(choices)
        rects = self.get_color_picker_rects(count)

        # Backdrop
        total_w = rects[-1].right - rects[0].left
        backdrop = pygame.Rect(
            rects[0].left - 10, rects[0].top - 30,
            total_w + 20, self._PICKER_ITEM_H + 50,
        )
        pygame.draw.rect(self.screen, (50, 45, 40), backdrop, border_radius=6)
        pygame.draw.rect(self.screen, (200, 190, 170), backdrop, 2, border_radius=6)

        # Title
        title = self.font_med.render("Pick a color:", True, (230, 220, 200))
        self.screen.blit(title, (backdrop.x + 10, backdrop.y + 6))

        # Color buttons
        for i, (rect, action) in enumerate(zip(rects, choices)):
            color_val = action.color
            bg = CARD_COLORS.get(color_val, (128, 128, 128))
            pygame.draw.rect(self.screen, bg, rect, border_radius=4)
            pygame.draw.rect(self.screen, (255, 255, 255), rect, 2, border_radius=4)
            text_color = (255, 255, 255) if color_val != CardColor.WHITE else (0, 0, 0)
            label = self.font_small.render(CardColor(color_val).name[:5], True, text_color)
            self.screen.blit(label, (rect.x + (rect.width - label.get_width()) // 2,
                                     rect.y + (rect.height - label.get_height()) // 2))
