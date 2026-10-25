#!/usr/bin/env python3
"""Wayback thread crawl v2: slower, resumable, 429-backoff, and external images.

- Same CDX page list as v1 (158 pages, 2-497), latest snapshot per page.
- Delay 4s between pages (not 1s), retry 429/5xx with 30/60/120/240s backoff.
- Extracts, per page:
  * StyleForum image IDs (/image/id/, /content/type/61/id/)
  * External post images in <img> tags: shopify CDN, imgur, and any
    http(s) image URL with .jpg/.jpeg/.png/.webp, excluding avatars,
    ads, smilies, logos, and styleforum static assets.
- Saves progress incrementally after every page to thread_wayback_v2.json,
  so a stop/resume loses nothing. Skips pages already in that file.
- Also tries to attribute images to a post chunk: splits HTML on
  data-post-id / message ids where present, records product keywords
  found in the chunk text (from the Adapt product-name vocabulary).
Usage: python3 wayback_thread_v2.py [out.json]
"""
import json, re, sys, time, gzip, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
UA = "Mozilla/5.0 (compatible; Muse-catalog-rebuild/1.0)"
CDX = "https://web.archive.org/cdx/search/cdx?url=styleforum.net/threads/s-e-h-kelly.277070/page-*&output=json&filter=statuscode:200&collapse=urlkey&limit=5000"
PRODUCTS = ["balaclava","balmacaan","boatneck","british warm","button-down","car coat","cardigan","chesterfield","crewneck","donkey jacket","dress trousers","duffle coat","duster coat","engineer jacket","field coat","field jacket","field shirt","field trousers","fishing jacket","flight jacket","gansey","granddad shirt","greatcoat","hunting jacket","overcoat","overshirt","parka","peacoat","polo shirt","popover","proper trousers","pyjama","reversible overshirt","sb jacket","sb3 jacket","scarf","shawl","shopcoat","slim trousers","smock","standard shirt","tie","tielocken","topcoat","trench coat","trucker jacket","ulster coat","v-neck","watch cap","work jacket","knitwear","trousers","jacket","coat","shirt","hat"]

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "identity"})
    with urllib.request.urlopen(req, timeout=90) as r:
        data = r.read()
    if data[:2] == b"\x1f\x8b":
        data = gzip.decompress(data)
    return data

def get_with_retry(url):
    for attempt, wait in enumerate([0, 30, 60, 120, 240, 600]):
        if wait:
            print(f"  retry in {wait}s (attempt {attempt+1})", flush=True)
            time.sleep(wait)
        try:
            return get(url)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < 5:
                continue
            raise
        except Exception:
            if attempt < 5:
                continue
            raise
    raise RuntimeError("exhausted retries")

def external_images(html):
    out = set()
    for src in re.findall(r'<img[^>]+(?:src|data-url)="([^"]+)"', html):
        s = src.strip()
        if not s or s.startswith("data:"):
            continue
        low = s.lower()
        if any(x in low for x in ["avatar", "smilie", "logo", "ad/", "ads.", "static/", "styles/", "data/smilies"]):
            continue
        if re.search(r"\.(jpe?g|png|webp)(\?|$)", low) or "cdn.shopify" in low or "imgur" in low:
            out.add(s)
    return sorted(out)

def main():
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DATA / "thread_wayback_v2.json"
    done = {}
    if out_path.exists():
        try:
            prev = json.loads(out_path.read_text())
            for p in prev.get("pages", []):
                done[p["page"]] = p
            print(f"Resuming: {len(done)} pages already done", flush=True)
        except Exception as e:
            print(f"Could not read previous output: {e}", flush=True)
    print("Querying CDX…", flush=True)
    rows = json.loads(get_with_retry(CDX))
    pages = {}
    for r in rows[1:]:
        ts, original = r[1], r[2]
        m = re.search(r"/page-(\d+)$", original)
        if not m:
            continue
        n = int(m.group(1))
        if n not in pages or ts > pages[n][0]:
            pages[n] = (ts, original)
    print(f"Wayback pages found: {len(pages)} (page numbers {min(pages)}-{max(pages)})", flush=True)
    seen_sf, seen_ext = set(), set()
    for p in done.values():
        seen_sf.update(p.get("image_ids", []))
        seen_ext.update(p.get("external_image_urls", []))
    for n in sorted(pages):
        if n in done:
            continue
        ts, original = pages[n]
        wb = f"https://web.archive.org/web/{ts}id_/{original}"
        try:
            html = get_with_retry(wb).decode("utf-8", errors="ignore")
        except Exception as e:
            print(f"page {n}: fetch failed after retries: {e}", flush=True)
            done[n] = {"page": n, "snapshot": ts, "original": original, "error": str(e)}
            continue
        sf = sorted(set(re.findall(r"(?:/image/id/|/content/type/61/id/)(\d+)", html)))
        ext = external_images(html)
        # product keywords in page text (stripped)
        text = re.sub(r"<[^>]+>", " ", html).lower()
        text = re.sub(r"\s+", " ", text)
        keywords = sorted(set(k for k in PRODUCTS if k in text))
        new_sf = [i for i in sf if i not in seen_sf]
        new_ext = [u for u in ext if u not in seen_ext]
        seen_sf.update(sf); seen_ext.update(ext)
        done[n] = {"page": n, "snapshot": ts, "original": original,
                   "html_bytes": len(html), "image_ids": sf,
                   "external_image_urls": ext, "product_keywords": keywords}
        print(f"page {n} ({ts}): SF {len(sf)} ({len(new_sf)} new), ext {len(ext)} ({len(new_ext)} new), cum SF {len(seen_sf)}, ext {len(seen_ext)}", flush=True)
        out = {"pages_fetched": len([d for d in done.values() if "error" not in d]),
               "unique_sf_image_ids": len(seen_sf), "unique_external_images": len(seen_ext),
               "pages": [done[k] for k in sorted(done)]}
        out_path.write_text(json.dumps(out, indent=2))
        time.sleep(4)
    print(f"DONE {out_path}: SF {len(seen_sf)} unique, external {len(seen_ext)} unique", flush=True)

if __name__ == "__main__":
    main()
