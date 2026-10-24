# Idea Atlas — Design Spec (2026-10-14)

## Vision
"Don't rebuild solved. Build what's new." A website listing:
1. **Known / Solved** — discovered laws (e.g. force=ma), software already built better (e.g. todo apps).
2. **Debated / Live problems** — what people are discussing on the internet across all fields incl. niche (high-dim vectors, arts, etc).
3. **Undiscovered / Frontier** — things yet to be discovered/invented.

Core jobs: **Idea Validator + Browse Encyclopedia** by category.

## Constraints (user-approved)
- 100% free: GitHub Pages hosting, free APIs only, free AI API only.
- Nothing runs locally in steady state: all fetching/mapping runs in GitHub Actions/workflows.
- API keys only via GitHub Secrets, never committed, never shipped to browser.
- No AI button in UI. AI works in background in Actions to map sources, validate, gather more from open internet.
- Not a single-page app: `index.html` + per-category pages `c/<field>.html`, each showing Known / Debated / Undiscovered.

## Architecture (B+A hybrid, static + Actions)
```
Browser (GitHub Pages, static)
  index.html (validator search + field grid)
  c/<field>.html (Known / Debated / Undiscovered per field)
  assets/app.js + data/*.json (pre-built, no secrets)

GitHub Actions cron (.github/workflows/update.yml, every 6h)
  python/fetch.py reads connectors/ registry
    -> free sources: HN Algolia, Reddit public JSON, StackExchange API, arXiv API, Wikipedia (seed)
    -> optional SECRET-backed sources (env, from Secrets)
  -> python/map.py: classify -> {known, debated, undiscovered} + category mapping
    -> AI mapper if AI_API_URL + AI_API_KEY present (free model endpoint, OpenAI-compatible)
    -> fallback: local keyword/TF heuristic (stdlib only, no deps)
  -> validate, dedupe, write data/live/*.json, data/index.json, data/known.json, data/undiscovered.json
  -> commit + Pages deploy
```

Why: Pages cannot run Python server/scheduler/DB. So compute moves to Actions, output is JSON. One repo, zero hosting cost, extensible connectors.

## Components
1. **Static site** (`site/` at repo root for Pages):
   - `index.html`: hero vision, validator `<input>`, field grid (physics, software, art, math, bio, niche...).
   - `c/<field>.html`: generated or template + JS render; 3 sections with source links, stale badge, "don't rebuild" callouts for Known.
   - `assets/app.js`: client search over `data/index.json` (substring + token overlap), no AI, no keys.
   - `assets/style.css`: clean, no framework.
2. **Fetcher** (`scripts/fetch.py`): `Connector` interface `{name, fetch() -> raw_items}`. Built-ins free/no-key. New APIs added by dropping a file + optional Secret name. Respects rate limits, timeout 15s, keeps last-good on failure.
3. **AI mapper** (`scripts/map.py`): `map_with_ai(items) -> classified`. Prompt: dedupe, classify known/debated/undiscovered, assign category, drop low-quality, return JSON. Validates JSON, falls back to `map_local()` on missing key/quota/error. Never logs Secrets.
4. **Seed data** (`data/seed/known.json`, `undiscovered.json`): curated starting atlas (force, acceleration, todo/notes/chat clones, etc + frontiers).
5. **Workflows** (`.github/workflows/update.yml` + `deploy.yml` or single Pages workflow): cron, `pip install -r scripts/requirements.txt` (requests only), run fetch+map, commit data if changed, deploy to Pages.

## Data flow
1. Cron triggers → checkout → setup-python → `python scripts/fetch.py --out data/live/`.
2. `map.py` loads seed + live → AI classify (if Secrets set) else local → writes `data/index.json` + per-category `data/c/<field>.jsone.g. physics, software, vectors`.
3. Validator in browser loads `index.json`, scores query vs Known (exact/substring high) → verdict: SOLVED/DON'T REBUILD vs DEBATED (link threads) vs OPEN/FRONTIER.
4. Failure mode: any connector error → log, keep previous JSON, UI shows `updated_at` + stale flag. AI quota error → local fallback, flag `ai: fallback` in build meta.

## Secrets handling
- Repo contains `.github/workflows`, `config.example.yml` (endpoint URL, model name, no secrets).
- Real values in GitHub Settings → Secrets: e.g. `AI_API_URL`, `AI_API_KEY`, `REDDIT_*` later, etc.
- `fetch.py`/`map.py` read only from env. No secret ever written to `data/` or `site/`. `.gitignore` covers local `.env`.

## Error handling
- Network timeouts, 429s → exponential backoff 1 retry, then skip source.
- Bad AI JSON → retry once with stricter prompt, then local fallback.
- Schema validation: every item must have `{id, title, url, source, category, status, updated_at}`; invalid dropped with log.
- Dead links: build step HEAD-checks sampled URLs (limit 50 to stay free/fast).

## Testing
- `pytest scripts/tests/`: test_local_classifier, test_dedupe, test_schema, test_no_secrets_in_output (scans data/ for secret patterns).
- Manual: `python -m http.server` + open `site/index.html` with local `data/`.

## Scope check (YAGNI)
- v1: 6 categories (physics, software, math, bio, art, vectors/niche), 4 free connectors, seed ~30 known + ~20 frontier, validator local-only.
- Out: user accounts, comments, live browser AI, Postgres, server rendering, paid APIs.

## Self-review
- No TBDs. No contradictions (static-only vs background AI resolved via Actions). Single-plan scope. Statuses fixed to 3 values. Secrets flow explicit.
