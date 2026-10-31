"""Every number used anywhere (page, paper, blog, collage, post) goes into data/results.json; page data into
data/site.json; arcs for reuse into data/moves.geojson."""
import statistics as stt
from collections import Counter, defaultdict
from common import *
import overrides as O

D = jload(f"{WORK}/moves.json")
M = D["moves"]
S = jload(f"{WORK}/states.json")
T = jload(f"{WORK}/statements.json")
LOG = jload(f"{WORK}/auto_log.json")
L = [m for m in M if m["kind"] == "lasting"]
R = {"retrieved": RETRIEVED, "first_year": FIRST_YEAR, "last_year": max(m["year"] for m in M)}

# ---------- the raw data ----------
alive = [q for q, s in S.items() if not (isinstance(s["dis"], int) and s["dis"] < FIRST_YEAR)]
R["raw"] = {"states": len(S), "statements": len(T), "states_since_1500": len(alive),
            "statements_dated": sum(1 for t in T if isinstance(t["start"], int) or isinstance(t["end"], int)),
            "unknown_value": sum(1 for t in T if t["cap"] == "?"), "deprecated": sum(1 for t in T if t["rank"] == "deprecated"),
            "undated_multi": len(LOG["undated_multi"]), "auto_moves": D["auto_since_1500"]}
R["raw"]["dated_pct"] = round(100 * R["raw"]["statements_dated"] / len(T), 1)
present = [q for q, s in S.items() if "sovereign state" in s["types"] and s["dis"] in (None, "")]
by_state = defaultdict(set)
for t in T:
    if t["cap"] != "?" and t["rank"] != "deprecated":
        by_state[t["s"]].add(t["cap"])
R["raw"]["sovereign_now"] = len(present)
R["raw"]["sovereign_one_capital"] = sum(1 for q in present if len(by_state[q]) <= 1)
R["raw"]["sovereign_one_capital_pct"] = round(100 * R["raw"]["sovereign_one_capital"] / len(present))

# ---------- edits ----------
E = Counter(e["action"] for e in D["edits"])
R["edits"] = {"n": sum(v for k, v in E.items() if k in ("drop", "fix", "add", "check", "merge")), "drop": E["drop"], "fix": E["fix"],
              "add": E["add"], "check": E["check"], "merge": E["merge"], "label": E["label"], "same_pairs": E["same place"],
              "rows": len(D["edits"]), "same_place_rows": len(D["same"])}

# ---------- counts ----------
R["n"] = len(M); R["n_lasting"] = len(L); R["n_temp"] = len(M) - len(L)
R["n_states"] = len({m["q"] or m["state"] for m in M}); R["n_countries"] = len({m["country"] for m in M})
conf = Counter(m["confidence"] for m in M)
R["conf"] = {k: conf.get(k, 0) for k in ("checked", "high", "medium", "low")}
R["basis"] = dict(Counter(m["basis"] for m in M))
R["n_added"] = R["basis"].get("added by hand", 0)
R["n_from_wikidata"] = R["n"] - R["n_added"]
cent = []
for c, name, col in CENTURIES:
    ms = [m for m in M if century(m["year"]) == c]
    cent.append({"c": c, "name": name, "col": col, "n": len(ms), "lasting": sum(m["kind"] == "lasting" for m in ms),
                 "temp": sum(m["kind"] == "temporary" for m in ms), "added": sum(m["basis"] == "added by hand" for m in ms),
                 "median_km": round(stt.median([m["km"] for m in ms])) if ms else 0})
R["by_century"] = cent
top_c = max(cent, key=lambda c: c["n"])
R["top_century"] = {"name": top_c["name"], "n": top_c["n"], "lasting": top_c["lasting"]}
R["c20"] = next(c for c in cent if c["c"] == 1900)
R["c21"] = next(c for c in cent if c["c"] == 2000)
dec = Counter(m["year"] // 10 * 10 for m in M)
decL = Counter(m["year"] // 10 * 10 for m in L)
R["by_decade"] = [{"d": d, "n": dec.get(d, 0), "lasting": decL.get(d, 0)} for d in range(1500, 2030, 10)]
bd = max(R["by_decade"], key=lambda x: (x["n"], x["d"]))
R["busiest_decade"] = bd
yrs = Counter(m["year"] for m in M)
R["busiest_year"] = {"y": max(yrs, key=lambda y: (yrs[y], y)), "n": max(yrs.values())}

# ---------- distance ----------
def brief(m):
    return {"id": m["id"], "state": m["state"], "country": m["country"], "from": m["from"], "to": m["to"], "year": m["year"],
            "km": round(m["km"]), "kind": m["kind"], "direction": m["direction"], "confidence": m["confidence"]}
srt = sorted(M, key=lambda m: -m["km"])
R["longest"] = [brief(m) for m in srt if not (m["from"] == "Rio de Janeiro" and m["to"] == "Lisbon")][:12]
R["longest_lasting"] = [brief(m) for m in sorted(L, key=lambda m: -m["km"])][:12]
R["shortest_lasting"] = [brief(m) for m in sorted(L, key=lambda m: m["km"])][:5]
R["median_km"] = round(stt.median(m["km"] for m in M))
R["median_km_lasting"] = round(stt.median(m["km"] for m in L))
R["mean_km_lasting"] = round(stt.mean(m["km"] for m in L))
R["over_500_lasting"] = sum(m["km"] >= 500 for m in L)
R["under_100_lasting"] = sum(m["km"] < 100 for m in L)
R["under_100_lasting_pct"] = round(100 * R["under_100_lasting"] / len(L))
R["over_1000"] = sum(m["km"] >= 1000 for m in M)
lr = next(m for m in M if m["from"] == "Lisbon" and m["to"] == "Rio de Janeiro")
R["lisbon_rio"] = {"km": round(lr["km"]), "year": lr["year"], "ratio_second": round(lr["km"] / R["longest"][1]["km"], 1)}
b = [0, 50, 100, 250, 500, 1000, 2000, 10000]
R["km_bins"] = [{"a": b[i], "b": b[i + 1], "n": sum(b[i] <= m["km"] < b[i + 1] for m in M), "lasting": sum(b[i] <= m["km"] < b[i + 1] for m in L)} for i in range(len(b) - 1)]

# ---------- direction, the sea, the centre ----------
R["direction"] = {d: sum(m["direction"] == d for m in L) for d in COMPASS}
modern = [m for m in L if m["year"] >= 1900]
inland = [m for m in modern if m["from_coast_km"] <= 50 and m["to_coast_km"] - m["from_coast_km"] >= 50]
seaward = [m for m in modern if m["to_coast_km"] <= 50 and m["from_coast_km"] - m["to_coast_km"] >= 50]
R["sea"] = {"modern_n": len(modern), "inland_n": len(inland), "inland_pct": round(100 * len(inland) / len(modern)), "seaward_n": len(seaward),
            "inland": [brief(m) | {"from_coast": round(m["from_coast_km"]), "to_coast": round(m["to_coast_km"])} for m in inland],
            "seaward": [brief(m) for m in seaward],
            "early_n": len([m for m in L if m["year"] < 1900]),
            "early_inland_n": len([m for m in L if m["year"] < 1900 and m["from_coast_km"] <= 50 and m["to_coast_km"] - m["from_coast_km"] >= 50])}
R["sea"]["early_inland_pct"] = round(100 * R["sea"]["early_inland_n"] / R["sea"]["early_n"])
cm = [m for m in modern if m["centre_change_km"] is not None]
closer = [m for m in cm if m["centre_change_km"] < -25]
further = [m for m in cm if m["centre_change_km"] > 25]
R["centre"] = {"n": len(cm), "closer": len(closer), "further": len(further), "closer_pct": round(100 * len(closer) / len(cm)),
               "brasilia": round(-next(m for m in M if m["to"] == "Brasília")["centre_change_km"]),
               "abuja": round(-next(m for m in M if m["to"] == "Abuja")["centre_change_km"])}

# ---------- who moved most ----------
cc = Counter(m["country"] for m in M); ccl = Counter(m["country"] for m in L)
R["countries"] = [{"name": k, "n": v, "lasting": ccl.get(k, 0), "states": len({m["state"] for m in M if m["country"] == k})} for k, v in sorted(cc.items(), key=lambda kv: (-kv[1], -ccl.get(kv[0], 0), kv[0]))][:15]
lin = Counter(); linname = {}
for m in M:
    k = m["q"] or m["state"]
    lin[k] += 1; linname.setdefault(k, m["state"])
R["states_most"] = [{"name": linname[k], "q": k, "n": v, "lasting": sum(1 for m in L if (m["q"] or m["state"]) == k)} for k, v in lin.most_common(10)]
R["us"] = {"n": sum(1 for m in M if m["state"] == "United States"), "first": min(m["year"] for m in M if m["state"] == "United States"),
           "last": max(m["year"] for m in M if m["state"] == "United States"), "lasting": sum(1 for m in L if m["state"] == "United States"),
           "cities": len({m["to"] for m in M if m["state"] == "United States"})}
roc = [m for m in M if m["state"] == "Republic of China"]
R["roc"] = {"n": len(roc), "y1949": sum(m["year"] == 1949 for m in roc)}
R["canada"] = {"n": sum(1 for m in M if m["state"] == "Province of Canada")}
R["germany"] = {"n": cc["Germany"], "states": len({m["state"] for m in M if m["country"] == "Germany"})}
R["n_countries_two_plus"] = sum(1 for v in cc.values() if v >= 2)

# ---------- purpose-built ----------
pb = [m for m in L if m["purpose_built"]]
seen = set(); PB = []
for m in sorted(pb, key=lambda m: m["year"]):
    if m["to"] in seen:
        continue
    seen.add(m["to"])
    w = O.PURPOSE_BUILT.get(m["to_wd"]) or O.PURPOSE_BUILT.get(m["to"])
    PB.append({"to": m["to"], "state": m["state"], "country": m["country"], "year": m["year"], "founded": w[0], "km": round(m["km"]), "note": w[1], "id": m["id"],
               "from_coast": round(m["from_coast_km"]), "to_coast": round(m["to_coast_km"])})
R["purpose_built"] = PB
R["n_purpose_built"] = len(PB)
R["n_pb_since_1900"] = sum(p["year"] >= 1900 for p in PB)
R["pb_since_1900_share"] = round(100 * R["n_pb_since_1900"] / len([m for m in modern]))
R["pb_inland_since_1900"] = sum(p["year"] >= 1900 and p["to_coast"] - p["from_coast"] >= 50 for p in PB)

# ---------- the famous moves, checked ----------
FAM = [("Rio de Janeiro", "Brasília"), ("Calcutta (Kolkata)", "Delhi (New Delhi from 1931)"), ("St Petersburg", "Moscow"), ("Istanbul", "Ankara"),
       ("Lagos", "Abuja"), ("Karachi", "Rawalpindi"), ("Rawalpindi", "Islamabad"), ("Almaty", "Astana"), ("Yangon", "Naypyidaw"),
       ("Dar es Salaam", "Dodoma"), ("Abidjan", "Yamoussoukro"), ("Berlin", "Bonn"), ("Bonn", "Berlin"), ("Melbourne", "Canberra"),
       ("Kyoto (Heian-kyō)", "Tokyo"), ("Lisbon", "Rio de Janeiro"), ("Rio de Janeiro", "Lisbon"), ("New York", "Philadelphia"),
       ("Philadelphia", "Washington"), ("Quebec City", "Ottawa"), ("Beijing", "Nanjing"), ("Nanjing", "Beijing"), ("Mukden (Shenyang)", "Beijing")]
fam = []
for f, t in FAM:
    ms = [m for m in M if m["from"] == f and m["to"] == t]
    assert ms, (f, t)
    for m in ms:
        st = "added by hand" if m["basis"] == "added by hand" else "corrected" if "corrected" in m["basis"] else "in Wikidata, checked"
        fam.append({"id": m["id"], "from": f, "to": t, "year": m["year"], "state": m["state"], "km": round(m["km"]), "status": st, "source": m["source"]})
R["famous"] = fam
R["famous_n"] = len(fam)
R["famous_in_wd"] = sum(1 for x in fam if x["status"] != "added by hand")
R["planned"] = [{"state": p["state"], "from": p["from"], "to": p["to"], "km": round(gc_km(*p["from_ll"], *p["to_ll"])), "status": p["status"], "sources": p["sources"]} for p in O.PLANNED]
eg = next(m for m in M if m["to"] == "Ciudad de la Paz")
R["latest"] = brief(eg)
R["first"] = brief(min(M, key=lambda m: (m["year"], m["order"])))
for k in ("brasilia", "abuja", "canberra", "astana", "naypyidaw", "ankara", "moscow"):
    pass
def mv(f, t):
    return brief(next(m for m in M if m["from"] == f and m["to"] == t))
R["ex"] = {"brasilia": mv("Rio de Janeiro", "Brasília"), "delhi": mv("Calcutta (Kolkata)", "Delhi (New Delhi from 1931)"), "moscow": mv("St Petersburg", "Moscow"),
           "stp": mv("Moscow", "St Petersburg"), "ankara": mv("Istanbul", "Ankara"), "abuja": mv("Lagos", "Abuja"), "astana": mv("Almaty", "Astana"),
           "naypyidaw": mv("Yangon", "Naypyidaw"), "canberra": mv("Melbourne", "Canberra"), "tokyo": mv("Kyoto (Heian-kyō)", "Tokyo"),
           "zanzibar": mv("Muscat", "Zanzibar (Stone Town)"), "taipei": mv("Chengdu", "Taipei"), "islamabad": mv("Rawalpindi", "Islamabad"),
           "karachi": mv("Karachi", "Rawalpindi"), "dodoma": mv("Dar es Salaam", "Dodoma"), "yam": mv("Abidjan", "Yamoussoukro"),
           "bonn": mv("Berlin", "Bonn"), "berlin": mv("Bonn", "Berlin"), "washington": mv("Philadelphia", "Washington"), "ottawa": mv("Quebec City", "Ottawa"),
           "belmopan": mv("Belize City", "Belmopan"), "salvador": mv("Salvador", "Rio de Janeiro"), "nanjing": mv("Beijing", "Nanjing"), "mukden": mv("Mukden (Shenyang)", "Beijing")}
R["meta"] = {"page": URL, "repo": REPO, "slug": SLUG}
jsave(R, f"{DATA}/results.json", indent=1)

# ---------- page data ----------
def story(m):
    """The note shown on the page: the hand-check reason without its 'Checked:' label, or Wikidata's own dates."""
    n = m["note"]
    if n.startswith("Checked (see above)"):
        return m["gen"]
    for p in ("Checked, with a caveat: ", "Checked: "):
        if n.startswith(p):
            n = n[len(p)].upper() + n[len(p) + 1:]
    return n



site = {"moves": [], "planned": [], "caps": []}
for m in M:
    site["moves"].append({"id": m["id"], "y": m["year"], "s": m["state"], "c": m["country"], "f": m["from"], "t": m["to"],
                          "fl": [round(m["from_lat"], 3), round(m["from_lon"], 3)], "tl": [round(m["to_lat"], 3), round(m["to_lon"], 3)],
                          "km": round(m["km"]), "d": m["direction"], "k": m["kind"][0], "tw": m["temp"], "cf": m["confidence"], "b": m["basis"],
                          "pb": 1 if m["purpose_built"] else 0, "pbn": m["pb_note"], "n": story(m), "src": m["source"], "q": m["q"],
                          "fq": m["from_q"], "tq": m["to_q"], "also": m["also"], "fc": round(m["from_coast_km"]), "tc": round(m["to_coast_km"]),
                          "g": gc_points(m["from_lat"], m["from_lon"], m["to_lat"], m["to_lon"], max(8, min(64, int(m["km"] / 60))))})
for p in O.PLANNED:
    site["planned"].append({"s": p["state"], "f": p["from"], "t": p["to"], "fl": list(p["from_ll"]), "tl": list(p["to_ll"]),
                            "km": round(gc_km(*p["from_ll"], *p["to_ll"])), "n": p["status"], "src": p["sources"],
                            "g": gc_points(*p["from_ll"], *p["to_ll"], 24)})
jsave(site, f"{DATA}/site.json")
gj = {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {k: m[k] for k in ("id", "year", "state", "country", "from", "to", "km", "direction", "kind", "confidence", "basis")},
       "geometry": {"type": "LineString", "coordinates": [[p[1], p[0]] for p in gc_points(m["from_lat"], m["from_lon"], m["to_lat"], m["to_lon"], 32)]}} for m in M]}
jsave(gj, f"{DATA}/moves.geojson")
print("results: n", R["n"], "lasting", R["n_lasting"], "by century", [(c["name"], c["n"], c["lasting"]) for c in cent])
print("longest", [(x["from"], x["to"], x["km"]) for x in R["longest"][:5]], "median", R["median_km"], R["median_km_lasting"])
print("sea", R["sea"]["inland_n"], "/", R["sea"]["modern_n"], "centre", R["centre"]["closer"], "/", R["centre"]["n"], "pb", R["n_purpose_built"], [p["to"] for p in PB])
print("countries", [(c["name"], c["n"], c["lasting"]) for c in R["countries"][:8]], "states", [(s["name"], s["n"]) for s in R["states_most"][:6]])
print("raw", R["raw"], "edits", R["edits"], "conf", R["conf"])
