import json
import os
import pathlib

from scripts.map import build_index, map_local, map_with_ai


def test_map_local_and_index(tmp_path):
    seeds = [{"id": "k1", "title": "Todo list app", "url": "https://e.com", "source": "seed", "category": "software", "status": "known"}]
    live = [{"id": "hn-1", "title": "Todo list app with sync?", "url": "https://e.com/1", "source": "hn", "category": "software", "status": "debated"}]
    mapped = map_local(live, seeds)
    assert any(x["status"] == "known" for x in mapped)
    idx = build_index(seeds, mapped, out=str(tmp_path))
    assert isinstance(idx, list)
    assert "meta" not in idx  # index is list
    assert any(x["status"] == "known" for x in idx)
    # 6 category files + index + meta written
    for c in ["physics", "software", "math", "bio", "art", "vectors"]:
        assert (tmp_path / "c" / f"{c}.json").exists()
    meta = json.loads((tmp_path / "meta.json").read_text())
    assert meta["count"] == len(idx)


def test_map_with_ai_fallback_missing_env(monkeypatch):
    monkeypatch.delenv("AI_API_URL", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    assert map_with_ai([]) is None


def test_no_secrets_in_output(tmp_path, monkeypatch, capsys):
    sentinel_key = "SECRET-SENTINEL-abc123-no-real-secret"
    monkeypatch.setenv("AI_API_KEY", sentinel_key)
    monkeypatch.setenv("AI_API_URL", "")
    monkeypatch.delenv("AI_MODEL", raising=False)
    assert map_with_ai([{"id": "x", "title": "t", "url": "https://e.com", "source": "hn", "category": "software", "status": "debated"}]) is None
    seeds = [{"id": "k1", "title": "Todo list app", "url": "https://e.com", "source": "seed", "category": "software", "status": "known"}]
    build_index(seeds, map_local([], seeds), out=str(tmp_path))
    for p in tmp_path.rglob("*.json"):
        assert sentinel_key not in p.read_text()
    # never log secrets to stdout/stderr
    out = capsys.readouterr().out
    assert sentinel_key not in out
    # also scan real data/ output if present (runtime artifacts)
    data_dir = pathlib.Path("data")
    if data_dir.exists():
        for p in data_dir.rglob("*.json"):
            assert sentinel_key not in p.read_text()
            assert "AI_API_KEY" not in p.read_text()
