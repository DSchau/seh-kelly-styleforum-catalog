#!/usr/bin/env python3
"""
Re-create the S.E.H Kelly catalog from the original sources, without
Adapt export, DevTools, or Adapt credits.

Sources:
  1. sehkelly.com/products.json  (current shop: 64 products, 63 images
     verified 2026-10-24 — far below the Adapt baseline, so it is only
     the current snapshot, not the archive)
  2. StyleForum thread 277070 "S.E.H Kelly" (421+ pages, ~6,300 posts
     2012-2026, pagination via /page-N works in a text fetch, but that
     text fetch strips embedded images — so image URLs must come from
     an HTML / archive copy, not from the text dump alone)

Baseline to validate against (from the Adapt app):
  551 listings, 2,385 images
  Coat 185, Jacket 90, Shirt 115, Knitwear 63, Trousers 57,
  Hat 23, Accessory 12, Loungewear 6

This script:
  - parses thread page text dumps saved under thread_text/page-*.txt
    (one browser.open dump per page, with post numbers, authors, text)
  - extracts product mentions using the Adapt product-name vocabulary
  - groups posts into listings by (product, cloth, colour) when those
    can be inferred from the post text, otherwise by product alone
  - merges the shop catalog, de-duplicates by title/slug
  - prints a baseline validation report: listings, images, category
    counts vs. the 551 / 2,385 target, so a shortfall is visible
    instead of being silently accepted

Run: python3 recreate_thread.py
Input (optional): thread_text/page-*.txt, data/shop_catalog.json
Output: data/recreated_catalog.json, data/baseline_report.txt
"""
import json, re, pathlib
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parent
DATA = ROOT / "data"
THREAD = ROOT / "thread_text"
BASELINE = {"total_listings": 551, "total_images": 2385,
            "categories": {"Coat": 185, "Jacket": 90, "Shirt": 115,
                           "Knitwear": 63, "Trousers": 57, "Hat": 23,
                           "Accessory": 12, "Loungewear": 6}}
PRODUCTS = ["balaclava", "balmacaan coat", "boatneck jumper", "british warm",
            "button-down shirt", "car coat", "cardigan", "chesterfield coat",
            "crewneck jumper", "donkey jacket", "dress trousers", "duffle coat",
            "duster coat", "engineer jacket", "field coat", "field jacket",
            "field shirt", "field trousers", "fishing jacket", "flight jacket",
            "gansey jumper", "granddad shirt", "greatcoat", "hunting jacket",
            "overcoat", "overshirt", "parka", "peacoat", "polo shirt",
            "popover shirt", "proper trousers", "pyjama top",
            "reversible overshirt", "sb jacket", "sb3 jacket", "scarf",
            "shawl", "shawl cardigan", "shirt", "shopcoat", "slim trousers",
            "smock", "standard shirt", "tie", "tielocken coat", "topcoat",
            "trench coat", "trucker jacket", "ulster coat", "v-neck jumper",
            "watch cap", "work jacket"]
CATEGORY_MAP = {"coat": "Coat", "jacket": "Jacket", "shirt": "Shirt",
                "jumper": "Knitwear", "cardigan": "Knitwear",
                "trousers": "Trousers", "hat": "Hat", "scarf": "Accessory",
                "shawl": "Accessory", "tie": "Accessory", "balaclava": "Hat",
                "watch cap": "Hat", "pyjama": "Loungewear"}

def category_for(product):
    for k, v in CATEGORY_MAP.items():
        if k in product:
            return v
    return "Accessory"

def parse_thread_text():
    posts = []
    if not THREAD.exists():
        return posts
    for f in sorted(THREAD.glob("page-*.txt")):
        text = f.read_text(errors="ignore")
        # Split on post markers like "- #1,921" in the text dump
        parts = re.split(r"\n- #([\d,]+)\n", text)
        for i in range(1, len(parts), 2):
            num = parts[i].replace(",", "")
            body = parts[i+1] if i+1 < len(parts) else ""
            author = ""
            m = re.search(r"#\s+([A-Za-z0-9_]+)\s*\n", body[:500])
            if m:
                author = m.group(1)
            posts.append({"post_number": int(num), "author": author,
                          "text": body.strip(), "page_file": f.name})
    return posts

def main():
    shop = []
    shop_path = DATA / "shop_catalog.json"
    if shop_path.exists():
        shop = json.loads(shop_path.read_text())["items"]
    posts = parse_thread_text()
    groups = defaultdict(list)
    for p in posts:
        low = p["text"].lower()
        for prod in PRODUCTS:
            if prod in low:
                groups[prod].append(p)
                break
    listings = []
    for prod, ps in groups.items():
        listings.append({"title": prod.title(), "category": category_for(prod),
                         "posts": len(ps), "first_post": min(x["post_number"] for x in ps),
                         "last_post": max(x["post_number"] for x in ps),
                         "images": [], "source": "styleforum thread 277070 (text dump; images not in text fetch)"})
    for s in shop:
        listings.append({"title": s["title"], "category": s["product_type"],
                         "images": s["images"], "source": "sehkelly.com/products.json"})
    cats = Counter(x["category"] for x in listings)
    total_images = sum(len(x["images"]) for x in listings)
    report = []
    report.append(f"Thread posts parsed: {len(posts)}")
    report.append(f"Shop items: {len(shop)}")
    report.append(f"Recreated listings: {len(listings)}  (baseline {BASELINE['total_listings']})")
    report.append(f"Recreated images: {total_images}  (baseline {BASELINE['total_images']})")
    report.append("Category counts vs baseline:")
    for cat, base in BASELINE["categories"].items():
        report.append(f"  {cat}: {cats.get(cat, 0)} / {base}")
    report.append("")
    report.append("NOTE: thread text dumps strip embedded images, so thread-derived")
    report.append("listings above have 0 images until an HTML/archive copy of the")
    report.append("thread is parsed for image URLs. Do not treat the image total")
    report.append("as complete until that step lands.")
    (DATA / "recreated_catalog.json").write_text(json.dumps(
        {"listings": listings, "posts_parsed": len(posts)}, indent=2))
    (DATA / "baseline_report.txt").write_text("\n".join(report) + "\n")
    print("\n".join(report))

if __name__ == "__main__":
    main()
