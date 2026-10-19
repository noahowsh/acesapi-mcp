---
name: backtesting
description: "Walk-forward backtests of tennis betting rules against historical moneylines from Grand Slams (mid-2020 on) and ATP Masters and WTA 1000 events (August 2024 on): closing-line value, ROI with bootstrap intervals, drawdown, edge compression, and the sample sizes needed. Use when the user asks if a strategy would have worked, what ROI over a season looks like, or whether an edge is real. Refuses in-sample testing. Do not use for today's prices: see edge-detection. Do not use for model accuracy alone: see walk-forward-validation. Do not use for prop strategies: not supported."
metadata:
  version: 1.0.0
  author: AcesAPI
---

# Backtesting

> **Default data tool:** AcesAPI (`acesapi-tool`).
> Results and ids: `get_matches` (2 credits per 100 matches). Historical prices: `get_match` (2 credits per match, `odds` array). **Credit warning:** odds cost 2 credits per match, so a covered season is roughly 3,500 matches and about 7,000 credits (3,574 calls in 2026 per the pricing page). Start with one tournament.
> With the user's own history, no calls are needed.

You falsify claims. A backtest here exists to find out whether a rule beat the closing price after the margin, with honest uncertainty. The default answer to "does it work?" is "not shown yet".

## Coverage Limits

- Prices exist for Grand Slam matches from mid-2020, and ATP Masters and WTA 1000 from August 2024. The data page counts 11,551 matches covered from 2020 to 2026.
- Each book has two snapshots: open and close. No full line history. No in-play. No props.
- Lines are refreshed hourly. Books differ by match; use matches where a given book appears for book-specific tests.
- A rule that needs other tournaments (tour 250s, 500s) cannot be tested on prices in this data.

## When to Use

- "Would betting every underdog over +300 at Slams have made money?"
- "Does my Elo model beat the Pinnacle close?"
- "Is my edge shrinking?"
- "How big a sample do I need?"

## When NOT to Use

- Live prices on tomorrow's matches: see `edge-detection`
- Model accuracy without prices: see `walk-forward-validation`
- Tracking bets going forward: keep your own log; no tracker tool exists

## Commands Available

| Command | What It Does | Credits |
|---------|-------------|---------|
| `list_tournaments` | Find the Slam or Masters editions and `tournament_id` | 1 |
| `get_tournament` | All matches of one event with ids (2 credits for the whole draw) | 2 |
| `get_matches` | Matches with `winner_id` and score; filter by `tournament_id` or `round` | 2 |
| `get_match` | The `odds` array (open and close per book) plus pre-match ratings | 2 |
| `get_player_matches` | Ratings before each match for one player | 5 |

## Commands That Do NOT Exist

| Not Available | Use Instead |
|--------------|-------------|
| `get_odds` | `get_match` |
| `get_historical_odds` | `get_match` on past `match_id` values |
| `get_line_movement` | Only open and close exist: compare `p1_open` with `p1_close` |
| `get_backtest_results` | This skill computes them |
| `get_bet_history` | Keep your own bet log |

## Credit Planning (Do This First)

```
Credits = 2 (tournament list) + 2 (draw or results) + 2 x (number of matches priced)

One Slam, one tour (127 main-draw matches):          about 260 credits
Four Slams, one tour:                                about 1,040
One covered season, all events (pricing page):       about 7,000
```

Warn the user before anything above about 500 credits, and sample a single event first. The free tier is 500 credits a month, which prices about 240 matches.

## Step 1: Define the Rule Before Looking

Write it down with its parameters: which matches (tournament tier, rounds), which side (favorite, underdog, model side), price range, minimum edge, the book. Count how many variants you will try, because the best of ten looks good by chance.

## Step 2: Build the Table

For each covered match, in date order:

1. `match_id`, `match_date`, `winner_id`, `player1_id`, `player2_id` from the results.
2. For each book: `p1_open`, `p2_open`, `p1_close`, `p2_close`.
3. Model probability, produced only from information before the match (see `feature-engineering`). Retrain walk-forward by season (see `walk-forward-validation`).
4. Fair close: devigged (see `odds-analysis`).

Sort ascending by `match_date` before any calculation.

## Step 3: Simulate

For each match where the rule fires:

```
price      = open or close price at the chosen book   # say which; "open" is optimistic, "close" is conservative
stake      = flat 1 unit, or fractional Kelly from walk-forward p
profit     = stake * (d - 1) if the bet side won else -stake
```

Exclude matches whose `outcome` is not `completed`, or apply the book's void rule consistently, and record how many you dropped. Never use a price from after the match started.

## Step 4: Measure

| Measure | Definition | Why |
|---------|------------|-----|
| Bets, wins | counts | Sample size |
| ROI | profit / total stake | Headline, noisy |
| CLV | fair_close(side) - implied(price taken) | Skill signal independent of results |
| Brier or log loss vs the close | on the bet set | Is the model informative? |
| Max drawdown | peak to trough in units | Pain |
| By season, tier, price band | splits | Where it works or does not |

**Bootstrap the ROI.** Resample bets (blocks by tournament to respect clustering) 2,000 times, report the 2.5 and 97.5 percentiles. If the interval includes zero, the backtest has not shown an edge.

**Sample size reality.** At a true 2 percent edge and a per-bet standard deviation near 1 unit, 400 bets give a standard error near 5 percent; 2,500 bets are needed to bring the standard error down to 2 percent. A single Slam gives well under 150 priced bets on a selective rule. Say the number out loud.

## Step 5: Stress

- **Edge compression.** Compute ROI and CLV by season. A shrinking edge is the usual outcome.
- **Price assumption.** Re-run at the close price. If the edge disappears, it came from the open.
- **Book assumption.** Re-run at the worst and the best book for each match. A rule that works only at the best price may not be fillable.
- **Parameter sensitivity.** Move the thresholds a notch. If the result flips, it was an accident.
- **Selection of tournaments.** Dropping one Slam should not change the story.

## Worked Example (design, with the real shape of the data)

Question: "Do underdogs over +300 at Slams beat their implied probability?"

```
1. list_tournaments {"season": 2025}           -> 1 credit, pick the four Slams (major = true)
2. get_matches {"tournament_id": "188-2025"}    -> 2 credits per 100 matches, with winner_id
3. get_match per row where an underdog fits     -> 2 credits each
```

Real row shape from step 3 (Pinnacle, Wimbledon 2025 final): `{"p1_open": 102, "p1_close": -116, "p2_open": -115, "p2_close": 105}`. For a +300 rule you would filter `p?_close >= 300`, devig with `odds-analysis`, then compare realized wins with the no-vig close. Run it first on one Slam (about 260 credits per tour), look at the count of qualifying bets, and decide whether the sample can answer the question at all. If you have fewer than a few hundred qualifying bets, the honest result is "inconclusive".

## Pitfalls

- **Look-ahead.** Using a model trained on the test season, using `rating.after`, or using the final draw to choose rounds. See `feature-engineering`.
- **Survivorship.** Slams drop weaker players quickly; late rounds contain only winners. Condition on pre-match information only.
- **Tuning on the test.** Report a rule chosen before seeing the test seasons.
- **Price realism.** Odds at the open are available for a short window and at limited stakes. Treat open-price backtests as upper bounds.
- **Void rules.** Retirement and walkover handling can swing small samples.
- **Multiple comparisons.** Ten variants tried means the best of ten is expected to look good.
- **Overlapping bets.** Two bets in the same match on both sides is not a strategy.
- **Variance.** A profitable-looking month is not evidence.

## Anti-patterns

| What Claude Might Do | Why It's Wrong | Do This Instead |
|---------------------|---------------|-----------------|
| Report ROI without an interval | Hides noise | Bootstrap |
| Backtest on covered Slams, then say it works "in tennis" | Coverage limited | Name the events |
| Use the best price at any book as fillable | May not be | Test the worst and best |
| Fit and test on the same seasons | In-sample | Walk forward |
| Count void bets as pushes in one run and losses in another | Inconsistent | Fix the rule first |
| Say "profitable" from 60 bets | Meaningless | State the standard error |

## Output Format

```
Rule: [definition]    Events: [list]    Period: [dates]
Bets [n], wins [w], avg price [x], ROI [r]% (95% interval [lo, hi]%)
CLV: [mean] pts   Max drawdown: [u] units
By season: ...
Credits used: [n]
Verdict: [shown / not shown / inconclusive], because [sample, interval, sensitivity]
```

Results are estimates from history, not predictions of future profit.

## What to Do Next

| What You Found | Next Action | Skill |
|----------------|-------------|-------|
| A promising rule | Check calibration and out-of-sample stability | `probability-calibration` |
| Edge only at the open | Treat as not obtainable | `edge-detection` |
| Inconclusive sample | Extend the period or stop | n/a |
