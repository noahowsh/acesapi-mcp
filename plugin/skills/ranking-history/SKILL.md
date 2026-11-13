---
name: ranking-history
description: "ATP and WTA ranking lists and trajectories: the current top list, the list in force on a past date, a player's ranking history, points movement, ranking versus Elo, and seeding context. Use when the user asks who is number one, how a ranking changed, what the ranking was on a date, or whether the ranking understates a player. Do not use for strength estimates: see surface-elo. Do not use for a full player profile: see player-scouting."
metadata:
  version: 1.0.0
  author: AcesAPI
---

# Ranking History

> **Default data tool:** AcesAPI (`acesapi-tool`).
> `get_rankings` (2 credits) returns a weekly list or, with `player_id`, one player's history. `get_ratings` (2) is the Elo leaderboard for comparison.

You answer ranking questions precisely and explain what a ranking is. A ranking is a rolling points total, not a strength estimate, so use it for seeding and bracket questions and use ratings for strength.

## Coverage

Weekly ATP and WTA lists since 2007, top 100 to 150 a week. The data page counts 1,637 weekly lists covered from 2007 to 2026. Players outside the top 100 to 150 are not in a given week. Some calendar weeks have no list (a real history skipped weeks 33 and 36 in 2026).

## When to Use

- "Who is number one?" "Show me the top 10."
- "What was the ranking list on 1 January 2020?"
- "How did Alcaraz's ranking move this season?"
- "Is the number two ranked player really the second best?"

## When NOT to Use

- Win probability or strength: see `surface-elo`
- A scouting report: see `player-scouting`
- Results: see `match-lookup`

## Commands Available

| Command | What It Does | Credits |
|---------|-------------|---------|
| `get_rankings` | Latest list (default), or by `season` and `week`, or the list in force on `date`; with `player_id`, that player's history and `best_rank`; `limit` caps list rows | 2 |
| `get_ratings` | Elo leaderboard, overall or by surface | 2 |
| `search_players` | Ids, and `current_rank` (null outside the list) | 1 |
| `get_player` | `ranking` block with latest rank and points, plus ratings | 5 |

## Commands That Do NOT Exist

| Not Available | Use Instead |
|--------------|-------------|
| `get_standings` | `get_rankings` |
| `get_race_rankings` | Not available: only the official weekly list |
| `get_ranking_points_breakdown` | Not available: only total points per week |
| `get_live_rankings` | Not available: lists are weekly |

## How It Works

**Step 1: Pick the query.**

| Question | Call |
|----------|------|
| Current top N | `get_rankings {"limit": 10}` |
| List on a past date | `get_rankings {"date": "2020-01-06"}` |
| A specific week | `get_rankings {"season": 2025, "week": 20}` |
| One player's path | `get_rankings {"player_id": "3623"}` |
| WTA | add `"league": "wta"` |

**Step 2: Read the shape.** A list row: `rank`, `previous_rank`, `points`, `player_id`, `name`, `country`; the response has `season`, `week` and `ranking_date`. The latest list at the time of the call was week 40 of 2026, dated 2026-10-01, with the top three as Sinner (11,000 points), Zverev (9,720) and Alcaraz (5,560). A history row: `season`, `week`, `ranking_date`, `rank`, `previous_rank`, `points`, newest first.

**Step 3: Compute what the user wants.** Peak, time at number one, net change over a window, biggest weekly drop. Always show the date range.

## Points Versus Rank

Points tell the story that rank hides. In the real history above, the world number one's points fell from 13,450 (week 31) to 11,000 (week 40) with rank 1 held throughout. That is a drop of 2,450 points, almost 18 percent, while the headline did not move. Read `points` for momentum and the gap to the next player for how safe the position is: 11,000 against 9,720 is a 1,280-point cushion.

Points move for two reasons: new results added, and last year's results dropped off after 52 weeks. A fall is therefore not always bad form. Compare with the player's results from the same weeks a year earlier (`get_player_matches` with `season`).

## Ranking Versus Rating

Compare `get_rankings` with `get_ratings` (overall) for the same player set:

```
rank_gap = rank_by_points - rank_by_elo
```

Large positive gaps (ranked far lower than Elo says) occur for players returning from injury, players who play fewer events and players who peaked recently. Large negative gaps occur for players riding points from one big result that Elo discounts. In the live data, Alcaraz was 3rd on points (5,560) and first on clay Elo. That is a comparison of two different measures, not a contradiction.

Both are summaries of results. Neither is verified by a serve-based model because that data does not exist here.

## Seeding Context

Seeds in a draw follow the ranking at entry. A top-8 seed cannot meet another top-8 seed before the quarterfinal in a standard draw, which makes the ranking relevant for route analysis: use `get_tournament` to see the draw, and `seed1`, `seed2` in matches. A player who is under-ranked relative to Elo is dangerous as an unseeded opponent in an early round.

## Pitfalls

- `current_rank` of `null` means outside the list, not unranked in the sense of zero points.
- Ranking dates are weekly. A question about a specific day needs the `date` parameter, which returns the list in force.
- Gaps in weeks are normal. Do not interpolate silently.
- Comparing rank across tours is meaningless.
- Points systems and the 52-week window mean historical points cannot be compared directly across eras unless the scale is the same. Use rank and the gap to others.

## Credit Usage

| Operation | Credits |
|-----------|---------|
| Current top 10 | 2 |
| A player's full history | 2 |
| List on a date | 2 |
| Elo comparison | + 2 |
| Season of weekly lists | 2 x about 40 = about 80 |

## Anti-patterns

| What Claude Might Do | Why It's Wrong | Do This Instead |
|---------------------|---------------|-----------------|
| Use rank as skill | It is a points total with a rolling window | Pair with Elo |
| Say a player "dropped" when only points fell | Rank may be unchanged | Report both |
| Fill a missing week with the neighbor | Invented data | Show the gap |
| Pass a week number without a season | Ambiguous | Always pass both |
| Quote `previous_rank` as last year's | It is the previous list | Label it "previous week's list" |

## Output Format

```
[Tour] ranking, week [w] of [season] ([date])
 1. [Name] ([country])  [points] pts  (prev [n])
 ...
[Player]: peak [n], now [n], change over [window]: [+/-] points, rank [moved / held]
```

## What to Do Next

| What You Found | Next Action | Skill |
|----------------|-------------|-------|
| Rank far from Elo | Check ratings and surfaces | `surface-elo` |
| A ranking slide | Look at recent results | `player-scouting` |
| A seeded favorite in the next round | Brief the match | `match-preview` |
