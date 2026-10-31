"""Parse the QLever dump of capital (P36) statements into one record per state and one per statement.

The dump has one row per combination of statement x state type x capital coordinate x inception x dissolution, so rows
are collapsed here. Dates are reduced to years (Wikidata's year precision is not in the dump, so 1 January dates are
treated as year-only). Blank nodes ("unknown value") are kept as flags: an unknown capital cannot be placed on a map.
Writes WORK/states.json and WORK/statements.json."""
import csv, re
from collections import defaultdict
from common import *

E = "http://www.wikidata.org/entity/"
TYPES = {"Q6256": "country", "Q3624078": "sovereign state", "Q3024240": "historical country", "Q417175": "kingdom",
         "Q1250464": "realm", "Q7270": "republic", "Q48349": "empire", "Q28171280": "ancient civilisation", "Q41614": "constitutional monarchy"}


def val(v):
    v = v.strip()
    if not v:
        return ""
    if v.startswith("<" + E):
        return v[len(E) + 1:-1]
    if "/.well-known/genid/" in v:
        return "?"
    if v.startswith("<") and v.endswith(">"):
        return v[1:-1]
    m = re.match(r'^"(.*)"(@[\w-]+|\^\^<[^>]+>)?$', v, re.S)
    return m.group(1).replace('\\"', '"') if m else v


def year(v):
    if v in ("", "?"):
        return None if v == "" else "?"
    m = re.match(r"^(-?\d+)-(\d\d)-(\d\d)", v)
    return int(m.group(1)) if m else None


def date(v):
    m = re.match(r"^(-?\d+)-(\d\d)-(\d\d)", v or "")
    return f"{int(m.group(1))}-{m.group(2)}-{m.group(3)}" if m else None


def point(v):
    m = re.match(r"POINT\(([-\d.eE]+) ([-\d.eE]+)\)", v or "")
    return (float(m.group(2)), float(m.group(1))) if m else None


rows = []
with open(CAPS, encoding="utf-8") as f:
    head = [h.lstrip("?") for h in f.readline().rstrip("\n").split("\t")]
    for ln in f:
        p = ln.rstrip("\n").split("\t")
        rows.append({h: val(x) for h, x in zip(head, p + [""] * (len(head) - len(p)))})
print("rows", len(rows))

states = {}
st = defaultdict(lambda: {"coords": set(), "types": set()})
for r in rows:
    s = states.setdefault(r["s"], {"q": r["s"], "label": r["sL"], "types": set(), "inc": set(), "dis": set()})
    s["types"].add(TYPES.get(r["stype"], r["stype"]))
    if r["inc"]:
        s["inc"].add(year(r["inc"]))
    if r["dis"]:
        s["dis"].add(year(r["dis"]))
    k = (r["s"], r["cap"] if r["cap"] != "?" else "?" + str(len(st)), r["start"], r["end"], r["rank"].split("#")[-1].replace("Rank", "").lower())
    if r["cap"] == "?":   # every unknown-value capital is its own statement
        k = (r["s"], "?", r["start"], r["end"], k[4])
    e = st[k]
    e["capL"] = r["capL"]
    pt = point(r["coord"])
    if pt:
        e["coords"].add(pt)

out = []
for (s, cap, start, end, rank), e in st.items():
    cs = sorted(e["coords"])
    out.append({"s": s, "cap": cap, "capL": e["capL"] or "", "start": year(start), "end": year(end),
                "start_date": date(start), "end_date": date(end), "rank": rank,
                "lat": cs[0][0] if cs else None, "lon": cs[0][1] if cs else None, "n_coords": len(cs)})
for s in states.values():
    inc = [y for y in s["inc"] if isinstance(y, int)]
    dis = [y for y in s["dis"] if isinstance(y, int)]
    s["inc"] = min(inc) if inc else ("?" if "?" in s["inc"] else None)
    s["dis"] = max(dis) if dis else ("?" if "?" in s["dis"] else None)
    s["types"] = sorted(s["types"])
jsave(states, f"{WORK}/states.json")
jsave(out, f"{WORK}/statements.json")
n_unknown = sum(1 for x in out if x["cap"] == "?")
print("states", len(states), "statements", len(out), "unknown-value capitals", n_unknown,
      "with start", sum(1 for x in out if x["start"] not in (None,)), "with end", sum(1 for x in out if x["end"] not in (None,)),
      "deprecated", sum(1 for x in out if x["rank"] == "deprecated"), "no coords", sum(1 for x in out if x["lat"] is None and x["cap"] != "?"))
