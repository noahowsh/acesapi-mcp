#!/usr/bin/env python3
"""Tennis head to head and surface Elo for two players. Usage: python3 tennis_head_to_head_surface_elo.py [name1] [name2]. Costs 11 credits (search_players 2 + get_head_to_head 3 + get_ratings 6)."""
import json
import os
import sys
import urllib.error
import urllib.request
import argparse

BRAND = "AcesAPI"
KEY_ENV = "ACESAPI_API_KEY"
BASE_URL = "https://mcp.acesapi.com/v1"
SIGNUP_URL = "https://acesapi.com/signup"
LAST_REMAINING = None


class ApiError(Exception):
    pass


def require_key():
    key = os.environ.get(KEY_ENV, "").strip()
    if not key:
        sys.exit(
            f"Set {KEY_ENV} first:\n"
            f"  export {KEY_ENV}=your_key\n"
            f"Get a free key (500 credits every month, no card): {SIGNUP_URL}"
        )
    return key


def call(key, tool, args=None):
    """POST /v1/<tool> with a JSON body and return the parsed response."""
    global LAST_REMAINING
    req = urllib.request.Request(
        f"{BASE_URL}/{tool}",
        data=json.dumps(args or {}).encode(),
        headers={
            "Content-Type": "application/json",
            "x-api-key": key,
            "User-Agent": "acesapi.com-examples/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            LAST_REMAINING = resp.headers.get("X-Credits-Remaining", LAST_REMAINING)
            body = json.load(resp)
            # Every response is wrapped as {"data": ...}.
            return body.get("data", body) if isinstance(body, dict) else body
    except urllib.error.HTTPError as err:
        raise ApiError(describe(err, tool)) from None
    except urllib.error.URLError as err:
        raise ApiError(f"Network error calling {tool}: {err.reason}") from None


def describe(err, tool):
    try:
        body = json.loads(err.read().decode() or "{}")
    except ValueError:
        body = {}
    message = body.get("message") or body.get("error") or err.reason
    if err.code == 401:
        return f"401 unauthorized. Check {KEY_ENV}. {message}"
    if err.code == 402:
        upgrade = body.get("upgrade_url") or SIGNUP_URL
        return f"402 out of credits. {message} Upgrade or wait for the monthly reset: {upgrade}"
    return f"HTTP {err.code} from {tool}: {message}"


def fmt(value, digits=None):
    if value is None:
        return "-"
    if digits is not None and isinstance(value, (int, float)):
        return f"{value:.{digits}f}"
    return str(value)


def pct(value, digits=1):
    return "-" if value is None else f"{value * 100:.{digits}f}%"


def table(headers, rows):
    rows = [["-" if c is None else str(c) for c in r] for r in rows]
    widths = [max([len(h)] + [len(r[i]) for r in rows]) for i, h in enumerate(headers)]
    line = lambda cells: "  ".join(c.ljust(w) for c, w in zip(cells, widths)).rstrip()
    print(line(headers))
    print("  ".join("-" * w for w in widths))
    for r in rows:
        print(line(r))


def finish():
    if LAST_REMAINING is not None:
        print(f"\nCredits remaining: {LAST_REMAINING}")

SURFACES = ["hard", "clay", "grass"]


def find_player(key, name):
    found = call(key, "search_players", {"name": name, "limit": 1}).get("players") or []
    if not found:
        sys.exit(f"No player found for {name!r}.")
    return found[0]


def main():
    ap = argparse.ArgumentParser(description="Head to head and surface Elo for two ATP players.")
    ap.add_argument("player1", nargs="?", default="sinner")
    ap.add_argument("player2", nargs="?", default="alcaraz")
    ap.add_argument("--meetings", type=int, default=5, help="recent meetings to list")
    args = ap.parse_args()
    key = require_key()

    p1 = find_player(key, args.player1)
    p2 = find_player(key, args.player2)
    id1, id2 = p1["player_id"], p2["player_id"]
    names = {id1: p1["name"], id2: p2["name"]}

    h2h = call(key, "get_head_to_head", {"player_id": id1, "opponent_id": id2})
    s = h2h.get("summary") or {}
    wins = s.get("wins") or {}
    print(f"{names[id1]} v {names[id2]}: {s.get('matches')} meetings, "
          f"{wins.get(id1, 0)}-{wins.get(id2, 0)}, finals {(s.get('in_finals') or {}).get(id1, 0)}-"
          f"{(s.get('in_finals') or {}).get(id2, 0)}")

    print("\nWins by surface")
    by_surface = s.get("by_surface") or {}
    table(["Surface", names[id1], names[id2]],
          [[surf, v.get(id1, 0), v.get(id2, 0)] for surf, v in by_surface.items()])

    print("\nMost recent meetings")
    table(["Date", "Tournament", "Round", "Surface", "Score", "Winner"],
          [[m.get("match_date"), m.get("tournament"), m.get("round"), m.get("surface"), m.get("score"),
            names.get(m.get("winner_id"), m.get("winner_id"))]
           for m in (h2h.get("matches") or [])[: args.meetings]])

    print("\nElo by surface (rank among active players)")
    rows = []
    for surface in SURFACES:
        board = call(key, "get_ratings", {"surface": surface, "limit": 100}).get("ratings") or []
        cell = {}
        for r in board:
            if r.get("player_id") in names:
                cell[r["player_id"]] = f"{r.get('rating')} (#{r.get('rank')})"
        rows.append([surface, cell.get(id1, "outside top 100"), cell.get(id2, "outside top 100")])
    table(["Surface", names[id1], names[id2]], rows)
    finish()


if __name__ == "__main__":
    try:
        main()
    except ApiError as err:
        sys.exit(f"Error: {err}")
