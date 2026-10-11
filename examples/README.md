# AcesAPI examples

Runnable examples for the [AcesAPI](https://acesapi.com). Python uses only the standard library (`urllib` and `json`). Node uses the built-in `fetch` (Node 18 or newer). No packages to install.

ATP and WTA tennis data API. Every tool is a REST call: `POST https://mcp.acesapi.com/v1/<tool_name>` with a JSON body and an `x-api-key` header. The same tools are available over MCP at `https://mcp.acesapi.com/mcp`.

## Get a key

1. Sign up at https://acesapi.com/signup. The free plan gives 500 credits every month, no card.
2. Copy a key from https://acesapi.com/dashboard/keys.
3. Export it. The scripts read it from the environment and never print it.

```bash
export ACESAPI_API_KEY=your_key
```

## What is here

| File | What it does | Tools | Credits |
| --- | --- | --- | --- |
| `python/quickstart.py` | Upcoming schedule plus one headline call, printed as small tables | `get_schedule`, `get_ratings` | about 4 |
| `python/tennis_head_to_head_surface_elo.py` | Two players side by side. Head to head record with wins by surface, finals and the most recent meetings, then each player's Elo rating and rank on hard, clay and grass. Defaults to Sinner v Alcaraz. | `search_players`, `get_head_to_head`, `get_ratings` | about 11 |
| `node/quickstart.mjs` | Same as the Python quickstart, for Node | `get_schedule`, `get_ratings` | about 4 |

## Run

```bash
python3 python/quickstart.py
python3 python/tennis_head_to_head_surface_elo.py
node node/quickstart.mjs
```

The use-case script takes optional arguments. For example:

```bash
python3 tennis_head_to_head_surface_elo.py djokovic zverev
```

Run any script with `--help` (Python) to see its options.

## Credits and errors

- Every call costs credits, priced per tool. The cost is shown next to each call in the script output, and the response header `X-Credits-Remaining` is printed at the end.
- To see what a call would cost without running it, send `"estimate_only": true` on the tools that accept it (see the tool schema).
- When you are out of credits the API returns HTTP 402 with `{"error": "insufficient_credits", "message": "...", "upgrade_url": "..."}`. The scripts print that message and the upgrade link.
- HTTP 401 means the key is missing or wrong. The scripts print a hint to check `ACESAPI_API_KEY`.
- ATP is the default. Pass `"league": "wta"` in the request body for the WTA tour.
- The tool list with input schemas is public: `curl https://mcp.acesapi.com/v1/tools`.

## More

- Docs and example responses for every tool: https://acesapi.com/docs
- Full reference in one file: https://acesapi.com/llms-full.txt
- Free key: https://acesapi.com/signup
