---
name: head-to-head-analysis
description: "Head-to-head analysis for two tennis players: wins each, sets won, record by surface and in finals, every meeting with its score, and how much weight a small head-to-head deserves. Use when the user asks who leads a rivalry, how two players match up on a surface, or whether a past result predicts the next one. Do not use for a player's overall profile: see player-scouting. Do not use for win probabilities from ratings: see surface-elo. Do not use for the pre-match brief that combines everything: see match-preview."
metadata:
  version: 1.0.0
  author: AcesAPI
---

# Head-to-Head Analysis

> **Default data tool:** AcesAPI (`acesapi-tool`).
> `get_head_to_head` (3 credits) returns the whole record: summary and every meeting. `search_players` (1) resolves the two ids. `get_player_matches` with `opponent_id` (5) adds ratings at the time of each meeting.

You read a rivalry honestly. A head-to-head is a tiny sample, often confounded by surface, age and form at the time. Report the record, then say how much it should move a forecast, which is usually very little once ratings are known.

## When to Use

- "Who leads Sinner against Alcaraz?"
- "How do they split on clay?"
- "Has she ever beaten her in a final?"
- "Does the head-to-head matter for tomorrow?"

## When NOT to Use

- One player only: see `player-scouting`
- The probability from ratings: see `surface-elo`
- A full pre-match brief with prices: see `match-preview`

## Commands Available

| Command | What It Does | Credits |
|---------|-------------|---------|
| `search_players` | Resolve each name to a `player_id` | 1 |
| `get_head_to_head` | `summary` (matches, wins, sets, `by_surface`, `in_finals`, walkovers) and `matches[]` | 3 |
| `get_player_matches` | Use `opponent_id` to get one player's meetings with `rating_before` for each | 5 |
| `get_match` | Detail on one meeting: sets, tiebreak points, ratings | 2 |
| `get_ratings` | Current ratings for context | 2 |

## Commands That Do NOT Exist

| Not Available | Use Instead |
|--------------|-------------|
| `get_h2h` | `get_head_to_head` |
| `get_rivalry` | `get_head_to_head` plus the method below |
| `get_head_to_head_odds` | Not available: pull `get_match` for the upcoming match |

## How It Works

**Step 1: Resolve both ids.** `search_players {"name": "sinner"}` returns `"player_id": "3623"`; `search_players {"name": "alcaraz"}` returns `"3782"`. Add `league: "wta"` for the WTA. Both players must be on the same tour.

**Step 2: One call.** `get_head_to_head {"player_id": "3623", "opponent_id": "3782"}`.

Real output (trimmed), `summary` as returned:

```json
{"matches": 17,
 "wins": {"3623": 7, "3782": 10},
 "sets_won": {"3623": 25, "3782": 26},
 "by_surface": {"clay": {"3623": 2, "3782": 3},
                "hard": {"3623": 3, "3782": 7},
                "grass": {"3623": 2, "3782": 0}},
 "in_finals": {"3623": 4, "3782": 5},
 "walkovers": 0}
```

Keys of `wins` and `by_surface` are `player_id` strings. Map them to names before writing the answer.

**Step 3: Read the matches.** `matches[]` is newest first. In the live response, the latest meeting was the 2026 Monte-Carlo Masters final on clay, `7-6(5) 6-3` for Sinner, and the one before it the 2025 Nitto ATP Finals final (indoor hard), `7-6(4) 7-5` for Sinner. Report recency: a record of 10-7 where the leader lost the last two is a different story from 10-7 the other way.

**Step 4: Weigh it.** Compute the rivalry as a sample, not a fact.

## Method: How Much Should a Head-to-Head Count?

A rivalry record of `a` wins to `b` wins is `n = a + b` observations of a process the ratings already summarize. Use it as a small adjustment:

```
P_h2h_shrunk = (a + m * P_rating) / (n + m)        # m = prior strength, try 10
```

where `P_rating` is the pre-match probability from `surface-elo` and `m` expresses how many matches' worth of weight the rating gets. At 10-7 and `P_rating = 0.50` with `m = 10`, the shrunk estimate is `(10 + 5) / 27 = 0.56` for the leader, not 10/17 = 0.59. With `n = 3` it barely moves. Pick `m` by out-of-sample log loss; if you cannot test it, state that `m` is a judgment call.

Better still, check whether the head-to-head adds information beyond ratings: regress the result of each meeting on the pre-match rating gap and a prior-meeting-record feature, in time order (see `walk-forward-validation`). In most datasets the second feature adds little.

## What Makes a Rivalry Misleading

- **Surface mix.** The 17 meetings above are spread over hard (10), clay (5) and grass (2). A hard-court lead says little about a clay match.
- **Time.** Meetings years ago involved younger versions of both players. Weight recent meetings, or use `rating_before` per meeting to see how mismatched each one was.
- **Format.** Slam meetings are best of five for men. Finals are a small subset that often involve two players in form.
- **Retirements and walkovers.** The tool lists walkovers but does not count them as wins. A retirement is counted if sets were recorded; read the `outcome` of the meeting.
- **Sample size.** With under about 8 meetings, any split is within noise. The Wilson interval for 10 of 17 is roughly 0.36 to 0.78.

## Worked Example

User: "How do Sinner and Alcaraz compare on clay?"

```
1. get_head_to_head {"player_id": "3623", "opponent_id": "3782"}      -> 3 credits
2. get_ratings {"surface": "clay", "limit": 10}                       -> 2 credits
```

Clay record: Alcaraz 3, Sinner 2. Clay ratings from the live call: Alcaraz 2247 (121 clay matches), Sinner 2209 (106). Rating gap 38 points gives Alcaraz about 55 percent on clay. The record, five matches, agrees in direction and adds almost nothing. The most recent clay meeting went to Sinner, in straight sets. The honest summary: a coin flip with a small lean to Alcaraz, and the head-to-head is too small to change it. Total cost: 5 credits.

## Credit Usage

| Operation | Credits |
|-----------|---------|
| Resolve two ids | 2 |
| Head to head | 3 |
| Ratings context | 2 to 10 |
| Per-meeting ratings via `get_player_matches` | 5 |

## Anti-patterns

| What Claude Might Do | Why It's Wrong | Do This Instead |
|---------------------|---------------|-----------------|
| Say "he owns her" off a 3-1 record | n = 4 | Report the record and say it is a small sample |
| Mix tours | Ids differ and the players never meet | Same `league` for both |
| Ignore surface | A grass record does not transfer to clay | Use `by_surface` |
| Count walkovers as wins | They are not counted by the tool | Use the summary |
| Use the record as the probability | Ignores everything else | Shrink toward the rating probability |

## Output Format

```
[A] vs [B]: [a]-[b] overall ([n] matches)
By surface: hard [x]-[y], clay [x]-[y], grass [x]-[y]
In finals: [x]-[y]
Last 3: [date] [tournament] [winner] [score] ...
Weight: [low / moderate], because [sample, surface mix, recency]
```

## What to Do Next

| What You Found | Next Action | Skill |
|----------------|-------------|-------|
| A clear surface split | Check surface ratings | `surface-elo` |
| A decision on an upcoming match | Build the brief | `match-preview` |
| A head-to-head feature idea | Add it with a time guard | `feature-engineering` |
