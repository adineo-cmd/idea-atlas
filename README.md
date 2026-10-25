# Idea Atlas

> An atlas of global problems, solved discoveries, and undiscovered ideas.

A searchable website mapping what humanity has figured out, what it is
actively arguing about, and what remains genuinely unknown — seeded with
163 curated items and refreshed automatically from live sources.

## Categories

- **Known** (55) — established laws, inventions, and results
- **Undiscovered** (60) — open problems (dark matter, P vs NP, aging, consciousness)
- **Debated** (48) — contested questions with live argument maps

## Architecture

| Piece | Stack |
|---|---|
| Site | Astro — file-based routing, shared layout |
| Data pipeline | Python (`scripts/fetch.py`, `scripts/map.py`) |
| Refresh | GitHub Actions every 6h — refetch, re-map, test, commit, deploy |

## Quick start

```bash
npm install
npm run dev
```

Data pipeline:

```bash
pip install -r scripts/requirements.txt
python scripts/fetch.py --out data/live
python scripts/map.py
pytest scripts/tests/ -q
```

## Live site

**https://adineo-cmd.github.io/idea-atlas/**

The `atlas-update` workflow runs every six hours: it refetches live debate
sources, re-maps the atlas, runs the test suite, commits refreshed data,
and redeploys the site.
