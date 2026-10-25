#!/usr/bin/env python3
"""
Parse a crawl inventory of the S.E.H Kelly StyleForum Catalog Adapt app,
download full-size images, persist structured files, and build a static site.

Input:  data/crawl.json
  Expected shape (flexible):
  {
    "app": "S.E.H Kelly StyleForum Catalog",
    "source_url": "https://app.adapt.com/apps/a5d06c23-bca1-4003-a39e-8a1a3d4e0187/view",
    "pages": [
      {
        "url": "...", "title": "...", "headings": [...],
        "text": "...", "metadata": {...},
        "images": [{"url": "...", "alt": "...", "caption": "..."}]
      }
    ]
  }
  A flat list of pages is also accepted, as is a {"items": [...]} shape
  where each item carries its own images/metadata.

Output:
  data/catalog.json   - normalized, de-duplicated structured catalog
  assets/<hash>.<ext> - downloaded full-size images
  site/index.html     - nicely styled static site built from catalog.json
  site/catalog.json   - copy for the site to read if needed

Run: python3 parse_and_build.py [crawl.json]
No third-party dependencies; stdlib only.
"""
import hashlib
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
ASSETS = ROOT / "assets"
SITE = ROOT / "site"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"


def slugify(text, fallback="image"):
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s[:80] or fallback


def load_crawl(path):
    raw = json.loads(Path(path).read_text())
    if isinstance(raw, list):
        return {"pages": raw}
    if "pages" in raw:
        return raw
    if "items" in raw:
        return {"pages": [{"title": "Catalog", "items": raw["items"]}]}
    return raw


def normalize(crawl):
    pages_out = []
    items_out = []
    seen_images = {}
    for page in crawl.get("pages", []):
        images = []
        for img in page.get("images", []) or []:
            url = img.get("url") if isinstance(img, dict) else img
            if not url:
                continue
            url = urllib.parse.urljoin(crawl.get("source_url", ""), url)
            images.append({
                "url": url,
                "alt": (img.get("alt") or "") if isinstance(img, dict) else "",
                "caption": (img.get("caption") or "") if isinstance(img, dict) else "",
            })
        page_out = {
            "url": page.get("url", ""),
            "title": page.get("title", ""),
            "headings": page.get("headings", []) or [],
            "text": page.get("text", "") or "",
            "metadata": page.get("metadata", {}) or {},
            "images": images,
        }
        pages_out.append(page_out)
        # Items: explicit items on the page, or one item per image-bearing block
        for it in page.get("items", []) or []:
            items_out.append({"page": page_out["title"], "page_url": page_out["url"], **it})
        if not page.get("items") and images:
            items_out.append({
                "page": page_out["title"],
                "page_url": page_out["url"],
                "title": page_out["title"],
                "text": page_out["text"],
                "metadata": page_out["metadata"],
                "images": images,
            })
    return {"app": crawl.get("app", "S.E.H Kelly StyleForum Catalog"),
            "source_url": crawl.get("source_url", ""),
            "pages": pages_out, "items": items_out}


def download_images(catalog):
    ASSETS.mkdir(parents=True, exist_ok=True)
    url_to_file = {}
    for item in catalog["items"]:
        for img in item.get("images", []) or []:
            url = img["url"]
            if url in url_to_file:
                img["local"] = url_to_file[url]
                continue
            digest = hashlib.sha256(url.encode()).hexdigest()[:12]
            ext = Path(urllib.parse.urlparse(url).path).suffix.lower() or ".jpg"
            if ext not in (".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"):
                ext = ".jpg"
            name = f"{digest}{ext}"
            dest = ASSETS / name
            try:
                req = urllib.request.Request(url, headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = resp.read()
                if data:
                    dest.write_bytes(data)
                    img["local"] = f"../assets/{name}"
                    url_to_file[url] = img["local"]
                else:
                    img["local"] = ""
            except Exception as e:
                print(f"WARN: could not download {url}: {e}", file=sys.stderr)
                img["local"] = ""
    return catalog


def build_site(catalog):
    SITE.mkdir(parents=True, exist_ok=True)
    (SITE / "catalog.json").write_text(json.dumps(catalog, indent=2, ensure_ascii=False))
    cards = []
    for item in catalog["items"]:
        title = html.escape(item.get("title") or item.get("page") or "Untitled")
        text = html.escape((item.get("text") or "")[:600])
        meta = item.get("metadata") or {}
        meta_html = "".join(
            f"<li><strong>{html.escape(str(k))}:</strong> {html.escape(str(v))}</li>"
            for k, v in meta.items() if v)
        imgs = "".join(
            f'<figure><img loading="lazy" src="{html.escape(img.get("local") or img.get("url", ""))}" alt="{html.escape(img.get("alt") or title)}"><figcaption>{html.escape(img.get("caption") or img.get("alt") or "")}</figcaption></figure>'
            for img in item.get("images", []) or [])
        if not imgs:
            continue
        cat = html.escape(item.get("product_type") or (item.get("metadata") or {}).get("category", "") or item.get("page") or "")
        date = html.escape(item.get("published_at") or "")
        cards.append(f"""<article class="card bg-white rounded-xl border border-stone-200 shadow-sm overflow-hidden" data-category="{cat}" data-title="{title.lower()}" data-images="{len(item.get('images', []))}" data-date="{date}">
  <div class="gallery [&_img]:w-full [&_img]:h-auto [&_img]:block">{imgs}</div>
  <div class="p-4"><h2 class="font-serif text-lg leading-snug">{title}</h2>
  {f'<p class="text-stone-500 text-sm mt-1">{text}</p>' if text else ''}
  {f'<ul class="flex flex-wrap gap-2 mt-3 text-xs text-stone-600">{meta_html}</ul>' if meta_html else ''}
  <p class="text-stone-400 text-xs mt-3">{cat}</p></div>
</article>""")
    body = "\n".join(cards) if cards else "<p>No images captured yet. Run the crawl first.</p>"
    page_count = len(catalog["pages"])
    item_count = len(cards)
    doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>S.E.H Kelly StyleForum Catalog</title>
<script src="https://cdn.tailwindcss.com"></script>
<script>tailwind.config = {{ theme: {{ extend: {{ fontFamily: {{ serif: ['Georgia','Times New Roman','serif'] }}, colors: {{ beige: '#faf8f4', sand: '#efe9df' }} }} }} }}</script>
<style>.pill.active {{ background:#1c1917; color:#fff; border-color:#1c1917; }}</style></head>
<body class="bg-beige text-stone-900 antialiased">
<header class="max-w-6xl mx-auto px-6 pt-12 pb-4"><h1 class="font-serif text-4xl tracking-tight">S.E.H Kelly — Catalog</h1>
<p>Recreated catalog — {page_count} pages, {item_count} entries with images. Baseline target from Adapt: 551 listings, 2,385 images.</p>
<div class="flex flex-wrap gap-3 mt-6 items-center"><input id="q" type="search" placeholder="Search by name, cloth, color…" class="rounded-full border border-stone-200 bg-white px-4 py-2 text-sm outline-none focus:ring-2 focus:ring-stone-900">
<select id="sort" class="rounded-full border border-stone-200 bg-white px-4 py-2 text-sm"><option value="name">Sort: Name</option><option value="images">Sort: Most images</option><option value="recent">Sort: Most recent</option><option value="oldest">Sort: Oldest first</option></select>
<div id="pills" class="flex flex-wrap gap-2"><button data-cat="" class="pill active rounded-full border border-stone-200 bg-sand px-4 py-1.5 text-sm">All</button></div></div></header>
<main id="grid" class="max-w-6xl mx-auto px-6 pb-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">{body}</main>
<script>
const grid=document.getElementById('grid'), q=document.getElementById('q'), sort=document.getElementById('sort'), pills=document.getElementById('pills');
let active='';
const cats=[...new Set([...grid.querySelectorAll('.card')].map(c=>c.dataset.category).filter(Boolean))].sort();
cats.forEach(c=>{{const b=document.createElement('button'); b.className='pill rounded-full border border-stone-200 bg-sand px-4 py-1.5 text-sm'; b.dataset.cat=c; b.textContent=c; b.onclick=()=>{{active=c; document.querySelectorAll('.pill').forEach(p=>p.classList.toggle('active',p.dataset.cat===c)); apply();}}; pills.appendChild(b);}});
pills.querySelector('[data-cat=""]').onclick=()=>{{active=''; document.querySelectorAll('.pill').forEach(p=>p.classList.toggle('active',p.dataset.cat==='')); apply();}};
function apply(){{const term=q.value.toLowerCase(); const cards=[...grid.querySelectorAll('.card')]; cards.forEach(c=>{{c.style.display=(!active||c.dataset.category===active)&&(!term||c.dataset.title.includes(term))?'':'none';}}); const vis=cards.filter(c=>c.style.display!=='none'); if(sort.value==='images') vis.sort((a,b)=>b.dataset.images-a.dataset.images); else if(sort.value==='recent') vis.sort((a,b)=>b.dataset.date.localeCompare(a.dataset.date)); else if(sort.value==='oldest') vis.sort((a,b)=>a.dataset.date.localeCompare(b.dataset.date)); else vis.sort((a,b)=>a.dataset.title.localeCompare(b.dataset.title)); vis.forEach(c=>grid.appendChild(c));}}
q.oninput=apply; sort.onchange=apply;
</script>
<footer class="max-w-6xl mx-auto px-6 pb-12 text-stone-500 text-sm"><p>Recreated from public sources for personal catalog use. Original source: {html.escape(catalog.get("source_url",""))}</p></footer>
</body></html>"""
    (SITE / "index.html").write_text(doc)
    return SITE / "index.html"


def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else DATA / "crawl.json"
    if not src.exists():
        print(f"No crawl file yet: {src}\n"
              f"Save the browser crawl inventory there as JSON, then re-run.", file=sys.stderr)
        return 2
    catalog = normalize(load_crawl(src))
    catalog = download_images(catalog)
    (DATA / "catalog.json").write_text(json.dumps(catalog, indent=2, ensure_ascii=False))
    site = build_site(catalog)
    print(f"Pages: {len(catalog['pages'])}  Items: {len(catalog['items'])}")
    print(f"Structured data: {DATA / 'catalog.json'}")
    print(f"Site: {site}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
