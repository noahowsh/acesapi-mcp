---
name: match-preview
description: "One-page pre-match brief for an upcoming ATP or WTA match: tournament and surface context, both players' ratings overall and on the surface, recent form, head to head, route through the draw, and the market price if the event is covered. Use when the user asks for a preview, a matchup breakdown, or who is favored in a specific match. Do not use for results: see match-lookup. Do not use for deep single-player work: see player-scouting. Do not use for the bet decision: see edge-detection."
metadata:
  version: 1.0.0
  author: AcesAPI
---

# Match Preview

> **Default data tool:** AcesAPI (`acesapi-tool`).
> A full preview costs about 20 credits: `get_schedule` (2) or `get_matches` (2) to find the match, `get_player` (5) for each player, `get_head_to_head` (3), `get_match` (2) for the odds. Add `get_surface_splits` (3 each) when the surface matters.

You assemble a decision-ready brief. Lead with who the evidence favors and by how much, then the reasons. Keep every number sourced from a call you made. Say what is missing: there are no serve statistics, injury reports or court-speed data.

## When to Use

- "Preview tomorrow's Alcaraz match"
- "Who is favored in the Shanghai third round, and why?"
- "Break down the final for me"

## When NOT to Use

- A finished match: see `match-lookup`
- A single player's whole profile: see `player-scouting`
- Whether to bet: see `edge-detection`

## Commands Available

| Command | What It Does | Credits |
|---------|-------------|---------|
| `get_schedule` | Find the match, `match_id`, start time, round, court | 2 |
| `get_match` | Match record, ratings (null before play), and the `odds` array | 2 |
| `get_player` | Bio, ratings by surface, career record, last 10 | 5 |
| `get_head_to_head` | Meetings, by surface, in finals | 3 |
| `get_surface_splits` | Record on today's surface | 3 |
| `get_player_stats` | Record against top-10 and top-50 opponents | 3 |
| `get_tournament` | The draw: who each player has beaten to get here | 2 |
| `get_rankings` | Ranking and points, if the question is about seeding | 2 |
| `search_players` | Ids from names | 1 |

## Commands That Do NOT Exist

| Not Available | Use Instead |
|--------------|-------------|
| `get_preview` | This skill builds it from the calls above |
| `get_odds` | `get_match` and read `odds` |
| `get_serve_stats` | Not available |
| `get_court_speed` | Not available: use surface and the `indoor` flag only |
| `get_injury_report` | Not available: say so, and look at recent retirements in `get_player_matches` |

## How It Works

**Step 1: Find the match.** `get_schedule {"days": 2}`. Real fields: `match_id`, `tournament`, `surface`, `indoor`, `round`, `court`, `starts_at`, `player1`, `player2`, `seed1`, `seed2`, `status`. `indoor` can be `null` when unknown; do not assume.

**Step 2: Pull the match record and price.** `get_match {"match_id": "..."}`. Before play, `players[].rating` is `null` (real response for a scheduled match), so take ratings from `get_player` or `get_ratings`. `odds` has one row per book if the event is a Grand Slam, a Masters or a WTA 1000; otherwise it is empty.

**Step 3: Ratings and form.** `get_player` for each player: overall rating, surface rating and match count on today's surface, career record, last 10. Compute the rating change over the last 10 completed matches as the form signal (see `player-scouting`).

**Step 4: Head to head.** `get_head_to_head`. Weigh by sample size (see `head-to-head-analysis`).

**Step 5: Route.** `get_tournament` for the event: list each player's wins so far, and total games or sets dropped. A player who has played three three-setters carries more load than one who has won in straight sets. This is a signal from scores, not from physical data, so say "load proxy".

**Step 6: Model probability.** Elo probability from `surface-elo`. If the event is covered, add the no-vig close from `odds-analysis`. Do not force them to agree; show both.

**Step 7: Write the brief.**

## Worked Example (structure with real fields)

Match: Alexander Zverev vs Quentin Halys, Shanghai Masters 2026, Round 3, hard, scheduled 2026-10-11. From `get_match`:

- `rating` was `null` for both (not played yet), so ratings come from `get_player`
- `odds` had six books. Pinnacle close: Zverev -673, Halys +537, margin 2.8%, no-vig Zverev about 84.7%
- `games_spread1` -3.5 and `games_total` 22.5 at Pinnacle (a two-set match line)

Brief:

```
Zverev (-673) vs Halys (+537), Shanghai R3, hard
Market: Zverev ~85% no-vig (Pinnacle), range across books [x]% to [y]%
Rating: Zverev [overall / hard], Halys [overall / hard]  -> model [z]%
H2H: [a]-[b] ([n] matches), last meeting [date]
Load: games and sets dropped so far this event
Games line: Zverev -3.5 games, total 22.5
Missing: serve data, injuries, court speed
```

Cost: 2 (schedule) + 2 (match) + 10 (two players) + 3 (head to head) = 17 credits.

## Reading Tennis Matchups from Scores

| Signal | Source | Use |
|--------|--------|-----|
| Surface fit | `get_surface_splits` games-won share on the surface, with match count | Is the surface rating real? |
| Big-match record | `get_player_stats` vs top 10 and top 50 | Quality of wins |
| Tiebreak record | `tiebreaks_won`, `tiebreaks_lost` | Close-set tendency (small sample) |
| Deciding sets | `deciding_sets_won` of `deciding_sets` | Noisy, do not lean on it |
| Time since last match | `last_match` in `search_players` | Rust or fatigue (days off) |
| Format | Best of five at men's Slams, otherwise best of three | Favorites win more in best of five |

## Credit Usage

| Brief depth | Calls | Credits |
|-------------|-------|---------|
| Quick: match, price, ratings | `get_schedule`, `get_match`, `get_ratings` | about 6 |
| Standard | + `get_player` x2, `get_head_to_head` | about 20 |
| Full with route and splits | + `get_tournament`, `get_surface_splits` x2 | about 28 |

## Anti-patterns

| What Claude Might Do | Why It's Wrong | Do This Instead |
|---------------------|---------------|-----------------|
| Invent serve numbers | Not in the data | Name the gap |
| Use `rating.after` from `get_match` | Contains the result | Pre-match ratings only |
| Declare a favorite from rank alone | Rank is a points total and can lag form | Use Elo plus market |
| Skip the tour check | WTA needs `league: "wta"` | Pass it everywhere |
| Quote odds for an uncovered event | The array is empty | Say the event is outside coverage |
| Rely on a 2-meeting head to head | Too small | Down-weight it |

## Output Format

```
[P1] vs [P2]  |  [Tournament], [Round], [Surface], [start time UTC]
Lean: [P] at [x]% (model), market [y]% (no-vig close, Pinnacle) 
Why: 1) ... 2) ... 3) ...
Risks and gaps: ...
```

Always include "Estimates, not guarantees" when probabilities are shown, and never present a lean as a bet recommendation.

## What to Do Next

| What You Found | Next Action | Skill |
|----------------|-------------|-------|
| Model and market disagree | Test it | `edge-detection` |
| Totals or set markets of interest | Model them | `set-score-modeling` |
| Thin surface sample | Check the rating blend | `surface-elo` |
