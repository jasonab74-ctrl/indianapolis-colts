# collect.py — robust collector (with bootstrap fallback)
import re, json, time, html, sys
from datetime import datetime, timezone
from urllib.parse import urlparse, urlunparse
import requests, feedparser
import feeds

USER_AGENT = "SportsNewsTemplate/1.0"
TIMEOUT = 12
MAX_ITEMS = 80
BOOTSTRAP_MIN = 18  # if fewer than this after filtering, fill from trusted feeds

def http_get_final(url: str) -> str:
    try:
        r = requests.get(url, allow_redirects=True, timeout=TIMEOUT,
                         headers={"User-Agent": USER_AGENT})
        return r.url
    except Exception:
        return url

def canonicalize(u: str) -> str:
    try:
        u = http_get_final(u)
        p = urlparse(u)
        path = re.sub(r"/+$", "", p.path)
        return urlunparse((p.scheme, p.netloc.lower(), path, "", "", ""))
    except Exception:
        return u

def normalize_title(t: str) -> str:
    t = html.unescape(t or "").strip()
    # strip trailing "— Outlet"
    t = re.sub(r"\s+[–—-]\s+[^|]+$", "", t)
    return re.sub(r"\s+", " ", t)

def extract_source(entry, feed_name: str) -> str:
    src = None
    if "source" in entry and entry.source:
        src = getattr(entry.source, "title", None) or getattr(entry.source, "href", None)
    if not src: src = feed_name
    src = (src or "Unknown").strip()
    src = re.sub(r"^https?://(www\.)?", "", src)
    return src[:60]

def ts_from_entry(entry) -> float:
    for key in ("published_parsed", "updated_parsed"):
        val = getattr(entry, key, None)
        if val:
            try:
                return time.mktime(val)
            except Exception:
                pass
    return time.time()

def allow_item(item) -> bool:
    # Trusted feeds bypass strict filtering
    if item.get("trusted"):
        return True
    blob = (item.get("title", "") + " " + item.get("summary", "")).lower()
    if not any(k.lower() in blob for k in feeds.TEAM_KEYWORDS):
        return False
    if not any(s.lower() in blob for s in feeds.SPORT_TOKENS):
        return False
    if any(bad.lower() in blob for bad in feeds.EXCLUDE_TOKENS):
        return False
    return True

def fetch_feed(fd):
    d = feedparser.parse(fd["url"])
    items = []
    for e in d.entries:
        title = normalize_title(getattr(e, "title", "") or "")
        link  = getattr(e, "link", "") or ""
        if not title or not link: 
            continue
        items.append({
            "title": title,
            "url": canonicalize(link),
            "source": extract_source(e, fd["name"]),
            "summary": html.unescape(getattr(e, "summary", "") or "").strip(),
            "published": datetime.fromtimestamp(ts_from_entry(e), tz=timezone.utc).isoformat(),
            "trusted": bool(fd.get("trusted", False)),
        })
    return items

def dedupe(items):
    seen, out = set(), []
    for it in items:
        key = (it["title"].lower(), it["url"])
        if key in seen: 
            continue
        seen.add(key)
        out.append(it)
    return out

def main():
    all_items = []
    trusted_raw = []
    for f in feeds.FEEDS:
        try:
            batch = fetch_feed(f)
            all_items.extend(batch)
            if f.get("trusted"):  # keep raw trusted for bootstrap
                trusted_raw.extend(batch)
        except Exception as e:
            print(f"[WARN] feed error {f['name']}: {e}", file=sys.stderr)

    # Primary filter
    filtered = [it for it in all_items if allow_item(it)]
    filtered = dedupe(filtered)
    filtered.sort(key=lambda x: x.get("published", ""), reverse=True)

    # Bootstrap fallback: if we filtered too hard, take trusted items as-is
    if len(filtered) < BOOTSTRAP_MIN:
        trusted_raw = dedupe(trusted_raw)
        trusted_raw.sort(key=lambda x: x.get("published", ""), reverse=True)
        # prefer trusted content; then add whatever already passed
        merged = trusted_raw + [it for it in filtered if it not in trusted_raw]
        filtered = merged

    filtered = filtered[:MAX_ITEMS]
    sources = sorted({it["source"] for it in filtered})

    payload = {
        "team": {"name": feeds.TEAM_NAME, "slug": feeds.TEAM_SLUG},
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "static_links": feeds.STATIC_LINKS,
        "items": filtered,
        "sources": sources,
    }
    with open("items.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"[collector] wrote {len(filtered)} items; {len(sources)} sources")

if __name__ == "__main__":
    main()