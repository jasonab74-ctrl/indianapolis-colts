#!/usr/bin/env python3
# Indianapolis Colts — News collector (STRICT, no Google News)
import json, time, re, hashlib
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from datetime import datetime, timezone
import feedparser
from feeds import FEEDS, STATIC_LINKS

MAX_ITEMS = 60

# Only these names may appear in the Source menu
ALLOWED_SOURCES = {
    "Colts.com", "Stampede Blue", "Colts Wire", "IndyStar",
    "ESPN", "Yahoo Sports", "Sports Illustrated", "CBS Sports",
    "SB Nation", "WTHR", "FOX59", "PFF", "NFL.com", "Bleacher Report",
    "Reddit — r/Colts"
}

def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

def _host(u):
    try:
        netloc = urlparse(u).netloc.lower()
        for pat in ("www.", "m.", "amp."):
            if netloc.startswith(pat): netloc = netloc[len(pat):]
        return netloc
    except Exception:
        return ""

def canonical(u: str) -> str:
    try:
        p = urlparse(u)
        keep = {"id","story","v","p"}
        q = parse_qs(p.query)
        q = {k:v for k,v in q.items() if k in keep}
        p = p._replace(query=urlencode(q, doseq=True), fragment="", netloc=_host(u))
        return urlunparse(p)
    except Exception:
        return u

def hid(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:16]

ALIASES = {
    "stampedeblue.com": "Stampede Blue",
    "coltswire.usatoday.com": "Colts Wire",
    "colts.com": "Colts.com",
    "espn.com": "ESPN",
    "sports.yahoo.com": "Yahoo Sports",
    "si.com": "Sports Illustrated",
    "sbnation.com": "SB Nation",
    "indystar.com": "IndyStar",
    "wthr.com": "WTHR",
    "fox59.com": "FOX59",
    "pff.com": "PFF",
    "nfl.com": "NFL.com",
    "bleacherreport.com": "Bleacher Report",
    "cbssports.com": "CBS Sports",
}

def source_label(entry_link: str, feed_name: str) -> str:
    # Reddit is a single clean label
    if "Reddit — r/Colts" in feed_name:
        return "Reddit — r/Colts"
    host = _host(entry_link)
    return ALIASES.get(host, feed_name)

COLTS_KEEP = [
    r"\bColts\b", r"\bIndianapolis\b", r"\bIndy\b",
    r"\bAnthony Richardson\b", r"\bJonathan Taylor\b", r"\bMichael Pittman\b",
    r"\bShane Steichen\b", r"\bQuenton Nelson\b", r"\bDeForest Buckner\b",
]
COLTS_DROP = [r"\bwomen'?s\b", r"\bWBB\b", r"\bvolleyball\b", r"\bbasketball\b", r"\bbaseball\b"]

def allowed(title: str, summary: str) -> bool:
    text = f"{title} {summary}"
    if not any(re.search(p, text, re.I) for p in COLTS_KEEP): return False
    if any(re.search(p, text, re.I) for p in COLTS_DROP): return False
    return True

def fetch_all():
    items, seen = [], set()
    for f in FEEDS:
        fname, furl = f["name"].strip(), f["url"].strip()
        try:
            parsed = feedparser.parse(furl)
        except Exception:
            continue
        for e in parsed.entries[:100]:
            link = canonical((e.get("link") or e.get("id") or "").strip())
            if not link: continue
            key = hid(link)
            if key in seen: continue

            src = source_label(link, fname)
            if src not in ALLOWED_SOURCES:  # hard gate
                continue

            title = (e.get("title") or "").strip()
            summary = (e.get("summary") or e.get("description") or "").strip()
            if not allowed(title, summary): continue

            pub = e.get("published_parsed") or e.get("updated_parsed")
            ts = time.strftime("%Y-%m-%dT%H:%M:%S%z", pub) if pub else now_iso()

            items.append({
                "id": key, "title": title, "link": link, "source": src,
                "feed": fname, "published": ts, "summary": summary
            })
            seen.add(key)

    items.sort(key=lambda x: x["published"], reverse=True)
    return items[:MAX_ITEMS]

def write_items(items):
    with open("items.json", "w", encoding="utf-8") as f:
        json.dump({"updated": now_iso(), "items": items, "links": STATIC_LINKS}, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    write_items(fetch_all())