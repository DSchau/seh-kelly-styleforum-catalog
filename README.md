# S.E.H Kelly — StyleForum Catalog (recreation)

A simple, minimal recreation of the Adapt app "S.E.H Kelly StyleForum
Catalog", rebuilt from public sources — sehkelly.com and the one long
StyleForum thread (s-e-h-kelly, thread 277070).

Site style: Tailwind + shadcn-style, minimal like sehkelly.com —
pale beige background, large black serif heading, white rounded cards,
category pills, search, and sort.

## Open the site

Open `index.html` in a browser. No build step needed.
Shop images are local in `assets/`; thread images are hotlinked from
their Wayback Machine snapshots (see below).

## Counts vs. the Adapt baseline

| | Recreated | Adapt baseline |
|---|---|---|
| Listings / items | 136 | 551 |
| Images | 1,145 | 2,385 |

- Shop: 63 items, 63 local images (sehkelly.com products.json, Oct 2026 snapshot)
- Thread: 73 archived pages with unique images, 1,082 images
  (1,013 StyleForum attachments + 52 StyleForum image IDs + sehkelly.com images)

The shortfall is real and explained, not hidden:
- Wayback only had usable snapshots for 158 of the thread's ~497 pages
  (latest snapshot per page, 157 fetched, 1 snapshot 404).
- Thread grouping here is page-level: one item per archived thread page,
  with all that page's unique post images. Adapt grouped by product /
  cloth / colour into 551 listings — that per-listing grouping could not
  be recovered from page-level Wayback HTML alone.
- Images are deduplicated by raw URL: the same attachment repeats across
  several archived pages (quotes / media strip), and counting those
  repeats would have inflated the total to ~3,400.

## Structure

- `index.html` — the site (also in `site/index.html`, with `../assets/` paths)
- `assets/` — 63 shop images downloaded from Shopify CDN
- `data/` — structured data:
  - `sehkelly_products.json`, `shop_catalog.json`, `catalog.json` — shop
  - `thread_wayback_v2.json` — per-page Wayback crawl (image IDs, external URLs, product keywords)
  - `recreated_full_catalog.json` — merged catalog the site is built from
- `parse_and_build.py` — normalizer, image downloader, Tailwind site builder
- `wayback_thread_v2.py` — Wayback crawl (4s delay, 429 backoff, saves after every page, resumable)
- `build_full.py` — merges shop + thread into the full catalog and site
- `PROGRESS.md` — working notes and resume instructions

## Re-run

```sh
python3 wayback_thread_v2.py data/thread_wayback_v2.json  # resumable crawl
python3 build_full.py                                     # rebuild site
```

## Sources

- https://www.sehkelly.com/products.json
- https://www.styleforum.net/threads/s-e-h-kelly.277070/ via
  https://web.archive.org (archived snapshots, original HTML)
- Adapt baseline (551 listings, 2,385 images, category counts) from the
  original Adapt app's own UI, for validation only — no Adapt data was
  exported or copied.
