# Idea Atlas ✦

**Don't rebuild solved. Build what's new.**

A free, static atlas of knowledge that charts every field the same way:

| Territory | Glyph | Meaning |
|---|---|---|
| **Known** | filled diamond | Solved — laws discovered, software already built better. Don't rebuild it. |
| **Debated** | open circle | Live problems people are actively discussing across the internet. |
| **Frontier** | hollow diamond | Genuinely undiscovered — open problems, missing inventions. |

The site ships an **Idea Validator** (type an idea, get a verdict) and per-field
**sheets** you can browse: physics, software, math, biology, arts & humanities,
high-dim vectors, astronomy & space, mind & psychology, chemistry, economics & society.

## How it works

Nothing runs locally and nothing costs money:

```
Browser (GitHub Pages, static)          GitHub Actions (cron, every 6h)
  index.html   validator + sheet index    scripts/fetch.py    free APIs (HN, arXiv, Reddit, StackExchange)
  c/*.html     per-field sheets    ◀──    scripts/map.py      classify + dedupe (optional free-AI via Secrets)
  assets/      app.js + style.css         scripts/check_links.py  sampled dead-link check
  data/*.json  pre-built, no secrets      pytest → commit data → deploy Pages
```

- 100% free: GitHub Pages hosting, free APIs only, optional free-AI endpoint only.
- API keys live in GitHub Secrets (`AI_API_URL`, `AI_API_KEY`, `AI_MODEL`) — never committed, never shipped to the browser.
- No AI in the UI; AI (if configured) runs only in the background mapper with a local keyword fallback.

## Local development

```bash
python3 -m http.server 8000        # serve the repo root
# open http://localhost:8000

python3 scripts/map.py             # regenerate data/ from data/seed/ + data/live/
python3 -m pytest scripts/tests/   # run the test suite
python3 scripts/check_links.py     # sample-check links (advisory)
```

If `data/index.json` is missing, run `python3 scripts/map.py` once — it builds
`data/index.json`, `data/c/<field>.json`, `data/categories.json`, and `data/meta.json`
from the curated seeds in `data/seed/`.

## Repository map

```
index.html            validator, stats, sheet index
c/<field>.html        one "sheet" per field — filter tabs + live search
assets/               style.css (chart-plate theme), app.js (client logic)
data/seed/            curated items: known.json, debated.json, undiscovered.json, categories.json
data/                 build output: index.json, c/*.json, categories.json, meta.json
scripts/              fetch.py, map.py, check_links.py, tests/
.github/workflows/    atlas-update.yml — cron fetch + map + test + commit + Pages deploy
docs/                 design spec + implementation plan
```

## Contributing an idea

Add entries to `data/seed/known.json`, `debated.json`, or `undiscovered.json`:

```json
{
  "id": "known-your-id",
  "title": "What it is — one line verdict",
  "url": "https://en.wikipedia.org/wiki/…",
  "source": "wikipedia",
  "category": "physics",
  "status": "known"
}
```

`status` ∈ `known | debated | undiscovered`, `category` must be a slug from
`data/seed/categories.json`. IDs must be unique across all three files.

## License

MIT — see [LICENSE](LICENSE).
