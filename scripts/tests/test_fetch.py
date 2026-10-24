from scripts.fetch import dedupe, to_item
def test_dedupe_and_to_item():
    a = to_item("hn","1","Ask: why is X unsolved?","https://example.com/1","physics")
    b = to_item("hn","1","Ask: why is X unsolved?","https://example.com/1","physics")
    assert dedupe([a,b]) == [a]
    assert a["status"] == "debated"
