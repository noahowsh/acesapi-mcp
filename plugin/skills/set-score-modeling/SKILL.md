---
name: set-score-modeling
description: "Modeling tennis scores without serve data: match win probability from set and game win probabilities, best-of-three versus best-of-five, set-score distributions (2-0, 2-1, 3-0), tiebreak rates, total games and games handicap lines, and the games_total and games_spread1 fields in match odds. Use when the user asks about straight sets odds, how many games a match will run, tiebreak frequency, or how a match probability maps to set scores. Do not use for rating-based win probability: see surface-elo. Do not use for player props: not supported. Do not use for the bet decision: see edge-detection."
metadata:
  version: 1.0.0
  author: AcesAPI
---

# Set Score Modeling

> **Default data tool:** AcesAPI (`acesapi-tool`).
> `get_matches` (2 credits per 100 matches) gives every set and tiebreak score for building distributions. `get_surface_splits` (3) and `get_player_stats` (3) give tiebreak and games-won rates. `get_match` (2) has the `games_total` and `games_spread1` lines inside `odds` for the few books that post them.

You model the shape of a match: how likely a straight-sets win is, how many games to expect, how often tiebreaks occur. The standard tool for this, a point-by-point serve and return model, needs first-serve and break-point data that this dataset does not contain. So this skill builds from what scores give: games won share, hold-rate proxies and empirical set distributions. Say that out loud when presenting results.

## When to Use

- "How likely is a straight-sets win?"
- "What is a reasonable total games line for this match?"
- "How often do ATP matches on grass go to a tiebreak?"
- "Convert a 70 percent match probability into set probabilities"
- "Is the market's games handicap consistent with its moneyline?"

## When NOT to Use

- A pure win probability from ratings: see `surface-elo`
- Serve speed, aces, break points, player props: not in the data
- Deciding on a bet: see `edge-detection`

## Commands Available

| Command | What It Does | Credits |
|---------|-------------|---------|
| `get_matches` | Matches with `sets[]` (`games1`, `games2`, `tiebreak1`, `tiebreak2`, `winner`) for building distributions | 2 |
| `get_match` | `stats.total_games`, `stats.tiebreaks`, `stats.went_the_distance`; `odds[].games_total`, `odds[].games_spread1` | 2 |
| `get_surface_splits` | Per-surface sets, games, tiebreaks, deciding sets, 6-0 sets | 3 |
| `get_player_stats` | Season record with tiebreaks and deciding sets, by round | 3 |
| `get_head_to_head` | Scores of prior meetings | 3 |
| `get_tournament` | All scores of an event (for event-level game totals) | 2 |

## Commands That Do NOT Exist

| Not Available | Use Instead |
|--------------|-------------|
| `get_serve_stats` | Not available. `get_match` returns `serve_stats: null` |
| `get_break_points` | Not available |
| `get_point_by_point` | Not available |
| `get_set_odds` | Not available: only moneylines plus `games_total` and `games_spread1` on some books |
| `get_total_games_line` | Read `games_total` from `get_match` |

## From Match Probability to Set Probability

Let `q` be a player's probability of winning any one set (assumed constant and independent, which is an approximation). Then:

```
Best of three:  P(match) = q^2 (3 - 2q)
Best of five:   P(match) = q^3 (10 - 15q + 6q^2)
```

To go from a match probability `P` (from `surface-elo` or a no-vig close) back to `q`, solve by bisection. Real example: a no-vig match probability of 0.524 (Pinnacle close for Sinner in the 2025 Wimbledon final, best of five) corresponds to `q = 0.5128`; in best of three the same match probability needs `q = 0.516`. The format matters: the same set strength gives a more extreme match probability in best of five.

**Set-score distribution, best of three, for player A with set probability q:**

```
P(A wins 2-0) = q^2
P(A wins 2-1) = 2 q^2 (1 - q)
P(B wins 2-1) = 2 (1-q)^2 q
P(B wins 2-0) = (1-q)^2
```

At `q = 0.6`: 36 percent for 2-0, 28.8 percent for 2-1, and 64.8 percent match win. These are model outputs; compare them with the empirical shares from `get_matches`.

## From Game Win Rate to Set Probability (without serve data)

Games-won share is available per player (`games_won_pct` in `get_surface_splits`, 0.58 for one top player over a career). Map two players' shares to a matchup game probability with a log5-style formula, then to a set probability with a hold model:

```python
from functools import lru_cache

def set_win(hA, hB, first='A'):
    """P(A wins a set). hA, hB = probability each holds serve. Alternating serve."""
    @lru_cache(None)
    def go(a, b, srv):
        if a >= 6 and a - b >= 2: return 1.0
        if b >= 6 and b - a >= 2: return 0.0
        if a == 7: return 1.0
        if b == 7: return 0.0
        if a == 6 and b == 6:
            return 0.5 + 0.5 * (hA - hB)     # crude tiebreak: tilts with the hold gap
        nxt = 'B' if srv == 'A' else 'A'
        if srv == 'A':
            return hA * go(a + 1, b, nxt) + (1 - hA) * go(a, b + 1, nxt)
        return hB * go(a, b + 1, nxt) + (1 - hB) * go(a + 1, b, nxt)
    return go(0, 0, first)
```

Equal holds of 0.80 give exactly 0.5; holds of 0.85 and 0.80 give `q = 0.591`. The problem: **hold rates are not in the data.** You can only calibrate them: choose `hA`, `hB` so that the model reproduces the match win probability (from ratings or the market) and the total games the market expects. That is a fitted model, not an observation. Present it as "consistent with a hold gap of about X points", never as measured serve strength.

## Total Games

Observed in `get_match` for a real final: `stats.total_games` 40 over four sets, no tiebreaks. The Pinnacle row carried `games_total` 41.5 and `games_spread1` -0.5.

Build the expectation from data, not memory:

1. `get_matches` for a season, filtered to completed matches of one tour, one surface, one format.
2. Per match, total games = sum over `sets[]` of `games1 + games2`.
3. Take mean and standard deviation by surface and by format. Total games are right-skewed: a few five-set matches run long.
4. Adjust for the matchup. Two evenly matched players generate more games and more sets than a mismatch. The relation is roughly monotone in the rating gap, so regress total games on the absolute rating gap, surface and format on past matches (time-ordered, see `walk-forward-validation`).

Use the market's `games_total` as a benchmark where it exists, not as a fact: it is one book's line.

## Tiebreak Frequency

Tiebreak share of sets is computable from `get_surface_splits`:

```
tiebreak_share = (tiebreaks_won + tiebreaks_lost) / (sets_won + sets_lost)
```

From a real call (one player's whole career): hard 92 of 545 sets (16.9 percent), clay 52 of 322 (16.1 percent), grass 21 of 128 (16.4 percent). The differences are inside sampling noise, which is a useful finding in itself. Do not claim grass produces more tiebreaks from one player's record; build the tour-level rate from `get_matches`.

Tiebreak outcomes are close to coin flips: keep the tiebreak model near 50 percent, tilted at most slightly by the hold gap or the rating gap, and shrink toward 0.5 when data is thin.

## Pitfalls

- **Independence.** Sets are not independent: momentum, fatigue and tactics link them. The formulas above are a baseline. Check them against empirical 2-0 and 2-1 frequencies in `get_matches` and correct with a fitted adjustment.
- **Format mixing.** Men's Grand Slams are best of five; everything else, and all WTA matches, are best of three. Never pool them for totals or set distributions.
- **Retirements.** A retired match has an incomplete score. Exclude `outcome != "completed"` from distributions, or you bias total games down.
- **Walkovers** have empty `sets`.
- **Survivorship in event totals.** Early rounds have more mismatches than late rounds. Condition on round or on rating gap.
- **Over-reading the line.** `games_total` appears for only a few books (Pinnacle in the examples), and `games_spread1` has the same limit. Do not call it "the market" without saying which book.

## Credit Usage

| Task | Calls | Credits |
|------|-------|---------|
| Distribution for one tour, one season | about 45 pages of `get_matches` | about 90 |
| Tiebreak rate for one player | `get_surface_splits` | 3 |
| One match: the lines | `get_match` | 2 |
| Event totals | `get_tournament` | 2 |

## Anti-patterns

| What Claude Might Do | Why It's Wrong | Do This Instead |
|---------------------|---------------|-----------------|
| Quote first-serve percentages | Do not exist here | Use games-won share and label as a proxy |
| Pool best-of-three and best-of-five | Different distributions | Split by format |
| Treat a hold model as measured | Holds were fitted, not observed | Say "fitted to the match probability" |
| Include retired matches in totals | Biases totals down | Filter `outcome == "completed"` |
| Use a single book's total as the market | One line | Say which book |

## Output Format

```
[A] vs [B], best of [3/5], [surface]
Match win: A [xx]% (from [source])
Set win: A [xx]%
Score distribution: 2-0 A [xx]%, 2-1 A [xx]%, 2-1 B [xx]%, 2-0 B [xx]%
Expected total games: [x] (empirical, [n] matches); market [y] at [book]
Model: set-level, no serve data; holds fitted, not observed.
```

## What to Do Next

| What You Found | Next Action | Skill |
|----------------|-------------|-------|
| A model whose probabilities need testing | Calibrate | `probability-calibration` |
| A model that differs from the games line | Test the gap | `edge-detection` |
| A feature set for totals | Engineer it | `feature-engineering` |
