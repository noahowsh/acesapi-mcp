# AcesAPI skills

16 skills that turn Claude into a tennis analyst for ATP and WTA singles. Each skill is a folder with a `SKILL.md`: when to use it, which AcesAPI tools it calls and what they cost, the method, a worked example and the pitfalls.

Point Claude at this folder (for example `git clone` the repo and add `skills/` as a skills directory), connect the MCP server for live data, and ask in plain language. Start with `dispatch` if you are unsure which skill applies.

| Skill | Category | What it does |
|-------|----------|--------------|
| [`match-lookup`](match-lookup/SKILL.md) | Data Exploration | Results, draws, schedules and set scores for ATP and WTA matches |
| [`player-scouting`](player-scouting/SKILL.md) | Data Exploration | Player profiles, surface fit, opposition quality and form |
| [`odds-explorer`](odds-explorer/SKILL.md) | Data Exploration | Moneylines by book, margins and open-to-close moves on Slams and Masters |
| [`match-preview`](match-preview/SKILL.md) | Data Exploration | One-page pre-match brief: ratings, form, head to head, route and price |
| [`surface-elo`](surface-elo/SKILL.md) | Tennis Analytics | Elo by surface, win probability from rating gaps, and blending |
| [`head-to-head-analysis`](head-to-head-analysis/SKILL.md) | Tennis Analytics | Rivalry records by surface and in finals, weighted for small samples |
| [`ranking-history`](ranking-history/SKILL.md) | Tennis Analytics | Weekly ranking lists, points movement and rank versus Elo |
| [`set-score-modeling`](set-score-modeling/SKILL.md) | Tennis Analytics | Set scores, total games and tiebreak rates without serve data |
| [`feature-engineering`](feature-engineering/SKILL.md) | Methodology | Leak-free pre-match features: Elo, form, rest, load, symmetric rows |
| [`walk-forward-validation`](walk-forward-validation/SKILL.md) | Methodology | Season-by-season validation, baselines and significance tests |
| [`probability-calibration`](probability-calibration/SKILL.md) | Methodology | Reliability tables, Platt scaling and calibration against the close |
| [`odds-analysis`](odds-analysis/SKILL.md) | Methodology | Implied probability, devigging (multiplicative, power, Shin) and fair odds |
| [`edge-detection`](edge-detection/SKILL.md) | Betting | Model versus no-vig close: EV, closing line value and fractional Kelly |
| [`backtesting`](backtesting/SKILL.md) | Betting | Walk-forward tests against Slam and Masters closing lines with bootstrap |
| [`acesapi-tool`](acesapi-tool/SKILL.md) | Infrastructure | Router for all 13 tools: credits, response envelope, REST and MCP setup |
| [`dispatch`](dispatch/SKILL.md) | Infrastructure | Routes a tennis request to the right 2 or 3 skills |

## Notes on the data

- 13 tools. There is no odds tool: moneylines are in the `odds` array of `get_match`, for Grand Slams (mid-2020 on) and ATP Masters and WTA 1000 events (August 2024 on).
- No serve statistics (aces, double faults, break points): ESPN does not publish them. The skills use score-based proxies and say so.
- Pass `"league": "wta"` to any tool for the WTA.
- Free tier: 500 credits every month, no card. Plans and top-ups: https://acesapi.com/pricing

Probabilities, edges and ratings in these skills are estimates. Nothing here is betting advice.
