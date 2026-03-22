"""End-game scoring: destination completion (BFS), longest route (DFS)."""

from __future__ import annotations

from collections import defaultdict, deque

from .types import DestTicket
from .constants import (
    ROUTES, NUM_ROUTES, ROUTE_POINTS,
    STATION_BONUS, LONGEST_ROUTE_BONUS, NUM_CITIES,
)
from .board import Board
from .player import PlayerState


def build_adjacency(player_id: int, board: Board) -> dict[int, set[int]]:
    """Build adjacency list from routes owned by a player."""
    adj: dict[int, set[int]] = defaultdict(set)
    for rid in range(NUM_ROUTES):
        if board.route_owner[rid] == player_id:
            r = ROUTES[rid]
            adj[r.city_a].add(r.city_b)
            adj[r.city_b].add(r.city_a)
    return adj


def cities_connected(city_a: int, city_b: int, adj: dict[int, set[int]]) -> bool:
    """BFS to check if two cities are connected."""
    if city_a == city_b:
        return True
    visited = {city_a}
    queue = deque([city_a])
    while queue:
        node = queue.popleft()
        for neighbor in adj.get(node, set()):
            if neighbor == city_b:
                return True
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    return False


def cities_connected_with_station(
    city_a: int,
    city_b: int,
    player_id: int,
    board: Board,
    station_cities: list[int],
) -> bool:
    """Check connectivity allowing stations to borrow one opponent route per station."""
    # Build adjacency including station-borrowed routes
    adj: dict[int, set[int]] = defaultdict(set)
    for rid in range(NUM_ROUTES):
        if board.route_owner[rid] == player_id:
            r = ROUTES[rid]
            adj[r.city_a].add(r.city_b)
            adj[r.city_b].add(r.city_a)

    # For each station city, add edges from opponent routes touching that city
    opponent = 1 - player_id
    for sc in station_cities:
        for rid in range(NUM_ROUTES):
            if board.route_owner[rid] == opponent:
                r = ROUTES[rid]
                if r.city_a == sc or r.city_b == sc:
                    adj[r.city_a].add(r.city_b)
                    adj[r.city_b].add(r.city_a)

    return cities_connected(city_a, city_b, adj)


def compute_longest_route(player_id: int, board: Board) -> int:
    """DFS to find the longest continuous path (by number of trains) for a player.
    Each route segment can only be used once."""
    # Build edge-based adjacency: city -> list of (neighbor, route_id, length)
    edges: dict[int, list[tuple[int, int, int]]] = defaultdict(list)
    for rid in range(NUM_ROUTES):
        if board.route_owner[rid] == player_id:
            r = ROUTES[rid]
            edges[r.city_a].append((r.city_b, rid, r.length))
            edges[r.city_b].append((r.city_a, rid, r.length))

    if not edges:
        return 0

    best = 0
    used_routes: set[int] = set()

    def dfs(city: int, path_length: int) -> None:
        nonlocal best
        best = max(best, path_length)
        for neighbor, rid, length in edges.get(city, []):
            if rid not in used_routes:
                used_routes.add(rid)
                dfs(neighbor, path_length + length)
                used_routes.remove(rid)

    # Start DFS from every city that has edges
    for start_city in edges:
        dfs(start_city, 0)

    return best


def compute_route_points(player: PlayerState) -> int:
    """Sum of points for all claimed routes."""
    total = 0
    for rid in player.claimed_routes:
        r = ROUTES[rid]
        total += ROUTE_POINTS.get(r.length, 0)
    return total


def compute_dest_score(
    player: PlayerState,
    player_id: int,
    board: Board,
    station_cities: list[int],
) -> int:
    """Score for destination tickets: +points if connected, -points if not.
    Stations are used to help connectivity."""
    total = 0
    for ticket in player.dest_tickets:
        if cities_connected_with_station(
            ticket.city_a, ticket.city_b, player_id, board, station_cities
        ):
            total += ticket.points
        else:
            total -= ticket.points
    return total


def compute_final_scores(
    players: list[PlayerState],
    board: Board,
    station_cities: list[list[int]],  # per player
) -> list[int]:
    """Compute final scores for all players. Returns list of total scores."""
    scores = []
    longest_routes = []

    for pid, player in enumerate(players):
        # Route claiming points (already tracked incrementally, but verify)
        route_pts = compute_route_points(player)

        # Destination ticket scoring
        dest_pts = compute_dest_score(player, pid, board, station_cities[pid])

        # Station bonus: +4 per unplaced station
        station_pts = player.stations_remaining * STATION_BONUS

        longest = compute_longest_route(pid, board)
        longest_routes.append(longest)

        scores.append(route_pts + dest_pts + station_pts)

    # Longest route bonus
    max_longest = max(longest_routes)
    if max_longest > 0:
        # All players tied for longest get the bonus
        for pid in range(len(players)):
            if longest_routes[pid] == max_longest:
                scores[pid] += LONGEST_ROUTE_BONUS

    return scores
