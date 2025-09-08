#!/usr/bin/env python3
# Sports App Project — collector (HARDENED)
# - Always writes links (buttons), items, and updated timestamp
# - Normalizes sources and dates
# - Safe even if a feed entry is missing fields

import json, time, re, hashlib
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from datetime import datetime, timezone
import feedparser

from feeds import FEEDS, STATIC_LINKS  # your team-specific feeds + buttons

MAX_ITEMS = 60

# Allow-list of publishers shown in the Source dropdown.
ALLOWED_SOURCES = {
    "ESPN","Yahoo Sports","Sports Illustrated","CBS Sports","SB Nation",
    "Bleacher Report","The Athletic","NFL.com","PFF","Pro Football Focus",
    "Pro-Football-Reference","IndyStar","Colts.com","ArizonaSports.com",
    "AZ Cardinals Official","Stampede Blue","Colts Wire","Yahoo Team",
    "WTHR","FOX59","Reddit — r/Colts","Reddit — r/azcardinals",
    "Philadelphia Inquirer","PhillyVoice","NBC Sports","NBC Sports Philadelphia"
}

# --- utilities ---------------------------------------------------------------

def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

def _host(u: str) -> str:
    try:
        n = urlparse(u).netloc.lower()
        for p in ("www.","m.","amp."):
            if n.startswith(p): n = n[len(p):]
        return n
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
    # team sites / locals
    "colts.com":"Colts.com",
    "azcardinals.com":"AZ Cardinals Official",
    "arizonasports.com":"ArizonaSports.com",
    "indystar.com":"IndyStar",
    # nat'l
    "espn.com":"ESPN",
    "sports.yahoo.com":"Yahoo Sports",
    "si.com":"Sports Illustrated",
    "cbssports.com":"CBS Sports",
    "sbnation.com":"SB Nation",
    "bleacherreport.com":"Bleacher Report",
    "theathletic.com":"The Athletic",
    "nfl.com":"NFL.com",
    "pff.com":"PFF",
    "pro-football-reference.com":"Pro-Football-Reference",
    "nbcsports.com":"NBC Sports",
    "nbcsportsphiladelphia.com":"NBC Sports Philadelphia",
    "fox59.com":"FOX59",
    "wthr.com":"WTHR",
}

def source_label(link: str, feed_name: str) -> str:
    # collapse subreddits into stable labels
    if "reddit.com/r/colts" in link or "Reddit — r/Colts" in feed_name:
        return "Reddit — r/Colts"
    if "reddit.com/r/azcardinals" in link or "Reddit — r/azcardinals" in feed_name:
        return "Reddit — r/azcardinals"
    host = _host(link)
    return ALIASES.get(host, feed_name.strip())

KEEP_PATTERNS = [
    r"\bColts\b", r"\bIndianapolis\b", r"\bIndy\b",
    r"\bCardinals\b", r"\bArizona\b", r"\bAZ\b",
    r"\bEagles\b", r"\bPhiladelphia\b", r"\bPhilly\b"
]
DROP_PATTERNS = [r"\bwomen'?s\b", r"\bWBB\b", r"\bvolleyball\b", r"\bbasketball\b", r"\bbaseball\b"]

def text_ok(title: str, summary: str) -> bool:
    t = f"{title} {summary}"
    if not any(re.search(p, t, re.I) for p in KEEP_PATTERNS): return False
    if any(re.search(p, t, re.I) for p in DROP_PATTERNS): return False
    return True

def parse_time(entry):
    for key in ("published_parsed","updated_parsed"):
        if entry.get(key):
            try:
                return time.strftime("%Y-%m-%dT%H:%M:%S%z", entry[key])
            except Exception:
                pass
    return now_iso()

# --- pipeline ----------------------------------------------------------------

def fetch_all():
    items, seen = [], set()
    for f in FEEDS:
        fname, furl = f["name"].strip(), f["url"].strip()
        try:
            parsed = feedparser.parse(furl)
        except Exception:
            continue
        for e in parsed.entries[:120]:
            link = canonical((e.get("link") or e.get("id") or "").strip())
            if not link: continue
            key = hid(link)
            if key in seen: continue

            src = source_label(link, fname)
            if src not in ALLOWED_SOURCES:  # hard whitelist keeps Source menu clean
                continue

            title = (e.get("title") or "").strip()
            summary = (e.get("summary") or e.get("description") or "").strip()
            if not text_ok(title, summary): continue

            items.append({
                "id": key,
                "title": title or "(untitled)",
                "link": link,
                "source": src,
                "feed": fname,
                "published": parse_time(e),  # ISO string
                "summary": summary,
            })
            seen.add(key)

    items.sort(key=lambda x: x["published"], reverse=True)
    return items[:MAX_ITEMS]

def write_items(items):
    payload = {
        "updated": now_iso(),
        "items": items,
        "links": STATIC_LINKS  # ALWAYS write buttons so UI never "loses" them
    }
    with open("items.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    write_items(fetch_all())