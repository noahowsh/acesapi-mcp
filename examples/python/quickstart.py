#!/usr/bin/env python3
"""AcesAPI quickstart: upcoming ATP matches, then clay-court Elo ratings. Needs ACESAPI_API_KEY. Costs about 4 credits."""
import json
import os
import sys
import urllib.error
import urllib.request

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
            return json.load(resp)
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

def main():
    key = require_key()

    sched = call(key, "get_schedule", {"days": 3})
    matches = sched.get("matches") or []
    print("Upcoming ATP matches (get_schedule, 2 credits)")
    if matches:
        table(
            ["Date", "Tournament", "Round", "Surface", "Match"],
            [[m.get("match_date"), m.get("tournament"), m.get("round"), m.get("surface"),
              f"{m.get('player1')} v {m.get('player2')}"] for m in matches[:8]],
        )
    else:
        print("No matches in the next 3 days.")

    ratings = call(key, "get_ratings", {"surface": "clay", "limit": 5})
    print("\nClay Elo ratings (get_ratings, 2 credits)")
    table(
        ["#", "Player", "Country", "Elo", "Clay matches", "Last match"],
        [[r.get("rank"), r.get("name"), r.get("country"), r.get("rating"), r.get("surface_matches"),
          r.get("last_match")] for r in ratings.get("ratings") or []],
    )
    finish()


if __name__ == "__main__":
    try:
        main()
    except ApiError as err:
        sys.exit(f"Error: {err}")
