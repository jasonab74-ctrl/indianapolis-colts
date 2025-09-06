# collect.py — fetch feeds, filter, dedupe, and write items.json (static site)
import re, json, time, html, sys
from datetime import datetime, timezone
from urllib.parse import urlparse, urlunparse
import requests, feedparser
import feeds  # team-config above

USER_AGENT = "SportsNewsTemplate/1.0 (+https://example.com)"
TIMEOUT = 12
MAX_ITEMS = 60

def http_head_then_get(url: str) -> str:
    try:
        r = requests.get(url, allow_redirects=True, timeout=TIMEOUT,
                         headers={"User-Agent": USER_AGENT})
        return r.url
    except Exception:
        return url

def canonicalize(u: str) -> str:
    try:
        u = http_head_then_get(u)
        p = urlparse(u)
        path = re.sub(r"/+$", "", p.path)
        return urlunparse((p.scheme, p.netloc.lower(), path, "", "", ""))
    except Exception:
        return u

def normalize_title(t: str) -> str:
    t = html.unescape(t or "").strip()
    # strip trailing "— Outlet" suffixes often appended by feeds
    t = re.sub(r"\s+[–—-]\s+[^|]+$", "", t)
    return re.sub(r"\s+", " ", t)

def extract_source(entry, feed_name: str) -> str:
    src = None
    if "source" in entry and entry.source:
        src = getattr(entry.source, "title", None) or getattr(entry.source, "href", None)
    if not src:
        src = feed_name
    src = (src or "Unknown").strip()
    src = re.sub(r"^https?://(www\.)?", "", src)
    return src[:60]

def ts_from_entry(entry) -> float:
    for key in ("published_parsed", "updated_parsed"):
        if getattr(entry, key, None):
            try:
                return time.mktime(getattr(entry, key))
            except Exception:
                pass
    return time.time()

def allow_item(item) -> bool:
    # Trusted feeds bypass strict filtering (prevents empty page on first run)
    if item.get("trusted"):
        return True
    title = item.get("title", "")
    summary = item.get("summary", "")
    blob = f"{title} {summary}".lower()
    if not any(k.lower() in blob for k in feeds.TEAM_KEYWORDS):
        return False
    if not any(s.lower() in blob for s in feeds.SPORT_TOKENS):
        return False
    if any(bad.lower() in blob for bad in feeds.EXCLUDE_TOKENS):
        return False
    return True

def fetch_feed(feed_def):
    d = feedparser.parse(feed_def["url"])
    items = []
    for e in d.entries:
        title = normalize_title(getattr(e, "title", "") or "")
        link = getattr(e, "link", "") or ""
        if not title or not link:
            continue
        clean_url = canonicalize(link)
        source = extract_source(e, feed_def["name"])
        summary = html.unescape(getattr(e, "summary", "") or "")
        published_ts = ts_from_entry(e)
        items.append({
            "title": title,
            "url": clean_url,
            "source": source,
            "summary": summary.strip(),
            "published": datetime.fromtimestamp(published_ts, tz=timezone.utc).isoformat(),
            "trusted": bool(feed_def.get("trusted", False)),
        })
    return items

def dedupe(items):
    seen = set()
    out = []
    for it in items:
        k = (it["title"].lower(), it["url"])
        if k in seen:
            continue
        seen.add(k)
        out.append(it)
    return out

def main():
    all_items = []
    for f in feeds.FEEDS:
        try:
            all_items.extend(fetch_feed(f))
        except Exception as e:
            print(f"[WARN] feed error {f['name']}: {e}", file=sys.stderr)

    # filter + dedupe + sort
    filtered = [it for it in all_items if allow_item(it)]
    filtered = dedupe(filtered)
    filtered.sort(key=lambda x: x.get("published", ""), reverse=True)
    filtered = filtered[:MAX_ITEMS]

    # collect distinct sources for dropdown
    sources = sorted({it["source"] for it in filtered})

    payload = {
        "team": {"name": getattr(feeds, "TEAM_NAME", "Team News"),
                 "slug": getattr(feeds, "TEAM_SLUG", "team")},
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "static_links": getattr(feeds, "STATIC_LINKS", []),
        "items": filtered,
        "sources": sources,
    }

    with open("items.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(filtered)} items to items.json")

if __name__ == "__main__":
    main()