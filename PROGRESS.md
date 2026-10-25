# S.E.H Kelly Catalog Recreation — Progress (saved, resumable)

All files live under `~/workspace/adapt-sehkelly-catalog/` — the persistent
workspace, NOT /tmp, so they survive VM restarts and conversation compaction.

## Goal
Recreate the Adapt app "S.E.H Kelly StyleForum Catalog" (551 listings,
2,385 images) from public sources, as a filtered/searchable/sortable site,
then push to a GitHub repo under DSchau.

## Style (user, 2026-10-24)
Tailwind + shadcn-style, simple and minimal like sehkelly.com:
pale beige background, large black serif heading, white rounded cards.

## What is saved
- `data/sehkelly_products.json` (264K) — raw sehkelly.com products.json, 64 products
- `data/shop_catalog.json` (64K) — normalized shop catalog
- `data/catalog.json` (37K) — shop catalog with local image paths
- `assets/` — 63 downloaded shop images, 25M total
- `site/index.html` + `site/catalog.json` — Tailwind shop-batch site, built 2026-10-24 19:48
- `parse_and_build.py` — normalizer + image downloader + Tailwind site builder
- `recreate_thread.py` — thread-text grouping scaffold
- `wayback_thread.py` — v1 Wayback crawl (1s delay, StyleForum IDs only)
- `wayback_thread_v2.py` — v2 crawl: 4s delay, 429 backoff retries,
  StyleForum IDs + external images (Shopify/Imgur/etc.), saves after every page

## Wayback v2 crawl — DONE 2026-10-24 20:04 PDT
- Script: `wayback_thread_v2.py`
- Output: `data/thread_wayback_v2.json`
- Log: `data/wayback_v2.log`
- CDX list: 158 Wayback pages, page numbers 2-497
- Result: 157 pages fetched, 1 error (page 227 snapshot 404),
  52 unique StyleForum image IDs, 1,170 unique external image URLs
  (1,013 attachments, 42 ads excluded, rest other hosts)

## Full catalog — BUILT 2026-10-24 20:05 PDT
- Script: `build_full.py` → `data/recreated_full_catalog.json`
- Site: `index.html` (root) and `site/index.html`, Tailwind
- Final counts: 136 items (63 shop + 73 thread pages), 1,145 images
  vs baseline 551 / 2,385. Thread grouping is page-level, not per-listing.
  Deduplicated by raw URL (occurrences would have been ~3,400).

## GitHub — DONE 2026-10-24 20:06 PDT
- Repo: https://github.com/DSchau/seh-kelly-styleforum-catalog (public, branch master)
- Commit b82eb96: scripts + data + assets + site, pushed and verified via ls-remote.

## Known issues
- Adapt itself exposed 0 image URLs (no img src in browser view).
- Live styleforum.net is Cloudflare-blocked from this VM (403 challenge);
  Wayback HTML is the working route.
- Wayback rate-limits (429) if fetched too fast — v2 uses 4s delay + backoff.
- External-image extraction may include some non-post images; filter
  avatars/ads/smilies/logos again before final build.
