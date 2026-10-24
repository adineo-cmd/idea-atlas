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
def fetch_stackexchange(site="mathoverflow", limit=10):
    try:
        r=requests.get(f"https://api.stackexchange.com/2.3/search/advanced?order=desc&sort=activity&site={site}&pagesize={limit}&filter=default&q=open%20problem", headers={"User-Agent":"idea-atlas/1.0"}, timeout=TIMEOUT)
        r.raise_for_status()
        cats={"mathoverflow":"math","physics":"physics","stackoverflow":"software","biology":"bio"}
        return [to_item("stackexchange", str(q["question_id"]), q["title"], q["link"], cats.get(site,"vectors")) for q in r.json().get("items",[]) if q.get("title")]
    except Exception as e: print(f"stackexchange skip: {e}"); return []
def fetch_all(out_dir="data/live"):
    items = dedupe(fetch_hn()+fetch_arxiv()+fetch_reddit()+fetch_stackexchange("mathoverflow")+fetch_stackexchange("physics"))
    pathlib.Path(out_dir).mkdir(parents=True, exist_ok=True)
    pathlib.Path(out_dir,"all.json").write_text(json.dumps(items, indent=2))
    print(f"fetched {len(items)}"); return items
if __name__=="__main__":
    import sys; fetch_all(sys.argv[sys.argv.index('--out')+1] if '--out' in sys.argv else "data/live")
