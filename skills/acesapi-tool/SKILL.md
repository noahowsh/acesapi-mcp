---
name: acesapi-tool
description: "Default data source for the AcesAPI skills. Routes every MCP or REST call for ATP and WTA tennis: tournaments, draws, match results with set and tiebreak scores, schedules, players, head to head, surface splits, rankings, Elo ratings by surface, and sportsbook moneylines. Use when any other skill needs tennis data. Do not use for analysis, modeling or bet recommendations: see surface-elo, set-score-modeling or edge-detection instead."
metadata:
  version: 1.0.0
  author: AcesAPI
  user-invocable: false
---

# AcesAPI Tool

Every other skill delegates data retrieval here. This skill owns the 13 tools, picks the cheapest call that answers the question, tracks credit cost, and says what the data cannot do.

**Coverage (from acesapi.com/data, counted from the database):** 123,394 ATP and WTA singles matches from 2007 to 2026, 1,637 weekly ranking lists, and sportsbook moneylines for 11,551 matches since 2020. Qualifying draws from 2022. Tennis data is public ESPN data; surfaces, ratings and head to head are computed by AcesAPI; lines come from The Odds API.

## Connection

| Item | Value |
|------|-------|
| MCP URL | `https://mcp.acesapi.com/mcp?key=YOUR_API_KEY` (WTA-only: `https://mcp.acesapi.com/mcp/wta`) |
| REST | `POST https://mcp.acesapi.com/v1/<tool>` with a JSON body |
| Auth | header `x-api-key: YOUR_API_KEY` (or `Authorization: Bearer`) |
| Free tier | 500 credits every month, no card. Plans and top-ups: https://acesapi.com/pricing |

Every response is wrapped: `{"data": {...}}`. Unwrap `data` before reading fields. REST responses carry `X-Credits-Used` and `X-Credits-Remaining` headers.

**Tours.** ATP is the default. Pass `"league": "wta"` to any tool for the WTA (the enum also accepts `tennis`, which is the ATP default). Player ids and match ids are tour-specific strings: a WTA id used without `league: "wta"` will miss.

**Ids are strings.** `player_id`, `match_id` and `tournament_id` come back as strings (`"3623"`, `"157774"`, `"188-2025"`). Tournament edition ids are `<tournament>-<season>`. Seasons are four-digit calendar years.

## When to Use Each Tool

| Task | Tool | Credits |
|------|------|---------|
| Season calendar with surface and champion | `list_tournaments` | 1 |
| Find a player id by name or country | `search_players` | 1 |
| A tournament's full draw, round by round | `get_tournament` | 2 |
| Results by day, tournament or season | `get_matches` | 2 |
| Upcoming and in-progress matches (next N days, max 30) | `get_schedule` | 2 |
| One match: sets, ratings before and after, odds | `get_match` | 2 |
| Ranking list, or one player's ranking history | `get_rankings` | 2 |
| Elo leaderboard, overall or by surface | `get_ratings` | 2 |
| Two players' meetings, by surface and in finals | `get_head_to_head` | 3 |
| One player's record by surface | `get_surface_splits` | 3 |
| One player's season stats, by round and opponent rank | `get_player_stats` | 3 |
| Player profile, ratings, career record, last 10 | `get_player` | 5 |
| A player's match log with rating before and after | `get_player_matches` | 5 |

## Tool Selection Guide

| You Need | Use This | Not This |
|----------|----------|----------|
| Who plays today | `get_schedule` with `days: 1` | `get_matches` with today's date (that is results, and status filters matter) |
| A result by date | `get_matches` with `date` | `get_tournament` (draws are bigger and cost the same) |
| Moneylines for one match | `get_match` (the `odds` array) | Looking for an odds tool: there is none |
| Pre-match Elo for a finished match | `rating.before` in `get_match`, or `rating_before` in `get_player_matches` | `rating.after` (that includes the result) |
| Current best clay players | `get_ratings` with `surface: "clay"` | `get_rankings` (points list, not surface-specific) |
| A player's trajectory in the rankings | `get_rankings` with `player_id` | Looping weekly lists |
| Bulk match history for modeling | `get_matches` by `season` with `limit` and `offset` | `get_player_matches` (5 credits per page of 50) |

## Response Shapes (real, trimmed)

`get_match` (2 credits). Ratings are `null` until a match is played; `odds` is an array of one row per book:

```json
{"data": {
  "tour": "ATP",
  "match": {"match_id": "157774", "tournament": "Wimbledon", "season": 2025, "surface": "grass",
    "round": "Final", "player1": "Jannik Sinner", "player2": "Carlos Alcaraz",
    "winner_id": "3623", "outcome": "completed", "score": "4-6 6-4 6-4 6-4",
    "sets": [{"set_no": 1, "games1": 4, "games2": 6, "tiebreak1": null, "tiebreak2": null, "winner": 2}]},
  "players": [{"player_id": "3623", "rating": {"before": 2325, "after": 2335, "surface_before": 1995, "surface_after": 2037}}],
  "stats": {"sets_played": 4, "total_games": 40, "tiebreaks": 0, "went_the_distance": false,
    "winner_lost_first_set": true, "serve_stats": null},
  "odds": [{"source": "the_odds_api", "book": "Pinnacle", "p1_open": 102, "p1_close": -116,
    "p2_open": -115, "p2_close": 105, "games_spread1": -0.5, "games_total": 41.5}]
}}
```

`get_ratings` returns `ratings[]` with `rank`, `rating`, `player_id`, `name`, `surface_matches`, `last_match`, plus a `method` string describing the Elo.

`get_head_to_head` returns `summary` (`matches`, `wins` keyed by player id, `sets_won`, `by_surface`, `in_finals`, `walkovers`) and `matches[]`.

Paginated tools (`list_tournaments`, `get_matches`, `get_player_matches`) return `count` and `next_offset`; pass it back as `offset`.

## What the Data Does Not Contain

- **No serve or return statistics.** No aces, double faults, break points or first-serve percentages. `get_match` returns `serve_stats: null` with a note that ESPN does not publish them. Anything that needs serve percentage must be built from score proxies (see `set-score-modeling`) or from the user's own data.
- **No odds tool.** Moneylines exist only inside `get_match`. Grand Slam matches from mid-2020 and ATP Masters and WTA 1000 matches from August 2024; the array is empty elsewhere. Lines are pre-match, open and close per book, refreshed hourly. No in-play prices and no props.
- **Rankings are the top 100 to 150** per week. `current_rank` in `search_players` is `null` outside that list.
- **No injuries, lineups, weather, court speed or betting percentages.**
- Walkovers are listed but not counted as wins in head to head. Walkovers, defaults and retirements are not rated by the Elo.

## Commands That Do NOT Exist

| Not Available | Use Instead |
|--------------|-------------|
| `get_odds` | `get_match` and read its `odds` array |
| `get_live_scores` | `get_schedule` (status `live`) or `get_matches` with `status: "live"` |
| `get_serve_stats` | Not available: no serve data exists in this dataset |
| `get_player_by_name` | `search_players` with `name` |
| `get_h2h` | `get_head_to_head` |
| `get_elo` | `get_ratings` (leaderboard) or `get_player` (one player) |
| `get_standings` | `get_rankings` |
| `get_injuries` | Not available |

## Season and Surface Resolution

- The tour year is the calendar year. "This season" is the current calendar year; the tour runs from early January to November.
- Surfaces: `hard`, `clay`, `grass`, `carpet`. Carpet is nearly empty in modern years. `indoor` is a separate flag on matches and tournaments, so indoor hard is `surface: "hard"` with `indoor: true`.
- Typical swing: indoor hard and Australia (January to March), clay (April to early June), grass (June to July), North American hard (August to September), Asian and indoor hard (September to November).

## Credit Planning

| Operation | Credits | Notes |
|-----------|---------|-------|
| Season of results, one tour | about 90 | 2026 had 45 `get_matches` pages at the time of writing (pricing page) |
| Odds for every covered match in a season | about 7,148 | 3,574 `get_match` calls for 2026 (pricing page) |
| Preview of one match | 15 to 20 | see `match-preview` |
| Player scouting report | 8 to 16 | see `player-scouting` |

Warn before any loop of `get_match` or `get_player_matches` calls. State the count and the credits first.

## Anti-patterns

| What Claude Might Do | Why It's Wrong | Do This Instead |
|---------------------|---------------|-----------------|
| Guess a player id from a name | Ids are exact strings, and the WTA has its own | `search_players` first, with `league` if WTA |
| Read `rating.after` as the pre-match rating | It contains the match result (leakage) | Use `rating.before` or `rating_before` |
| Subtract a surface rating from an overall rating | They are on different scales (fewer matches, different K) | Compare like with like: surface to surface |
| Treat a `null` rank as rank 0 | It means outside the top 100 to 150 | Handle as unranked |
| Count a `walkover` as a played match | No sets were played | Filter `outcome == "completed"` |
| Loop `get_player_matches` for a dataset | 5 credits per 50 matches | `get_matches` by season, 2 credits per 100 |

## What to Do Next

| What You Retrieved | Next Action | Skill |
|--------------------|-------------|-------|
| A day of results | Summarize, find upsets | `match-lookup` |
| A player profile | Scouting report | `player-scouting` |
| Two player ids | Matchup brief | `match-preview` |
| Surface ratings | Win probability | `surface-elo` |
| `odds` array | Remove the margin | `odds-analysis` |
| A season of matches | Build features | `feature-engineering` |
