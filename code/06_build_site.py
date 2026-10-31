"""Build index.html from code/page_template.html. Every number in the text is a {{path|format}} token filled from
data/results.json (embedded); data/site.json, data/cities.json and data/borders_today.json are loaded by the page.
Facts stated in words are checked here. The full-screen map snippet (code/fullscreen_snippet.html, from the
drinks-map reference) is pasted before </body>."""
import json, re
from common import *

R = jload(f"{DATA}/results.json")


def checks():
    """Facts the page, blog and paper state in words."""
    assert R["top_century"]["name"] == "20th century" and all(c["n"] < R["c20"]["n"] for c in R["by_century"] if c["c"] != 1900)
    assert R["us"]["n"] == 11 and R["countries"][0]["name"] == "United States" and R["countries"][1]["name"] == "Germany"
    assert [c["name"] for c in R["countries"][2:4]] == ["India", "China"] and R["countries"][2]["n"] == R["countries"][3]["n"]
    assert [c["name"] for c in R["countries"][4:6]] == ["Russia", "France"] and R["countries"][4]["n"] == R["countries"][5]["n"]
    assert R["longest"][0]["from"] == "Lisbon" and R["longest"][0]["to"] == "Rio de Janeiro" and R["lisbon_rio"]["ratio_second"] == 2.0
    assert R["longest_lasting"][0]["to"].startswith("Zanzibar") and R["longest_lasting"][1]["to"] == "Taipei" and R["longest_lasting"][2]["from"].startswith("Calcutta")
    assert R["shortest_lasting"][0]["from"] == "Thon Buri" and R["shortest_lasting"][0]["to"] == "Bangkok"
    assert R["busiest_decade"]["d"] == 1940 and R["busiest_decade"]["lasting"] < R["busiest_decade"]["n"] / 2
    assert R["busiest_year"]["y"] == 1949
    assert R["sea"]["seaward_n"] == 1 and R["sea"]["seaward"][0]["to"] == "Taipei"
    assert 1976 - 1948 == 28 and 1821 - 1808 == 13 and R["last_year"] - 2000 == 26 and R["c21"]["n"] == 4
    assert R["latest"]["to"] == "Ciudad de la Paz" and R["latest"]["year"] == 2026
    inl = {(x["from"], x["to"]) for x in R["sea"]["inland"]}
    for f, t in [("Rio de Janeiro", "Brasília"), ("Lagos", "Abuja"), ("Dar es Salaam", "Dodoma"), ("Yangon", "Naypyidaw"), ("Abidjan", "Yamoussoukro"), ("Karachi", "Rawalpindi"), ("Malabo", "Ciudad de la Paz")]:
        assert (f, t) in inl, (f, t)
    pb = {p["to"] for p in R["purpose_built"] if p["year"] >= 1900}
    for c in ("Delhi (New Delhi from 1931)", "Canberra", "Brasília", "Islamabad", "Belmopan", "Gaborone", "Abuja", "Naypyidaw"):
        assert c in pb, c
    assert {"St Petersburg", "Karlsruhe", "Washington"} <= {p["to"] for p in R["purpose_built"]}
    assert R["germany"]["states"] == R["countries"][1]["states"]
    assert R["conf"]["low"] == 0


def build():
    checks()
    tpl = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
    html = fill(tpl, R)
    assert not re.search(r"\{\{(?!DOI|BLOG_URL|DOI_URL)", html), re.findall(r"\{\{[^}]*\}\}", html)[:5]
    J = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    html = html.replace("/*RESULTS*/", J(R))
    html = html.replace("/*FULLSCREEN*/", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    check_dashes(vis, "page text")
    for scr in re.findall(r"<script[^>]*>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    for bad in ("DSIT", "DCMS", "civil serv"):
        assert bad.lower() not in html.lower(), bad
    s = open(f"{DATA}/site.json", encoding="utf-8").read()
    for bad in ("—", "–", "--"):
        assert bad not in s, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()) // 1024, "KB")


if __name__ == "__main__":
    build()
