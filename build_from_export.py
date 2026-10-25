#!/usr/bin/env python3
"""Build the site from the uploaded Adapt export SEHKelly_Catalog.json.

551 listings, 2,385 images, categories exactly matching the Adapt baseline.
Images are hotlinked to their StyleForum attachment src_url (the export's
thumb/full paths were Adapt-internal and are not in this repo).
Site: Tailwind + shadcn-style, minimal like sehkelly.com, with category
pills, search (name/cloth/color), sort, and a detail modal per listing
(images, cloth, color, first/last seen, forum post links).
"""
import json, html
from pathlib import Path

ROOT = Path("/home/hatch/workspace/adapt-sehkelly-catalog")
SRC = ROOT / "data" / "SEHKelly_Catalog.json"

def esc(s):
    return html.escape(str(s or ""), quote=True)

def main():
    data = json.loads(SRC.read_text())
    listings = data["listings"]
    assert len(listings) == 551, len(listings)
    assert sum(len(x["images"]) for x in listings) == 2385
    cats = []
    for x in listings:
        if x["category"] not in cats:
            cats.append(x["category"])
    # category counts, in Adapt order
    from collections import Counter
    counts = Counter(x["category"] for x in listings)
    # Category filters as plain text links (like sehkelly.com nav),
    # active one underlined — no pills, no sand backgrounds.
    pills = "".join(
        f'<button data-cat="{esc(c)}" class="pill text-sm text-stone-500 hover:text-black pb-1">{esc(c)} ({counts[c]})</button>'
        for c in sorted(cats)
    )
    cards = []
    for x in listings:
        # Local images from Drive (images.zip, 2385 files, 0 missing)
        # take precedence over the StyleForum hotlink.
        first = x["images"][0].get("full") or x["images"][0].get("src_url") if x.get("images") else ""
        search = f"{x['name']} {x.get('cloth','')} {x.get('color','')}".lower()
        # S.E.H Kelly style: no card chrome at all — just the photo, then
        # text below it on white. One title only (no figcaption duplicate),
        # and no square crop: h-auto shows the whole garment, not a cut-off strip.
        cards.append(f"""<article class="card cursor-pointer" data-category="{esc(x['category'])}" data-title="{esc(x['name'].lower())}" data-search="{esc(search)}" data-images="{len(x['images'])}" data-first="{esc(x.get('first_seen',''))}" data-last="{esc(x.get('last_seen',''))}" data-slug="{esc(x['slug'])}">
  <img loading="lazy" src="{esc(first)}" alt="{esc(x['name'])}" class="w-full h-auto block bg-white">
  <h2 class="font-serif text-base leading-snug mt-3">{esc(x['name'])}</h2>
  <p class="text-stone-500 text-sm mt-0.5">{esc(x.get('cloth',''))} · {esc(x.get('color',''))}</p>
  <p class="text-stone-400 text-xs mt-1">{esc(x['category'])} · {len(x['images'])} images</p>
</article>""")
    body = "\n".join(cards)
    # Embed full listings for the modal (descriptions/posts included)
    embedded = json.dumps(listings, ensure_ascii=False).replace("</", "<\\/")
    doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>S.E.H Kelly — Catalog</title>
<script src="https://cdn.tailwindcss.com"></script>
<script>tailwind.config = {{ theme: {{ extend: {{ fontFamily: {{ serif: ['Georgia','Times New Roman','serif'] }} }} }} }}</script>
<style>.pill.active {{ color:#000; border-bottom:2px solid #000; }}</style></head>
<body class="bg-white text-neutral-900 antialiased">
<header class="max-w-7xl mx-auto px-6 pt-16 pb-8">
<h1 class="font-serif text-3xl tracking-tight">S.E.H Kelly — Catalog</h1>
<p class="text-stone-500 text-sm mt-2">551 listings · 2,385 images · parsed from the StyleForum S.E.H Kelly thread. Click an item for all photos, cloth, colour, dates, and forum posts.</p>
<div class="flex flex-wrap gap-x-6 gap-y-3 mt-8 items-center border-b border-stone-200 pb-4">
<input id="q" type="search" placeholder="Search by name, cloth, color…" class="border-b border-stone-300 focus:border-black bg-transparent py-1 text-sm outline-none">
<select id="sort" class="bg-transparent py-1 text-sm outline-none"><option value="name">Sort: Name</option><option value="images">Sort: Most images</option><option value="recent">Sort: Most recent</option><option value="oldest">Sort: Oldest first</option></select>
<div id="pills" class="flex flex-wrap gap-x-5 gap-y-2"><button data-cat="" class="pill active text-sm text-stone-500 hover:text-black pb-1">All (551)</button>{pills}</div></div></header>
<main id="grid" class="max-w-7xl mx-auto px-6 pb-20 grid gap-x-6 gap-y-12 grid-cols-2 md:grid-cols-3 xl:grid-cols-4">{body}</main>
<div id="modal" class="fixed inset-0 bg-black/60 hidden items-center justify-center p-4 z-50"><div class="bg-white max-w-3xl w-full max-h-[90vh] overflow-y-auto p-6"><button id="close" class="float-right text-stone-500 text-2xl leading-none">&times;</button><div id="modal-body"></div></div></div>
<footer class="max-w-7xl mx-auto px-6 pb-12 text-stone-500 text-sm"><p>Source: Adapt export SEHKelly_Catalog.json (2026-10-25), from the StyleForum thread. Photos are the export's local images/ files (2,385, from the Drive images.zip).</p></footer>
<script type="application/json" id="data">{embedded}</script>
<script>
const LISTINGS = JSON.parse(document.getElementById('data').textContent);
const bySlug = Object.fromEntries(LISTINGS.map(x => [x.slug, x]));
const grid=document.getElementById('grid'), q=document.getElementById('q'), sort=document.getElementById('sort'), pills=document.getElementById('pills'), modal=document.getElementById('modal'), mbody=document.getElementById('modal-body');
let active='';
pills.querySelectorAll('.pill').forEach(b=>{{b.onclick=()=>{{active=b.dataset.cat; pills.querySelectorAll('.pill').forEach(p=>p.classList.toggle('active',p.dataset.cat===active)); apply();}}}});
function apply(){{const term=q.value.toLowerCase(); const cards=[...grid.querySelectorAll('.card')]; cards.forEach(c=>{{c.style.display=(!active||c.dataset.category===active)&&(!term||c.dataset.search.includes(term))?'':'none';}}); const vis=cards.filter(c=>c.style.display!=='none'); if(sort.value==='images') vis.sort((a,b)=>b.dataset.images-a.dataset.images); else if(sort.value==='recent') vis.sort((a,b)=>b.dataset.last.localeCompare(a.dataset.last)); else if(sort.value==='oldest') vis.sort((a,b)=>a.dataset.first.localeCompare(b.dataset.first)); else vis.sort((a,b)=>a.dataset.title.localeCompare(b.dataset.title)); vis.forEach(c=>grid.appendChild(c));}}
q.oninput=apply; sort.onchange=apply;
grid.addEventListener('click', e=>{{const card=e.target.closest('.card'); if(!card) return; const x=bySlug[card.dataset.slug]; if(!x) return; const imgs=x.images.map(i=>`<figure class="mb-6"><img loading="lazy" src="${{i.full || i.src_url}}" class="w-full h-auto block"></figure>`).join(''); const posts=(x.posts||[]).map(p=>`<a href="${{p.url}}" target="_blank" rel="noopener" class="text-stone-700 underline">${{p.id}} — ${{p.date}}</a>`).join('<br>'); const desc=(x.descriptions||[]).map(d=>`<p class="text-stone-600 text-sm whitespace-pre-line mb-3">${{d.replace(/</g,'&lt;')}}</p>`).join(''); mbody.innerHTML=`<h2 class="font-serif text-2xl">${{x.name}}</h2><p class="text-stone-500 text-sm mt-1">CATEGORY ${{x.category}} · CLOTH ${{x.cloth}} · COLOUR ${{x.color}} · IMAGES ${{x.images.length}} · FORUM MENTIONS ${{x.post_count}}</p><p class="text-stone-500 text-sm">FIRST SEEN ${{x.first_seen}} · LAST SEEN ${{x.last_seen}} · SLUG ${{x.slug}}</p><div class="mt-4">${{imgs}}</div>${{desc}}<div class="mt-4 text-sm">${{posts}}</div>`; modal.classList.remove('hidden'); modal.classList.add('flex');}});
document.getElementById('close').onclick=()=>{{modal.classList.add('hidden'); modal.classList.remove('flex');}};
modal.onclick=e=>{{if(e.target===modal){{modal.classList.add('hidden'); modal.classList.remove('flex');}}}};
</script>
</body></html>"""
    (ROOT / "index.html").write_text(doc)
    # site/ copy: local image paths go up one level
    site_doc = doc.replace('"full": "images/', '"full": "../images/').replace('src="images/', 'src="../images/')
    (ROOT / "site" / "index.html").write_text(site_doc)
    (ROOT / "site" / "catalog.json").write_text(json.dumps(data, indent=2))
    print(f"Built site: {len(listings)} listings, {sum(len(x['images']) for x in listings)} images")
    print(f"Categories: {dict(counts)}")

if __name__ == "__main__":
    main()
