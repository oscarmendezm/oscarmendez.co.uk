"""Build the published site (docs/) from the single-file source.
Usage (from the repository root):  python3 source/build.py
Optional: python3 source/build.py <source.html> <output-dir>"""
import re, sys, json, os, shutil, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "oscarmendez-site.html")
out = os.path.normpath(sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "docs"))
SITE = "https://oscarmendez.co.uk"
TODAY = datetime.date.today().isoformat()
s = open(src, encoding="utf-8").read()
PAGES = {
 "home": ("/", "Dr Oscar Mendez · Physical AI leader",
   "Dr Oscar Mendez leads physical AI: AI for robots and autonomous machines that work in the real world. Director of AI & Data Science at Locus Robotics and Visiting Associate Professor at the University of Surrey."),
 "leadership": ("/leadership/", "Leadership · Dr Oscar Mendez",
   "How Oscar Mendez leads physical AI: Director of AI & Data Science at Locus Robotics, former Machine Vision Lead, and Visiting Associate Professor at the University of Surrey."),
 "research": ("/research/", "Research · Dr Oscar Mendez",
   "Oscar Mendez's research in bird's-eye-view mapping, localisation, Gaussian splatting, hyperspectral sensing and embodied AI, plus funded projects, researchers supervised and the SeDAR dataset."),
 "publications": ("/publications/", "Publications · Dr Oscar Mendez",
   "Publications and patents by Oscar Mendez: 38 papers at venues including CVPR, ICCV, ICRA and IROS, the ICRA 2022 Best Paper, and four US patents."),
 "media": ("/media/", "Media and talks · Dr Oscar Mendez",
   "Press coverage, interviews and talks featuring Dr Oscar Mendez, including the Sullivan Doctoral Thesis Prize and Autonomous Valet Parking."),
}
graph = json.loads(re.search(r'<script type="application/ld\+json" id="jsonld">(.*?)</script>', s, re.S).group(1).replace("<\\/", "</"))
nodes = graph["@graph"]
base = [n for n in nodes if n["@type"] in ("WebSite", "Person")]
profile = [n for n in nodes if n["@type"] == "ProfilePage"]
articles = [n for n in nodes if n["@type"] == "ScholarlyArticle"]
page_divs = {m.group(1): m for m in re.finditer(r'<div class="page" data-page="(\w+)">', s)}
order = sorted(page_divs, key=lambda k: page_divs[k].start())
def page_block(key):
    i = order.index(key); a = page_divs[key].start()
    b = page_divs[order[i+1]].start() if i+1 < len(order) else s.index("</main>")
    return s[a:b]
blocks = {k: page_block(k) for k in order}
first, last = page_divs[order[0]].start(), s.index("</main>")
def esc(t): return t.replace("&", "&amp;").replace('"', "&quot;")
os.makedirs(out, exist_ok=True)
for key, (path, title, desc) in PAGES.items():
    h = s[:first] + blocks[key].replace('class="page"', 'class="page active"', 1) + s[last:]
    url = SITE + path
    h = re.sub(r"<title>.*?</title>", f"<title>{esc(title)}</title>", h, 1)
    h = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{esc(desc)}">', h, 1)
    h = re.sub(r'<link rel="canonical" href="[^"]*">', f'<link rel="canonical" href="{url}">', h, 1)
    h = re.sub(r'<meta property="og:url" content="[^"]*">', f'<meta property="og:url" content="{url}">', h, 1)
    for prop in ('property="og:title"', 'name="twitter:title"'):
        h = re.sub(rf'<meta {prop} content="[^"]*">', f'<meta {prop} content="{esc(title)}">', h, 1)
    for prop in ('property="og:description"', 'name="twitter:description"'):
        h = re.sub(rf'<meta {prop} content="[^"]*">', f'<meta {prop} content="{esc(desc)}">', h, 1)
    if key != "home":
        h = h.replace('<meta property="og:type" content="profile">', '<meta property="og:type" content="website">')
    g = list(base)
    if key == "home":
        p = dict(profile[0]); p["dateModified"] = TODAY; g += [p]
    else:
        g += [{"@type": "WebPage", "@id": url + "#webpage", "url": url, "name": title, "description": desc,
               "isPartOf": {"@id": SITE + "/#website"}, "about": {"@id": SITE + "/#person"}, "inLanguage": "en-GB"}]
    if key == "publications":
        g += [{"@type": "CollectionPage", "@id": url + "#collection", "url": url, "name": title,
               "hasPart": [{"@id": a["@id"]} for a in articles]}] + articles
    ld = json.dumps({"@context": "https://schema.org", "@graph": g}, ensure_ascii=False).replace("</", "<\\/")
    h = re.sub(r'(<script type="application/ld\+json" id="jsonld">).*?(</script>)', lambda m: m.group(1) + ld + m.group(2), h, 1, re.S)
    h = h.replace("<body>", f'<body data-static="1" data-page="{key}">', 1)
    h = h.replace('href="#/"', 'href="/"')
    h = re.sub(r'href="#/(\w+)"', r'href="/\1/"', h)
    h = h.replace('href="OscarMendezCV.pdf"', 'href="/OscarMendezCV.pdf"')
    d = os.path.join(out, path.strip("/"))
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(h)
open(os.path.join(out, "sitemap.xml"), "w").write(
 '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
 "".join(f"  <url><loc>{SITE}{p}</loc><lastmod>{TODAY}</lastmod></url>\n" for p, _, _ in PAGES.values()) + "</urlset>\n")
open(os.path.join(out, "robots.txt"), "w").write(
 "# Search engines and AI assistants are welcome to read and cite this site.\nUser-agent: *\nAllow: /\n\n"
 f"Sitemap: {SITE}/sitemap.xml\n")
for extra in ("llms.txt", "og-image.png", "OscarMendezCV.pdf"):
    p = os.path.join(HERE, extra)
    if os.path.exists(p): shutil.copy(p, os.path.join(out, extra))
open(os.path.join(out, "CNAME"), "w").write("oscarmendez.co.uk\n")
open(os.path.join(out, ".nojekyll"), "w").write("")
open(os.path.join(out, "404.html"), "w", encoding="utf-8").write("""<!DOCTYPE html><html lang="en-GB"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex">
<title>Page not found · Dr Oscar Mendez</title>
<style>body{margin:0;min-height:100vh;display:grid;place-items:center;background:#0A1322;color:#E7ECF4;font-family:system-ui,-apple-system,"Segoe UI",sans-serif;padding:2rem}
main{max-width:34rem}h1{font-size:2.4rem;margin:0 0 1rem;letter-spacing:-.02em}p{color:#93A0B8;line-height:1.6}
a{display:inline-block;margin-top:1rem;background:#F2A93B;color:#1A1206;font-weight:600;text-decoration:none;padding:.7rem 1.1rem;border-radius:8px}</style></head>
<body><main><h1>Page not found.</h1><p>The page you were looking for has moved or no longer exists.</p><a href="/">Go to the home page</a></main></body></html>
""")
if not os.path.exists(os.path.join(out, "OscarMendezCV.pdf")):
    print("note: source/OscarMendezCV.pdf not found, so the Download CV button has nothing to serve yet")
print("built", len(PAGES), "pages into", out)
