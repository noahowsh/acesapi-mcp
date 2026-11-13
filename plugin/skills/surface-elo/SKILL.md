---
name: surface-elo
description: "Tennis Elo by surface: how AcesAPI ratings are built, reading overall versus hard, clay and grass ratings, converting a rating gap to a win probability, tracking rating change over time, and building your own surface-weighted blend. Use when the user asks who is best on clay, how likely A is to beat B on grass, how a rating moved, or how to build a surface rating. Do not use for direct meetings: see head-to-head-analysis. Do not use for set or game-count markets: see set-score-modeling. Do not use for betting decisions: see edge-detection."
metadata:
  version: 1.0.0
  author: AcesAPI
---

# Surface Elo

> **Default data tool:** AcesAPI (`acesapi-tool`).
> `get_ratings` (2 credits) is the leaderboard overall or by surface. `get_player` (5) gives one player's overall and surface ratings with peak. `get_match` (2) gives both players' ratings before and after a match. `get_player_matches` (5 per page) gives `rating_before` and `rating_after` over time.

You turn ratings into probabilities. The ratings are AcesAPI's own, computed from every completed tour-level singles match since 2007, so they are inspectable and you can check any claim against `get_match`.

## How the Rating Is Built

From the `method` field returned by `get_ratings`:

- Elo from every completed singles match on the tour since 2007 (main draw and qualifying), start 1500
- `K = 250 / (matches + 5)^0.4`, so new players move fast and veterans move slowly
- The surface rating counts only matches on that surface, so it has its own match count and its own K
- Walkovers, defaults and retirements are not rated
- A player is listed once they have at least 10 rated matches and a rated match since `active_since` (default one year ago)

**Consistency check on the 2025 Wimbledon final** (real `get_match` output): Sinner overall 2325 to 2335 (+10), Alcaraz 2278 to 2267 (-11). With the standard 400-point logistic, Sinner's expected score was 0.567, so a +10 change implies K of about 23. The formula gives about 23 for a player with roughly 400 rated matches. The overall rating is therefore consistent with a 400-point logistic scale.

## When to Use

- "Who is the best clay-court player right now?"
- "What is Sinner's chance against Alcaraz on grass?"
- "How much did that loss cost him?"
- "Is a player's grass rating real or based on 12 matches?"
- "Build a better rating than the overall one"

## When NOT to Use

- The direct record between the two: see `head-to-head-analysis`
- Total games, set scores, tiebreak odds: see `set-score-modeling`
- Whether a price is worth taking: see `edge-detection`

## Commands Available

| Command | What It Does | Credits |
|---------|-------------|---------|
| `get_ratings` | Leaderboard: `rank`, `rating`, `surface_matches`, `last_match`; filter `surface`, `active_since`, `limit` | 2 |
| `get_player` | One player: overall rating, per-surface ratings, peak | 5 |
| `get_match` | `players[].rating`: `before`, `after`, `surface_before`, `surface_after` | 2 |
| `get_player_matches` | `rating_before`, `rating_after` per match, filter by `surface` | 5 |
| `get_surface_splits` | `ratings` block with a rating and match count per surface | 3 |

## Commands That Do NOT Exist

| Not Available | Use Instead |
|--------------|-------------|
| `get_elo` | `get_ratings` |
| `get_win_probability` | Compute from the formula below |
| `get_rating_history` | `get_player_matches` and read `rating_after` in date order |
| `get_serve_rating` | Not available: no serve data |

## Win Probability

For ratings `Ra` and `Rb` on the same scale:

```
P(A beats B) = 1 / (1 + 10^(-(Ra - Rb) / 400))
```

This is a single-match probability for the whole match, regardless of format. A 100-point gap is 64 percent, 200 is 76 percent, 300 is 85 percent.

**Worked example (real ratings before the 2025 Wimbledon final, grass):** Sinner surface 1995, Alcaraz surface 2176. Gap -181, so P(Sinner) = 1 / (1 + 10^(0.4525)) = 0.26. The overall ratings (2325 against 2278) said 0.57. The two numbers disagree by 31 points of probability because the grass ratings had few matches behind them. The market's no-vig close was 0.524 for Sinner (Pinnacle, see `odds-explorer`), closer to the overall number. Neither rating alone is the answer: blend them.

## The Scale Pitfall

Overall and surface ratings are on different scales. A surface rating sees fewer matches, so it is less settled, and it starts at the same 1500 baseline with a different number of updates. In the example, Sinner's overall was 2325 and his grass was 1995. Never subtract a surface rating from an overall rating, and never compare two players' ratings from different surfaces. Compare overall to overall, or the same surface to the same surface.

## Blending Overall and Surface

A practical blend that respects small samples:

```
w = n_surface / (n_surface + c)          # c = shrinkage, try 30
R_blend = w * (R_surface - R_surface_baseline) + (1 - w) * 0 + R_overall
```

where `R_surface_baseline` is the tour average of that surface rating among active players (take it from `get_ratings` with a large `limit`). The idea: start from the overall rating, add the player's surface edge, and trust the edge in proportion to its match count. Fit `c` by walk-forward log loss (see `walk-forward-validation`), not by feel. Report it as a model, because it is.

## Rating Change and Form

`rating_after - rating_before` per match is the update. Over a window it measures results against expectation:

- Sum over the last 10 completed matches = rating form
- A player who wins a lot at low-rated opponents barely moves; a single loss to a much lower-rated opponent costs a lot
- Retirements and walkovers have `null` rating fields (real example: a walkover row had `rating_before: null`), so drop them

## Pitfalls

- **Leakage.** Using `rating.after` or `surface_after` to predict that same match. Always use `before`.
- **Stale ratings.** A player who has not played for months keeps the old rating. `last_match` in `get_ratings` tells you. Returns from injury are the largest errors.
- **Small surface samples.** `surface_matches` below about 30 means the surface rating is mostly noise. Grass is usually the thinnest because the grass season is short (Alcaraz had 39 grass matches against 121 on clay).
- **Best-of-five.** Men's Grand Slam matches are best of five, which favors the better player more than best of three. The rating does not know the format, so a gap understates favorites at Slams. Check this with a calibration table (see `probability-calibration`) before relying on it.
- **Inactive players are filtered.** Players with no rated match since `active_since` and fewer than 10 rated matches are missing from `get_ratings`.
- **Tour boundaries.** ATP and WTA ratings are separate pools. Never compare a WTA rating to an ATP rating.

## Credit Usage

| Task | Calls | Credits |
|------|-------|---------|
| Top 20 on a surface | `get_ratings` | 2 |
| One match probability, both players | 2 x `get_player` or `get_ratings` for both | 4 to 10 |
| Rating history for one player, last 50 | `get_player_matches` | 5 |
| Pre-match ratings for one player's season | `get_player_matches` with `season` | 5 per 50 matches |

For a model, take pre-match ratings from `get_player_matches` (5 credits per 50 matches) rather than calling `get_match` per row.

## Anti-patterns

| What Claude Might Do | Why It's Wrong | Do This Instead |
|---------------------|---------------|-----------------|
| Predict with `rating.after` | Contains the outcome | Use `before` |
| Compare a clay rating to a hard rating | Different scales | Same surface only |
| Trust a 12-match surface rating | Noise | Blend with overall, or say it is thin |
| Quote 76 percent as "the model says" without a source | Needs the method and the ratings | Show both ratings and the formula |
| Mix ATP and WTA ratings | Separate pools | Keep tours apart |

## Output Format

```
[A] vs [B], [surface]
Overall:   A 2325  B 2278   -> A 57%
Surface:   A 1995  B 2176   -> A 26%   (grass sample thin)
Blend:     A xx%
Market (no-vig close): xx%
```

## What to Do Next

| What You Found | Next Action | Skill |
|----------------|-------------|-------|
| A probability | Compare with the market | `edge-detection` |
| A rating gap with a thin sample | Look at the direct record | `head-to-head-analysis` |
| A model-ready rating column | Build features | `feature-engineering` |
| Probabilities to be trusted | Check calibration | `probability-calibration` |
