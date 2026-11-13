---
name: edge-detection
description: "Comparing a tennis model's probability with the market: no-vig close, expected value at the best available price, closing line value, fractional Kelly sizing, and the checks that separate an estimated edge from noise. Use when the user has a probability and wants to know whether a price is better than fair, how large a stake is reasonable, or whether an edge is real. Requires a probability the user trusts. Do not use for fetching prices: see odds-explorer. Do not use for devig math alone: see odds-analysis. Do not use for historical testing: see backtesting."
metadata:
  version: 1.0.0
  author: AcesAPI
---

# Edge Detection

> **Default data tool:** AcesAPI (`acesapi-tool`).
> Prices come from `get_match` (2 credits per match), in the `odds` array. Find the match with `get_schedule` (2). Your probability comes from your model or from `surface-elo`.

You compare two estimates of the same event: yours and the market's. An edge is an estimate of a difference, with error on both sides, and the market is usually the better estimate. Your job is to be skeptical in the direction of the market while still doing the arithmetic carefully.

## When to Use

- "My model says 68 percent, the book has -150. Is that value?"
- "Which book has the best price on my side?"
- "How much should I stake?"
- "Was that a good bet regardless of the result?" (closing line value)

## When NOT to Use

- Just looking at prices: see `odds-explorer`
- Computing the fair line: see `odds-analysis`
- Testing a rule over many matches: see `backtesting`
- Models whose probabilities are not calibrated yet: see `probability-calibration` first

## Commands Available

| Command | What It Does | Credits |
|---------|-------------|---------|
| `get_match` | `odds` rows: `p1_open`, `p1_close`, `p2_open`, `p2_close` per book | 2 |
| `get_schedule` | Upcoming matches and ids | 2 |
| `get_ratings` | Input to a rating-based probability | 2 |
| `get_player` | Ratings by surface | 5 |

## Commands That Do NOT Exist

| Not Available | Use Instead |
|--------------|-------------|
| `get_odds` | `get_match` |
| `get_edge` | Compute from the formulas below |
| `get_closing_line` | `p1_close` and `p2_close` in `get_match` |
| `get_live_odds` | Not available: pre-match only |
| `get_player_props` | Not available |

## Step 1: Require a Probability

Ask for the model probability `p` for a named player, and where it came from. If it is the rating logistic from `surface-elo`, say so. If it was not tested out of sample (see `walk-forward-validation`) and calibrated (see `probability-calibration`), say that the result below is an illustration, not an edge.

## Step 2: Market Reference

From `get_match`, for each book at close:

```
q1 = implied(p1_close),  q2 = implied(p2_close)
fair1 = q1 / (q1 + q2)                       # or power or Shin for lopsided prices
consensus = mean of fair1 across books (weight low-margin books more)
```

See `odds-analysis` for the methods. Use close as the market's final estimate. Use open only to see movement.

## Step 3: Edge and Expected Value

For the side you like, with the best close price at some book (decimal `d`):

```
edge_prob  = p - fair_market
EV per unit = p * d - 1
```

Two things to check before believing the number:

1. **Is the gap bigger than the margin?** A positive `p - fair` can still be negative EV after paying the book's margin. EV at the best price is the number that matters.
2. **Is the gap bigger than your error?** A probability from a rating model has a standard error of several points. A 2 point edge on a 150-match-calibrated model is noise.

## Worked Example (real prices, illustration of the arithmetic)

2025 Wimbledon final, Sinner as player 1, Pinnacle close `-116`, Alcaraz `+105`. No-vig Sinner 0.524 (see `odds-analysis`).

Suppose a model said 0.58 for Sinner (a hypothetical input).

```
decimal for -116 = 1 + 100/116 = 1.862
EV = 0.58 * 1.862 - 1 = +0.080     (8.0 percent per unit staked)
edge_prob = 0.58 - 0.524 = 0.056
```

The market would have to be wrong by 5.6 points on a match between the world's top two players. Reasonable skepticism: check where the model differs from the market (for example, a model built on overall Elo, 2325 against 2278 before that match, ignores the surface rating gap), and compare it with the close on a sample of earlier matches before staking anything.

## Step 4: Closing Line Value (CLV)

CLV measures whether the price you took was better than the close, independent of the result.

```
CLV = fair_close(side) - implied(price_taken)       # in probability points
```

If a bettor takes the side at the open (+102 on Sinner, implied 0.495) and the no-vig close is 0.524, CLV is +2.9 points. Persistent positive CLV across many bets is the best available evidence of skill because it does not depend on variance in results. Here only two snapshots exist per book (open and close), so use open as a proxy for "price taken early" and say so. The line you actually got matters, so record it (see `backtesting`).

## Step 5: Sizing

Fractional Kelly on a probability you trust:

```
f* = (p * d - 1) / (d - 1)            # full Kelly fraction of bankroll
stake = 0.25 * f* (or less), capped at 1 to 2 percent of bankroll
```

Kelly assumes `p` is exact. When `p` is an estimate, full Kelly overbets. Use a quarter or less, and shrink `p` toward the market first:

```
p_used = 0.5 * p_model + 0.5 * fair_market        # a starting point; tune walk-forward
```

For the example above, `p_used = 0.552`, EV at -116 is `0.552 * 1.862 - 1 = +0.028`, and quarter-Kelly is `0.25 * 0.028 / 0.862 = 0.8 percent` of bankroll. State that it is an estimate.

## Tennis-Specific Cautions

- **Favorite-longshot bias.** Books often shade longshots. A +537 underdog with a 14 to 15 percent fair probability is easy to overrate by 3 points. Use the power or Shin method (see `odds-analysis`) before claiming value.
- **Lopsided markets.** On a -2500 favorite (888sport in an early Shanghai example) the favorite's probability barely moves with price, while the underdog's moves a lot. Value claims live almost entirely on the underdog side, where model error is largest.
- **Withdrawals and retirements.** Rules differ by book: a retirement before a set or two is complete may void the bet, and a walkover is usually void. Check the book's rules; the data marks these with `outcome`.
- **Correlation.** Bets in the same tournament, same surface or same player share risk. Treat them as correlated when sizing.
- **Format.** Best-of-five Slams make favorites stronger. If the model does not know the format, expect it to underrate favorites there.
- **Coverage.** Odds exist only for Grand Slams (from mid-2020), and Masters and WTA 1000 events (from August 2024). Elsewhere there is no price in this data.
- **Exchange rows.** A back price is not a two-sided quote. Do not use it as the only reference.

## Checks Before Calling Anything an Edge

1. Model tested out of sample and calibrated.
2. The probability gap exceeds the model's error and the margin.
3. Edge persists across books (not one stale row).
4. Positive CLV on the history of similar bets.
5. Sample: at least a few hundred bets before judging profit. At a 2 percent true edge and typical tennis prices the per-bet standard deviation is near 1 unit, so 400 bets give a standard error near 5 percent: results will not distinguish a real 2 percent edge from zero.

## Credit Usage

| Task | Credits |
|------|---------|
| One match: prices and edge | 2 |
| A day of 20 priced matches | about 44 (schedule + 20 matches) |
| Multiple books | included, all books are in one call |

## Anti-patterns

| What Claude Might Do | Why It's Wrong | Do This Instead |
|---------------------|---------------|-----------------|
| Call any positive `p - implied` an edge | Implied includes margin | Use fair probability and EV at the price |
| Use full Kelly | Probability error | Quarter Kelly or less |
| Show the edge without a source for `p` | Unverifiable | Name the model and its test |
| Promise profit | Variance and error | Say estimate, variance, sample size |
| Ignore CLV | Skips the best skill signal | Track it |
| Use open prices as obtainable | Stale | Use what the user actually had |

## Output Format

```
[Player] to beat [Opponent], [price] @ [book]
Model p: xx.x% ([source])  Market fair: xx.x%  Gap: +x.x pts
EV at price: +x.x% per unit (estimate)  Margin paid: x.x%
Suggested stake: quarter-Kelly on shrunk p = x.x% of bankroll
Caveats: model sample, format, price source, variance
```

This is analysis, not a recommendation to bet. Edges here are estimates, and a bet can lose even at a real edge.

## What to Do Next

| What You Found | Next Action | Skill |
|----------------|-------------|-------|
| A candidate edge | Test the rule historically | `backtesting` |
| Probabilities off in the tails | Recalibrate | `probability-calibration` |
| A price not in the data | Use the user's own price | `odds-analysis` |
