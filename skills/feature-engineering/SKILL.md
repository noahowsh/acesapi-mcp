---
name: feature-engineering
description: "Building leak-free features for tennis match prediction from AcesAPI data: pre-match Elo (overall and surface), rating gaps, rolling form, days of rest and recent load, head-to-head with a time guard, surface and format flags, and a symmetric pair layout. Use when the user is building a model, asks what features to use, or suspects leakage. Do not use for model fitting or tuning: see walk-forward-validation. Do not use for calibration: see probability-calibration. Do not use for quick lookups: see match-lookup."
metadata:
  version: 1.0.0
  author: AcesAPI
---

# Feature Engineering

> **Default data tool:** AcesAPI (`acesapi-tool`).
> Bulk results: `get_matches` by `season` (2 credits per 100 matches, use `offset`). Per-match pre-match ratings: `get_match` (2 each) or `get_player_matches` (5 per 50). Ages, hand, height: `get_player` (5). Ranking on a date: `get_rankings` with `date` (2).
> The cheapest design: pull seasons of results with `get_matches` and compute your own Elo and rolling features locally. About 90 credits per tour-season.

You turn match records into a table where each row is one match and every feature was knowable before the first ball. The single biggest risk is leakage, so every feature below states what it is allowed to see.

## When to Use

- "What features should I use to predict tennis matches?"
- "How do I build a rating feature without leakage?"
- "My model is 80 percent accurate, why?" (it is leaking)
- "Build a dataset from 2015 to 2025"

## When NOT to Use

- Evaluating the model: see `walk-forward-validation`
- Probability quality: see `probability-calibration`
- Using a price as a feature: see `odds-analysis` first, and treat it separately (see below)

## Commands Available

| Command | What It Does | Credits |
|---------|-------------|---------|
| `get_matches` | Season of results with sets, surface, round, seeds, winner; paginate with `limit`, `offset` | 2 |
| `get_player_matches` | One player's matches with `rating_before`, `rating_after` | 5 |
| `get_match` | `players[].rating.before` and `surface_before`, `stats`, `odds` | 2 |
| `get_player` | `date_of_birth`, `height_in`, `plays`, country, debut year via the profile | 5 |
| `get_rankings` | List in force on a `date`, for rank and points as of before the match | 2 |
| `get_head_to_head` | Prior meetings (only ever use meetings before the match date) | 3 |
| `get_tournament` | Draw structure | 2 |

## Commands That Do NOT Exist

| Not Available | Use Instead |
|--------------|-------------|
| `get_features` | Build locally from the calls above |
| `get_serve_stats` | Not available: no serve or break-point features |
| `get_pre_match_ratings` | `rating.before` in `get_match`, `rating_before` in `get_player_matches` |
| `get_injuries` | Not available: proxy with long gaps and retirements |

## Row Design: One Match, Symmetric Pair

Each match record has `player1` and `player2`. Do not treat position as meaningful. Two valid layouts:

1. **Difference layout.** Pick the focal player at random per row (or alternate), compute `feature_focal - feature_opponent`, and the label is "focal won". Mirror the dataset (add the swapped row) so the model sees both orientations; evaluate on one orientation only.
2. **Paired layout.** Keep both players' features and enforce symmetry: `P(A beats B) + P(B beats A) = 1`, by averaging the model's output across the swap.

A model that learns "player1 wins more often" has learned data ordering, not tennis.

## Feature Families

**Strength (pre-match only)**

| Feature | Source | Rule |
|---------|--------|------|
| `elo_gap` | `rating.before` for each player | Never `after` |
| `surf_elo_gap` | `surface_before` | Same surface only; thin early in a career |
| `elo_blend_gap` | shrink surface toward overall (see `surface-elo`) | Fit shrinkage by walk-forward |
| `rank_gap_log` | `log(rank2) - log(rank1)` from the list in force before the match | Rank is null outside the top 100 to 150; use an indicator plus a cap (e.g. 200) |
| `points_gap` | list points before the match | Same cap logic |

**Form and load**

| Feature | Definition | Rule |
|---------|------------|------|
| `form_10` | sum of `rating_after - rating_before` over the last 10 completed matches | Shift by one: exclude the current match |
| `win_rate_surface_20` | wins in last 20 matches on this surface | Min 5, else missing |
| `games_share_10` | games won divided by games played, last 10 | A serve and return proxy |
| `days_rest` | days since the previous match | Cap at 60; flag returns after long gaps |
| `sets_last_7d`, `games_last_7d` | sets or games played in the previous 7 days | Fatigue proxy |
| `deciding_sets_14d` | three or five set matches in 14 days | Same |

**Context**

| Feature | Source |
|---------|--------|
| `surface`, `indoor` | match record (`indoor` may be null; encode as unknown) |
| `best_of_5` | men's Grand Slam main draw; known in advance |
| `round_order` | match record |
| `seed_gap` | `seed1`, `seed2`; null for unseeded, encode as 33 or a missing flag |
| `age_gap`, `height_gap`, `hand_matchup` | `get_player` bio (compute age at match date) |
| `tourney_tier` | `major` flag from `list_tournaments`, or Masters/1000 by name |

**Head to head with a time guard**

Compute from `get_head_to_head` only meetings with `match_date` before the current match. Use `wins_a - wins_b` shrunk by `n / (n + 10)`; set to zero when `n < 3`. Do not call `get_head_to_head` per row of a large dataset (3 credits each). Build the history from your own results table instead.

## Rebuilding Elo Locally

If you compute ratings yourself from `get_matches`, you can reproduce the published method: start 1500, update both players with `K = 250 / (matches + 5)^0.4` where `matches` is the player's own count of rated matches so far (separately for each surface rating), skip walkovers, defaults and retirements, and expected score `1 / (1 + 10^(-(Ra - Rb)/400))`. Your numbers will differ from `rating.before` where your match pool differs from AcesAPI's (qualifying is included in theirs, from 2022). Validate on a sample: compare your pre-match value with `rating_before` from `get_player_matches` for one player, and expect agreement to within a few points when pools match.

```python
def update(ra, rb, na, nb, a_won):
    ea = 1 / (1 + 10 ** (-(ra - rb) / 400))
    ka = 250 / (na + 5) ** 0.4
    kb = 250 / (nb + 5) ** 0.4
    s = 1.0 if a_won else 0.0
    return ra + ka * (s - ea), rb + kb * ((1 - s) - (1 - ea))
```

Process matches strictly in date order (`starts_at`), and write the pre-match rating into the row before applying the update.

## Leakage Checklist

| Leak | Why | Fix |
|------|-----|-----|
| `rating.after`, `surface_after` | Contains this match's result | Use `before` |
| Score, `sets`, `games1`, `stats.total_games` of the target match | It is the outcome | Drop from features |
| Rank from the list dated after the match | Includes the result | Take `get_rankings` with `date` set to the day before |
| Rolling means that include the current row | Self-reference | Shift by 1 before windowing |
| Career record from `get_player` pulled today | Includes later matches | Rebuild from results as of the match date |
| Random train/test split | Future matches train the past | Time split, see `walk-forward-validation` |
| Odds close as a feature, then reporting accuracy | The market already knows | Report it as a market-informed model; compare against the market baseline |
| Round and draw knowledge | Fine, known in advance | Keep |
| Final-round survivors | Winners reach late rounds | Do not condition on round reached by outcome |

Sanity test: a pre-match tennis model that beats the closing line by a wide margin is leaking. Rating-only models usually land in the mid-60s for accuracy on tour-level matches (run the Elo baseline on your own data to confirm); treat 75 percent as a bug to explain.

## Missing Data

- Walkovers, retirements: drop from training and from rating updates, keep as a "retired recently" flag for the next match.
- Qualifying draw matches: available from 2022; the rating updates include them, so models trained before and after 2022 see different coverage.
- Rank null: indicator plus cap. Never fill with 0.
- First matches of a career: few prior matches means the rating is unsettled; include `matches_played_log` as a feature so the model can discount.

## Credit Usage

| Dataset | Calls | Credits |
|---------|-------|---------|
| One tour, one season of results | about 45 `get_matches` pages | about 90 |
| Ten seasons, one tour | about 450 pages | about 900 |
| Ratings from `get_match` per row | 1 per match | 2 per match: avoid, recompute locally |
| Player bios for 300 players | 300 `get_player` | 1,500: sample or only fetch finalists |

State the credit estimate before pulling more than one season.

## Anti-patterns

| What Claude Might Do | Why It's Wrong | Do This Instead |
|---------------------|---------------|-----------------|
| Use `rating.after` as a feature | Leak | `before` |
| Let `player1` mean something | It is record order | Symmetrize |
| Fill missing rank with 0 | 0 would be better than #1 | Indicator and cap |
| Add career win rate from today's profile | Includes the future | Rebuild as-of |
| Evaluate on a shuffled split | Leak | Walk forward |
| Add 80 features for 20,000 rows | Overfit | Start with Elo gap, surface Elo gap, rest, form |

## What to Do Next

| What You Built | Next Action | Skill |
|----------------|-------------|-------|
| A feature table | Fit and evaluate in time order | `walk-forward-validation` |
| Predictions | Check probabilities | `probability-calibration` |
| A strategy | Test against closing lines | `backtesting` |
