---
name: odds-explorer
description: "Multi-book tennis moneyline comparison, best price, margin (vig) per book, and open-to-close line movement for Grand Slam, ATP Masters and WTA 1000 matches. Use when the user asks about the odds on a match, which book has the best price, how a line moved, or what the market thinks. Do not use for devigging math or true probabilities: see odds-analysis. Do not use for comparing a model to the market: see edge-detection. Do not use for results: see match-lookup."
metadata:
  version: 1.0.0
  author: AcesAPI
---

# Odds Explorer

> **Default data tool:** AcesAPI (`acesapi-tool`).
> There is no odds tool. Moneylines live in the `odds` array of `get_match` (2 credits per match). Get the `match_id` first from `get_schedule` (2) or `get_matches` (2).

You are an expert in reading a two-way tennis market. Your goal is to help the user see the best available price, how much margin each book charges, and how the market moved from open to close.

## Coverage, Stated Plainly

- Grand Slam singles matches from mid-2020, and ATP Masters and WTA 1000 matches from August 2024. Other tournaments return an empty `odds` array.
- Pre-match only: one open price and one close price per book. No in-play prices, no props, no set betting.
- Refreshed hourly. Books seen in live responses: 888sport, Betfair Exchange, DraftKings, FanDuel, Pinnacle, William Hill.
- Prices are American odds. `p1_*` is the player in the `player1` position of the match record, not the favorite.

## When to Use

- "What are the odds on tomorrow's Masters match?"
- "Which book has the best price on the underdog?"
- "How much did the line move before the final?"
- "What does Pinnacle think compared with DraftKings?"

## When NOT to Use

- Removing the margin or computing fair probabilities: see `odds-analysis`
- Deciding whether a price is worth betting against your own number: see `edge-detection`
- Historical sweeps for testing a strategy: see `backtesting`

## Commands Available

| Command | What It Does | Credits |
|---------|-------------|---------|
| `get_match` | One match with its `odds` array: per book `p1_open`, `p1_close`, `p2_open`, `p2_close`, `games_spread1`, `games_total` | 2 |
| `get_schedule` | Upcoming matches with `match_id`, to find what is priced | 2 |
| `get_matches` | Past matches with `match_id`, for historical lines | 2 |
| `search_players` | Resolve a name before searching the schedule | 1 |

## Commands That Do NOT Exist

| Not Available | Use Instead |
|--------------|-------------|
| `get_odds` | `get_match` and read `odds` |
| `get_line_movement` | Compare `p1_open` with `p1_close` from `get_match`; only two points exist per book |
| `get_live_odds` | Not available: pre-match only |
| `get_player_props` | Not available |
| `get_set_betting` | Not available |

## Fields in the odds Array

| Field | Meaning |
|-------|---------|
| `book` | Sportsbook name |
| `p1_open`, `p2_open` | American odds at the first snapshot |
| `p1_close`, `p2_close` | American odds at the last pre-match snapshot |
| `games_spread1` | Handicap in games for player 1, present for a few books only (Pinnacle in the examples), else `null` |
| `games_total` | Total games line, present for a few books only, else `null` |

For a match that has not started, "close" is the latest price, not yet final.

## How It Works

**Step 1: Find the match.** `get_schedule {"days": 2}` lists matches with `match_id`. If the user names players, filter by `player1` and `player2`. Check the tournament is a Slam, Masters or WTA 1000 before spending credits on odds.

**Step 2: Pull odds.** `get_match {"match_id": "184930"}`. Read `odds`.

**Step 3: Price table.** For each book show both players' close price, the margin, and the no-vig probability for player 1.

```
implied(a) = 100 / (a + 100)      if a > 0
           = -a / (-a + 100)      if a < 0
margin     = implied(p1) + implied(p2) - 1
no_vig_p1  = implied(p1) / (implied(p1) + implied(p2))
```

**Step 4: Best price.** Per side, the best price is the highest number (+250 beats +230, -110 beats -120). In tennis the sides are far from symmetric, so the best price for the favorite and for the underdog are usually at different books.

**Step 5: Movement.** `p1_close` against `p1_open` gives direction. Convert both to no-vig probability before comparing; raw cents are not comparable between -110 and +250.

## Worked Example (real data, 2025 Wimbledon final, Sinner as player 1)

Pinnacle row: `p1_open 102`, `p2_open -115`, `p1_close -116`, `p2_close 105`.

```
open : implied(+102) = 0.4950, implied(-115) = 0.5349, margin 2.99%, no-vig p1 = 0.4807
close: implied(-116) = 0.5370, implied(+105) = 0.4878, margin 2.48%, no-vig p1 = 0.5240
```

The market moved about 4.3 percentage points toward Sinner between open and close. The other books at close, by margin: Betfair Exchange 0.7%, 888sport and William Hill 3.6%, FanDuel 4.6%, DraftKings 5.6%. Sinner won. One result says nothing about whether the close was right.

Cost: 2 credits for `get_match`.

## Credit Usage

| Operation | Credits |
|-----------|---------|
| Odds for one match | 2 |
| Find ids for a day | 2 |
| Odds for a full Slam round (64 matches) | 128 plus 2 to list them |
| Odds for every covered match in a season | roughly 7,000 (3,574 calls in 2026 per the pricing page) |

State the count first for anything above a handful of matches.

## Reading the Market

- **Margin is lower at sharp books.** Betfair Exchange and Pinnacle showed 0.7% and 2.5% on the final; DraftKings 5.6%. Use the sharpest book as the reference for fair probability, and the softest for shopping.
- **Lopsided prices hide a larger margin.** On a -673 / +537 match (Pinnacle, 2026 Shanghai Masters third round) the margin is 2.8%, but the favorite's and underdog's implied probabilities are 87.1% and 15.7%. See `odds-analysis` for why the longshot side carries more of the margin.
- **Exchange prices can be inconsistent.** A back price on an exchange is not a two-sided quote. Use it as a signal, not a fillable price.
- **Open and close are snapshots, not a time series.** Do not describe steam moves or timing.

## Anti-patterns

| What Claude Might Do | Why It's Wrong | Do This Instead |
|---------------------|---------------|-----------------|
| Look for a separate odds tool | There is none | `get_match` |
| Assume `p1` is the favorite | It is the record position | Compute the favorite from the prices |
| Compare movement in cents | -110 to -125 and +250 to +275 are different probability moves | Convert to no-vig probability |
| Quote odds for a tour 250 | Empty array, not an error | Check the tournament tier first |
| Say a book "moved sharply" | Only open and close exist | Describe the net move |
| Mix `p1_open` from one book and `p2_open` from another | The pair must come from one quote | Always use the two sides of one row |

## Output Format

```
[Player 1] vs [Player 2]   [Tournament], [Round], [Surface]

Close prices:
  Book           P1      P2      Margin   No-vig P1
  Pinnacle       -116    +105    2.5%     52.4%
  ...
Best price: P1 [price] @ [book]; P2 [price] @ [book]
Move (Pinnacle, no-vig): 48.1% -> 52.4% for P1 (+4.3 pts)
```

## What to Do Next

| What You Found | Next Action | Skill |
|----------------|-------------|-------|
| Prices in hand | Compute fair probability | `odds-analysis` |
| A model probability to test | Compare with the market | `edge-detection` |
| A pattern across many matches | Test it historically | `backtesting` |
