---
name: walk-forward-validation
description: "Time-ordered validation of tennis models: expanding or rolling windows, season-by-season walk-forward, purging, log loss, Brier score and accuracy, baselines (Elo, ranking, market close), and significance tests. Use when the user asks if a model is any good, how to split data, whether cross-validation is okay, or how to compare two models. Refuses random k-fold on matches. Do not use for building features: see feature-engineering. Do not use for probability reliability: see probability-calibration. Do not use for betting profit: see backtesting."
metadata:
  version: 1.0.0
  author: AcesAPI
---

# Walk-Forward Validation

> **Default data tool:** AcesAPI (`acesapi-tool`).
> Results come from `get_matches` (2 credits per 100 matches). Use `get_ratings` or `get_player_matches` (`rating_before`) for baseline ratings. For the market baseline, `get_match` (2 each) on Slam and Masters matches.

You make sure a tennis model is judged only on matches that happened after the data it learned from. Tennis models fail in a specific way: a player's rating, form and context drift week to week, so shuffled validation looks excellent and forecasts look average.

## When to Use

- "Is my model any good?"
- "Can I use k-fold cross-validation?" (no)
- "How do I split a multi-season dataset?"
- "Is model B really better than model A?"

## When NOT to Use

- Constructing features: see `feature-engineering`
- Judging probability calibration alone: see `probability-calibration`
- Judging a betting rule: see `backtesting`

## Commands Available

| Command | What It Does | Credits |
|---------|-------------|---------|
| `get_matches` | Source of labeled matches by season | 2 |
| `get_player_matches` | `rating_before` for baselines | 5 |
| `get_match` | Pre-match ratings and market close for a baseline | 2 |
| `get_ratings` | Current leaderboard, only for current-season sanity checks | 2 |
| `list_tournaments` | Season boundaries and tiers | 1 |

## Commands That Do NOT Exist

| Not Available | Use Instead |
|--------------|-------------|
| `get_train_test_split` | Split by `match_date` yourself |
| `get_model_score` | Compute locally |
| `get_historical_predictions` | Not available: keep your own prediction log |

## The Rule

Every prediction for a match on date `t` uses only information with timestamps before `t`: model weights trained on matches before `t` and features built from the past. No exceptions for "just a few features" or "the same tournament".

## Split Schemes

**Season walk-forward (default).** Tour data runs by calendar year, so evaluate each season in turn:

```
train: 2007..2018   test: 2019
train: 2007..2019   test: 2020
train: 2007..2020   test: 2021
...
```

Expanding window keeps all history. Rolling window (for example the last 8 seasons) adapts to change at the cost of data. Compare both; with Elo-style features, expanding usually wins.

**Month or tournament-level folds** for more test points: refit monthly and predict the next month. Costly but gives a finer drift picture.

**Purging.** Matches on the same day, and consecutive rounds of one tournament, share players and context. Leave a one-week gap between train and test when the model uses short-window form, so a player's recent matches do not appear on both sides.

**Embargo for ratings.** If your rating is updated daily, evaluate with the rating as of the morning of the match, built from earlier dates only.

## Metrics

| Metric | Formula | Notes |
|--------|---------|-------|
| Log loss | `-mean(y ln p + (1-y) ln(1-p))` | The primary score. Punishes confident errors |
| Brier score | `mean((p - y)^2)` | Easier to read, 0.25 is a coin flip |
| Accuracy | `mean((p > 0.5) == y)` | Context only; ignores confidence |
| Calibration error | see `probability-calibration` | Separate check |

Reference points to compute on your own data, not to quote as constants: a coin flip scores log loss 0.693 and Brier 0.25. Elo from `get_match` ratings is the baseline to beat. The market no-vig close (see `odds-analysis`) is the stronger baseline where it exists; beating Elo and losing to the close is the normal result.

## Baselines (always report)

1. **Coin flip:** p = 0.5.
2. **Higher-ranked player wins:** the `current_rank` or list rank baseline.
3. **Pre-match Elo:** `rating.before` gap through the logistic (see `surface-elo`).
4. **Surface Elo:** same with `surface_before`.
5. **Market close:** only on covered events (Slams from mid-2020; Masters and WTA 1000 from August 2024). Compare on the subset where odds exist, not on the full set.

A model that cannot beat baseline 3 is not a model.

## Significance

Differences between models are small, and match counts decide whether they are real.

**Paired bootstrap on log loss.** Per match, compute `d_i = loss_A_i - loss_B_i`. Resample matches (block by tournament to respect dependence) 2,000 times, and report the mean difference and its 95 percent interval. If the interval contains 0, call it a tie.

Rough scale: the standard error of a mean log loss over `n` matches is about `0.01 * sqrt(5000 / n)`, so with 500 matches a 0.01 difference is not distinguishable from noise. A Slam main draw has 127 singles matches per tour; a whole tour season has several thousand (about 45 pages of 100 at the time of writing, qualifying included), enough to see differences of about 0.005 to 0.01.

## Pitfalls

- **Random k-fold.** Puts a player's 2025 matches in train and their 2024 matches in test. Refuse it.
- **Tuning on the test seasons.** Pick hyperparameters on a validation block inside the training window, then report on seasons that were never used for choices. Count how many variants you tried.
- **Survivor bias in players.** Evaluating only top-100 players inflates accuracy: mismatches are easier. Report by tier of matchup (rating gap buckets).
- **Retirements and walkovers.** Decide in advance and apply to every model identically.
- **Covariate shift.** Qualifying data appears from 2022, which changes the match pool. Check results before and after.
- **Format.** Best-of-five Slams behave differently. Report them separately.
- **Peeking via rank.** Use the list in force before the match.

## Worked Pattern

```python
import numpy as np
import pandas as pd

def walk_forward(df, seasons, fit, predict):
    rows = []
    for s in seasons:
        train = df[df.season < s]
        test  = df[df.season == s]
        model = fit(train)
        p = predict(model, test)                 # pre-match features only
        rows.append(test.assign(p=p))
    out = pd.concat(rows)
    out["ll"] = -(out.y * np.log(out.p) + (1 - out.y) * np.log(1 - out.p))
    return out.groupby("season").ll.mean(), out
```

Run it for each baseline and the candidate, then compare per-season. A model that wins five of six seasons by 0.01 or more is more convincing than one that wins by 0.02 on the pooled mean thanks to one season.

## Credit Usage

| Task | Credits |
|------|---------|
| Ten seasons of results, one tour | about 900 |
| Market baseline for one Slam (127 matches) | 254 |
| Market baseline for all covered matches in a recent season | about 7,000 |
| User-provided data | 0 |

Plan the baseline sample first; the market baseline is the expensive part, and a Slam or two is enough to learn something.

## Anti-patterns

| What Claude Might Do | Why It's Wrong | Do This Instead |
|---------------------|---------------|-----------------|
| Report in-sample accuracy | Not a forecast | Report out-of-sample by season |
| Compare models on different match sets | Not like for like | Same matches, paired differences |
| Call 0.003 log loss an improvement | Inside noise | Bootstrap interval |
| Skip the Elo baseline | Cannot tell whether work added anything | Always include it |
| Report accuracy alone | Hides overconfidence | Log loss plus calibration |
| Test on the same season used to choose hyperparameters | Optimistic | Hold out untouched seasons |

## What to Do Next

| What You Found | Next Action | Skill |
|----------------|-------------|-------|
| Model beats Elo out of sample | Check calibration | `probability-calibration` |
| Model matches Elo | Improve features | `feature-engineering` |
| Model approaches the close | Test against prices | `backtesting` |
