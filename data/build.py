#!/usr/bin/env python3
"""Business Approach guide site builder + Netlify deployer.

Usage:
  python3 build.py build            # render every page from data/guides/*.json into dist/
  python3 build.py pull             # download data/guides/*.json + assets list from the live Netlify site
  python3 build.py deploy           # upload dist/ (only changed files) and keep every other live file
Env: NETLIFY_TOKEN_FILE (default ~/.nftoken), SITE_ID below.
"""
import json, sys, os, re, html, hashlib, pathlib, datetime, urllib.request, urllib.parse

SITE_ID = "7bbeb850-999f-4da7-8b40-49869f448d2e"
SITE_URL = "https://businessapproach.netlify.app"
NAME = "Business Approach"
HANDLE = "@businessapproach"
SOCIAL = {"Instagram": "https://www.instagram.com/businessapproach",
          "Facebook": "https://www.facebook.com/753870484474104"}
AMAZON_TAG = "hajrajsstudio-20"   # e.g. "yourtag-20". Empty = no Amazon links anywhere.
CONTACT_EMAIL = ""  # optional public contact address

ROOT = pathlib.Path(__file__).parent
DATA = ROOT / "data" / "guides"
DIST = ROOT / "dist"
ASSETS = ROOT / "assets"
E = html.escape

CATS = {"seasonal": "Seasonal", "service": "Home & local services", "pets": "Pets", "craft": "Crafts & makers",
        "reselling": "Reselling", "digital": "Laptop & digital", "events": "Parties & events",
        "photo": "Photo & video", "tech": "Tech help", "errands": "Errands & helpers"}

CSS = """
@font-face{font-family:'Bricolage Grotesque';font-weight:700;font-display:swap;src:url(/assets/fonts/bricolage-grotesque-latin-700-normal.woff2) format('woff2')}
@font-face{font-family:'Bricolage Grotesque';font-weight:800;font-display:swap;src:url(/assets/fonts/bricolage-grotesque-latin-800-normal.woff2) format('woff2')}
@font-face{font-family:'DM Sans';font-weight:500;font-display:swap;src:url(/assets/fonts/dm-sans-latin-500-normal.woff2) format('woff2')}
@font-face{font-family:'DM Sans';font-weight:600;font-display:swap;src:url(/assets/fonts/dm-sans-latin-600-normal.woff2) format('woff2')}
@font-face{font-family:'DM Sans';font-weight:700;font-display:swap;src:url(/assets/fonts/dm-sans-latin-700-normal.woff2) format('woff2')}
@font-face{font-family:'Caveat';font-weight:700;font-display:swap;src:url(/assets/fonts/caveat-latin-700-normal.woff2) format('woff2')}
:root{--cream:#fbf3e8;--paper:#fffdf9;--peach:#fde2d2;--aqua:#d5eeeb;--ink:#0b2433;--muted:#4a5a63;--teal:#0b7472;--coral:#d9481c;--tang:#ff8a5c;--sun:#ffc94d;--line:#e6cfb6}
*{box-sizing:border-box;margin:0;padding:0}
html{-webkit-text-size-adjust:100%}
body{background:var(--cream);color:var(--ink);font:500 18px/1.65 "DM Sans",system-ui,sans-serif}
a{color:var(--teal);text-underline-offset:3px}
a:hover{color:var(--coral)}
img{max-width:100%;height:auto;display:block}
.wrap{max-width:1080px;margin:0 auto;padding:0 20px}
.narrow{max-width:760px;margin:0 auto;padding:0 20px}
h1,h2,h3{font-family:"Bricolage Grotesque",system-ui,sans-serif;font-weight:800;line-height:1.08;letter-spacing:-.02em}
h1{font-size:clamp(34px,6vw,58px)}
h2{font-size:clamp(26px,4vw,36px);margin:56px 0 14px}
h3{font-size:24px;margin:26px 0 8px}
p{margin:0 0 14px}
ul,ol{margin:0 0 16px 22px}
li{margin:4px 0}
header.top{border-bottom:2px solid var(--ink);background:var(--cream);position:sticky;top:0;z-index:5}
header.top .wrap{display:flex;align-items:center;justify-content:space-between;gap:16px;height:64px}
.brand{white-space:nowrap;display:flex;align-items:center;gap:10px;font:800 21px "Bricolage Grotesque",sans-serif;color:var(--ink);text-decoration:none}
.brand i{width:14px;height:14px;border-radius:50%;background:var(--coral)}
nav a{color:var(--ink);text-decoration:none;font-weight:700;font-size:16px;margin-left:20px}
nav a:hover{color:var(--coral)}
@media(max-width:620px){nav a.hide-s{display:none}nav a{margin-left:14px}.brand{font-size:18px}table{font-size:14px}.idea{padding:18px}}
[id]{scroll-margin-top:80px}
.hero{padding:64px 0 40px}
.hero p.lead{font-size:21px;color:var(--muted);max-width:640px;margin-top:16px}
.hand{font:700 30px "Caveat",cursive;color:var(--coral);display:inline-block;transform:rotate(-4deg)}
.hl{color:var(--coral)}
.btn{display:inline-block;background:var(--ink);color:#fff;text-decoration:none;font-weight:700;padding:12px 20px;border-radius:14px;border:2px solid var(--ink)}
.btn:hover{background:var(--coral);border-color:var(--coral);color:#fff}
.btn.ghost{background:transparent;color:var(--ink)}
.btn.ghost:hover{background:var(--ink);color:#fff}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:22px;margin:22px 0}
.card{background:var(--paper);border:2px solid var(--ink);border-radius:20px;padding:18px;text-decoration:none;color:var(--ink);display:flex;flex-direction:column;gap:10px}
.card:nth-child(3n+2){background:var(--peach)}.card:nth-child(3n){background:var(--aqua)}
.card:hover{transform:translateY(-2px)}
.card img{border-radius:12px;border:2px solid var(--ink);aspect-ratio:4/5;object-fit:cover}
.card h3{margin:0;font-size:22px}
.card .meta{font-size:14px;color:var(--muted);font-weight:600}
.pill{display:inline-block;font-size:13px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;color:var(--teal)}
.strip{background:var(--ink);color:#fff;border-radius:22px;padding:28px;margin:40px 0;display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:22px}
.strip b{font-family:"Bricolage Grotesque",sans-serif;font-size:20px;display:block;color:var(--sun)}
.strip p{margin:6px 0 0;font-size:16px;color:#dfe7ea}
article .byline{color:var(--muted);font-size:15px;font-weight:600;margin:14px 0 0}
article .byline+p:not(.byline){margin-top:24px}
.post-img{width:100%;max-width:420px;margin:28px 0;border:2px solid var(--ink);border-radius:18px}
table{width:100%;border-collapse:collapse;font-size:16px;background:var(--paper)}
th,td{text-align:left;padding:10px 12px;border-bottom:1px solid var(--line);vertical-align:top}
th{background:var(--ink);color:#fff;font-weight:700}
.tablewrap{overflow-x:auto;border:2px solid var(--ink);border-radius:14px;margin:14px 0 22px}
tr:last-child td{border-bottom:0}
.idea{background:var(--paper);border:2px solid var(--ink);border-radius:22px;padding:24px;margin:26px 0}
.idea:nth-of-type(3n+2){background:#fff8f3}.idea:nth-of-type(3n){background:#f3fbfa}
.idea h2{margin:0 0 6px}
.idea .num{font:700 16px "Bricolage Grotesque",sans-serif;color:var(--teal);letter-spacing:.05em}
.tag{display:inline-block;background:var(--ink);color:#fff;font:800 20px "Bricolage Grotesque",sans-serif;padding:4px 12px;border-radius:12px;margin:4px 0 12px}
.kit li span{color:var(--muted);font-size:15px}
.box{border-left:5px solid var(--sun);background:#fff6dc;padding:12px 16px;border-radius:0 12px 12px 0;margin:14px 0;font-size:16px}
.box.warn{border-color:var(--coral);background:#fdeee7}
.tip{background:var(--ink);color:#fff;border-radius:20px;padding:22px 24px;margin:34px 0;display:flex;gap:16px;align-items:flex-start}
.tip b{flex:none;background:var(--sun);color:var(--ink);font:800 16px "Bricolage Grotesque",sans-serif;padding:6px 12px;border-radius:10px;transform:rotate(-2deg);text-transform:uppercase;letter-spacing:.06em}
.tip p{margin:0}
details{background:var(--paper);border:2px solid var(--ink);border-radius:14px;padding:12px 16px;margin:10px 0}
summary{font-weight:700;cursor:pointer}
.sources{font-size:15px;color:var(--muted)}
.sources li{word-break:break-word}
.toc{background:var(--paper);border:2px dashed var(--ink);border-radius:16px;padding:16px 20px;margin:24px 0;font-size:16px}
.toc ol{margin-bottom:0}
footer{border-top:2px solid var(--ink);margin-top:72px;padding:30px 0 44px;font-size:15px;color:var(--muted)}
footer .wrap{display:flex;flex-wrap:wrap;gap:12px 28px;justify-content:space-between}
footer a{color:var(--ink);font-weight:600;margin-right:16px}
.disc{font-size:14px;color:var(--muted);border:1px solid var(--line);border-radius:12px;padding:10px 14px;margin:18px 0}
.links a.btn{display:block;text-align:center;margin:12px 0}
"""

def layout(title, desc, body, path="/", image=None, jsonld=None):
    canon = SITE_URL + path
    img = SITE_URL + (image or "/assets/img/og.jpg")
    ld = f'<script type="application/ld+json">{json.dumps(jsonld)}</script>' if jsonld else ""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title><meta name="description" content="{E(desc)}">
<link rel="canonical" href="{canon}"><meta property="og:type" content="article"><meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}"><meta property="og:url" content="{canon}"><meta property="og:image" content="{img}">
<meta name="twitter:card" content="summary_large_image"><meta name="theme-color" content="#fbf3e8">
<link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/assets/site.css">{ld}</head><body>
<header class="top"><div class="wrap"><a class="brand" href="/"><i></i>Business Approach</a>
<nav><a href="/guides/">Guides</a><a class="hide-s" href="/how-we-check-prices/">How we check</a><a href="/about/">About</a></nav></div></header>
<main>{body}</main>
<footer><div class="wrap"><div><strong style="color:var(--ink)">{HANDLE}</strong><br>Legit, low-cost business ideas. Rough US costs; check local rules first.{"<br>As an Amazon Associate we earn from qualifying purchases." if AMAZON_TAG else ""}</div>
<div><a href="/guides/">Guides</a><a href="/about/">About</a><a href="/how-we-check-prices/">How we check prices</a><a href="/disclosure/">Disclosure</a><a href="/privacy/">Privacy</a>
{"".join(f'<a href="{u}" rel="noopener">{k}</a>' for k,u in SOCIAL.items())}</div></div></footer></body></html>"""

def money(s):
    return E(s).replace("~", "~")

def amazon_link(q):
    if not AMAZON_TAG or not q: return ""
    u = "https://www.amazon.com/s?" + urllib.parse.urlencode({"k": q, "tag": AMAZON_TAG})
    return f' · <a href="{u}" rel="sponsored nofollow noopener">See options on Amazon</a>'

def fmt_date(d):
    return datetime.date.fromisoformat(d[:10]).strftime("%b %-d, %Y")

def rich(t):
    """tiny inline markup: **bold**, [text](url)"""
    t = E(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\[(.+?)\]\((https?://[^)]+)\)", r'<a href="\2" rel="noopener">\1</a>', t)
    return t

def guide_page(g):
    has_aff = bool(AMAZON_TAG) and any(k.get("amazon") for i in g["ideas"] for k in i["kit"])
    rows = "".join(f'<tr><td><a href="#idea-{n+1}">{E(i["name"])}</a></td><td><strong>{money(i["price"])}</strong></td><td>{E(i["skill"])}</td><td>{E(i["first_job"])}</td></tr>'
                   for n, i in enumerate(g["ideas"]))
    toc = "".join(f'<li><a href="#idea-{n+1}">{E(i["name"])}</a></li>' for n, i in enumerate(g["ideas"]))
    ideas = []
    for n, i in enumerate(g["ideas"]):
        kit = "".join(f'<li>{E(k["item"])} — <strong>{money(k["price"])}</strong> <span>({("<a href=\"%s\" rel=\"noopener\">%s</a>" % (E(k["url"]), E(k["store"]))) if k.get("url") else E(k.get("store",""))}{amazon_link(k.get("amazon"))})</span></li>' for k in i["kit"])
        charge = ""
        if i.get("charge"):
            c = i["charge"]
            charge = f'<h3>What customers pay pros</h3><p>{rich(c["text"])} <span class="sources">(<a href="{E(c["url"])}" rel="noopener">{E(c["source"])}</a>)</span></p><p>As a beginner, quote below that range until you have reviews and photos of your work.</p>'
        else:
            charge = '<h3>What to charge</h3><p>We could not find a reliable national price guide for this one. Search your ZIP code on Thumbtack or Nextdoor and price yourself just under local listings.</p>'
        steps = "".join(f"<li>{rich(s)}</li>" for s in i["first_customers"])
        ideas.append(f'''<section class="idea" id="idea-{n+1}"><div class="num">{n+1:02d}</div><h2>{E(i["name"])}</h2><div class="tag">{money(i["price"])} to start</div>
<p>{rich(i["what"])}</p><p><strong>Good fit if:</strong> {rich(i["who"])}</p>
<h3>Your starter kit</h3><ul class="kit">{kit}</ul>{('<p class="sources">'+rich(i["kit_note"])+'</p>') if i.get("kit_note") else ""}
{charge}<h3>Landing your first 3 customers</h3><ol>{steps}</ol>
<div class="box warn"><strong>Watch out:</strong> {rich(i["watch_out"])}</div></section>''')
    faq = "".join(f'<details><summary>{E(q["q"])}</summary><p>{rich(q["a"])}</p></details>' for q in g["faq"])
    src = "".join(f'<li>{E(s["label"])}{" — <a href=\"%s\" rel=\"noopener\">%s</a>" % (E(s["url"]), E(s["url"].split("//")[-1][:70])) if s.get("url") else ""}</li>' for s in g["sources"])
    img = f'<img class="post-img" src="/assets/img/{g["image"]}" alt="{E(g["image_alt"])}" width="1080" height="1350">' if g.get("image") else ""
    intro = "".join(f"<p>{rich(p)}</p>" for p in g["intro"])
    start = "".join(f"<li>{rich(s)}</li>" for s in g["getting_started"])
    social = ""
    if g.get("fb_post") or g.get("ig_post"):
        social = '<p class="byline">Saw this on social? '+" · ".join(f'<a href="{E(u)}" rel="noopener">{k} post</a>' for k,u in (("Facebook",g.get("fb_post")),("Instagram",g.get("ig_post"))) if u)+'</p>'
    body = f'''<article class="narrow" style="padding-top:44px"><span class="pill">{E(CATS.get(g["category"], g["category"]))} · Guide</span>
<h1>{E(g["title"])}</h1>
<p class="byline">By the {NAME} team · Published {fmt_date(g["published"])} · Prices checked {fmt_date(g["checked_on"])}</p>{social}
{('<div class="disc">This guide contains affiliate links. If you buy through them we may earn a small commission at no cost to you. <a href="/disclosure/">Details</a>. As an Amazon Associate we earn from qualifying purchases.</div>') if has_aff else ""}
{intro}{img}
<h2>At a glance</h2><div class="tablewrap"><table><tr><th>Idea</th><th>Starter cost</th><th>Skill level</th><th>Fastest first job</th></tr>{rows}</table></div>
<div class="toc"><strong>Jump to</strong><ol>{toc}</ol></div>
{"".join(ideas)}
<h2>Before you take your first job</h2><ol>{start}</ol>
<div class="tip"><b>Pro tip</b><p>{rich(g["tip"])}</p></div>
<h2>FAQ</h2>{faq}
<h2>Sources</h2><ul class="sources">{src}</ul>
<p class="sources">Prices are rough US estimates from the retailer pages above on the date shown and change often. Customer price ranges are national averages from the cost guides cited, not earnings promises. Rules differ by city and state, so check your local business license and insurance requirements before you start. <a href="/how-we-check-prices/">How we check prices</a>.</p>
<p style="margin-top:28px"><a class="btn" href="/guides/">More guides</a></p></article>'''
    ld = {"@context": "https://schema.org", "@type": "Article", "headline": g["title"], "description": g["description"],
          "datePublished": g["published"][:10], "dateModified": g.get("updated", g["published"])[:10],
          "author": {"@type": "Organization", "name": NAME}, "publisher": {"@type": "Organization", "name": NAME},
          "image": SITE_URL + "/assets/img/" + g["image"] if g.get("image") else None}
    return layout(g["title"] + " | " + NAME, g["description"], body, f"/guides/{g['slug']}/", "/assets/img/" + g["image"] if g.get("image") else None, ld)

def card(g):
    img = f'<img src="/assets/img/{g["image"]}" alt="" loading="lazy" width="1080" height="1350">' if g.get("image") else ""
    return f'<a class="card" href="/guides/{g["slug"]}/">{img}<span class="pill">{E(CATS.get(g["category"], g["category"]))}</span><h3>{E(g["title"])}</h3><span class="meta">{fmt_date(g["published"])} · {len(g["ideas"])} ideas, real prices</span></a>'

def static_page(path, title, desc, inner):
    return layout(title + " | " + NAME, desc, f'<div class="narrow" style="padding-top:48px">{inner}</div>', path)

def pages(guides):
    out = {}
    gs = sorted(guides, key=lambda g: g["published"], reverse=True)
    latest = "".join(card(g) for g in gs[:6]) or "<p>The first guide is on its way.</p>"
    out["index.html"] = layout(f"{NAME} — legit, low-cost business ideas with real prices",
        "Step-by-step guides to small businesses and side hustles you can start on a real budget. Every starter cost is checked on a real store page.",
        f'''<section class="hero wrap"><span class="hand">no fluff, no get-rich-quick ↓</span><h1>Legit businesses you can start <span class="hl">on a real budget</span>.</h1>
<p class="lead">Every idea from our posts gets a full guide here: the starter kit with checked prices, what customers pay, how to land your first 3 clients and what to watch out for.</p>
<p style="margin-top:22px"><a class="btn" href="/guides/">Browse the guides</a> <a class="btn ghost" href="/how-we-check-prices/">How we check prices</a></p></section>
<section class="wrap"><h2 style="margin-top:10px">Latest guides</h2><div class="grid">{latest}</div>
<div class="strip"><div><b>Real prices</b><p>Every starter cost is checked on a retailer or official page and the source is listed.</p></div>
<div><b>Only legit ideas</b><p>No MLMs, no passive-income fantasies, nothing that needs a big following or luck.</p></div>
<div><b>Honest numbers</b><p>Customer prices come from published cost guides. We never promise earnings.</p></div></div></section>''', "/")
    bycat = {}
    for g in gs: bycat.setdefault(g["category"], []).append(g)
    secs = "".join(f'<h2>{E(CATS.get(c, c))}</h2><div class="grid">{"".join(card(g) for g in L)}</div>' for c, L in bycat.items())
    out["guides/index.html"] = layout(f"All guides | {NAME}", "Every Business Approach guide, grouped by type of business.",
        f'<section class="wrap" style="padding-top:44px"><h1>All guides</h1><p class="lead" style="color:var(--muted);margin-top:10px">{len(gs)} guides so far. A new one lands a few days after each post.</p>{secs or "<p>Coming soon.</p>"}</section>', "/guides/")
    for g in gs:
        out[f"guides/{g['slug']}/index.html"] = guide_page(g)
    links = "".join(f'<a class="btn" href="/guides/{g["slug"]}/">{E(g["title"])}</a>' for g in gs[:8])
    out["links/index.html"] = static_page("/links/", "Links", "Latest Business Approach guides.",
        f'<div class="links" style="max-width:520px;margin:0 auto;text-align:center"><span class="hand">from our posts ↓</span><h1 style="font-size:40px">Latest guides</h1>{links}<a class="btn ghost" href="/guides/">See every guide</a></div>')
    out["about/index.html"] = static_page("/about/", "About", "Who is behind Business Approach and what we stand for.", f'''<h1>About {NAME}</h1>
<p class="byline">Legit, low-cost business ideas. Researched, priced and explained.</p>
<p>{NAME} started as an Instagram and Facebook page sharing one simple post a day: a handful of small businesses you can start for a clear, honest budget. This site is where each of those posts gets the full story.</p>
<h2>What we believe</h2><ul><li><strong>Only legit, doable ideas.</strong> Legal, proven work that pays. No MLMs, no get-rich-quick schemes, nothing that needs savings, a big following or luck.</li>
<li><strong>Budget-honest.</strong> If a post says "under $100", the starter kit really costs under $100, and we show you where we found each price.</li>
<li><strong>No earnings promises.</strong> We share what customers typically pay professionals, from published cost guides. What you earn depends on your area, your effort and your prices.</li>
<li><strong>Check your local rules.</strong> Licenses, permits and insurance vary by city and state. We point you to them; we can't give legal or tax advice.</li></ul>
<h2>Follow along</h2><p>{" · ".join(f'<a href="{u}" rel="noopener">{k}</a>' for k,u in SOCIAL.items())}</p>
{f'<p>Contact: <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></p>' if CONTACT_EMAIL else '<p>Questions or a correction? Send us a message on Instagram or Facebook.</p>'}''')
    out["how-we-check-prices/index.html"] = static_page("/how-we-check-prices/", "How we check prices", "Our research rules for every post and guide.", '''<h1>How we check prices</h1>
<p>Every number on our posts and guides follows the same rules.</p>
<ol><li><strong>Real store pages only.</strong> Each starter-kit price comes from a current product page at a US retailer (like Home Depot, Walmart, Target or Best Buy) or an official site. Search snippets alone don't count.</li>
<li><strong>Rounded honestly.</strong> We round to a simple estimate with a tilde (~$13) and never round down to make an idea look cheaper.</li>
<li><strong>"Free" means free.</strong> We only say free when the tool or plan is free to start, and we mention any fee taken when you get paid.</li>
<li><strong>Sources listed.</strong> Every guide ends with the store, product and link we used, plus the date we checked.</li>
<li><strong>Customer prices are cited.</strong> "What customers pay" ranges come from published cost guides (like Angi or HomeGuide). If we can't find a reliable one, we say so instead of guessing.</li>
<li><strong>Prices change.</strong> Sales end and stock runs out. Treat our numbers as a starting point and check before you buy.</li></ol>
<p>Spotted a price that's out of date? Message us on social and we'll fix it.</p>''')
    out["disclosure/index.html"] = static_page("/disclosure/", "Affiliate disclosure", "How Business Approach makes money.", f'''<h1>Affiliate disclosure</h1>
<p>Some links on this site may be affiliate links. If you buy something through one, {NAME} may earn a small commission at no extra cost to you.</p>
<p><strong>As an Amazon Associate we earn from qualifying purchases.</strong></p>
<p>Affiliate links never decide which products we recommend. We pick the cheapest honest option that does the job, show the price from the store where we checked it, and only add an Amazon link where Amazon sells the same or a clearly equivalent item. We don't show Amazon prices on this site; check the current price on Amazon before you buy.</p>''')
    out["privacy/index.html"] = static_page("/privacy/", "Privacy policy", "Privacy policy for the Business Approach website.", f'''<h1>Privacy policy</h1><p class="byline">Last updated {datetime.date.today().strftime("%b %-d, %Y")}</p>
<p>This site does not ask you to create an account and does not collect your name, email or payment details. We do not use advertising trackers.</p>
<p><strong>Hosting.</strong> The site is hosted by Netlify, which may process standard server logs (such as IP address and browser type) to deliver and secure the site.</p>
<p><strong>Affiliate links.</strong> If you click an affiliate link (for example to Amazon), that retailer may use cookies to credit the referral. Their own privacy policy applies on their site.</p>
<p><strong>Social links.</strong> Links to Instagram and Facebook take you to those services, which have their own privacy policies.</p>
<p>Questions? Message us on Instagram or Facebook.</p>''')
    out["404.html"] = static_page("/404.html", "Page not found", "Page not found.", '<h1>That page took a day off.</h1><p>Try the <a href="/guides/">guide library</a> instead.</p>')
    urls = ["/", "/guides/", "/about/", "/how-we-check-prices/", "/disclosure/", "/privacy/"] + [f"/guides/{g['slug']}/" for g in gs]
    out["sitemap.xml"] = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(f"<url><loc>{SITE_URL}{u}</loc></url>" for u in urls) + "</urlset>"
    out["robots.txt"] = f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n"
    out["assets/site.css"] = CSS
    out["favicon.svg"] = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#0b2433"/><text x="32" y="44" text-anchor="middle" font-family="Arial Black,Arial" font-weight="900" font-size="30" fill="#ffc94d">BA</text><circle cx="52" cy="12" r="5" fill="#d9481c"/></svg>'
    for g in gs:
        out[f"data/guides/{g['slug']}.json"] = json.dumps(g, ensure_ascii=False, indent=1)
    out["data/index.json"] = json.dumps([g["slug"] for g in gs])
    return out

def build():
    guides = [json.load(open(f)) for f in sorted(DATA.glob("*.json"))]
    if DIST.exists():
        import shutil; shutil.rmtree(DIST)
    for p, c in pages(guides).items():
        f = DIST / p; f.parent.mkdir(parents=True, exist_ok=True); f.write_text(c)
    if ASSETS.exists():
        import shutil
        for f in ASSETS.rglob("*"):
            if f.is_file():
                t = DIST / "assets" / f.relative_to(ASSETS); t.parent.mkdir(parents=True, exist_ok=True); shutil.copy(f, t)
    import shutil
    (DIST / "data").mkdir(parents=True, exist_ok=True); shutil.copy(__file__, DIST / "data" / "build.py")
    print("built", len(guides), "guides,", sum(1 for _ in DIST.rglob("*") if _.is_file()), "files")

def api(method, path, data=None, ctype="application/json", raw=False):
    tok = open(os.path.expanduser(os.environ.get("NETLIFY_TOKEN_FILE", "/home/claude/.nftoken"))).read().strip()
    req = urllib.request.Request("https://api.netlify.com/api/v1" + path, method=method, data=data,
                                 headers={"Authorization": "Bearer " + tok, "Content-Type": ctype})
    with urllib.request.urlopen(req, timeout=120) as r:
        b = r.read()
        return b if raw else (json.loads(b) if b else None)

def live_files():
    return {f["id"]: f["sha"] for f in api("GET", f"/sites/{SITE_ID}/files")}

def pull():
    """Download every guide JSON (and images) from the live site so a fresh machine can rebuild."""
    files = live_files()
    DATA.mkdir(parents=True, exist_ok=True)
    for p in files:
        if p.startswith("/data/guides/") and p.endswith(".json"):
            b = api("GET", f"/sites/{SITE_ID}/files{urllib.parse.quote(p)}", ctype="application/vnd.bitballoon.v1.raw", raw=True)
            (DATA / p.split("/")[-1]).write_bytes(b)
    print("pulled", len(list(DATA.glob('*.json'))), "guides;", len(files), "live files")

def deploy():
    """Digest deploy: keep every live file, replace/add files in dist/."""
    keep = live_files()
    local = {}
    for f in DIST.rglob("*"):
        if f.is_file():
            p = "/" + str(f.relative_to(DIST)); b = f.read_bytes()
            local[p] = (hashlib.sha1(b).hexdigest(), b)
    manifest = dict(keep); manifest.update({p: s for p, (s, _) in local.items()})
    d = api("POST", f"/sites/{SITE_ID}/deploys", json.dumps({"files": manifest}).encode())
    need = set(d.get("required", []))
    n = 0
    for p, (s, b) in local.items():
        if s in need:
            api("PUT", f"/deploys/{d['id']}/files{urllib.parse.quote(p)}", b, "application/octet-stream"); n += 1; need.discard(s)
    if need: print("WARNING missing uploads for", len(need), "files")
    import time
    for _ in range(40):
        st = api("GET", f"/deploys/{d['id']}")
        if st["state"] in ("ready", "error"): break
        time.sleep(3)
    print("deploy", d["id"], st["state"], "uploaded", n, "files; total", len(manifest), "->", SITE_URL)

if __name__ == "__main__":
    {"build": build, "pull": pull, "deploy": deploy}[sys.argv[1]]()
