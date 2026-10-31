"""Blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.23847842, https://doi.org/10.5281/zenodo.23847842 and https://blog.tristanhotham.com/2026/10/31/moving-capitals/ are left for the publisher to fill."""
import re, shutil, zipfile, json as _json, importlib.util
from common import *

R = jload(f"{DATA}/results.json")
REL = os.path.join(ROOT, "release")
NAME = "Hotham_Capitals_That_Moved"
spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "06_build_site.py")); B = importlib.util.module_from_spec(spec); spec.loader.exec_module(B)
B.checks()
# facts written in words in the blog
assert 1927 - 1901 in (25, 26) and 1866 - 1841 == 25 and R["us"]["n"] == 11
assert R["countries"][2]["name"] == "India" and R["countries"][3]["name"] == "China"

post = fill(open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read(), R)
post = re.sub(r"\{\{IMG\|([^|]+)\|([^|]*)\|([^}]*)\}\}", lambda m: "{{IMG|" + m.group(1) + "|" + fill(m.group(2), R) + "|" + fill(m.group(3), R) + "}}", post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
for img in used:
    assert os.path.exists(f"{REL}/blog/{img}"), img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert all(re.fullmatch(r"\{\{IMG\|[^}]*\}\}", ln) for ln in post.splitlines() if "{{IMG" in ln)
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
check_dashes(vis, "blog")
assert AI in post
for bad in ("DSIT", "DCMS", "civil serv"):
    assert bad.lower() not in post.lower()
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
meta = {"title": "Capitals that moved: every capital move since 1500, and how far each went",
        "slug": "moving-capitals",
        "excerpt": f"{R['n']} moves of a capital since 1500, from St Petersburg to Brasília to Ciudad de la Paz. The longest was a flight: the Portuguese court, {R['lisbon_rio']['km']:,} km from Lisbon to Rio de Janeiro in 1808.",
        "seo_description": f"An interactive map of every capital move since 1500: {R['n']} moves, how far each went, purpose-built capitals, and Nusantara's status in 2026.",
        "tags": ["capitals", "capital cities", "history", "geography", "maps", "data visualisation", "Wikidata"],
        "header_alt": f"Title card reading 'Capitals that moved' in black, brick red and navy on cream, beside a light world map criss-crossed by coloured arcs from old capitals to new ones, with a long dashed arc across the Atlantic from Lisbon to Rio de Janeiro. Text: {R['n']} moves of a capital since 1500; the longest, Lisbon to Rio de Janeiro, {R['lisbon_rio']['km']:,} km, in 1808."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/moving-capitals_code_and_data.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d in ("code", "data", "reddit"):
        for fn in sorted(os.listdir(os.path.join(ROOT, d))):
            p = os.path.join(ROOT, d, fn)
            if os.path.isdir(p) or fn.endswith(".pyc") or fn.endswith(".png"):
                continue
            z.write(p, f"moving-capitals/{d}/{fn}")
    for fn in ("README.md", "LICENSE"):
        z.write(os.path.join(ROOT, fn), f"moving-capitals/{fn}")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("{,}", ",")
zmeta = {"title": "Capitals That Moved: Every Capital Move since 1500 in Wikidata, Checked and Corrected, with Distances, Directions and Purpose-Built Capitals",
         "upload_type": "publication", "publication_type": "workingpaper",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{URL}\">{URL}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {{https://blog.tristanhotham.com/2026/10/31/moving-capitals/}}.</p><p>Licences: paper, figures and derived data CC BY 4.0; code MIT. Wikidata is CC0; Natural Earth is public domain.</p><p>{AI}</p>",
         "keywords": ["capital cities", "capital relocation", "planned capitals", "historical geography", "Wikidata", "data quality", "maps", "open data"],
         "license": "cc-by-4.0",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": URL, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "https://www.wikidata.org/", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://www.naturalearthdata.com/", "relation": "isDerivedFrom", "resource_type": "dataset"}]}
s = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
check_dashes(s, "zenodo/meta")
with open(f"{Z}/metadata.json", "w", encoding="utf-8") as f:
    _json.dump(zmeta, f, ensure_ascii=False, indent=2)
print("blog words", words, "figures", used, "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
