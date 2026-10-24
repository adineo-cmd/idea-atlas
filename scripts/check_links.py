"""Sample dead links from data/index.json (advisory, exit 0 unless --strict).

Spec (docs/DESIGN.md): build step HEAD-checks sampled URLs, limit 50 to stay
free/fast. Uses only the stdlib so it runs anywhere without requirements.txt.
"""

import argparse
import json
import pathlib
import random
import urllib.request

UA = {"User-Agent": "idea-atlas-linkcheck/1.0"}
SAMPLE_LIMIT = 50
TIMEOUT = 5


def sample_urls(items, limit=SAMPLE_LIMIT):
    urls = sorted({it["url"] for it in items if it.get("url", "").startswith("http")})
    random.seed(42)  # deterministic samples between runs
    return random.sample(urls, min(limit, len(urls)))


def check(url):
    req = urllib.request.Request(url, headers=UA, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status
    except Exception:
        # Some servers reject HEAD; retry with a ranged GET before giving up.
        req = urllib.request.Request(url, headers={**UA, "Range": "bytes=0-512"})
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return r.status
        except Exception as e:
            return getattr(e, "code", str(e))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", default="data/index.json")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any link is dead")
    args = ap.parse_args()

    p = pathlib.Path(args.index)
    if not p.exists():
        print(f"linkcheck: {p} missing, nothing to check")
        return 0

    items = json.loads(p.read_text())
    dead = []
    for url in sample_urls(items):
        status = check(url)
        ok = isinstance(status, int) and 200 <= status < 400
        print(f"{'ok  ' if ok else 'DEAD'} {status} {url}")
        if not ok:
            dead.append(url)

    print(f"linkcheck: {len(dead)} dead of {min(SAMPLE_LIMIT, len(items))} sampled")
    if dead and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
