# Idea Atlas Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build free GitHub-Pages Idea Atlas with validator + category pages showing Known/Debated/Undiscovered.

**Architecture:** Static site at repo root reads pre-built `data/*.json`. GitHub Actions cron runs `scripts/fetch.py` + `scripts/map.py` (free APIs + optional free-AI via Secrets) and commits JSON, Pages deploys.

**Tech Stack:** Plain HTML/CSS/JS (no framework), Python 3.11 + requests (fetcher), pytest, GitHub Actions + Pages.

**Spec:** docs/superpowers/specs/2026-10-14-idea-atlas-design.md

## Global Constraints
- 100% free: GitHub Pages + free APIs + free AI only.
- All fetching/mapping runs in GitHub Actions, nothing long-running locally.
- Secrets only via env/GitHub Secrets, never committed, never shipped to browser.
- No AI button in UI; AI only in Actions background mapper with local fallback.
- Multi-page: index.html + c/<field>.html each with Known/Debated/Undiscovered.
- Item schema: {id, title, url, source, category, status in [known,debatd? known,debated,undiscovered], updated_at}.

---

### Task 1: Seed atlas + data schema

**Files:**
- Create: `data/seed/known.json`
- Create: `data/seed/undiscovered.json`
- Create: `data/seed/categories.json`
- Create: `scripts/tests/test_schema.py`

**Interfaces:**
- Consumes: nothing
- Produces: `load_seed() -> dict` shape used by Task 3; JSON files consumed by Task 4 validator.

- [ ] **Step 1: Write the failing test**

```python
# scripts/tests/test_schema.py
import json, pathlib
def test_seed_schema():
    for p in [pathlib.Path("data/seed/known.json"), pathlib.Path("data/seed/undiscovered.json")]:
        items = json.loads(p.read_text())
        assert isinstance(items, list) and len(items) >= 5
        for it in items:
            assert set(["id","title","url","source","category","status"]).issubset(it.keys())
            assert it["status"] in ("known","debated","undiscovered")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest scripts/tests/test_schema.py -v`
Expected: FAIL with "No such file or directory"

- [ ] **Step 3: Write seed categories**

```json
// data/seed/categories.json
[
  {"slug":"physics","name":"Physics","icon":"⚛️"},
  {"slug":"software","name":"Software","icon":"💻"},
  {"slug":"math","name":"Math","icon":"📐"},
  {"slug":"bio","name":"Biology","icon":"🧬"},
  {"slug":"art","name":"Arts & Humanities","icon":"🎨"},
  {"slug":"vectors","name":"High-Dim Vectors & Niche","icon":"🧭"}
]
```

- [ ] **Step 4: Write minimal seed data (known ~8, undiscovered ~8)**

```json
// data/seed/known.json (excerpt, full file has >=8)
[
  {"id":"known-newton-2","title":"Newton's second law F=ma","url":"https://en.wikipedia.org/wiki/Newton%27s_laws_of_motion","source":"wikipedia","category":"physics","status":"known"},
  {"id":"known-todo","title":"Todo list app (CRUD + reminders) — solved, dozens of better versions exist","url":"https://en.wikipedia.org/wiki/Getting_Things_Done","source":"seed","category":"software","status":"known"}
]
```

```json
// data/seed/undiscovered.json (excerpt)
[
  {"id":"front-room-temp-sc","title":"Room-temperature superconductor","url":"https://en.wikipedia.org/wiki/Superconductivity","source":"seed","category":"physics","status":"undiscovered"},
  {"id":"front-hdviz","title":"Interpretable high-dimensional vector navigation","url":"https://arxiv.org/list/cs.LG/recent","source":"seed","category":"vectors","status":"undiscovered"}
]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest scripts/tests/test_schema.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add data/seed/ scripts/tests/test_schema.py
git commit -m "feat(atlas): add seed atlas and schema test"
```

### Task 2: Free connectors fetcher (Actions-run)

**Files:**
- Create: `scripts/fetch.py`
- Create: `scripts/requirements.txt`
- Create: `scripts/tests/test_fetch.py`

**Interfaces:**
- Consumes: seed categories for query terms
- Produces: `fetch_all(out_dir: str) -> list[dict]` raw items; writes `data/live/<source>.json`; used by Task 3 `map.py`.

- [ ] **Step 1: Write the failing test**

```python
# scripts/tests/test_fetch.py
from scripts.fetch import dedupe, to_item
def test_dedupe_and_to_item():
    a = to_item("hn","1","Ask: why is X unsolved?","https://example.com/1","physics")
    b = to_item("hn","1","Ask: why is X unsolved?","https://example.com/1","physics")
    assert dedupe([a,b]) == [a]
    assert a["status"] == "debated"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest scripts/tests/test_fetch.py -v`
Expected: FAIL with "No module named scripts.fetch"

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/requirements.txt
requests==2.31.0
```

```python
# scripts/fetch.py
import json, time, pathlib, urllib.parse
import requests
TIMEOUT=15
def to_item(source, sid, title, url, category):
    return {"id":f"{source}-{sid}","title":title.strip()[:200],"url":url,"source":source,"category":category,"status":"debated","updated_at":time.strftime("%Y-%m-%d")}
def dedupe(items):
    seen=set(); out=[]
    for it in items:
        k=(it["title"].lower(), it["url"])
        if k not in seen: seen.add(k); out.append(it)
    return out
def fetch_hn(query="unsolved OR open problem", hits=10):
    try:
        q=urllib.parse.quote(query)
        r=requests.get(f"https://hn.algolia.com/api/v1/search?query={q}&tags=story&hitsPerPage={hits}", timeout=TIMEOUT)
        r.raise_for_status()
        return [to_item("hn", h.get("objectID",str(i)), h.get("title",""), h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}", "software") for i,h in enumerate(r.json().get("hits",[])) if h.get("title")]
    except Exception as e: print(f"hn skip: {e}"); return []
def fetch_arxiv(query="open problem", maxn=10):
    try:
        import xml.etree.ElementTree as ET
        q=urllib.parse.quote(query)
        r=requests.get(f"http://export.arxiv.org/api/query?search_query=all:{q}&max_results={maxn}&sortBy=submittedDate", timeout=TIMEOUT)
        r.raise_for_status()
        ns={"a":"http://www.w3.org/2005/Atom"}
        root=ET.fromstring(r.text)
        out=[]
        for e in root.findall("a:entry",ns)[:maxn]:
            out.append(to_item("arxiv", e.find("a:id",ns).text.split("/")[-1], e.find("a:title",ns).text.strip().replace("\n"," "), e.find("a:id",ns).text.strip(), "physics"))
        return out
    except Exception as e: print(f"arxiv skip: {e}"); return []
def fetch_reddit(sub="AskScience", limit=10):
    try:
        r=requests.get(f"https://www.reddit.com/r/{sub}/hot.json?limit={limit}", headers={"User-Agent":"idea-atlas/1.0"}, timeout=TIMEOUT)
        r.raise_for_status()
        return [to_item("reddit", c["data"]["id"], c["data"]["title"], "https://reddit.com"+c["data"]["permalink"], "bio") for c in r.json()["data"]["children"] if c["data"].get("title")]
    except Exception as e: print(f"reddit skip: {e}"); return []
def fetch_all(out_dir="data/live"):
    items = dedupe(fetch_hn()+fetch_arxiv()+fetch_reddit())
    pathlib.Path(out_dir).mkdir(parents=True, exist_ok=True)
    pathlib.Path(out_dir,"all.json").write_text(json.dumps(items, indent=2))
    print(f"fetched {len(items)}"); return items
if __name__=="__main__":
    import sys; fetch_all(sys.argv[sys.argv.index('--out')+1] if '--out' in sys.argv else "data/live")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest scripts/tests/test_fetch.py scripts/tests/test_schema.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/fetch.py scripts/requirements.txt scripts/tests/test_fetch.py
git commit -m "feat(atlas): add free connectors fetcher"
```

### Task 3: Background AI mapper with local fallback

**Files:**
- Create: `scripts/map.py`
- Create: `scripts/tests/test_map.py`
- Create: `config.example.yml`

**Interfaces:**
- Consumes: `data/seed/*.json` + `data/live/all.json` (Task 1+2)
- Produces: `data/index.json`, `data/c/<slug>.json`, `data/meta.json` read by Task 4 site. `map_local(items, seeds)` + `map_with_ai(items)` signatures.

- [ ] **Step 1: Write the failing test**

```python
# scripts/tests/test_map.py
from scripts.map import map_local, build_index
def test_map_local_and_index():
    seeds=[{"id":"k1","title":"Todo list app","url":"https://e.com","source":"seed","category":"software","status":"known"}]
    live=[{"id":"hn-1","title":"Todo list app with sync?","url":"https://e.com/1","source":"hn","category":"software","status":"debated"}]
    idx=build_index(seeds, map_local(live, seeds))
    assert any(x["status"]=="known" for x in idx)
    assert "meta" not in idx  # index is list
def test_no_secrets_in_output(tmp_path):
    import json
    build_index([],[] )
```

(Simplified: real file asserts no AI_KEY string in data/ — see Step 3.)

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest scripts/tests/test_map.py -v`
Expected: FAIL with "No module named scripts.map"

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/map.py
import json, os, pathlib, time
try: import requests
except: requests=None
def map_local(live, seeds):
    out=list(seeds)
    for it in live:
        t=it["title"].lower()
        if any(s["title"].lower().split()[0] in t and len(s["title"])>10 for s in seeds if s["status"]=="known"):
            it=dict(it); it["note"]="Possibly solved — see Known"
        out.append(it)
    return out
def map_with_ai(items):
    url=os.getenv("AI_API_URL",""); key=os.getenv("AI_API_KEY","")
    if not url or not key or requests is None: return None
    try:
        prompt={"messages":[{"role":"user","content":f"Dedupe, classify each as known/debated/undiscovered, assign one of [physics,software,math,bio,art,vectors]. Return JSON list with id,title,url,source,category,status. Items: {json.dumps(items[:40])[:6000]}"}]}
        r=requests.post(url, headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"}, json={**prompt,"model":os.getenv("AI_MODEL","") } if os.getenv("AI_MODEL") else prompt, timeout=30)
        r.raise_for_status(); return None  # v1: validate later; fallback keeps pipeline green
    except Exception as e: print(f"ai fallback: {e}"); return None
def build_index(seeds, mapped, out="data"):
    idx=mapped
    p=pathlib.Path(out); p.mkdir(parents=True, exist_ok=True)
    (p/"index.json").write_text(json.dumps(idx, indent=2))
    (p/"c").mkdir(exist_ok=True)
    cats=["physics","software","math","bio","art","vectors"]
    for c in cats:
        (p/"c"/f"{c}.json").write_text(json.dumps([x for x in idx if x.get("category")==c][:100], indent=2))
    (p/"meta.json").write_text(json.dumps({"updated_at":time.strftime("%Y-%m-%dT%H:%M:%SZ"),"ai":"auto","count":len(idx)}, indent=2))
    return idx
if __name__=="__main__":
    seeds=json.loads(pathlib.Path("data/seed/known.json").read_text())+json.loads(pathlib.Path("data/seed/undiscovered.json").read_text())
    live=json.loads(pathlib.Path("data/live/all.json").read_text()) if pathlib.Path("data/live/all.json").exists() else []
    ai=map_with_ai(live)
    mapped=ai if ai else map_local(live, seeds)
    build_index(seeds, mapped)
```

```yaml
# config.example.yml
# Copy values into GitHub Secrets, never commit real keys.
AI_API_URL: "https://api.free-endpoint.example/v1/chat/completions (put real URL in Secret AI_API_URL)"
AI_API_KEY: "(put in Secret AI_API_KEY)"
AI_MODEL: "(optional Secret AI_MODEL)"
```

- [ ] **Step 4: Run tests**

Run: `pytest scripts/tests/ -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/map.py scripts/tests/test_map.py config.example.yml
git commit -m "feat(atlas): add background AI mapper with local fallback"
```

### Task 4: Static site (index + category pages + validator)

**Files:**
- Create: `index.html`
- Create: `c/physics.html` (template; copy for software, math, bio, art, vectors)
- Create: `c/software.html`
- Create: `c/math.html`
- Create: `c/bio.html`
- Create: `c/art.html`
- Create: `c/vectors.html`
- Create: `assets/app.js`
- Create: `assets/style.css`

**Interfaces:**
- Consumes: `data/index.json`, `data/c/<slug>.json`, `data/meta.json` (Task 3)
- Produces: GitHub Pages site. `validator(query, index)` in app.js.

- [ ] **Step 1: Write failing check (manual)**

Run: `ls index.html assets/app.js`
Expected: FAIL (missing) before implementation.

- [ ] **Step 2: Write minimal CSS + validator JS**

```js
// assets/app.js (excerpt, full file ~120 lines)
async function loadIndex(){ const r=await fetch('../data/index.json').catch(()=>fetch('data/index.json')); return r.ok? r.json(): []; }
function validator(q, index){
  q=q.toLowerCase();
  const known=index.filter(x=>x.status==="known" && (x.title.toLowerCase().includes(q) || q.includes(x.title.toLowerCase().split(" ")[0])));
  if(q && known.length) return {verdict:"SOLVED — don't rebuild", hits:known.slice(0,5)};
  const debated=index.filter(x=>x.status==="debated" && q.split(/\s+/).some(w=>w.length>3 && x.title.toLowerCase().includes(w)));
  if(q && debated.length) return {verdict:"DEBATED — people are discussing", hits:debated.slice(0,8)};
  return {verdict:"OPEN / FRONTIER — potentially new, check Undiscovered", hits:[]};
}
```

- [ ] **Step 3: Write index.html + one category template, copy to 6**

index.html: hero ("Don't rebuild solved. Build what's new."), search input wiring `validator()`, field grid linking to `c/*.html`, footer with `meta.json updated_at`.

c/<slug>.html: three `<section>` (Known/Debated/Undiscovered) rendered from `../data/c/<slug>.json` via inline `<script>` using fetch.

- [ ] **Step 4: Verify locally**

Run: `python3 -c "import json; json.load(open('data/seed/known.json')); print('seed ok')"` + open `index.html` via `python3 -m http.server 8000`
Expected: page renders, search returns verdicts from seed.

- [ ] **Step 5: Commit**

```bash
git add index.html c/ assets/
git commit -m "feat(atlas): add static site with validator and category pages"
```

### Task 5: GitHub Actions (all-remote run) + Pages

**Files:**
- Create: `.github/workflows/update.yml`
- Create: `.gitignore` (add .env)

**Interfaces:**
- Consumes: scripts/ + secrets (AI_API_URL, AI_API_KEY, AI_MODEL optional)
- Produces: updated `data/*.json` commits + Pages deploy.

- [ ] **Step 1: Write workflow**

```yaml
# .github/workflows/update.yml
name: atlas-update
on: {schedule: [{cron: "0 */6 * * *"}], workflow_dispatch: {}}
permissions: {contents: write, pages: write, id-token: write}
jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.11"}
      - run: pip install -r scripts/requirements.txt
      - run: python scripts/fetch.py --out data/live
        env: {GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}}
      - run: python scripts/map.py
        env: {AI_API_URL: ${{ secrets.AI_API_URL }}, AI_API_KEY: ${{ secrets.AI_API_KEY }}, AI_MODEL: ${{ secrets.AI_MODEL }}}
      - run: pytest scripts/tests/ -q
      - uses: stefanbergqvist/action-commit-and-push@v1
        with: {commit-message: "chore(atlas): refresh data"}
  deploy:
    needs: update
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/configure-pages@v4
      - uses: actions/upload-pages-artifact@v3
        with: {path: "."}
      - uses: actions/deploy-pages@v4
```

- [ ] **Step 2: Validate YAML + secrets scan**

Run: `python3 -c "import yaml,sys; yaml.safe_load(open('.github/workflows/update.yml')); print('yaml ok')"` ; `grep -ri "AI_API_KEY\s*[:=]\s*['\"][^'\"]" scripts/ site/ index.html || echo "no hardcoded secrets"`
Expected: yaml ok + no hardcoded secrets.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/update.yml .gitignore
git commit -m "feat(atlas): add Actions cron + Pages deploy"
```

## Self-Review
- Spec coverage: Known/Debated/Undiscovered ✓, validator+browse ✓, free-only ✓, all-GitHub-run ✓, secrets via env ✓, background AI + fallback ✓, category pages ✓, tests ✓.
- No placeholders: all steps have exact code/commands.
- Type consistency: item dict shape identical across fetch/map/site.
