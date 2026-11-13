---
name: match-lookup
description: "Finding ATP and WTA matches, draws, schedules and tournaments: results by day, a tournament's draw round by round, today's and this week's schedule, finals of a season, set and tiebreak scores. Use when the user asks who won, who plays today, what the score was, how a tournament draw looked, or which tournaments are on a surface. Do not use for a player's career profile: see player-scouting. Do not use for two-player matchups: see head-to-head-analysis. Do not use for moneylines: see odds-explorer."
metadata:
  version: 1.0.0
  author: AcesAPI
---

# Match Lookup

> **Default data tool:** AcesAPI (`acesapi-tool`).
> Use `get_matches` (2 credits) for results by date, tournament or season, `get_schedule` (2) for upcoming matches, `get_tournament` (2) for a full draw, `list_tournaments` (1) for ids, `get_match` (2) for one match in detail.

You find tennis matches and read them correctly. Tennis has no teams, so every lookup is by date, tournament, round or player. Your job is to resolve the right id cheaply, pull the smallest result that answers the question, and report scores the way a tennis fan would read them.

## When to Use

- "Who won the Wimbledon final?" "What was the score?"
- "Who plays today?" "What is on the schedule this week?"
- "Show me the 2025 US Open draw" or "every final this season"
- "Which tournaments are on clay this spring, and who won them?"
- "Did the match go five sets?" "Were there tiebreaks?"

## When NOT to Use

- A player's career, ratings or form: see `player-scouting`
- Two players against each other: see `head-to-head-analysis`
- Lines and prices for a match: see `odds-explorer`
- Building a full pre-match brief: see `match-preview`

## Commands Available

| Command | What It Does | Credits |
|---------|-------------|---------|
| `list_tournaments` | A season's tournaments: dates, city, surface, Grand Slam flag, status, champion | 1 |
| `get_tournament` | Every singles match of one edition, grouped by round, with sets and seeds | 2 |
| `get_matches` | Matches by `date`, `tournament_id` or `season`; filter `round`, `status` | 2 |
| `get_schedule` | Scheduled and in-progress matches for the next `days` (default 7, max 30) | 2 |
| `get_match` | One match: sets, tiebreak points, ratings before and after, stats, odds | 2 |
| `search_players` | Resolve a name to a `player_id` when the question names a player | 1 |

## Commands That Do NOT Exist

| Not Available | Use Instead |
|--------------|-------------|
| `get_live_scores` | `get_schedule`, or `get_matches` with `status: "live"`; scores are set by set, not point by point |
| `search_matches` | `get_matches` with filters, or `get_player_matches` for one player |
| `get_draw` | `get_tournament` |
| `get_team_schedule` | There are no teams: use `get_schedule` or `get_player_matches` |

## How It Works

**Step 1: Resolve the target.**

| User says | Resolve with |
|-----------|--------------|
| A date ("yesterday", "last Sunday") | Convert to `YYYY-MM-DD`. Dates are UTC, so a late match in the Americas can land on the next date |
| A tournament name | `list_tournaments` for the season, match on `name`, take `tournament_id` (format `188-2025`) |
| A player name | `search_players`, then `get_player_matches` (5 credits) if their log is needed |
| "This week" | `get_schedule` with `days: 7` for upcoming, `get_matches` with `date` for each past day |
| WTA | Add `"league": "wta"` to every call |

**Step 2: Pull the narrowest result.**

- One day of results: `get_matches {"date": "2025-07-13"}`
- One tournament's final: `get_matches {"tournament_id": "188-2025", "round": "Final"}`
- All finals of a season: `get_matches {"season": 2025, "round": "Final", "limit": 100}`
- The whole draw: `get_tournament {"tournament_id": "188-2025"}` (`draw: "all"` adds qualifying, available from 2022)

**Step 3: Read the score.**

`score` is a string such as `4-6 6-4 6-4 6-4` or `7-6(5) 6-3`. In a set decided by a tiebreak the number in brackets is the loser's tiebreak points. `sets[]` has the same information as numbers: `games1`, `games2`, `tiebreak1`, `tiebreak2`, `winner` (1 or 2). Player 1 and player 2 are positions in the record, not seeds or favorites.

**Step 4: Check `outcome` before counting anything.** A real response for a walkover looked like this (trimmed): `"outcome": "walkover", "score": "w/o", "sets": []`. Retirements, defaults and walkovers have partial or empty set data. Count a match as played only when `outcome` is `completed`, and say so when you drop rows.

**Step 5: Report.** Lead with the answer, then the context: tournament, surface, round, score, and one line on what the score says (straight sets, five sets, tiebreaks, a comeback). `get_match` gives `stats.went_the_distance` and `stats.winner_lost_first_set` directly.

## Worked Example

User: "Who won the 2025 Wimbledon final and how?"

```
1. list_tournaments {"season": 2025, "surface": "grass"}     -> 1 credit, find "188-2025"
2. get_matches {"tournament_id": "188-2025", "round": "Final"} -> 2 credits
```

Real record (trimmed): `Jannik Sinner` (seed 1) beat `Carlos Alcaraz` (seed 2) `4-6 6-4 6-4 6-4`, Centre Court, grass. Answer: "Sinner won in four sets after dropping the first (22 games to 18, no tiebreaks). It was the Wimbledon final of 2025 on grass." Total cost: 3 credits.

## Season Logic

- "Last season" is the previous calendar year. A tournament edition belongs to the year it starts.
- Two events can share a week. A date query returns all of them; group by `tournament` before summarizing.
- `status` values are `scheduled`, `live`, `final`. A match with `status: "final"` and `outcome: "walkover"` is final but unplayed.
- Rounds are named as the data lists them (seen in live responses: `Round 1` to `Round 4`, `Group Stage`, `Semifinal`, `Final`). Pass the name exactly; if a filter returns nothing, read `round` from a `get_tournament` response. Use `round_order` to sort them (the Final is 22).
- Draw sizes vary by event (`main_draw_matches` in `list_tournaments` shows 27 to 31 for tour events). Do not assume a fixed number of rounds.

## Credit Usage

| Operation | Credits |
|-----------|---------|
| Resolve tournament id | 1 |
| One day of results (up to 100 matches) | 2 |
| One full draw | 2 |
| One season of results, one tour | about 90 (45 pages of 100 at the time of writing) |
| Detail on one match | 2 |

Do not call `get_match` on every row of a day just to read a score. `get_matches` already returns score and sets. Use `get_match` only for ratings, `stats` or `odds`.

## Anti-patterns

| What Claude Might Do | Why It's Wrong | Do This Instead |
|---------------------|---------------|-----------------|
| Treat `player1` as the favorite or the winner | It is only a record position | Read `winner_id` |
| Report a walkover as a straight-set win | No sets were played | Check `outcome`, say "walkover" |
| Pass "Quarter-finals" or "R1" as `round` | The filter needs the listed name | Use the names from the data, or pull the draw and read `round` |
| Query "today" without UTC in mind | A match that ends after midnight UTC is on the next date | Query the adjacent date when a result is missing |
| Assume five sets | Best of five is for men at Grand Slams only; everything else is best of three | Read the actual `sets[]` |

## Output Format

```
[Tournament] [Year], [Surface], [Round]
[Winner] (seed) d. [Loser] (seed)  [score]
[One line: duration of the match in sets, tiebreaks, comeback, upset by seed or rating]
```

For a day of results, group by tournament and list matches by `round_order`, newest first.

## What to Do Next

| What You Found | Next Action | Skill |
|----------------|-------------|-------|
| An upset | Check ratings and prices before the match | `surface-elo`, `odds-explorer` |
| Tomorrow's match worth a brief | Build the matchup page | `match-preview` |
| A player who keeps appearing | Profile them | `player-scouting` |
| Two players who met again | Pull the full history | `head-to-head-analysis` |
