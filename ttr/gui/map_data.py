"""City pixel coordinates for rendering on a 1200x800 map."""

from __future__ import annotations

# (x, y) pixel positions for each city, indexed by city ID.
# Coordinates designed for a 1200x800 window.
CITY_POSITIONS: list[tuple[int, int]] = [
    (280, 85),    # 0  Edinburgh
    (290, 200),   # 1  London
    (310, 290),   # 2  Dieppe
    (225, 330),   # 3  Brest
    (350, 340),   # 4  Paris
    (380, 240),   # 5  Bruxelles
    (390, 190),   # 6  Amsterdam
    (460, 190),   # 7  Essen
    (450, 280),   # 8  Frankfurt
    (430, 370),   # 9  Zürich
    (380, 470),   # 10 Marseille
    (290, 460),   # 11 Pamplona
    (320, 520),   # 12 Barcelona
    (210, 530),   # 13 Madrid
    (180, 600),   # 14 Cádiz
    (130, 560),   # 15 Lisboa
    (510, 340),   # 16 München
    (560, 310),   # 17 Wien
    (490, 410),   # 18 Venezia
    (500, 490),   # 19 Roma
    (520, 590),   # 20 Palermo
    (580, 520),   # 21 Brindisi
    (650, 540),   # 22 Athina
    (600, 440),   # 23 Sarajevo
    (560, 380),   # 24 Zagreb
    (620, 350),   # 25 Budapest
    (720, 400),   # 26 Bucureşti
    (780, 470),   # 27 Constantinople
    (850, 490),   # 28 Angora
    (760, 540),   # 29 Smyrna
    (830, 380),   # 30 Sévastopol
    (950, 430),   # 31 Erzurum
    (900, 370),   # 32 Sochi
    (870, 310),   # 33 Rostov
    (820, 270),   # 34 Kharkov
    (740, 280),   # 35 Kyiv
    (680, 200),   # 36 Wilno
    (620, 240),   # 37 Warszawa
    (530, 160),   # 38 Danzig
    (510, 220),   # 39 Berlin
    (460, 120),   # 40 Kobenhavn
    (530, 70),    # 41 Stockholm
    (730, 80),    # 42 Petrograd
    (830, 140),   # 43 Moskva
    (770, 190),   # 44 Smolensk
    (650, 120),   # 45 Riga
    (670, 470),   # 46 Sofia
]
