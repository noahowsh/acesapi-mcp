---
name: odds-analysis
description: "Odds math for two-way tennis markets: American to implied probability, margin, devigging (multiplicative, power, Shin), no-vig fair odds, consensus across books, favorite-longshot bias, and expected value of a price. Use when the user asks what a price implies, how to remove the vig, what the true probability is, or how to compare books. Do not use for fetching or comparing live prices: see odds-explorer. Do not use for deciding a bet against a model: see edge-detection."
metadata:
  version: 1.0.0
  author: AcesAPI
---

# Odds Analysis

> **Default data tool:** AcesAPI (`acesapi-tool`).
> Prices come from the `odds` array of `get_match` (2 credits per match). The math here needs no calls. With the user's own prices, it costs nothing.

You are an expert in converting prices to probabilities. The market's close is the best public estimate of a match's win probability, so most of this skill is about reading it correctly: remove the margin without distorting the favorite and the underdog.

## When to Use

- "What probability does -450 imply?"
- "Remove the vig from this line"
- "What is the fair price if the book charges 4 percent?"
- "Which book is sharpest?" (lowest margin, closest to consensus)
- "Why does the underdog look like value after I devig?" (usually a method problem)

## When NOT to Use

- Fetching and displaying prices: see `odds-explorer`
- Deciding to bet against a model number: see `edge-detection`
- Testing a rule on past matches: see `backtesting`

## Commands Available

| Command | What It Does | Credits |
|---------|-------------|---------|
| `get_match` | Source of `odds`: `p1_open`, `p1_close`, `p2_open`, `p2_close` per book | 2 |
| `get_schedule` | Find `match_id` for upcoming matches | 2 |
| `get_matches` | Find `match_id` for past matches | 2 |

## Commands That Do NOT Exist

| Not Available | Use Instead |
|--------------|-------------|
| `get_odds` | `get_match` |
| `get_implied_probability` | Compute from the formulas below |
| `get_consensus_line` | Average no-vig probabilities across the rows of `odds` |

## Conversion

```
American a > 0:  decimal = 1 + a/100;  implied = 100/(a+100)
American a < 0:  decimal = 1 + 100/(-a);  implied = (-a)/(-a+100)
fair American from probability p:  p >= 0.5 -> -100p/(1-p);  p < 0.5 -> 100(1-p)/p
margin (overround) = implied1 + implied2 - 1
```

A two-way tennis market has exactly two outcomes (no draw), which makes devigging a one-parameter problem.

## Devigging Methods

Let `q1`, `q2` be the raw implied probabilities with `q1 + q2 = 1 + m`.

**1. Multiplicative (proportional).** `p_i = q_i / (q1 + q2)`. Fast, standard. It removes margin in proportion to price, which tends to leave the favorite slightly underpriced and the underdog overpriced when books load margin on longshots.

**2. Additive.** `p_i = q_i - m/2`. Equal subtraction per side. Can push a longshot's probability below zero on lopsided matches. Do not use when either price is beyond about +1000.

**3. Power.** Find `k` such that `q1^k + q2^k = 1`, then `p_i = q_i^k`. Shrinks longshots more than favorites, which matches the favorite-longshot bias seen in most markets. Solve with bisection on `k` in [1, 2].

**4. Shin.** Models the margin as protection against informed bettors. Solve numerically for `z` (the insider proportion):

```
with S = q1 + q2:
p_i(z) = (sqrt(z^2 + 4(1-z) q_i^2 / S) - z) / (2(1-z))
find z in [0, 0.4] such that p_1(z) + p_2(z) = 1   (bisection)
```

Treat Shin and power as the better choices for lopsided matches and multiplicative for near-even matches. When methods differ by less than 0.5 percentage points, the choice does not matter.

## Worked Example (real data: Pinnacle, 2025 Wimbledon final, close)

`p1_close = -116`, `p2_close = 105`.

```
q1 = 116/216 = 0.5370      q2 = 100/205 = 0.4878      margin = 2.48%
multiplicative: p1 = 0.5370 / 1.0248 = 0.5240
fair American for p1: -100*0.5240/0.4760 = -110
```

So the market's fair price on Sinner was about -110 against -116 on offer.

Lopsided case (real data: Pinnacle close, 2026 Shanghai Masters third round, scheduled at time of the call): `-673` and `+537`.

```
q1 = 673/773 = 0.8706      q2 = 100/637 = 0.1570      margin = 2.76%
multiplicative: favorite 0.8472, underdog 0.1528
```

Power (k = 1.070): favorite 0.8622, underdog 0.1378. Shin (z = 0.028): favorite 0.8568, underdog 0.1432. The underdog's fair probability ranges from 13.8% to 15.3% depending on method, a gap larger than most claimed edges. Run two methods before arguing about value on a +537 price.

## Consensus and Sharpness

1. Devig each book at close with the same method.
2. Weight books by inverse margin (or give Pinnacle 2x weight if present).
3. Consensus close = weighted mean of no-vig probabilities.

On the Wimbledon final, the six books' no-vig close for Sinner ranged from 0.506 to 0.531 (multiplicative). A spread under 3 points is normal; wider than 5 means one row is stale or a quirk of an exchange back price. The lowest-margin book is not automatically the sharpest, but it is a good reference.

## Expected Value of a Price

For a stake of 1 and decimal odds `d` with win probability `p`:

```
EV = p * (d - 1) - (1 - p) = p * d - 1
break-even p = 1 / d
```

EV is only as good as `p`. If `p` comes from the no-vig market, the EV of the best price at any book equals minus the margin gap between the best price and the fair price. That is the benchmark: any claimed edge should be measured against the closing no-vig number, not against zero.

## Pitfalls

- Using `p1_open` from one row and `p2_close` from another.
- Treating `p1` as the favorite.
- Averaging American odds. Average probabilities instead.
- Devigging an exchange back price as if it were a two-sided quote: Betfair's margin of 0.7% on the final reflects that it is a tight market, not a free lunch.
- Applying a margin that was measured on a favorite to an underdog price. Margin is not evenly split.
- Concluding value from a single match. One outcome cannot confirm a probability.

## Credit Usage

| Operation | Credits |
|-----------|---------|
| Devig prices the user pasted | 0 |
| Devig one match from AcesAPI | 2 (plus 2 to find the id) |
| Consensus for a day of 20 priced matches | about 40 |

## Anti-patterns

| What Claude Might Do | Why It's Wrong | Do This Instead |
|---------------------|---------------|-----------------|
| Treat implied probability as true probability | It includes margin | Devig first |
| Use additive devig on +1000 or longer | Can go negative or distort | Power or Shin |
| Average American odds across books | Not linear in probability | Average no-vig probabilities |
| Say the underdog is "+EV" after one devig method | The method choice can create the edge | Show two methods; if they disagree, say so |
| Use open prices as the fair line | Close is more informed | Use close for fair probability, open for movement |

## Output Format

```
Price: [p1 price] / [p2 price]   Margin: X.X%
Raw implied:   P1 xx.x%   P2 xx.x%
No-vig (multiplicative): P1 xx.x%   (power: xx.x%)
Fair American: P1 [price]
```

## What to Do Next

| What You Found | Next Action | Skill |
|----------------|-------------|-------|
| A fair probability | Compare with your model | `edge-detection` |
| A model that disagrees with the close | Test it over many matches | `backtesting` |
| A model whose probabilities look off | Check calibration | `probability-calibration` |
