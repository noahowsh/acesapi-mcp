# AcesAPI MCP server

[![Smithery](https://img.shields.io/badge/Smithery-listed-ff5601?style=flat-square)](https://smithery.ai/servers/noahowsh/AcesAPI) [![MCP Registry](https://img.shields.io/badge/MCP%20Registry-listed-0b7285?style=flat-square)](https://registry.modelcontextprotocol.io/v0/servers?search=io.github.noahowsh/acesapi)

**The tennis data API.** ATP and WTA singles matches with every set and tiebreak score, tournament draws round by round, player profiles, weekly rankings, head to head, surface splits, our own Elo by surface, and sportsbook moneylines on Grand Slam and Masters / WTA 1000 matches. REST API and MCP server. 500 free credits every month, no card.

Website: https://acesapi.com · Docs: https://acesapi.com/docs · Get a key: https://acesapi.com/signup

```
You:    "What is Carlos Alcaraz's record on clay against top-10 players?"
Claude: [calls get_surface_splits]

You:    "Who leads the Sinner and Alcaraz head to head, and how many of their meetings were finals?"
Claude: [calls get_head_to_head]

You:    "Which moneylines were posted for the 2025 US Open men's final?"
Claude: [calls get_matches, then get_match]
```

## Skills

This repo also ships 16 free Claude skills in [`skills/`](skills/) that turn Claude into a tennis analyst on top of the tools below: match and player lookup, surface Elo, head to head, ranking history, set-score modeling, odds math, edge detection and backtesting. They call the AcesAPI tools and keep to what the data holds (no serve statistics, moneylines on Slams, Masters and WTA 1000 only).

```bash
git clone https://github.com/noahowsh/acesapi-mcp.git
```

Or install them as a Claude Code plugin:

```
/plugin marketplace add noahowsh/acesapi-mcp
/plugin install acesapi-skills@acesapi
```

Or with the skills CLI: `npx skills add noahowsh/acesapi-mcp`.

Point Claude at the `skills/` folder, add the MCP server (see Quick start), and ask a question such as "who is favored in tomorrow's Shanghai match and why?". Full catalog: [`skills/README.md`](skills/README.md). The skills also work on your own CSV or JSON without a key.

## Useful pages

- [Docs](https://acesapi.com/docs): every endpoint with parameters and live examples
- [Tennis odds](https://acesapi.com/odds): upcoming ATP and WTA matches with each sportsbook's moneyline
- [Data atlas](https://acesapi.com/docs/atlas): what exists and where coverage is partial
- [Guides](https://acesapi.com/guides): Python walkthroughs for surface Elo, head to head, rankings, set scores and surface splits
- [Data](https://acesapi.com/data): [results](https://acesapi.com/data/tennis-results-api), [rankings history](https://acesapi.com/data/tennis-rankings-history), [odds history](https://acesapi.com/data/tennis-odds-history)
- [Pricing](https://acesapi.com/pricing): credits per call, 500 free every month
- [Surface Elo explained](https://acesapi.com/glossary/surface-elo)
- Compare: [API Tennis](https://acesapi.com/compare/api-tennis), [ESPN's tennis feed](https://acesapi.com/compare/espn-tennis-api), [Sportradar](https://acesapi.com/compare/sportradar-tennis), [SportsDataIO](https://acesapi.com/compare/sportsdataio-tennis)

## Quick start

This is a hosted (remote) MCP server over Streamable HTTP. There is nothing to install.

**Claude Code**

```bash
claude mcp add --transport http acesapi "https://mcp.acesapi.com/mcp?key=YOUR_API_KEY"
```

**Claude Desktop, Cursor and other clients**

```json
{
  "mcpServers": {
    "acesapi": {
      "url": "https://mcp.acesapi.com/mcp?key=YOUR_API_KEY"
    }
  }
}
```

The key can also be sent as an `x-api-key` header or `Authorization: Bearer`. Connecting and listing tools works without a key; calling a tool needs one.

**REST**

```bash
curl -X POST https://mcp.acesapi.com/v1/list_tournaments -H "x-api-key: YOUR_API_KEY"
```

Every tool is `POST /v1/{tool}` with a JSON body.

## Examples

Runnable Python (standard library only) and Node 18+ (no dependencies) examples live in [`examples/`](examples/):

- [`examples/python/quickstart.py`](examples/python/quickstart.py) and [`examples/node/quickstart.mjs`](examples/node/quickstart.mjs): schedule plus a headline call.
- [`examples/python/tennis_head_to_head_surface_elo.py`](examples/python/tennis_head_to_head_surface_elo.py): Two players side by side.

```bash
export ACESAPI_API_KEY=your_key
python3 examples/python/quickstart.py
node examples/node/quickstart.mjs
```

See [`examples/README.md`](examples/README.md) for details. Get a free key (500 credits a month, no card) at https://acesapi.com/signup.

## Tools (13)

| Tool | What it returns |
|------|-----------------|
| `list_tournaments` | A season's tournaments with dates, surface, status and champion |
| `search_players` | Find players by name or country |
| `get_tournament` | A tournament's draw and results, round by round, with every set |
| `get_matches` | Match results by day, tournament or season, with set and tiebreak scores |
| `get_schedule` | Upcoming and in-progress matches for the next days |
| `get_match` | One match: sets, tiebreak points, seeds, ratings and what the score says |
| `get_rankings` | Weekly ranking lists since 2007, or one player's ranking history |
| `get_ratings` | Our Elo ratings, overall or by surface |
| `get_head_to_head` | Two players' meetings, wins by surface and in finals |
| `get_surface_splits` | A player's record by surface: sets, games, tiebreaks, deciding sets |
| `get_player_stats` | A player's season statistics from scores, by round and opponent rank |
| `get_player` | Profile, ranking, ratings, career record, titles and recent matches |
| `get_player_matches` | A player's matches with scores and ratings, filtered by season, surface or opponent |

Leagues: tennis (default, ATP), wta (pass `league: "wta"` to any tool).

## Data

- ATP and WTA singles since 2007 (qualifying from 2022) with set and tiebreak scores
- Tournament draws and results round by round; weekly rankings since 2007
- Head to head, surface splits, player season statistics derived from scores, our Elo overall and by surface
- Sportsbook moneylines, returned in the `odds` array of `get_match` (there is no separate odds tool): Grand Slam matches from mid-2020 and ATP Masters and WTA 1000 matches from August 2024, pre-match, refreshed hourly; the array is empty for other tournaments
- No serve statistics (aces, double faults, break points): ESPN does not publish them

Coverage by season, read live from the database: https://acesapi.com/docs

## Pricing

500 free credits every month, no card. Plans: Starter $19/mo (10,000 credits), Pro $49/mo (30,000), Scale $149/mo (125,000). Wallet top-ups from $5, never expire. https://acesapi.com/pricing

## Attribution

Tennis data from public ESPN data; sportsbook lines from The Odds API. Surfaces and ratings are ours. Not affiliated with the ATP, WTA, ITF or any tournament.

## License

MIT for the contents of this repository. Data terms as above.
