#!/usr/bin/env python3
"""
Fetch StyleForum thread 277070 pages from the Wayback Machine (which
bypasses the live site's Cloudflare challenge and preserves the original
HTML, including bbCodeImage URLs that a text fetch strips out).

Steps:
  1. CDX query for page-* URLs, collapse by urlkey, keep latest snapshot
     per page number.
  2. Fetch each snapshot with id_ (original HTML, no Wayback rewrite).
  3. Extract post-image URLs: /image/id/<n>/ and /content/type/61/id/<n>/
     (avatars, ads, smilies, logos excluded).
  4. Dedupe image IDs across pages, save structured JSON + a report
     vs. the Adapt baseline (551 listings, 2,385 images).

Usage: python3 wayback_thread.py [max_pages] [out.json]
Defaults: max_pages=20 (proof-of-concept batch; raise once it works).
Rate: one request at a time, with a small delay, to stay close to
ordinary Wayback use.
"""
import json, re, sys, time, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
UA = "Mozilla/5.0 (compatible; Muse-catalog-rebuild/1.0)"
CDX = "https://web.archive.org/cdx/search/cdx?url=styleforum.net/threads/s-e-h-kelly.277070/page-*&output=json&filter=statuscode:200&collapse=urlkey&limit=5000"

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "identity"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    # Wayback sometimes returns gzip regardless of Accept-Encoding
    if data[:2] == b"\x1f\x8b":
        import gzip
        data = gzip.decompress(data)
    return data

def main():
    max_pages = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DATA / "thread_wayback.json"
    print("Querying CDX…", flush=True)
    rows = json.loads(get(CDX))
    pages = {}
    for r in rows[1:]:
        ts, original = r[1], r[2]
        m = re.search(r"/page-(\d+)$", original)
        if not m:
            continue
        n = int(m.group(1))
        # keep latest snapshot per page number
        if n not in pages or ts > pages[n][0]:
            pages[n] = (ts, original)
    print(f"Wayback pages found: {len(pages)} (page numbers {min(pages)}-{max(pages)})", flush=True)
    chosen = sorted(pages)[:max_pages]
    results = []
    seen_images = set()
    total_images = 0
    for n in chosen:
        ts, original = pages[n]
        wb = f"https://web.archive.org/web/{ts}id_/{original}"
        try:
            html = get(wb).decode("utf-8", errors="ignore")
        except Exception as e:
            print(f"page {n}: fetch failed: {e}", flush=True)
            continue
        # post images only: bbCodeImage with /image/id/ or /content/type/61/id/
        imgs = sorted(set(re.findall(r"(?:/image/id/|/content/type/61/id/)(\d+)", html)))
        # full URLs as they appear in src/data-url
        full = sorted(set(re.findall(r"https?://www\.styleforum\.net/(?:image/id/\d+/width/\d+/height/\d+|content/type/61/id/\d+/width/\d+/height/\d+)", html)))
        new = [i for i in imgs if i not in seen_images]
        seen_images.update(imgs)
        total_images += len(imgs)
        results.append({"page": n, "snapshot": ts, "original": original,
                        "html_bytes": len(html), "image_ids": sorted(set(imgs)),
                        "image_urls_sample": full[:5]})
        print(f"page {n} ({ts}): {len(set(imgs))} image ids, {len(new)} new, cumulative unique {len(seen_images)}", flush=True)
        time.sleep(1)
    out = {"pages_fetched": len(results), "unique_image_ids": len(seen_images),
           "total_image_occurrences": total_images, "pages": results}
    out_path.write_text(json.dumps(out, indent=2))
    print(f"Saved {out_path}: {len(results)} pages, {len(seen_images)} unique post-image ids", flush=True)
    print("Baseline target: 551 listings, 2,385 images — image-id count is a")
    print("lower bound (one id per embedded post image; a listing groups several).", flush=True)

if __name__ == "__main__":
    main()
