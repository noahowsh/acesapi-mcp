#!/usr/bin/env node
// AcesAPI quickstart: upcoming ATP matches, then clay-court Elo ratings. Node 18+, no dependencies. Needs ACESAPI_API_KEY. Costs about 4 credits.
const BRAND = "AcesAPI";
const KEY_ENV = "ACESAPI_API_KEY";
const BASE_URL = "https://mcp.acesapi.com/v1";
const SIGNUP_URL = "https://acesapi.com/signup";

const key = (process.env[KEY_ENV] || "").trim();
if (!key) {
  console.error(
    `Set ${KEY_ENV} first:\n  export ${KEY_ENV}=your_key\n` +
      `Get a free key (500 credits every month, no card): ${SIGNUP_URL}`,
  );
  process.exit(1);
}

let remaining = null;

async function call(tool, args = {}) {
  let res;
  try {
    res = await fetch(`${BASE_URL}/${tool}`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "x-api-key": key },
      body: JSON.stringify(args),
    });
  } catch (err) {
    throw new Error(`Network error calling ${tool}: ${err.cause?.code ?? err.message}`);
  }
  remaining = res.headers.get("x-credits-remaining") ?? remaining;
  const text = await res.text();
  let body = {};
  try {
    body = JSON.parse(text);
  } catch {}
  if (res.ok) return body;
  const message = body.message || body.error || res.statusText;
  if (res.status === 401) throw new Error(`401 unauthorized. Check ${KEY_ENV}. ${message}`);
  if (res.status === 402) {
    throw new Error(
      `402 out of credits. ${message} Upgrade or wait for the monthly reset: ${body.upgrade_url || SIGNUP_URL}`,
    );
  }
  throw new Error(`HTTP ${res.status} from ${tool}: ${message}`);
}

const fmt = (v, digits) => (v == null ? "-" : digits != null && typeof v === "number" ? v.toFixed(digits) : String(v));
const pct = (v, digits = 1) => (v == null ? "-" : `${(v * 100).toFixed(digits)}%`);

function table(headers, rows) {
  const cells = rows.map((r) => r.map((c) => (c == null ? "-" : String(c))));
  const widths = headers.map((h, i) => Math.max(h.length, ...cells.map((r) => r[i].length)));
  const line = (r) => r.map((c, i) => c.padEnd(widths[i])).join("  ").trimEnd();
  console.log(line(headers));
  console.log(widths.map((w) => "-".repeat(w)).join("  "));
  cells.forEach((r) => console.log(line(r)));
}

function finish() {
  if (remaining !== null) console.log(`\nCredits remaining: ${remaining}`);
}

async function main() {
  const sched = await call("get_schedule", { days: 3 });
  const matches = sched.matches ?? [];
  console.log("Upcoming ATP matches (get_schedule, 2 credits)");
  if (matches.length) {
    table(
      ["Date", "Tournament", "Round", "Surface", "Match"],
      matches.slice(0, 8).map((m) => [m.match_date, m.tournament, m.round, m.surface, `${m.player1} v ${m.player2}`]),
    );
  } else {
    console.log("No matches in the next 3 days.");
  }

  const ratings = await call("get_ratings", { surface: "clay", limit: 5 });
  console.log("\nClay Elo ratings (get_ratings, 2 credits)");
  table(
    ["#", "Player", "Country", "Elo", "Clay matches", "Last match"],
    (ratings.ratings ?? []).map((r) => [r.rank, r.name, r.country, r.rating, r.surface_matches, r.last_match]),
  );
  finish();
}

main().catch((err) => {
  console.error(`Error: ${err.message}`);
  process.exit(1);
});
