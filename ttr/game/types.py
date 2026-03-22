from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class CardColor(IntEnum):
    RED = 0
    ORANGE = 1
    YELLOW = 2
    GREEN = 3
    BLUE = 4
    PURPLE = 5  # aka pink/violet
    BLACK = 6
    WHITE = 7
    LOCOMOTIVE = 8


class Phase(IntEnum):
    DRAW_FIRST_CARD = 0     # Player must draw 1st card (face-up or deck)
    DRAW_SECOND_CARD = 1    # Player must draw 2nd card (no face-up loco)
    KEEP_DESTINATIONS = 2   # Player must choose which destinations to keep
    MAIN = 3                # Player chooses: draw cards, claim route, draw destinations, place station


class ActionType(IntEnum):
    DRAW_FACE_UP = 0
    DRAW_DECK = 1
    CLAIM_ROUTE = 2
    PLACE_STATION = 3
    DRAW_DESTINATIONS = 4
    KEEP_DESTINATIONS = 5


@dataclass(frozen=True)
class Route:
    id: int
    city_a: int
    city_b: int
    length: int
    color: CardColor | None  # None = gray
    is_tunnel: bool = False
    ferry_locomotives: int = 0
    parallel_id: int | None = None  # id of the other route in a double pair


@dataclass(frozen=True)
class DestTicket:
    id: int
    city_a: int
    city_b: int
    points: int


@dataclass(frozen=True)
class Action:
    type: ActionType
    route_id: int | None = None
    color: CardColor | None = None  # color used to pay for route/station
    face_up_slot: int | None = None
    dest_mask: int | None = None  # bitmask for keep-destinations (over pending set)
    city_id: int | None = None  # for place station
