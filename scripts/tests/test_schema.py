import json, pathlib

SEED = pathlib.Path("data/seed")
STATUS_FILES = [SEED / "known.json", SEED / "undiscovered.json", SEED / "debated.json"]


def categories():
    return {c["slug"] for c in json.loads((SEED / "categories.json").read_text())}


def test_categories_registry():
    cats = json.loads((SEED / "categories.json").read_text())
    assert len(cats) >= 6
    for c in cats:
        assert set(["slug", "name", "icon"]).issubset(c.keys())
        assert c["slug"] and " " not in c["slug"]


def test_seed_schema():
    for p in STATUS_FILES:
        items = json.loads(p.read_text())
        assert isinstance(items, list) and len(items) >= 5
        for it in items:
            assert set(["id","title","url","source","category","status"]).issubset(it.keys())
            assert it["status"] in ("known","debated","undiscovered")
            assert it["url"].startswith("http")
            assert it["category"] in categories()
            if "era" in it:
                assert isinstance(it["era"], str) and it["era"]


def test_seed_ids_unique():
    ids = []
    for p in STATUS_FILES:
        ids += [it["id"] for it in json.loads(p.read_text())]
    assert len(ids) == len(set(ids)), "duplicate seed ids"


def test_all_categories_covered():
    """Every seed category exists in the registry, and every registry
    category has at least one seed item somewhere (no empty fields)."""
    used = set()
    for p in STATUS_FILES:
        used |= {it["category"] for it in json.loads(p.read_text())}
    reg = categories()
    assert used <= reg, f"seed categories missing from registry: {used - reg}"
    assert reg <= used, f"registry categories with no seed items: {reg - used}"
