import json, time, hashlib, pathlib, concurrent.futures
from urllib.parse import urlparse
import feedparser

# ---- config
from feeds import FEEDS

OUT = pathlib.Path("items.json")
MAX_PER_FEED = 60         # collect extra, we’ll trim globally
MAX_TOTAL = 200           # keep recent across all (frontend trims to 50)
TIMEOUT = 15

def norm_item(feed_name, e, feed_href):
    # Prefer entry link; some feeds use "id" or "link"
    link = e.get("link") or e.get("id") or ""
    title = (e.get("title") or "").strip()
    # published parsed
    t = None
    for k in ("published_parsed", "updated_parsed", "created_parsed"):
        if e.get(k):
            t = e[k]
            break

    # Build ISO if we have struct_time
    iso_date = ""
    if t:
        try:
            iso_date = time.strftime("%Y-%m-%dT%H:%M:%SZ", t)
        except Exception:
            iso_date = ""
    # Fallback: raw strings (let frontend parse if possible)
    if not iso_date:
        for k in ("published", "updated", "created"):
            if e.get(k):
                iso_date = e[k]
                break

    # Source: explicit feed name; fallback to host
    src = feed_name or (urlparse(feed_href).netloc if feed_href else "")

    return {
        "id": hashlib.md5((link or title).encode("utf-8","ignore")).hexdigest(),
        "title": title,
        "link": link,
        "iso_date": iso_date,
        "source": src
    }

def fetch(feed):
    name = feed["name"]
    url = feed["url"]
    try:
        d = feedparser.parse(url, request_headers={"User-Agent":"news-bot/1.0"})
        items = []
        for e in d.entries[:MAX_PER_FEED]:
            it = norm_item(name, e, d.feed.get("link") or url)
            if it["title"] and it["link"]:
                items.append(it)
        return items
    except Exception:
        return []

def main():
    start = time.time()
    items = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(8, len(FEEDS))) as ex:
        for batch in ex.map(fetch, FEEDS):
            if batch:
                items.extend(batch)

    # Sort by iso_date (best effort) newest first
    def sort_key(i):
        # try to parse yyyy-mm-dd first; else last 20 chars timestamp-ish
        s = i.get("iso_date") or ""
        try:
            # fast path for %Y-%m-%dT%H:%M:%S
            if len(s) >= 19 and s[4] == "-" and s[7] == "-" and s[10] in " T":
                # rough rank: remove non-digits
                return int("".join(ch for ch in s if ch.isdigit())[:14])
        except Exception:
            pass
        return 0

    items.sort(key=sort_key, reverse=True)
    items = items[:MAX_TOTAL]

    # Build sources list for dropdown
    sources = sorted({i["source"] for i in items if i.get("source")})

    out = {
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sources": sources,
        "items": items
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(items)} items from {len(FEEDS)} feeds in {time.time()-start:.1f}s")

if __name__ == "__main__":
    main()