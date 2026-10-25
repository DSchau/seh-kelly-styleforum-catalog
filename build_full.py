#!/usr/bin/env python3
"""Build the full recreated catalog: shop (local images) + thread pages
(Wayback attachment / StyleForum-ID / sehkelly images, hotlinked).

Thread grouping is page-level, not Adapt's per-listing grouping:
each thread item is one archived thread page, with all its post images,
product keywords from that page as searchable text, and a category
inferred from those keywords. This is stated in the site footer and README.

Output:
  data/recreated_full_catalog.json
  site/index.html (Tailwind, via parse_and_build.build_site)
  index.html at repo root (same site, assets/ paths)
"""
import json, sys, html
sys.path.insert(0, "/home/hatch/workspace/adapt-sehkelly-catalog")
from pathlib import Path
from parse_and_build import build_site

ROOT = Path("/home/hatch/workspace/adapt-sehkelly-catalog")
DATA = ROOT / "data"

CATEGORY_MAP = [
    ("balmacaan", "Coat"), ("overcoat", "Coat"), ("chesterfield", "Coat"),
    ("duffle coat", "Coat"), ("trench coat", "Coat"), ("topcoat", "Coat"),
    ("greatcoat", "Coat"), ("peacoat", "Coat"), ("parka", "Coat"),
    ("car coat", "Coat"), ("tielocken", "Coat"), ("ulster coat", "Coat"),
    ("british warm", "Coat"), ("duster coat", "Coat"),
    ("work jacket", "Jacket"), ("field jacket", "Jacket"),
    ("engineer jacket", "Jacket"), ("flight jacket", "Jacket"),
    ("fishing jacket", "Jacket"), ("hunting jacket", "Jacket"),
    ("donkey jacket", "Jacket"), ("trucker jacket", "Jacket"),
    ("sb jacket", "Jacket"), ("sb3 jacket", "Jacket"),
    ("overshirt", "Shirt"), ("field shirt", "Shirt"),
    ("button-down", "Shirt"), ("granddad shirt", "Shirt"),
    ("standard shirt", "Shirt"), ("popover", "Shirt"),
    ("polo shirt", "Shirt"),
    ("crewneck", "Knitwear"), ("gansey", "Knitwear"), ("cardigan", "Knitwear"),
    ("boatneck", "Knitwear"), ("v-neck", "Knitwear"), ("knitwear", "Knitwear"),
    ("shawl", "Knitwear"),
    ("dress trousers", "Trousers"), ("field trousers", "Trousers"),
    ("proper trousers", "Trousers"), ("slim trousers", "Trousers"),
    ("trousers", "Trousers"),
    ("balaclava", "Hat"), ("watch cap", "Hat"), ("hat", "Hat"),
    ("scarf", "Accessory"), ("tie", "Accessory"),
    ("pyjama", "Loungewear"),
]

def category_for(keywords):
    kws = [k.lower() for k in keywords]
    for kw, cat in CATEGORY_MAP:
        if kw in kws:
            return cat
    # generic fallbacks, in Adapt category order
    for kw, cat in [("coat", "Coat"), ("jacket", "Jacket"), ("shirt", "Shirt"),
                    ("trousers", "Trousers")]:
        if kw in kws:
            return cat
    return "Thread"

def main():
    thread = json.loads((DATA / "thread_wayback_v2.json").read_text())
    shop = json.loads((DATA / "catalog.json").read_text())
    items = []
    # Shop first
    for it in shop["items"]:
        if not it.get("images"):
            continue
        items.append(it)
    # Dedupe by RAW url, not by Wayback timestamp: the same attachment
    # repeats across several archived pages (quoted posts / media strip),
    # and timestamp-prefixing it would inflate the count ~3x.
    seen_raw = set()
    thread_items = 0
    thread_images = 0
    for p in thread["pages"]:
        if "error" in p:
            continue
        ts = p["snapshot"]
        imgs = []
        for sid in p.get("image_ids", []):
            raw = f"styleforum-image-{sid}"
            if raw in seen_raw:
                continue
            seen_raw.add(raw)
            url = f"https://web.archive.org/web/{ts}id_/https://www.styleforum.net/image/id/{sid}/width/1000/height/1000"
            imgs.append({"url": url, "local": url, "alt": f"StyleForum image {sid}", "caption": ""})
        for u in p.get("external_image_urls", []):
            if "styleforum_ads" in u or "notice_images" in u:
                continue
            if "/data/attachments/" in u:
                url = f"https://web.archive.org/web/{ts}id_/https://www.styleforum.net{u}"
            elif "sehkelly" in u and ("/images/" in u or "/cdn/shop/" in u):
                url = u.replace("&amp;", "&")
            else:
                continue
            if u in seen_raw:
                continue
            seen_raw.add(u)
            imgs.append({"url": url, "local": url, "alt": "", "caption": ""})
        if not imgs:
            continue
        kws = p.get("product_keywords", [])
        items.append({
            "page": f"Thread page {p['page']}",
            "page_url": p["original"],
            "title": f"StyleForum thread — page {p['page']}",
            "product_type": category_for(kws),
            "published_at": "",
            "text": "Product mentions on this archived page: " + ", ".join(kws) if kws else "",
            "metadata": {"snapshot": ts, "thread_page": str(p["page"])},
            "images": imgs,
            "source": "web.archive.org / styleforum.net",
        })
        thread_items += 1
        thread_images += len(imgs)
    catalog = {"source_url": "https://www.styleforum.net/threads/s-e-h-kelly.277070/",
               "pages": [{"page": "Shop", "url": ""}] + [{"page": f"Thread page {p['page']}", "url": p["original"]} for p in thread["pages"] if "error" not in p],
               "items": items}
    (DATA / "recreated_full_catalog.json").write_text(json.dumps(catalog, indent=2))
    site = build_site(catalog)
    # Root copy: site/index.html uses ../assets/ for shop images; root uses assets/
    root_html = (ROOT / "site" / "index.html").read_text().replace("../assets/", "assets/")
    (ROOT / "index.html").write_text(root_html)
    # site/catalog.json also written by build_site; copy to root for reference
    print(f"Shop items: {len([i for i in shop['items'] if i.get('images')])}")
    print(f"Thread items: {thread_items}, thread images: {thread_images}")
    print(f"Total items: {len(items)}, total images: {sum(len(i['images']) for i in items)}")
    print(f"Baseline target: 551 listings, 2,385 images")
    print(f"Site: {site}")
    print(f"Root site: {ROOT / 'index.html'}")

if __name__ == "__main__":
    main()
