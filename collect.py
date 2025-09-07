#!/usr/bin/env python3
import json, time, re, hashlib
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
import feedparser
from datetime import datetime, timezone

from feeds import FEEDS, STATIC_LINKS

MAX_ITEMS = 60  # write up to this many newest items

TRUSTED_FEEDS = {
    "Colts.com", "Stampede Blue", "Colts Wire", "ESPN", "Yahoo Sports",
    "The Athletic", "Sports Illustrated", "CBS Sports", "SB Nation",
    "WTHR", "FOX59", "IndyStar", "Pro Football Focus", "PFF",
    "Pro-Football-Reference", "The Sporting News", "USA Today", "NFL.com",
    "Bleacher Report", "Reddit — r/Colts"
}

# --- Utilities ---------------------------------------------------------------

def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

HOST_CLEANUP = (
    (r"^www\.", ""), (r"^m\.", ""), (r"^amp\.", ""), (r"\.amp$", "")
)

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
    """Strip tracking params and normalize so dupes collapse."""
    try:
        u = urlparse(url)
        # keep only core params that affect content
        keep = {"id", "story", "v", "p"}
        q = parse_qs(u.query)
        q_keep = {k: v for k, v in q.items() if k in keep}
        new_q = urlencode(q_keep, doseq=True)
        # drop fragments
        clean = u._replace(query=new_q, fragment="")
        # normalize netloc (remove www., m.)
        netloc = hostname(url)
        clean = clean._replace(netloc=netloc)
        return urlunparse(clean)
    except Exception:
        return url

def hash_id(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:16]

def is_reddit(feed_url: str, feed_name: str) -> bool:
    h = hostname(feed_url)
    return "reddit.com" in h or "redd.it" in h or "r/" in feed_url or "Reddit" in feed_name

def is_google_news(feed_url: str) -> bool:
    return "news.google.com" in hostname(feed_url)

def normalize_source(entry, feed_name: str, feed_url: str) -> str:
    """Return a clean publisher name for the UI filter."""
    # 1) Reddit -> subreddit label
    if is_reddit(feed_url, feed_name):
        # try to extract subreddit from link or feed_url
        sub = None
        for s in (entry.get("link",""), feed_url, entry.get("id","")):
            m = re.search(r"/r/([A-Za-z0-9_]+)/", s)
            if m:
                sub = m.group(1)
                break
        return f"Reddit — r/{sub or 'Colts'}"

    # 2) Google News -> original source title if present
    if is_google_news(feed_url):
        try:
            src = entry.get("source", {})
            if isinstance(src, dict):
                title = src.get("title")
                if title: return title.strip()
        except Exception:
            pass
        # fallback: host from link
        site = hostname(entry.get("link",""))
        return site.title() if site else "Google News"

    # 3) Generic: prefer host of the entry link
    site = hostname(entry.get("link",""))
    if site:
        label = {
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
        }.get(site)
        return label or site.title()
    return feed_name.strip() or "Unknown"

COLTS_KEYWORDS = [
    r"\bColts\b", r"\bIndianapolis\b", r"\bIndy\b",
    # key players/coaches (add freely)
    r"\bAnthony Richardson\b", r"\bJonathan Taylor\b", r"\bMichael Pittman\b",
    r"\bShane Steichen\b", r"\bQuenton Nelson\b", r"\bDeForest Buckner\b"
]

COLTS_EXCLUDES = [
    r"\bPacers\b", r"\bBoilermakers\b", r"\bNotre Dame\b", r"\bwomen'?s\b",
    r"\bWBB\b", r"\bvolleyball\b", r"\bbasketball\b", r"\bbaseball\b",
]

def allow_item(title: str, summary: str, source_label: str, feed_name: str) -> bool:
    text = f"{title} {summary}".lower()

    # trusted feeds always allowed
    if source_label in TRUSTED_FEEDS or feed_name in TRUSTED_FEEDS:
        return True

    # must mention Colts context
    if not any(re.search(pat, text, flags=re.I) for pat in COLTS_KEYWORDS):
        return False

    # exclude obvious non-football or wrong teams
    if any(re.search(pat, text, flags=re.I) for pat in COLTS_EXCLUDES):
        return False

    return True

# --- Collect ----------------------------------------------------------------

def fetch_all():
    items = []
    seen = set()

    for feed in FEEDS:
        feed_name = feed["name"].strip()
        feed_url  = feed["url"].strip()
        try:
            parsed = feedparser.parse(feed_url)
        except Exception:
            continue

        for e in parsed.entries[:100]:
            link = canonicalize_url(e.get("link","").strip() or e.get("id","").strip())
            if not link:
                continue

            key = hash_id(link)
            if key in seen:
                continue

            source = normalize_source(e, feed_name, feed_url)
            title = (e.get("title") or "").strip()
            summary = (e.get("summary") or e.get("description") or "").strip()

            if not allow_item(title, summary, source, feed_name):
                continue

            # published time (fallback to now)
            pub = e.get("published_parsed") or e.get("updated_parsed")
            if pub:
                ts = time.strftime("%Y-%m-%dT%H:%M:%S%z", pub)
            else:
                ts = now_iso()

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

    # sort newest first
    items.sort(key=lambda x: x["published"], reverse=True)
    return items[:MAX_ITEMS]

def write_items(items):
    payload = {
        "updated": now_iso(),
        "items": items,
        "links": STATIC_LINKS
    }
    with open("items.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

def main():
    items = fetch_all()
    write_items(items)
    print(f"Wrote {len(items)} items at {now_iso()}")

if __name__ == "__main__":
    main()