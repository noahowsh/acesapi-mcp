---
name: player-scouting
description: "Scouting and comparing ATP and WTA players: profile, ranking, Elo overall and by surface, career record, titles, form, record by surface, round and opponent ranking, and ranking trajectory. Use when the user asks about a player, who is better on a surface, recent form, how a player does against top-10 opponents, or to compare two players side by side. Do not use for a single match result: see match-lookup. Do not use for two players' direct meetings: see head-to-head-analysis. Do not use for win probabilities: see surface-elo."
metadata:
  version: 1.0.0
  author: AcesAPI
---

# Player Scouting

> **Default data tool:** AcesAPI (`acesapi-tool`).
> Start with `search_players` (1 credit) for the id. `get_player` (5) is the one-call profile. Add `get_surface_splits` (3), `get_player_stats` (3) and `get_rankings` (2, with `player_id`) for depth. `get_player_matches` (5 per page) is the match log.

You build scouting reports from results data. Be honest about what the data is: scores, surfaces, rankings and Elo. It has no serve statistics, no injuries and no fitness data, so a report on "serve strength" is a proxy report and must say so.

## When to Use

- "Tell me about Jannik Sinner" or "profile Iga Swiatek"
- "Who is better on clay, A or B?" (see also `head-to-head-analysis`)
- "How does she do against top-10 players?"
- "Is he in form?" "Has the ranking moved?"
- "Compare these two players across everything"

## When NOT to Use

- One match's score or schedule: see `match-lookup`
- Two players' direct meetings only: see `head-to-head-analysis`
- A win probability for a specific match: see `surface-elo`
- Betting prices: see `odds-explorer`

## Commands Available

| Command | What It Does | Credits |
|---------|-------------|---------|
| `search_players` | Find ids by `name` and or `country` (3-letter code); most-played first | 1 |
| `get_player` | Bio, latest ranking, overall and per-surface rating with peak, career record, titles, Grand Slam titles, last 10 matches | 5 |
| `get_surface_splits` | Record by surface: wins, losses, win rate, sets, share of games won, tiebreaks, deciding sets, 6-0 sets; `season`, `by_season` | 3 |
| `get_player_stats` | Season stats counted from scores; record by round and by opponent ranking (top 10, 11-50, 51-100) | 3 |
| `get_rankings` | With `player_id`: ranking history with `previous_rank` and points | 2 |
| `get_player_matches` | Match log newest first with `rating_before` and `rating_after`; filters `season`, `surface`, `opponent_id`, `tournament_id`, `draw` | 5 |
| `get_ratings` | Elo leaderboard, to place the player among peers | 2 |

## Commands That Do NOT Exist

| Not Available | Use Instead |
|--------------|-------------|
| `get_serve_stats` | Not available. Use proxies from `get_surface_splits` (tiebreaks, share of games won) and say they are proxies |
| `get_player_injuries` | Not available |
| `get_player_form` | Build it from `get_player_matches` (see below) |
| `compare_players` | Run the calls for each player and tabulate |

## How It Works

**Step 1: Resolve the id.** `search_players {"name": "alcaraz"}`. Real output includes `player_id`, `country`, `date_of_birth`, `matches`, `last_match`, `current_rank` (null outside the top 100 to 150), `plays`. If two players match, ask or use `country`. For the WTA add `"league": "wta"`.

**Step 2: Profile.** `get_player {"player_id": "3782"}` for bio, rating and last 10 matches. This is the single best 5-credit call.

**Step 3: Surface fit.** `get_surface_splits` returns, per surface, `win_pct`, `games_won_pct`, `tiebreaks_won`, `tiebreaks_lost`, `deciding_sets_won`, `sets_won_6_0`, and a `ratings` block with a rating and match count per surface. Real example, trimmed (Alcaraz, career at the time of the call):

```json
{"overall": {"wins": 307, "losses": 69, "win_pct": 0.816, "games_won_pct": 0.58},
 "splits": [
  {"surface": "hard",  "wins": 168, "losses": 46, "win_pct": 0.785, "games_won_pct": 0.579},
  {"surface": "clay",  "wins": 104, "losses": 19, "win_pct": 0.846, "games_won_pct": 0.588},
  {"surface": "grass", "wins": 35,  "losses": 4,  "win_pct": 0.897, "games_won_pct": 0.569}],
 "ratings": {"clay": {"rating": 2247, "matches": 121}, "grass": {"rating": 2135, "matches": 39}, "hard": {"rating": 2216, "matches": 204}}}
```

Read it with sample size in view: 39 grass matches is a small sample, so a 0.897 win rate carries far more uncertainty than 0.846 over 123 clay matches. A Wilson interval is the right way to say so (see Method).

**Step 4: Quality of opposition.** `get_player_stats` returns record by opponent ranking band. A player with a high win rate built against opponents outside the top 50 is a different player from one who is 60 percent against the top 10. Report both.

**Step 5: Trajectory.** `get_rankings {"player_id": "3623"}` returns `best_rank` and `history[]` (`season`, `week`, `ranking_date`, `rank`, `previous_rank`, `points`). Points can fall while the rank holds (the real history for the world number one fell from 13,450 to 11,000 points over a few months with the rank unchanged at 1, because old results dropped off). Use `get_rankings` for the shape, not for form.

**Step 6: Form.** Use `get_player_matches {"player_id": "...", "limit": 20}` or the `last 10` in `get_player`. Form is the last N completed matches, weighted by opponent rating. Net rating change over the last 10 (`rating_after` of the newest minus `rating_before` of the oldest) is the cleanest one-number form signal here: it already adjusts for who the opponents were.

## Method: Honest Intervals on Small Samples

Wilson 95 percent interval for a win rate with `w` wins in `n` matches:

```
p = w / n;  z = 1.96
center = (p + z^2/(2n)) / (1 + z^2/n)
half   = z * sqrt(p(1-p)/n + z^2/(4n^2)) / (1 + z^2/n)
interval = center +/- half
```

For 35 wins in 39 matches this gives roughly 0.76 to 0.96. Do not rank two players' surface win rates when their intervals overlap heavily. Say "similar".

## Serve and Return Without Serve Data

The data has no serve statistics, so do not invent them. What the scores do support:

| Proxy | Source | What it says |
|-------|--------|--------------|
| Share of games won | `games_won_pct` | Overall dominance, serve and return combined |
| Tiebreak record | `tiebreaks_won` and `tiebreaks_lost` | Holds under pressure; tiebreaks occur when both players hold |
| Deciding-set record | `deciding_sets_won` of `deciding_sets` | Closing ability and fitness, noisy |
| 6-0 sets won and lost | `sets_won_6_0`, `sets_lost_0_6` | Blowout tendency |
| Total games per match | `stats.total_games` in `get_match` | Lots of games and tiebreaks suggests serve-dominant play; few suggests breaks |

Label every one of these "proxy".

## Comparing Two Players

Build one table and name the winner of each row only when the gap is meaningful:

```
                    Player A      Player B
Rank / points       1 / 11000     3 / 5560
Elo overall         2407          ...
Elo clay            2209          2247
Win pct clay        .xxx (n)      .xxx (n)
vs top 10           W-L           W-L
Tiebreaks W-L       ...           ...
Last 10 rating chg  +xx           -xx
```

Then one paragraph of judgment. For the direct record use `head-to-head-analysis`.

## Credit Usage

| Report | Calls | Credits |
|--------|-------|---------|
| Quick profile | `search_players` + `get_player` | 6 |
| Surface and opposition depth | + `get_surface_splits` + `get_player_stats` | 12 |
| Full report with ranking history | + `get_rankings` | 14 |
| Two-player comparison | double the above | 12 to 28 |

## Anti-patterns

| What Claude Might Do | Why It's Wrong | Do This Instead |
|---------------------|---------------|-----------------|
| Quote "serve rating" or "first-serve percentage" | Not in the data | Say it is unavailable and show proxies |
| Rank players by raw win rate | Ignores opponent strength and sample size | Use Elo, win rate against top-10, and intervals |
| Use `current_rank` as strength | Rank is a 52-week points total, and null outside the top 100 to 150 | Use Elo for strength, rank for seeding context |
| Call a 4-match win streak "form" | Four matches is noise | Use 10 to 20 matches and the rating change |
| Compare a hard-court Elo to a clay Elo on one scale | Different match counts and update speeds | Compare the same surface across players |

## What to Do Next

| What You Found | Next Action | Skill |
|----------------|-------------|-------|
| Two players with similar Elo | Look at direct history | `head-to-head-analysis` |
| A surface specialist | Convert ratings to a probability | `surface-elo` |
| A decision needed on a specific match | Build the brief | `match-preview` |
| A ranking slide | Study the trajectory | `ranking-history` |
