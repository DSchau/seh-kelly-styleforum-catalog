# S.E.H Kelly — StyleForum Catalog

A clean, minimal recreation of the Adapt app "S.E.H Kelly StyleForum
Catalog", built from the Adapt export and its photos.

Site style, like sehkelly.com: white background, black serif titles,
no cards, borders, shadows, or rounded corners — just the photo, then
the name, cloth, and colour below it on white, with generous whitespace.
Photos are shown at their natural height (no square crop). Category
filters are plain text links (active one underlined), search is a simple
underline input, and clicking an item opens all its photos plus cloth,
colour, dates, and forum post links.

## Open the site

https://dschau.github.io/seh-kelly-styleforum-catalog/ — GitHub Pages,
from this repo's master branch, root.

## Counts — full baseline, met

| | This site | Adapt baseline |
|---|---|---|
| Listings | 551 | 551 |
| Images | 2,385 | 2,385 |

Categories: Coat 185, Shirt 115, Jacket 90, Knitwear 63, Trousers 57,
Hat 23, Accessory 12, Loungewear 6.

## Sources

- `data/SEHKelly_Catalog.json` — Adapt export (2026-10-25), from the
  StyleForum thread https://www.styleforum.net/threads/s-e-h-kelly.277070/
- `images/` — 2,385 photos from the Drive folder "S.E.H Kelly
  StyleForum Catalog" (images.zip, 786 MB), filenames matching the
  export's `full` paths exactly (0 missing, 0 extra).
- `build_from_export.py` — builds `index.html` (root, for Pages) and
  `site/index.html` from the export.

## Rebuild

```sh
python3 build_from_export.py
```
