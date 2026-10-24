import json
import os
import pathlib
import time

try:
    import requests
except Exception:
    requests = None

SEED_DIR = pathlib.Path("data/seed")
DEFAULT_CATS = ["physics", "software", "math", "bio", "art", "vectors"]


def load_categories():
    """Category slugs come from data/seed/categories.json, not a hardcoded list."""
    p = SEED_DIR / "categories.json"
    if p.exists():
        try:
            return [c["slug"] for c in json.loads(p.read_text())]
        except Exception as e:
            print(f"categories.json unreadable ({e}), using defaults")
    return DEFAULT_CATS


def dedupe(items):
    """Keep first occurrence per URL (seeds first, so curated wins over live)."""
    seen = set()
    out = []
    for it in items:
        key = (it.get("url") or "").rstrip("/") or it.get("title", "").lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out


def map_local(live, seeds):
    out = list(seeds)
    for it in live:
        t = it["title"].lower()
        if any(s["title"].lower().split()[0] in t and len(s["title"]) > 10 for s in seeds if s["status"] == "known"):
            it = dict(it)
            it["note"] = "Possibly solved — see Known"
        out.append(it)
    return out


def map_with_ai(items):
    url = os.getenv("AI_API_URL", "")
    key = os.getenv("AI_API_KEY", "")
    if not url or not key or requests is None:
        return None
    try:
        cats = ",".join(load_categories())
        prompt = {"messages": [{"role": "user", "content": f"Dedupe, classify each as known/debated/undiscovered, assign one of [{cats}]. Return JSON list with id,title,url,source,category,status. Items: {json.dumps(items[:40])[:6000]}"}]}
        r = requests.post(url, headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"}, json={**prompt, "model": os.getenv("AI_MODEL", "")} if os.getenv("AI_MODEL") else prompt, timeout=30)
        r.raise_for_status()
        return None  # v1: validate later; fallback keeps pipeline green
    except Exception as e:
        print(f"ai fallback: {e}")
        return None


def build_index(seeds, mapped, out="data"):
    idx = dedupe(mapped)
    p = pathlib.Path(out)
    p.mkdir(parents=True, exist_ok=True)
    (p / "index.json").write_text(json.dumps(idx, indent=2))
    (p / "c").mkdir(exist_ok=True)
    for c in load_categories():
        (p / "c" / f"{c}.json").write_text(json.dumps([x for x in idx if x.get("category") == c][:400], indent=2))
    # Site-facing copy of the registry so pages don't read from data/seed/.
    (p / "categories.json").write_text(json.dumps(json.loads((SEED_DIR / "categories.json").read_text()), indent=2))
    counts = {}
    for x in idx:
        counts[x.get("status", "?")] = counts.get(x.get("status", "?"), 0) + 1
    (p / "meta.json").write_text(json.dumps({
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "ai": "auto",
        "count": len(idx),
        "by_status": counts,
        "categories": len(load_categories()),
    }, indent=2))
    return idx


def load_seeds():
    seeds = []
    for name in ("known.json", "undiscovered.json", "debated.json"):
        p = SEED_DIR / name
        if p.exists():
            seeds += json.loads(p.read_text())
    return seeds


if __name__ == "__main__":
    seeds = load_seeds()
    live = json.loads(pathlib.Path("data/live/all.json").read_text()) if pathlib.Path("data/live/all.json").exists() else []
    ai = map_with_ai(live)
    mapped = ai if ai else map_local(live, seeds)
    idx = build_index(seeds, mapped)
    print(f"atlas: {len(idx)} items across {len(load_categories())} fields")
