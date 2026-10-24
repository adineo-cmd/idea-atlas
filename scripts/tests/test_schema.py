import json, pathlib
def test_seed_schema():
    for p in [pathlib.Path("data/seed/known.json"), pathlib.Path("data/seed/undiscovered.json"), pathlib.Path("data/seed/debated.json")]:
        items = json.loads(p.read_text())
        assert isinstance(items, list) and len(items) >= 5
        for it in items:
            assert set(["id","title","url","source","category","status"]).issubset(it.keys())
            assert it["status"] in ("known","debated","undiscovered")
            assert it["url"].startswith("http")
            assert it["category"] in ("physics","software","math","bio","art","vectors")
def test_all_categories_covered():
    for p in [pathlib.Path("data/seed/known.json"), pathlib.Path("data/seed/undiscovered.json"), pathlib.Path("data/seed/debated.json")]:
        cats = {it["category"] for it in json.loads(p.read_text())}
        assert cats == {"physics","software","math","bio","art","vectors"}
