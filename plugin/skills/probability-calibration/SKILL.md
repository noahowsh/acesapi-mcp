---
name: probability-calibration
description: "Checking and fixing tennis win probabilities: reliability tables, calibration slope and intercept, Brier decomposition, Platt scaling, isotonic regression, temperature scaling, and calibrating against the market close. Use when the user asks whether a model's 70 percent means 70 percent, why a model is overconfident on favorites, or how to correct probabilities before betting. Do not use for training the model: see feature-engineering. Do not use for choosing validation splits: see walk-forward-validation. Do not use for finding edges: see edge-detection."
metadata:
  version: 1.0.0
  author: AcesAPI
---

# Probability Calibration

> **Default data tool:** AcesAPI (`acesapi-tool`).
> Out-of-sample predictions with outcomes are the input. Results and `winner_id` come from `get_matches` (2 credits per 100). Market closes for comparison come from `get_match` (2 each).

You test whether predicted probabilities match reality. In tennis this is where models usually fail: a rating gap turns into a probability through a formula with assumptions (a fixed 400-point scale, one format, constant surface effect) and those assumptions break at the extremes and in best-of-five.

## When to Use

- "When my model says 75 percent, how often does the player win?"
- "My Elo probabilities seem too extreme for heavy favorites"
- "Should I calibrate before betting?"
- "Is the market better calibrated than my model?"

## When NOT to Use

- Building features or fitting models: see `feature-engineering`
- Deciding how to split data: see `walk-forward-validation`
- Bet sizing: see `edge-detection`

## Commands Available

| Command | What It Does | Credits |
|---------|-------------|---------|
| `get_matches` | Outcomes (`winner_id`) and format context for scoring predictions | 2 |
| `get_match` | Pre-match ratings and market closes for comparison | 2 |
| `get_ratings` | Current ratings for forward predictions | 2 |
| `get_player_matches` | `rating_before` for many matches of one player | 5 |

## Commands That Do NOT Exist

| Not Available | Use Instead |
|--------------|-------------|
| `get_calibration` | Compute from your prediction log |
| `get_model_probability` | Your model; the API serves data only |
| `get_historical_predictions` | Not available |

## Step 1: Orient the Predictions

Calibration needs one probability per match for one named side and a 0 or 1 label. Make it unambiguous: `p` = probability that the focal player wins, `y` = 1 if `winner_id` equals the focal player's id. If you keep both orientations of each match, score one orientation, or the table duplicates every row and halves your apparent uncertainty.

## Step 2: Reliability Table

Bin predictions, then compare predicted and realized.

```
bins:    [0.0, 0.1) ... [0.9, 1.0]     # use equal-count bins when n is small
for each bin: n, mean(p), mean(y), mean(y) - mean(p)
```

For tennis, put extra bins above 0.8, because heavy favorites are common (the best players are favored at 85 to 95 percent in early rounds). A model that says 92 percent and wins 88 percent costs real money when a price is -1000.

Report `n` per bin. A bin with 12 matches has a standard error near 0.14 for a 50 percent rate. Show intervals (Wilson) for bins under 100.

## Step 3: Summary Numbers

| Measure | Definition | Reading |
|---------|------------|---------|
| Brier | `mean((p - y)^2)` | 0.25 for a coin flip |
| Log loss | `-mean(y ln p + (1-y) ln(1-p))` | 0.693 for a coin flip |
| Calibration intercept and slope | Fit `logit(P(y=1)) = a + b * logit(p)` | Perfect: a = 0, b = 1. b < 1 means overconfident; b > 1 means underconfident |
| Expected calibration error | `sum(n_k / n * abs(mean y_k - mean p_k))` | Sensitive to binning; report with the bin scheme |

Slope is the clearest single number. Elo-based tennis probabilities tend to show a slope below 1 in best-of-three matches among close players and above 1 in best-of-five, because best of five amplifies the better player's edge. Test it on your data; do not assume.

## Step 4: Fix It

Fit the calibrator on a validation block earlier than the test block (see `walk-forward-validation`). Never fit and score on the same matches.

| Method | Use When | Notes |
|--------|----------|-------|
| Platt (logistic on logit(p)) | Under about 2,000 matches; slope off but shape monotone | Two parameters, stable |
| Temperature scaling | Same, simpler | One parameter `T` in `sigmoid(logit(p)/T)` |
| Isotonic | Over 3,000 matches and non-sigmoid miscalibration | Flat steps; overfits small samples |
| Per-format correction | Best-of-five vs best-of-three differ | Add a format term in the logistic |
| Blend with the market | Covered events | `logit(p_final) = a + b logit(p_model) + c logit(p_market)`, fit walk-forward |

Format and surface often matter more than the method: fit separate intercepts or slopes by format first.

## Step 5: Calibration Against the Market

The no-vig close (see `odds-analysis`) is the benchmark where it exists. Build the reliability table for both on the same matches. If the market is better calibrated and sharper (lower log loss), your model has not found information; it has found noise or a rating bias. If your model improves the market blend (the coefficient `b` on the model is significantly positive in the logistic above, given the market term), it carries independent information. That is the evidence that a betting edge can exist; it is not proof (see `backtesting`).

## Worked Example (method, with the credit cost)

You score 1,200 Masters and Slam matches from 2025 with an Elo model.

1. `get_matches` pages for the season to collect outcomes: about 90 credits per tour.
2. Predictions from your own Elo (see `feature-engineering`), pre-match only.
3. Reliability table in ten bins, plus extra bins at 0.8, 0.85, 0.9, 0.95.
4. Fit `logit(P(y)) = a + b logit(p)` on 2023 and 2024, apply to 2025.
5. Report slope, Brier and log loss before and after, per format.
6. For the 2025 matches that have odds, add the market column. This costs 2 credits per match.

Expected deliverable: a table of bins, the fitted `a` and `b`, the before and after scores, and one sentence stating whether the correction survives the next season.

## Pitfalls

- Calibrating on the same data you evaluate on.
- Pooling best-of-three and best-of-five.
- Judging calibration with accuracy.
- Over-binning small samples; use equal-count bins.
- Treating a calibrated model as a profitable one. Calibration is necessary for betting, not sufficient. The market is also calibrated.
- Using walkovers and retirements in the evaluation set inconsistently.
- Rating drift: Elo ratings stretch over time as players cluster; recalibrate every season.

## Credit Usage

| Task | Credits |
|------|---------|
| Outcomes for a tour season | about 90 |
| Market column for covered matches | 2 per match |
| Calibration on user data | 0 |

## Anti-patterns

| What Claude Might Do | Why It's Wrong | Do This Instead |
|---------------------|---------------|-----------------|
| Report accuracy as calibration | Different property | Reliability table and slope |
| Fit isotonic on 400 matches | Overfits | Platt or temperature |
| Calibrate on the test season | Leak | Calibrate on earlier seasons |
| Merge formats | Hides the best-of-five effect | Split or add a format term |
| Say "well calibrated" from the Brier score | Brier mixes sharpness and calibration | Show the table |

## Output Format

```
n = [matches], seasons [a-b], format [bo3 / bo5 / both]
Calibration intercept [a], slope [b]
Brier [x] (coin flip 0.250), log loss [y] (coin flip 0.693)
Bin   n    mean p   mean y   gap
0.9+  ..   0.93     0.89    -0.04
```

## What to Do Next

| What You Found | Next Action | Skill |
|----------------|-------------|-------|
| Calibrated probabilities | Compare with prices | `edge-detection` |
| Persistent bias by surface | Revisit features | `feature-engineering` |
| Calibrated and priced | Test over history | `backtesting` |
