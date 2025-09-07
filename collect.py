#!/usr/bin/env python3
# Indianapolis Colts — News collector (tight sources + proper logo/icons already in repo)
import json, time, re, hashlib
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from datetime import datetime, timezone
import feedparser

from feeds import FEEDS, STATIC_LINKS

MAX_ITEMS = 60

# Show up in Source dropdown and allowed from Google News
ALLOWED_SOURCES = {
    "Colts.com", "Stampede Blue", "Colts Wire", "IndyStar",
    "ESPN", "Yahoo Sports", "Sports Illustrated", "CBS Sports",
    "SB Nation", "WTHR", "FOX59", "PFF", "USA Today", "NFL.com",
    "Bleacher Report", "Reddit — r/Colts"
}
TRUSTED_FEEDS = set(ALLOWED_SOURCES)

def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

HOST_CLEANUP = ((r"^www\.", ""), (r"^m\.", ""), (r"^amp\.", ""), (r"\.amp$", ""))

def hostname(url):
    try:
        netloc = urlparse(url).netloc or ""
        h = netloc.lower()
        for pat, rep in HOST_CLEANUP:
            h = re.sub(pat, rep, h)
        return h
    except Exception:
        return ""

def canonicalize_url(url: str) -> str:
    try:
        u = urlparse(url)
        keep = {"id","story","v","p"}
        q = parse_qs(u.query)
        q_keep = {k:v for k,v in q.items() if k in keep}
        clean = u._replace(query=urlencode(q_keep, doseq=True), fragment="", netloc=hostname(url))
        return urlunparse(clean)
    except Exception:
        return url

def hash_id(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:16]

def is_reddit(feed_url: str, feed_name: str) -> bool:
    h = hostname(feed_url)
    return "reddit.com" in h or "Reddit" in feed_name

def is_google_news(feed_url: str) -> bool:
    return "news.google.com" in hostname(feed_url)

def normalize_source(entry, feed_name: str, feed_url: str) -> str:
    if is_reddit(feed_url, feed_name):
        sub = None
        for s in (entry.get("link",""), feed_url, entry.get("id","")):
            m = re.search(r"/r/([A-Za-z0-9_]+)/", s)
            if m: sub = m.group(1); break
        return f"Reddit — r/{sub or 'Colts'}"

    if is_google_news(feed_url):
        src = entry.get("source", {})
        if isinstance(src, dict):
            t = (src.get("title") or "").strip()
            if t: return t
        site = hostname(entry.get("link",""))
        return site.title() if site else "Google News"

    site = hostname(entry.get("link",""))
    if site:
        alias = {
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
            "usatoday.com": "USA Today",
            "cbssports.com": "CBS Sports",
        }.get(site)
        return alias or site.title()
    return feed_name.strip() or "Unknown"

COLTS_KEYWORDS = [
    r"\bColts\b", r"\bIndianapolis\b", r"\bIndy\b",
    r"\bAnthony Richardson\b", r"\bJonathan Taylor\b", r"\bMichael Pittman\b",
    r"\bShane Steichen\b", r"\bQuenton Nelson\b", r"\bDeForest Buckner\b"
]
COLTS_EXCLUDES = [
    r"\bwomen'?s\b", r"\bWBB\b", r"\bvolleyball\b", r"\bbasketball\b", r"\bbaseball\b"
]

def allow_item(title: str, summary: str, source_label: str, feed_name: str, from_google: bool) -> bool:
    # Only allow whitelisted outlets from Google News
    if from_google and source_label not in ALLOWED_SOURCES:
        return False
    # Trusted feeds always in
    if source_label in TRUSTED_FEEDS or feed_name in TRUSTED_FEEDS:
        return True
    text = f"{title} {summary}"
    if not any(re.search(p, text, flags=re.I) for p in COLTS_KEYWORDS):
        return False
    if any(re.search(p, text, flags=re.I) for p in COLTS_EXCLUDES):
        return False
    return True

def fetch_all():
    items, seen = [], set()
    for feed in FEEDS:
        feed_name, feed_url = feed["name"].strip(), feed["url"].strip()
        try:
            parsed = feedparser.parse(feed_url)
        except Exception:
            continue
        for e in parsed.entries[:100]:
            link = canonicalize_url((e.get("link") or e.get("id") or "").strip())
            if not link: continue
            key = hash_id(link)
            if key in seen: continue

            source = normalize_source(e, feed_name, feed_url)
            title = (e.get("title") or "").strip()
            summary = (e.get("summary") or e.get("description") or "").strip()

            if not allow_item(title, summary, source, feed_name, is_google_news(feed_url)):
                continue

            pub = e.get("published_parsed") or e.get("updated_parsed")
            ts = time.strftime("%Y-%m-%dT%H:%M:%S%z", pub) if pub else now_iso()

            items.append({
                "id": key,
                "title": title,
                "link": link,
                "source": source,
                "feed": feed_name,
                "published": ts,
                "summary": summary,
            })
            seen.add(key)

    items.sort(key=lambda x: x["published"], reverse=True)
    return items[:MAX_ITEMS]

def write_items(items):
    payload = {"updated": now_iso(), "items": items, "links": STATIC_LINKS}
    with open("items.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

def main():
    write_items(fetch_all())

if __name__ == "__main__":
    main()