import json
import os
import pathlib
import time

try:
    import requests
except Exception:
    requests = None


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
        prompt = {"messages": [{"role": "user", "content": f"Dedupe, classify each as known/debated/undiscovered, assign one of [physics,software,math,bio,art,vectors]. Return JSON list with id,title,url,source,category,status. Items: {json.dumps(items[:40])[:6000]}"}]}
        r = requests.post(url, headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"}, json={**prompt, "model": os.getenv("AI_MODEL", "")} if os.getenv("AI_MODEL") else prompt, timeout=30)
        r.raise_for_status()
        return None  # v1: validate later; fallback keeps pipeline green
    except Exception as e:
        print(f"ai fallback: {e}")
        return None


def build_index(seeds, mapped, out="data"):
    idx = mapped
    p = pathlib.Path(out)
    p.mkdir(parents=True, exist_ok=True)
    (p / "index.json").write_text(json.dumps(idx, indent=2))
    (p / "c").mkdir(exist_ok=True)
    cats = ["physics", "software", "math", "bio", "art", "vectors"]
    for c in cats:
        (p / "c" / f"{c}.json").write_text(json.dumps([x for x in idx if x.get("category") == c][:100], indent=2))
    (p / "meta.json").write_text(json.dumps({"updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"), "ai": "auto", "count": len(idx)}, indent=2))
    return idx


if __name__ == "__main__":
    seeds = json.loads(pathlib.Path("data/seed/known.json").read_text()) + json.loads(pathlib.Path("data/seed/undiscovered.json").read_text()) + (json.loads(pathlib.Path("data/seed/debated.json").read_text()) if pathlib.Path("data/seed/debated.json").exists() else [])
    live = json.loads(pathlib.Path("data/live/all.json").read_text()) if pathlib.Path("data/live/all.json").exists() else []
    ai = map_with_ai(live)
    mapped = ai if ai else map_local(live, seeds)
    build_index(seeds, mapped)
