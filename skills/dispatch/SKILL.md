---
name: dispatch
description: "Routes tennis analytics requests to the right 2 or 3 skills. Load this FIRST when an ATP or WTA data or analytics request comes in and you are unsure which skills to activate. Prevents loading all 16 skills when only a few are needed. Also sets expectations on what the data cannot answer (serve statistics, in-play, props)."
metadata:
  version: 1.0.0
  author: AcesAPI
---

# Skill Dispatch Guide

Match the request to a pattern below. Load those skills only.

**Default data tool:** `acesapi-tool`. It covers 13 tools for ATP and WTA singles. Load it alongside the strategy skill unless the request needs no data (user-supplied numbers).

**Tour check first.** ATP is the default. For WTA questions, every call needs `"league": "wta"`. Ask which tour only if the player or event is ambiguous.

## First-Use Persona Detection

| Signal | Persona | Start With |
|--------|---------|-----------|
| "What matches are on today?" / exploring | **Explorer** | `match-lookup` + `acesapi-tool` |
| "Tell me about this player" | **Scout** | `player-scouting` + `ranking-history` |
| "Who wins tomorrow?" | **Previewer** | `match-preview` + `surface-elo` |
| "I want to build a prediction model" | **Builder** | `feature-engineering` + `surface-elo` |
| "Is my model any good?" | **Validator** | `walk-forward-validation` + `probability-calibration` |
| "Where is the value?" / prices | **Bettor** | `odds-explorer` + `edge-detection` |
| "I am new to odds" | **New Bettor** | `odds-analysis` + `odds-explorer` |

## Request Patterns -> Skills to Load

### "Who plays today?" / "Who won?" / "Show me the draw" / "Every final this season"
1. `match-lookup`: results, schedules, draws
2. `acesapi-tool`: `get_matches`, `get_schedule`, `get_tournament`, `list_tournaments`

### "Tell me about [player]" / "How is she doing?" / "Compare these two players"
1. `player-scouting`: profile, surface fit, opposition quality, form
2. `acesapi-tool`: `search_players`, `get_player`, `get_surface_splits`, `get_player_stats`
3. Two players with a direct record: also `head-to-head-analysis`

### "[A] vs [B] head to head" / "Who leads the rivalry?" / "How do they split on clay?"
1. `head-to-head-analysis`: record, surface split, finals, weighting
2. `surface-elo` if a probability is wanted

### "Who is number one?" / "Ranking on a date" / "How did the ranking change?"
1. `ranking-history`: lists, trajectories, points versus rank
2. `surface-elo` if the question is really about strength

### "Who is best on clay?" / "Win probability for A vs B" / "How does the rating work?"
1. `surface-elo`: ratings, probability formula, blending
2. `head-to-head-analysis` for context if a rivalry exists

### "Preview the match" / "Who is favored tomorrow and why?"
1. `match-preview`: assembles ratings, form, record, route, price
2. `surface-elo` for the probability
3. `odds-explorer` if the event is a Slam, Masters or WTA 1000

### "What are the odds?" / "Best price" / "How did the line move?"
1. `odds-explorer`: prices, margins, open to close
2. `odds-analysis` for devigging
3. Remember: odds exist only for Grand Slams (mid-2020 on) and Masters and WTA 1000 (August 2024 on)

### "What probability does +450 imply?" / "Remove the vig" / "Shin vs power"
1. `odds-analysis`: no data needed unless prices must be fetched

### "Is this a value bet?" / "My model says 62 percent" / "How much to stake?"
1. `edge-detection`: EV, CLV, fractional Kelly
2. `odds-explorer` for current prices
3. `probability-calibration` if the model probability is untested

### "Would this strategy have worked?" / "ROI over a Slam" / "Is my edge real?"
1. `backtesting`: walk-forward simulation with closing lines
2. `walk-forward-validation` if the question is about model accuracy only
3. Warn about credits first (2 per priced match)

### "How many games will the match go?" / "Straight sets chance" / "Tiebreak frequency"
1. `set-score-modeling`: set distributions, totals, tiebreaks
2. `surface-elo` for the match probability that feeds it
3. State that serve data does not exist

### "Build features" / "What should I feed the model?" / "Is there leakage?"
1. `feature-engineering`: pre-match ratings, form, rest, symmetric layout
2. `walk-forward-validation` when evaluation comes next

### "Cross-validation okay?" / "Compare two models" / "How many matches do I need?"
1. `walk-forward-validation`: time-ordered evaluation and significance
2. `probability-calibration` for reliability

### "Are my probabilities calibrated?" / "Overconfident on favorites"
1. `probability-calibration`: reliability tables, Platt, isotonic
2. `walk-forward-validation` for the split

## Things the Data Cannot Answer

Say so immediately and offer the closest proxy.

| Request | Reality | Offer |
|---------|---------|-------|
| Aces, double faults, first-serve percentage, break points | No serve statistics exist | Games-won share, tiebreak record, total games per match (`player-scouting`, `set-score-modeling`) |
| Live or in-play prices | Pre-match open and close only | Open to close movement (`odds-explorer`) |
| Player props (aces, games won, sets) | No props data | Not supported: do not build a prop model |
| Injury or fitness reports | None | Rest days and recent load from scores (`feature-engineering`) |
| Prices for tour 250 and 500 events | Not covered | Ratings-only analysis |
| Rankings outside the top 100 to 150 | Not in the lists | Ratings via `get_ratings` for active players with 10 or more rated matches |
| Doubles | Singles only | State the limit |

## Multi-Skill Workflows

**Pre-match workflow:** `match-lookup` (find the match) -> `match-preview` (brief) -> `odds-explorer` (price) -> `edge-detection` (only with a tested model).

**Model workflow:** `feature-engineering` -> `walk-forward-validation` -> `probability-calibration` -> `backtesting`.

**Research workflow:** `ranking-history` and `surface-elo` to find an anomaly (a rank far from rating) -> `player-scouting` to explain it -> `head-to-head-analysis` for the direct record.

## Credit Awareness

Before any request that loops over many matches or players, state the number of calls and the credits (see `acesapi-tool`). Cheap by default: one preview is about 20 credits; a day of results is 2; odds for a Slam round of 64 matches is 128. The free tier is 500 credits a month with no card; plans and top-ups are on https://acesapi.com/pricing.

## Rules for Every Answer

- Cite the tool results used, and name the tour.
- Use pre-match ratings only (`rating.before`), never `rating.after`.
- Probabilities and edges are estimates. Mention variance and sample size, and prefer closing-line value over short-run results.
- If a user asks for a lock, a guarantee or a pick to bet the house on, decline that framing and give the analysis.

## Anti-patterns

| What Claude Might Do | Why It's Wrong | Do This Instead |
|---------------------|---------------|-----------------|
| Load all 16 skills | Wastes context | 2 or 3 per request |
| Reach for a nonexistent odds tool | Odds are inside `get_match` | `odds-explorer` |
| Start betting analysis without checking coverage | Tour 250 events have no prices | Check the tournament tier |
| Skip the tour | WTA ids and ATP ids differ | Pass `league` |
| Answer serve questions | No data | Offer proxies |
