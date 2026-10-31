"""Build the paper: fill code/paper_template.tex from data/results.json, add tables, compile with xelatex.
Output: release/paper/Hotham_Capitals_That_Moved.tex and .pdf (figures f_*.png beside them).
The DOI is a placeholder (10.5281/zenodo.23847842) unless the environment variable DOI is set."""
import re, subprocess
from collections import Counter
from common import *

R = jload(f"{DATA}/results.json")
D = jload(f"{WORK}/moves.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Capitals_That_Moved"
tex = lambda s: str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#")
tfmt = lambda v, f: tex(fmt(v, f or "raw"))
short = lambda s: s.replace(" (New Delhi from 1931)", "").replace("Calcutta (Kolkata)", "Calcutta").replace("Zanzibar (Stone Town)", "Zanzibar").replace("Kyoto (Heian-kyō)", "Kyoto")

# facts stated in words in the paper
assert [m["to"] for m in D["moves"] if m["year"] >= 2000] == ["Naypyidaw", "Ngerulmud", "Gitega", "Ciudad de la Paz"]
assert R["shortest_lasting"][1]["from"] == "Al-Muharraq" and R["shortest_lasting"][2]["to"] == "Karlsruhe"
assert R["by_century"][3]["name"] == "19th century" and R["by_century"][2]["name"] == "18th century"
assert [s["name"] for s in R["states_most"][:4]] == ["United States", "Republic of China", "France", "Province of Canada"]
pb = [p["to"] for p in R["purpose_built"] if p["year"] >= 1900]
assert pb == ["Delhi (New Delhi from 1931)", "Canberra", "Quezon City", "Brasília", "Gaborone", "Islamabad", "Belmopan", "Palikir", "Abuja", "Naypyidaw", "Ngerulmud", "Ciudad de la Paz"], pb

E = Counter(e["action"] for e in D["edits"])
TE = ("\\begin{table}[tbp]\\centering\\small\\caption{Hand edits to the automatic table, all listed with reasons and sources in \\texttt{data/manual\\_edits.csv}.}\\label{tab:edits}"
      "\\begin{tabular}{>{\\raggedright\\arraybackslash}p{2.4cm}r>{\\raggedright\\arraybackslash}p{10.2cm}}\\toprule Edit & Rows & Examples\\\\\\midrule\n"
      f"Removed & {E['drop']} & Wrong order (Herat to Samarkand, 1507); institution not capital (Regensburg, Wetzlar); duplicate with a wrong year (Kraków to Warsaw, 1795); wrong item (West Pakistan); Republic of China and Vichy France statements replaced\\\\\n"
      f"Corrected & {E['fix']} & Moscow to St Petersburg 1730 to 1732; Muscat to Zanzibar 1824 to 1840; Diriyah to Riyadh 1819 to 1824; Helvetic Republic and Central America sequences\\\\\n"
      f"Confirmed & {E['check']} & Rio to Brasília, Lagos to Abuja, Almaty to Astana, Yangon to Naypyidaw, Melbourne to Canberra and others\\\\\n"
      f"Added & {E['add']} & Istanbul to Ankara; Kyoto to Tokyo; Karachi to Rawalpindi; Continental Congress 1776 to 1785; Province of Canada 1844 to 1866; Republic of China 1912 to 1949; France 1879 and 1940 to 1944\\\\\n"
      f"Merged & {E['merge']} & The same move on two items with different years, kept once\\\\\n"
      f"Same place & {E['same place']} & Pairs of names for one city (Edo and Tokyo, Constantinople and Istanbul), not counted\\\\\n"
      f"Relabelled & {E['label']} & Display names only (Fengtian Fu as Mukden, Nan-ching as Nanjing)\\\\\n"
      "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{c['name']} & {c['n']} & {c['lasting']} & {c['temp']} & {c['added']} & {c['median_km']:,}\\\\\n" for c in R["by_century"])
TC = ("\\begin{table}[tbp]\\centering\\small\\caption{Moves by century.}\\label{tab:century}"
      "\\begin{tabular}{lrrrrr}\\toprule Century & Moves & Lasting & Temporary & Added by hand & Median km\\\\\\midrule\n" + rows +
      f"\\midrule All & {R['n']} & {R['n_lasting']} & {R['n_temp']} & {R['n_added']} & {R['median_km']:,}\\\\\\bottomrule\\end{{tabular}}\\end{{table}}")
rows = "".join(f"{tex(short(d['from']))} to {tex(short(d['to']))} & {d['year']} & {tex(d['state'])} & {d['km']:,} & {d['kind']}\\\\\n" for d in R["longest"][:10])
TL = ("\\begin{table}[tbp]\\centering\\small\\caption{The ten longest moves since 1500 (great-circle distance).}\\label{tab:longest}"
      "\\begin{tabular}{llp{4.6cm}rl}\\toprule Move & Year & State & km & Kind\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
src = lambda u: tex(re.sub(r"^https?://(en\.)?(www\.)?", "", u).replace("wikipedia.org/wiki/", "WP: ").replace("_", " ")[:34])
rows = "".join(f"{tex(short(f['from']))} to {tex(short(f['to']))} & {f['year']} & {tex(f['state'])} & {f['km']:,} & {f['status']} & {src(f['source'])}\\\\\n" for f in R["famous"])
TF = ("\\begin{table}[tbp]\\centering\\scriptsize\\caption{The famous moves checked by hand: whether Wikidata had them, and the source used.}\\label{tab:famous}"
      "\\begin{tabular}{>{\\raggedright\\arraybackslash}p{3.6cm}l>{\\raggedright\\arraybackslash}p{3.2cm}r>{\\raggedright\\arraybackslash}p{2.2cm}>{\\raggedright\\arraybackslash}p{3.6cm}}\\toprule Move & Year & State & km & Status & Source\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
t = t.replace("\\url{{{meta.page}}}", "\\url{%s}" % URL).replace("\\url{{{meta.repo}}}", "\\url{%s}" % REPO)
t = fill(t, R, tfmt)
t = t.replace("\u02bb", "'")
t = t.replace("{{TABLE_EDITS}}", TE).replace("{{TABLE_CENTURY}}", TC).replace("{{TABLE_LONGEST}}", TL).replace("{{TABLE_FAMOUS}}", TF)
if os.environ.get("DOI"):
    t = t.replace("10.5281/zenodo.23847842", os.environ["DOI"])
assert not re.search(r"\{\{(?!DOI\}\})", t), re.findall(r"\{\{[^}]*\}\}", t)[:5]
check_dashes(t, "paper")
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or l.startswith("!") or "undefined" in l][:12])
for ext in (".aux", ".log", ".out"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("\u2014") + txt.count("\u2013") + txt.count("--"))
