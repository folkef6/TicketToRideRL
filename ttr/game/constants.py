"""Map data for Ticket to Ride Europe.

All routes, cities, destination tickets, and scoring tables.
Routes, cities, and tickets based on the official board game.
"""

from __future__ import annotations

from .types import CardColor, Route, DestTicket

# ── Cities (46) ─────────────────────────────────────────────────
# fmt: off
CITY_NAMES: list[str] = [
    "Edinburgh",       # 0
    "London",          # 1
    "Dieppe",          # 2
    "Brest",           # 3
    "Paris",           # 4
    "Bruxelles",       # 5
    "Amsterdam",       # 6
    "Essen",           # 7
    "Frankfurt",       # 8
    "Zürich",          # 9
    "Marseille",       # 10
    "Pamplona",        # 11
    "Barcelona",       # 12
    "Madrid",          # 13
    "Cádiz",           # 14
    "Lisboa",          # 15
    "München",         # 16
    "Wien",            # 17
    "Venezia",         # 18
    "Roma",            # 19
    "Palermo",         # 20
    "Brindisi",        # 21
    "Athina",          # 22
    "Sarajevo",        # 23
    "Zagreb",          # 24
    "Budapest",        # 25
    "Bucureşti",       # 26
    "Constantinople",  # 27
    "Angora",          # 28
    "Smyrna",          # 29
    "Sévastopol",      # 30
    "Erzurum",         # 31
    "Sochi",           # 32
    "Rostov",          # 33
    "Kharkov",         # 34
    "Kyiv",            # 35
    "Wilno",           # 36
    "Warszawa",        # 37
    "Danzig",          # 38
    "Berlin",          # 39
    "Kobenhavn",       # 40
    "Stockholm",       # 41
    "Petrograd",       # 42
    "Moskva",          # 43
    "Smolensk",        # 44
    "Riga",            # 45
    "Sofia",           # 46
]
# fmt: on

NUM_CITIES = len(CITY_NAMES)
CITY_ID = {name: i for i, name in enumerate(CITY_NAMES)}

_c = CITY_ID
_C = CardColor

# ── Routes ──────────────────────────────────────────────────────
# (city_a, city_b, length, color|None for gray, is_tunnel, ferry_locos)
# Parallel routes get linked after construction.

_ROUTE_DEFS: list[tuple[int, int, int, CardColor | None, bool, int]] = [
    # --- British Isles ---
    (_c["Edinburgh"], _c["London"], 4, _C.BLACK, False, 1),        # 0
    (_c["Edinburgh"], _c["London"], 4, _C.ORANGE, False, 1),       # 1
    (_c["London"], _c["Dieppe"], 2, None, False, 1),               # 2
    (_c["London"], _c["Dieppe"], 2, None, False, 1),               # 3
    (_c["London"], _c["Amsterdam"], 2, None, False, 2),            # 4
    # --- France ---
    (_c["Dieppe"], _c["Paris"], 1, _C.PURPLE, False, 0),           # 5
    (_c["Dieppe"], _c["Bruxelles"], 2, _C.GREEN, False, 0),        # 6
    (_c["Dieppe"], _c["Brest"], 2, _C.ORANGE, False, 0),           # 7
    (_c["Brest"], _c["Paris"], 3, _C.BLACK, False, 0),             # 8
    (_c["Brest"], _c["Pamplona"], 4, _C.PURPLE, False, 0),          # 9
    (_c["Paris"], _c["Bruxelles"], 2, _C.YELLOW, False, 0),        # 10
    (_c["Paris"], _c["Bruxelles"], 2, _C.RED, False, 0),           # 11
    (_c["Paris"], _c["Frankfurt"], 3, _C.WHITE, False, 0),         # 12
    (_c["Paris"], _c["Frankfurt"], 3, _C.ORANGE, False, 0),        # 13
    (_c["Paris"], _c["Zürich"], 3, None, True, 0),                 # 14
    (_c["Paris"], _c["Pamplona"], 4, _C.BLUE, False, 0),           # 15
    (_c["Paris"], _c["Pamplona"], 4, _C.GREEN, False, 0),          # 16
    (_c["Paris"], _c["Marseille"], 4, None, False, 0),             # 17
    # --- Iberia ---
    (_c["Pamplona"], _c["Barcelona"], 2, None, True, 0),           # 18
    (_c["Pamplona"], _c["Madrid"], 3, _C.BLACK, True, 0),          # 19
    (_c["Pamplona"], _c["Madrid"], 3, _C.WHITE, True, 0),          # 20
    (_c["Pamplona"], _c["Marseille"], 4, _C.RED, False, 0),        # 21
    (_c["Barcelona"], _c["Madrid"], 2, _C.YELLOW, False, 0),       # 22
    (_c["Barcelona"], _c["Marseille"], 4, None, False, 0),         # 23
    (_c["Madrid"], _c["Cádiz"], 3, _C.ORANGE, False, 0),           # 24
    (_c["Madrid"], _c["Lisboa"], 3, _C.PURPLE, False, 0),          # 25
    (_c["Cádiz"], _c["Lisboa"], 2, _C.BLUE, False, 0),             # 26
    # --- Switzerland / Italy ---
    (_c["Marseille"], _c["Zürich"], 2, _C.PURPLE, True, 0),        # 27
    (_c["Marseille"], _c["Roma"], 4, None, True, 0),                # 28
    (_c["Zürich"], _c["München"], 2, _C.YELLOW, True, 0),          # 29
    (_c["Zürich"], _c["Venezia"], 2, _C.GREEN, True, 0),           # 30
    (_c["München"], _c["Wien"], 3, _C.ORANGE, False, 0),           # 31
    (_c["München"], _c["Venezia"], 2, _C.BLUE, True, 0),           # 32
    (_c["München"], _c["Frankfurt"], 2, _C.PURPLE, False, 0),      # 33
    (_c["Venezia"], _c["Roma"], 2, _C.BLACK, False, 0),            # 34
    (_c["Venezia"], _c["Zagreb"], 2, None, False, 0),              # 35
    (_c["Roma"], _c["Palermo"], 4, None, False, 1),                # 36
    (_c["Roma"], _c["Brindisi"], 2, _C.WHITE, False, 0),           # 37
    (_c["Palermo"], _c["Brindisi"], 3, None, False, 1),            # 38
    (_c["Palermo"], _c["Smyrna"], 6, None, False, 2),              # 39
    (_c["Brindisi"], _c["Athina"], 4, None, False, 1),             # 40
    # --- Benelux / Germany ---
    (_c["Bruxelles"], _c["Amsterdam"], 1, _C.BLACK, False, 0),     # 41
    (_c["Bruxelles"], _c["Frankfurt"], 2, _C.BLUE, False, 0),      # 42
    (_c["Amsterdam"], _c["Essen"], 3, _C.YELLOW, False, 0),        # 43
    (_c["Amsterdam"], _c["Frankfurt"], 2, _C.WHITE, False, 0),     # 44
    (_c["Essen"], _c["Berlin"], 2, _C.BLUE, False, 0),             # 45
    (_c["Essen"], _c["Kobenhavn"], 3, None, False, 1),             # 46
    (_c["Essen"], _c["Kobenhavn"], 3, None, False, 1),             # 47
    (_c["Frankfurt"], _c["Essen"], 2, _C.GREEN, False, 0),          # 48
    (_c["Frankfurt"], _c["Berlin"], 3, _C.RED, False, 0),          # 49
    (_c["Frankfurt"], _c["Berlin"], 3, _C.BLACK, False, 0),        # 50
    # --- Balkans ---
    (_c["Athina"], _c["Sarajevo"], 4, _C.GREEN, False, 0),         # 51
    (_c["Athina"], _c["Smyrna"], 2, None, False, 1),               # 52
    (_c["Sarajevo"], _c["Zagreb"], 3, _C.RED, False, 0),            # 53
    (_c["Sarajevo"], _c["Budapest"], 3, _C.PURPLE, False, 0),      # 54
    (_c["Zagreb"], _c["Wien"], 2, None, False, 0),                  # 55
    (_c["Zagreb"], _c["Budapest"], 2, _C.ORANGE, False, 0),         # 56
    (_c["Budapest"], _c["Wien"], 1, _C.RED, False, 0),              # 57
    (_c["Budapest"], _c["Wien"], 1, _C.WHITE, False, 0),            # 58
    (_c["Budapest"], _c["Bucureşti"], 4, None, True, 0),            # 59
    (_c["Budapest"], _c["Kyiv"], 6, None, True, 0),                 # 60
    # --- Sofia ---
    (_c["Sofia"], _c["Athina"], 3, _C.PURPLE, False, 0),              # 61
    (_c["Sofia"], _c["Sarajevo"], 2, None, True, 0),                  # 62
    (_c["Sofia"], _c["Bucureşti"], 2, None, True, 0),                 # 63
    (_c["Sofia"], _c["Constantinople"], 3, _C.BLUE, False, 0),        # 64
    # --- Turkey / Black Sea ---
    (_c["Bucureşti"], _c["Constantinople"], 3, _C.YELLOW, False, 0),  # 65
    (_c["Bucureşti"], _c["Sévastopol"], 4, _C.WHITE, False, 0),       # 66
    (_c["Bucureşti"], _c["Kyiv"], 4, None, False, 0),                 # 67
    (_c["Constantinople"], _c["Angora"], 2, None, True, 0),           # 68
    (_c["Constantinople"], _c["Smyrna"], 2, None, True, 0),           # 69
    (_c["Constantinople"], _c["Sévastopol"], 4, None, False, 2),      # 70
    (_c["Angora"], _c["Erzurum"], 3, _C.BLACK, False, 0),             # 71
    (_c["Angora"], _c["Smyrna"], 3, _C.ORANGE, True, 0),              # 72
    (_c["Erzurum"], _c["Sévastopol"], 4, None, False, 2),             # 73
    (_c["Erzurum"], _c["Sochi"], 3, _C.RED, False, 0),                # 74
    # --- Russia ---
    (_c["Sochi"], _c["Sévastopol"], 2, None, False, 1),               # 75
    (_c["Sochi"], _c["Rostov"], 2, None, False, 0),                   # 76
    (_c["Rostov"], _c["Sévastopol"], 4, None, False, 0),              # 77
    (_c["Rostov"], _c["Kharkov"], 2, _C.GREEN, False, 0),             # 78
    (_c["Kharkov"], _c["Kyiv"], 4, None, False, 0),                   # 79
    (_c["Kharkov"], _c["Moskva"], 4, None, False, 0),                 # 80
    (_c["Kyiv"], _c["Warszawa"], 4, None, False, 0),                  # 81
    (_c["Kyiv"], _c["Wilno"], 2, None, False, 0),                     # 82
    (_c["Kyiv"], _c["Smolensk"], 3, _C.RED, False, 0),                # 83
    # --- Poland / Baltics / Scandinavia ---
    (_c["Wilno"], _c["Warszawa"], 3, _C.RED, False, 0),               # 84
    (_c["Wilno"], _c["Smolensk"], 3, _C.YELLOW, False, 0),            # 85
    (_c["Wilno"], _c["Riga"], 4, _C.GREEN, False, 0),                 # 86
    (_c["Wilno"], _c["Petrograd"], 4, _C.BLUE, False, 0),             # 87
    (_c["Warszawa"], _c["Berlin"], 4, _C.PURPLE, False, 0),           # 88
    (_c["Warszawa"], _c["Berlin"], 4, _C.YELLOW, False, 0),           # 89
    (_c["Warszawa"], _c["Wien"], 4, _C.BLUE, False, 0),               # 90
    (_c["Danzig"], _c["Berlin"], 4, None, False, 0),                  # 91
    (_c["Danzig"], _c["Riga"], 3, _C.BLACK, False, 0),                # 92
    (_c["Danzig"], _c["Warszawa"], 2, None, False, 0),                # 93
    (_c["Berlin"], _c["Wien"], 3, _C.GREEN, False, 0),                # 94
    (_c["Kobenhavn"], _c["Stockholm"], 3, _C.YELLOW, False, 1),       # 95
    (_c["Stockholm"], _c["Petrograd"], 8, None, True, 0),             # 96
    (_c["Riga"], _c["Petrograd"], 4, None, False, 0),                 # 97
    (_c["Petrograd"], _c["Moskva"], 4, _C.WHITE, False, 0),           # 98
    (_c["Moskva"], _c["Smolensk"], 2, _C.ORANGE, False, 0),           # 99
]

# ── Parallel route pairs ────────────────────────────────────────
# (route_a, route_b) — in 2-player, only one of a pair may be claimed total
_PARALLEL_PAIRS: list[tuple[int, int]] = [
    (0, 1),    # Edinburgh – London
    (2, 3),    # London – Dieppe
    (10, 11),  # Paris – Bruxelles
    (12, 13),  # Paris – Frankfurt
    (15, 16),  # Paris – Pamplona
    (19, 20),  # Pamplona – Madrid
    (46, 47),  # Essen – Kobenhavn
    (49, 50),  # Frankfurt – Berlin
    (57, 58),  # Budapest – Wien
    (88, 89),  # Warszawa – Berlin
]

NUM_ROUTES = len(_ROUTE_DEFS)

ROUTES: list[Route] = []
for i, (ca, cb, length, color, tunnel, ferry) in enumerate(_ROUTE_DEFS):
    ROUTES.append(Route(
        id=i,
        city_a=ca,
        city_b=cb,
        length=length,
        color=color,
        is_tunnel=tunnel,
        ferry_locomotives=ferry,
        parallel_id=None,  # filled below
    ))

# Link parallel routes
for a, b in _PARALLEL_PAIRS:
    ROUTES[a] = Route(
        id=a, city_a=ROUTES[a].city_a, city_b=ROUTES[a].city_b,
        length=ROUTES[a].length, color=ROUTES[a].color,
        is_tunnel=ROUTES[a].is_tunnel,
        ferry_locomotives=ROUTES[a].ferry_locomotives,
        parallel_id=b,
    )
    ROUTES[b] = Route(
        id=b, city_a=ROUTES[b].city_a, city_b=ROUTES[b].city_b,
        length=ROUTES[b].length, color=ROUTES[b].color,
        is_tunnel=ROUTES[b].is_tunnel,
        ferry_locomotives=ROUTES[b].ferry_locomotives,
        parallel_id=a,
    )


# ── Destination Tickets (40 regular) ───────────────────────────
_DEST_DATA: list[tuple[str, str, int]] = [
    ("Athina", "Angora", 5),
    ("Budapest", "Sofia", 5),
    ("Frankfurt", "Kobenhavn", 5),
    ("Rostov", "Erzurum", 5),
    ("Sofia", "Smyrna", 5),
    ("Kyiv", "Petrograd", 6),
    ("Zürich", "Brindisi", 6),
    ("Zürich", "Budapest", 6),
    ("Warszawa", "Smolensk", 6),
    ("Zagreb", "Brindisi", 6),
    ("Paris", "Zagreb", 7),
    ("Brest", "Marseille", 7),
    ("London", "Berlin", 7),
    ("Edinburgh", "Paris", 7),
    ("Amsterdam", "Pamplona", 7),
    ("Roma", "Smyrna", 8),
    ("Palermo", "Constantinople", 8),
    ("Sarajevo", "Sévastopol", 8),
    ("Madrid", "Dieppe", 8),
    ("Barcelona", "Bruxelles", 8),
    ("Paris", "Wien", 8),
    ("Barcelona", "München", 8),
    ("Brest", "Venezia", 8),
    ("Smolensk", "Rostov", 8),
    ("Marseille", "Essen", 8),
    ("Kyiv", "Sochi", 8),
    ("Madrid", "Zürich", 8),
    ("Berlin", "Bucureşti", 8),
    ("Bruxelles", "Danzig", 9),
    ("Berlin", "Roma", 9),
    ("Angora", "Kharkov", 10),
    ("Riga", "Bucureşti", 10),
    ("Essen", "Kyiv", 10),
    ("Venezia", "Constantinople", 10),
    ("London", "Wien", 10),
    ("Athina", "Wilno", 11),
    ("Stockholm", "Wien", 11),
    ("Berlin", "Moskva", 12),
    ("Amsterdam", "Wilno", 12),
    ("Frankfurt", "Smolensk", 13),
]

DEST_TICKETS: list[DestTicket] = []
for i, (ca_name, cb_name, pts) in enumerate(_DEST_DATA):
    DEST_TICKETS.append(DestTicket(
        id=i,
        city_a=CITY_ID[ca_name],
        city_b=CITY_ID[cb_name],
        points=pts,
    ))

NUM_DEST_TICKETS = len(DEST_TICKETS)  # 40

# ── Long Destination Tickets (6, dealt separately) ────────────
_LONG_DEST_DATA: list[tuple[str, str, int]] = [
    ("Lisboa", "Danzig", 20),
    ("Brest", "Petrograd", 20),
    ("Palermo", "Moskva", 20),
    ("Kobenhavn", "Erzurum", 21),
    ("Edinburgh", "Athina", 21),
    ("Cádiz", "Stockholm", 21),
]

LONG_DEST_TICKETS: list[DestTicket] = []
for i, (ca_name, cb_name, pts) in enumerate(_LONG_DEST_DATA):
    LONG_DEST_TICKETS.append(DestTicket(
        id=NUM_DEST_TICKETS + i,
        city_a=CITY_ID[ca_name],
        city_b=CITY_ID[cb_name],
        points=pts,
    ))

NUM_LONG_DEST_TICKETS = len(LONG_DEST_TICKETS)  # 6

# ── Scoring Table ───────────────────────────────────────────────
ROUTE_POINTS: dict[int, int] = {
    1: 1,
    2: 2,
    3: 4,
    4: 7,
    5: 10,
    6: 15,
    8: 21,
}

# ── Train Card Deck Composition ────────────────────────────────
CARDS_PER_COLOR = 12
LOCOMOTIVE_COUNT = 14
TOTAL_CARDS = CARDS_PER_COLOR * 8 + LOCOMOTIVE_COUNT  # 110

# ── Player Constants ────────────────────────────────────────────
INITIAL_TRAINS = 45
INITIAL_STATIONS = 3
INITIAL_HAND_SIZE = 4
INITIAL_DEST_DRAW = 3   # draw 3 at game start, keep at least 2
DEST_DRAW_COUNT = 3      # draw 3 during game, keep at least 1
DEST_KEEP_MIN_INITIAL = 2
DEST_KEEP_MIN = 1
FACE_UP_COUNT = 5
END_GAME_TRAIN_THRESHOLD = 2
STATION_BONUS = 4        # points per unplaced station
LONGEST_ROUTE_BONUS = 10
