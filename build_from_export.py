#!/usr/bin/env python3
"""Build the site from the uploaded Adapt export SEHKelly_Catalog.json.

551 listings, 2,385 images, categories exactly matching the Adapt baseline.
Images are the local images/ files from the Drive images.zip.
Site: Tailwind + shadcn/ui components (cards, badges, buttons, inputs,
dialog), with category filters, search (name/cloth/color), sort, and a
detail dialog per listing. Keyboard: cards are focusable, Enter/Space
opens, Esc closes the dialog, Tab is trapped in the dialog, focus
returns to the card on close.
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
    # shadcn/ui-style filter buttons: outline by default, solid black
    # (primary) when active. No beige pills.
    pills = "".join(
        f'<button data-cat="{esc(c)}" class="pill inline-flex h-9 items-center justify-center rounded-md border border-slate-200 bg-white px-3 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-950">{esc(c)} ({counts[c]})</button>'
        for c in sorted(cats)
    )
    cards = []
    for x in listings:
        # Local images from Drive (images.zip, 2385 files, 0 missing)
        # take precedence over the StyleForum hotlink.
        first = x["images"][0].get("full") or x["images"][0].get("src_url") if x.get("images") else ""
        search = f"{x['name']} {x.get('cloth','')} {x.get('color','')}".lower()
        # shadcn/ui card: rounded, bordered, subtle shadow, hover lift.
        # One title only (no figcaption duplicate). Portrait 3:4 crop —
        # not square — so garments are not cut to a strip, and the grid
        # stays clean and uniform. Keyboard: focusable, Enter/Space opens.
        cards.append(f"""<article class="card group cursor-pointer rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden transition-all hover:shadow-md hover:-translate-y-0.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-950" tabindex="0" role="button" aria-label="{esc(x['name'])} — {esc(x.get('cloth',''))} {esc(x.get('color',''))}" data-category="{esc(x['category'])}" data-title="{esc(x['name'].lower())}" data-search="{esc(search)}" data-images="{len(x['images'])}" data-first="{esc(x.get('first_seen',''))}" data-last="{esc(x.get('last_seen',''))}" data-slug="{esc(x['slug'])}">
  <div class="overflow-hidden bg-slate-100"><img loading="lazy" src="{esc(first)}" alt="{esc(x['name'])}" class="w-full aspect-[3/4] object-cover transition-transform group-hover:scale-105"></div>
  <div class="p-4"><h2 class="font-serif text-base leading-snug">{esc(x['name'])}</h2>
  <p class="text-slate-500 text-sm mt-1">{esc(x.get('cloth',''))} · {esc(x.get('color',''))}</p>
  <div class="flex items-center gap-2 mt-3"><span class="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-700">{esc(x['category'])}</span><span class="text-xs text-slate-400">{len(x['images'])} images</span></div></div>
</article>""")
    body = "\n".join(cards)
    # Embed full listings for the modal (descriptions/posts included)
    embedded = json.dumps(listings, ensure_ascii=False).replace("</", "<\\/")
    doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>S.E.H Kelly — Catalog</title>
<script src="https://cdn.tailwindcss.com"></script>
<script>tailwind.config = {{ theme: {{ extend: {{ fontFamily: {{ serif: ['Georgia','Times New Roman','serif'] }}, colors: {{ background: '#ffffff', foreground: '#0f172a', muted: '#f1f5f9', border: '#e2e8f0', primary: '#0f172a' }} }} }} }}</script>
<style>.pill.active {{ background:#0f172a; color:#fff; border-color:#0f172a; }}</style></head>
<body class="bg-slate-50 text-slate-900 antialiased">
<header class="sticky top-0 z-40 border-b border-slate-200 bg-white/80 backdrop-blur">
<div class="max-w-7xl mx-auto px-6 py-5 flex flex-wrap items-baseline gap-x-4 gap-y-2">
<h1 class="font-serif text-3xl tracking-tight">S.E.H Kelly — Catalog</h1>
<p class="text-slate-500 text-sm">551 listings · 2,385 images</p></div></header>
<div class="max-w-7xl mx-auto px-6 pt-8 pb-4">
<p class="text-slate-500 text-sm">Parsed from the StyleForum S.E.H Kelly thread. Click an item — or Tab to it and press Enter — for all photos, cloth, colour, dates, and forum posts. Press Esc to close.</p>
<div class="flex flex-wrap gap-3 mt-6 items-center">
<input id="q" type="search" placeholder="Search by name, cloth, color…" class="flex h-10 w-full max-w-sm rounded-md border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm outline-none focus-visible:ring-2 focus-visible:ring-slate-950 placeholder:text-slate-400">
<select id="sort" class="flex h-10 rounded-md border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm outline-none focus-visible:ring-2 focus-visible:ring-slate-950"><option value="name">Sort: Name</option><option value="images">Sort: Most images</option><option value="recent">Sort: Most recent</option><option value="oldest">Sort: Oldest first</option></select>
<div id="pills" class="flex flex-wrap gap-2"><button data-cat="" class="pill active inline-flex h-9 items-center justify-center rounded-md border border-slate-200 bg-white px-3 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-950">All (551)</button>{pills}</div></div></div>
<main id="grid" class="max-w-7xl mx-auto px-6 pb-20 grid gap-6 grid-cols-2 md:grid-cols-3 xl:grid-cols-4">{body}</main>
<div id="modal" class="fixed inset-0 z-50 hidden items-center justify-center p-4 bg-slate-950/80" role="dialog" aria-modal="true" aria-label="Item details"><div class="relative bg-white rounded-lg shadow-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto p-6"><button id="close" aria-label="Close" class="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-white transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-slate-950 text-2xl leading-none">&times;</button><div id="modal-body"></div></div></div>
<footer class="max-w-7xl mx-auto px-6 pb-12 text-slate-500 text-sm"><p>Source: Adapt export SEHKelly_Catalog.json (2026-10-25), from the StyleForum thread. Photos are the export's local images/ files (2,385, from the Drive images.zip).</p></footer>
<script type="application/json" id="data">{embedded}</script>
<script>
const LISTINGS = JSON.parse(document.getElementById('data').textContent);
const bySlug = Object.fromEntries(LISTINGS.map(x => [x.slug, x]));
const grid=document.getElementById('grid'), q=document.getElementById('q'), sort=document.getElementById('sort'), pills=document.getElementById('pills'), modal=document.getElementById('modal'), mbody=document.getElementById('modal-body');
let active='';
pills.querySelectorAll('.pill').forEach(b=>{{b.onclick=()=>{{active=b.dataset.cat; pills.querySelectorAll('.pill').forEach(p=>p.classList.toggle('active',p.dataset.cat===active)); apply();}}}});
function apply(){{const term=q.value.toLowerCase(); const cards=[...grid.querySelectorAll('.card')]; cards.forEach(c=>{{c.style.display=(!active||c.dataset.category===active)&&(!term||c.dataset.search.includes(term))?'':'none';}}); const vis=cards.filter(c=>c.style.display!=='none'); if(sort.value==='images') vis.sort((a,b)=>b.dataset.images-a.dataset.images); else if(sort.value==='recent') vis.sort((a,b)=>b.dataset.last.localeCompare(a.dataset.last)); else if(sort.value==='oldest') vis.sort((a,b)=>a.dataset.first.localeCompare(b.dataset.first)); else vis.sort((a,b)=>a.dataset.title.localeCompare(b.dataset.title)); vis.forEach(c=>grid.appendChild(c));}}
q.oninput=apply; sort.onchange=apply;
let lastFocused=null;
function openModal(card){{const x=bySlug[card.dataset.slug]; if(!x) return; const imgs=x.images.map(i=>`<figure class="mb-6"><img loading="lazy" src="${{i.full || i.src_url}}" class="w-full h-auto block rounded-md"></figure>`).join(''); const posts=(x.posts||[]).map(p=>`<a href="${{p.url}}" target="_blank" rel="noopener" class="text-slate-700 underline">${{p.id}} — ${{p.date}}</a>`).join('<br>'); const desc=(x.descriptions||[]).map(d=>`<p class="text-slate-600 text-sm whitespace-pre-line mb-3">${{d.replace(/</g,'&lt;')}}</p>`).join(''); mbody.innerHTML=`<h2 class="font-serif text-2xl pr-8">${{x.name}}</h2><p class="text-slate-500 text-sm mt-1">${{x.category}} · ${{x.cloth}} · ${{x.color}} · ${{x.images.length}} images · ${{x.post_count}} forum mentions</p><p class="text-slate-500 text-sm">First seen ${{x.first_seen}} · Last seen ${{x.last_seen}}</p><div class="mt-4">${{imgs}}</div>${{desc}}<div class="mt-4 text-sm">${{posts}}</div>`; lastFocused=document.activeElement; modal.classList.remove('hidden'); modal.classList.add('flex'); document.getElementById('close').focus();}}
function closeModal(){{modal.classList.add('hidden'); modal.classList.remove('flex'); if(lastFocused && lastFocused.focus) lastFocused.focus();}}
grid.addEventListener('click', e=>{{const card=e.target.closest('.card'); if(card) openModal(card);}});
grid.addEventListener('keydown', e=>{{const card=e.target.closest('.card'); if(!card) return; if(e.key==='Enter' || e.key===' '){{e.preventDefault(); openModal(card);}}}});
document.getElementById('close').onclick=closeModal;
modal.onclick=e=>{{if(e.target===modal) closeModal();}};
document.addEventListener('keydown', e=>{{if(e.key==='Escape' && !modal.classList.contains('hidden')) closeModal();}});
modal.addEventListener('keydown', e=>{{if(e.key!=='Tab') return; const focusable=[...modal.querySelectorAll('button, a[href]')].filter(el=>el.offsetParent!==null); if(!focusable.length) return; const first=focusable[0], last=focusable[focusable.length-1]; if(e.shiftKey && document.activeElement===first){{e.preventDefault(); last.focus();}} else if(!e.shiftKey && document.activeElement===last){{e.preventDefault(); first.focus();}}}});
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
