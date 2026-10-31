"""Apply the hand edits (code/overrides.py) to the automatic moves, merge duplicates, classify and measure every move.

Steps: drop wrong automatic moves; fix years and cities; add moves Wikidata lacks; set aside renamings ("same place");
merge the same move recorded on several Wikidata items (both ends within 10 km, years within 3); keep 1500 onwards;
order each state's moves and mark temporary ones (the capital was back where it started within 10 years, or the new seat
was held for less than a year, or a wartime seat listed in overrides.TEMPORARY); measure great-circle distance and
initial bearing; place each capital in a present-day country (Natural Earth) and measure its distance from the sea
(Natural Earth land). Writes data/moves.csv, data/manual_edits.csv, data/same_place.csv, data/planned.csv and
WORK/moves.json."""
import csv
import numpy as np
from collections import Counter, defaultdict
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
from common import *
import overrides as O

S = jload(f"{WORK}/states.json")
T = jload(f"{WORK}/statements.json")
AUTO = jload(f"{WORK}/auto_moves.json")
SAME = jload(f"{WORK}/auto_same.json")

LINEAGE = {}
for key, qs in {"PT": "Q45670 Q200464 Q903779 Q45", "RU": "Q4304392 Q186096 Q34266 Q2305208 Q2184 Q159", "ROC": "Q13426199 Q865 Q2308761",
                "BR": "Q155 Q210542", "HU": "Q171150 Q253094 Q16056854 Q25395037", "ES": "Q29 Q80702 Q600093", "IT": "Q38 Q172579",
                "GR": "Q41 Q209065", "FI": "Q33 Q62633", "FR": "Q142 Q70972", "JP": "Q17 Q188712", "PK": "Q843 Q2342822",
                "SY": "Q139708 Q12183911", "TG": "Q23039102 Q519718", "PR": "Q38872 Q27306", "PL": "Q172107 Q36 Q8890160",
                "DE": "Q183", "US": "Q30"}.items():
    for q in qs.split():
        LINEAGE[q] = key
edits = []   # rows for data/manual_edits.csv


def lab(q, l):
    return O.LABELS.get(q) or O.LABELS.get(l) or l


# ---------- 1. drops ----------
def match(m, q, f, t, y):
    return m["q"] == q and (f == "*" or m["from"] == f) and (t == "*" or m["to"] == t) and (y is None or m["year"] == y)


moves = []
used = Counter()
for m in AUTO:
    hit = [d for d in O.DROPS if match(m, d[0], d[1], d[2], d[3])]
    if hit:
        d = hit[0]; used[d] += 1
        if m["year"] >= FIRST_YEAR:
            edits.append({"action": "drop", "state": m["state"], "state_qid": m["q"], "from": m["from"], "to": m["to"], "year": m["year"],
                          "change": "removed", "reason": d[4], "source": d[5]})
        continue
    moves.append(dict(m, basis="wikidata", note="", source="", checked=False))
for d in O.DROPS:
    assert used[d], ("drop not used", d)

# ---------- 2. fixes ----------
for (q, f, t, y), new, reason, src in O.FIXES:
    hit = [m for m in moves if match(m, q, f, t, y)]
    assert len(hit) == 1, (q, f, t, y, len(hit))
    m = hit[0]
    ch = []
    for k, v in new.items():
        if k == "year":
            ch.append(f"year {m['year']} to {v}"); m["year"] = v
        else:   # from / to replaced by another of the same state's capitals
            c = next(x for x in T if x["s"] == q and x["capL"] == v and x["lat"] is not None)
            ch.append(f"{k} {m[k]} to {v}")
            m[k], m[k + "_q"], m[k + "_lat"], m[k + "_lon"] = v, c["cap"], c["lat"], c["lon"]
            m["km"] = round(gc_km(m["from_lat"], m["from_lon"], m["to_lat"], m["to_lon"]), 1)
    m["checked"] = True; m["source"] = src; m["note"] = reason if not new else reason
    m["basis"] = "wikidata, corrected" if new else "wikidata, checked"
    edits.append({"action": "fix" if new else "check", "state": m["state"], "state_qid": q, "from": f, "to": t, "year": y,
                  "change": "; ".join(ch) if ch else "none (confirmed)", "reason": reason, "source": src})

# ---------- 3. additions ----------
for i, (st, q, ctry, f, fll, t, tll, y, note, src) in enumerate(O.ADDS):
    s = S.get(q, {}) if q else {}
    moves.append({"q": q or "", "state": st, "types": s.get("types", []), "inc": s.get("inc"), "dis": s.get("dis"),
                  "from_q": "", "from": f, "from_lat": fll[0], "from_lon": fll[1], "to_q": "", "to": t, "to_lat": tll[0], "to_lon": tll[1],
                  "year": y, "km": round(gc_km(*fll, *tll), 1), "conf": "added by hand from a cited source", "basis": "added by hand",
                  "note": note, "source": src, "checked": True, "country": ctry if not q or q not in S else None, "seq": i})
    edits.append({"action": "add", "state": st, "state_qid": q or "", "from": f, "to": t, "year": y, "change": "added",
                  "reason": note, "source": src})
# Wikidata items for the cities added by hand, where the dump has them
qid_of = {}
for x in T:
    if x["lat"] is not None and x["capL"]:
        qid_of.setdefault(x["capL"], x["cap"])
for m in moves:
    for k in ("from", "to"):
        if not m[k + "_q"]:
            base = m[k].split(" (")[0]
            m[k + "_q"] = qid_of.get(m[k], qid_of.get(base, ""))

# ---------- 4. same place ----------
pairs = {frozenset(p) for p in O.SAME_CITY}
same_rows = []
keep = []
for m in moves + [dict(x, basis="wikidata", note="", source="", checked=False) for x in SAME]:
    if m["km"] < 2 or frozenset((m["from"], m["to"])) in pairs:
        if m["year"] >= FIRST_YEAR:
            same_rows.append({"state": m["state"], "state_qid": m["q"], "from": m["from"], "to": m["to"], "year": m["year"], "km": m["km"],
                              "why": "same city under another name or item" if frozenset((m["from"], m["to"])) in pairs else "under 2 km apart"})
    elif m in moves:
        keep.append(m)
    elif m["year"] >= FIRST_YEAR:   # a short real move (2 to 10 km) that 02 had set aside
        keep.append(m)
moves = keep
# the same-city pairs from the hand list are logged once
for p in O.SAME_CITY:
    edits.append({"action": "same place", "state": "", "state_qid": "", "from": p[0], "to": p[1], "year": "", "change": "not counted as a move",
                  "reason": "Two names or two Wikidata items for the same city.", "source": "https://www.wikidata.org/"})

# ---------- 5. labels ----------
for m in moves:
    for k in ("from", "to"):
        old = m[k]
        m[k + "_wd"] = old
        m[k] = lab(m[k + "_q"], old) if m["basis"] != "added by hand" else old
for l, new in sorted({(k, v) for k, v in O.LABELS.items() if ":" not in k}):
    edits.append({"action": "label", "state": "", "state_qid": "", "from": l, "to": new, "year": "", "change": f"shown as {new}",
                  "reason": "Clearer or more usual English name for display; the Wikidata item is unchanged.",
                  "source": O.LABEL_SRC.get(new, "https://www.wikidata.org/")})

# ---------- 6. merge duplicates ----------
RANK = {"added by hand from a cited source": 0, "both ends dated": 1, "old capital's end not recorded": 2, "new capital's start not recorded": 3, "gap between the two": 4}
def prio(m):
    present = ("country" in m["types"] or "sovereign state" in m["types"]) and m["dis"] in (None, "")
    return (0 if m["basis"] == "added by hand" else 1 if m["checked"] else 2, RANK[m["conf"]], 0 if present else 1, m["state"])
near = lambda a, b, k: gc_km(a[k + "_lat"], a[k + "_lon"], b[k + "_lat"], b[k + "_lon"]) < 10
moves.sort(key=prio)
merged = []
for m in moves:
    d = next((x for x in merged if near(x, m, "from") and near(x, m, "to") and abs(x["year"] - m["year"]) <= 3), None)
    if d is None:
        m["also"] = []; merged.append(m)
    elif m["state"] != d["state"] and m["state"] not in d["also"]:
        d["also"].append(m["state"])
        if m["year"] != d["year"] and m["year"] >= FIRST_YEAR:
            edits.append({"action": "merge", "state": m["state"], "state_qid": m["q"], "from": m["from_wd"], "to": m["to_wd"], "year": m["year"],
                          "change": f"merged into {d['state']} {d['year']}", "reason": "Same move recorded on another Wikidata item with a different year.",
                          "source": d["source"] or "https://www.wikidata.org/"})
moves = [m for m in merged if m["year"] >= FIRST_YEAR]
n_auto_dups = len([m for m in AUTO if m["year"] >= FIRST_YEAR])

# ---------- 7. countries ----------
NE = [f for f in jload(NE50)["features"]]
NG = [shape(f["geometry"]) for f in NE]
NN = [f["properties"]["ADMIN"] for f in NE]
NT = STRtree(NG)
FIXNAME = {"United States of America": "United States", "Republic of Serbia": "Serbia", "United Republic of Tanzania": "Tanzania",
           "Republic of the Congo": "Republic of the Congo", "Czech Republic": "Czechia", "The Bahamas": "Bahamas"}


def country_at(lat, lon):
    p = Point(lon, lat)
    for i in NT.query(p):
        if NG[i].contains(p):
            return FIXNAME.get(NN[i], NN[i])
    i = NT.nearest(p)
    return FIXNAME.get(NN[i], NN[i]) if NG[i].distance(p) < .5 else None


caps_of = defaultdict(list)
for x in T:
    if x["lat"] is not None and x["rank"] != "deprecated":
        caps_of[x["s"]].append(x)
st_country = {}
for q, xs in caps_of.items():
    c = Counter(country_at(x["lat"], x["lon"]) for x in xs)
    c.pop(None, None)
    if c:
        best = max(c.values())
        tops = [k for k, v in c.items() if v == best]
        last = max(xs, key=lambda x: (x["start"] if isinstance(x["start"], int) else -9999, x["rank"] == "preferred"))
        lc = country_at(last["lat"], last["lon"])
        st_country[q] = lc if lc in tops else sorted(tops)[0]
for m in moves:
    m["from_country"] = country_at(m["from_lat"], m["from_lon"])
    m["to_country"] = country_at(m["to_lat"], m["to_lon"])
    if not m.get("country"):
        m["country"] = st_country.get(m["q"]) or m["to_country"]
# names a reader would look for: the Wikidata label for present-day countries
CNAME = {"Q30": "United States"}

# ---------- 8. order, temporary moves ----------
lin = lambda m: LINEAGE.get(m["q"], m["q"] or m["state"])
groups = defaultdict(list)
for m in moves:
    groups[lin(m)].append(m)
for g in groups.values():
    out = []
    for y in sorted({m["year"] for m in g}):
        ys = [m for m in g if m["year"] == y]
        if len(ys) > 1:   # chain same-year moves: the first is the one whose start is not another's end
            chain, rest = [], ys[:]
            cur = next((m for m in rest if not any(gc_km(o["to_lat"], o["to_lon"], m["from_lat"], m["from_lon"]) < 10 for o in rest if o is not m)), rest[0])
            while rest:
                chain.append(cur); rest.remove(cur)
                nxt = [m for m in rest if gc_km(cur["to_lat"], cur["to_lon"], m["from_lat"], m["from_lon"]) < 10]
                cur = nxt[0] if nxt else (rest[0] if rest else None)
            ys = chain
        out += ys
    for i, m in enumerate(out):
        m["order"] = i
        m["temp"] = ""
    for i, m in enumerate(out):
        nxt = out[i + 1] if i + 1 < len(out) else None
        if nxt and nxt["year"] == m["year"] and gc_km(m["to_lat"], m["to_lon"], nxt["from_lat"], nxt["from_lon"]) < 10:
            m["temp"] = "new seat held for less than a year"
        elif (m["q"], m["year"]) in O.TEMPORARY:
            m["temp"] = "wartime, exile or crisis seat"
    for i, m in enumerate(out):
        for j in range(i + 1, len(out)):
            if out[j]["year"] - m["year"] > 10:
                break
            if gc_km(out[j]["to_lat"], out[j]["to_lon"], m["from_lat"], m["from_lon"]) < 10:
                for k in range(i, j + 1):
                    out[k]["temp"] = out[k]["temp"] or "there and back within 10 years"
                break

# ---------- 9. geography: bearing, the sea, the centre ----------
LAND = [shape(f["geometry"]) for f in jload(LAND50)["features"]]
pts = []
for g in LAND:
    for p in (g.geoms if g.geom_type == "MultiPolygon" else [g]):
        if p.area < .02:   # small islands do not count as "the sea" for a mainland capital, but island states keep their coast
            pass
        pts.append(np.asarray(p.exterior.coords))
C = np.vstack(pts)
lat, lon = np.radians(C[:, 1]), np.radians(C[:, 0])
XYZ = np.column_stack([np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)])


def coast_km(la, lo):
    a, b = math.radians(la), math.radians(lo)
    v = np.array([math.cos(a) * math.cos(b), math.cos(a) * math.sin(b), math.sin(a)])
    d = np.clip(XYZ @ v, -1, 1).max()
    return round(6371.0088 * math.acos(d), 1)


CEN = {}
for f, g, n in zip(NE, NG, NN):
    big = max(g.geoms, key=lambda p: p.area) if g.geom_type == "MultiPolygon" else g
    CEN[FIXNAME.get(n, n)] = (big.centroid.y, big.centroid.x)
for m in moves:
    b = bearing(m["from_lat"], m["from_lon"], m["to_lat"], m["to_lon"])
    m["bearing"] = round(b)
    m["direction"] = compass(b)
    m["from_coast_km"] = coast_km(m["from_lat"], m["from_lon"])
    m["to_coast_km"] = coast_km(m["to_lat"], m["to_lon"])
    c = m["from_country"]
    if c and c == m["to_country"] and c in CEN:
        cy, cx = CEN[c]
        m["centre_change_km"] = round(gc_km(m["to_lat"], m["to_lon"], cy, cx) - gc_km(m["from_lat"], m["from_lon"], cy, cx), 1)
    else:
        m["centre_change_km"] = None
    pb = O.PURPOSE_BUILT.get(m["to_wd"]) or O.PURPOSE_BUILT.get(m["to"])
    m["purpose_built"] = bool(pb)
    m["pb_note"] = pb[1] if pb else ""
    m["pb_source"] = pb[2] if pb else ""
    m["kind"] = "temporary" if m["temp"] else "lasting"
    m["confidence"] = "checked" if m["checked"] else "high" if m["conf"] == "both ends dated" else "low" if m["conf"] == "gap between the two" else "medium"
    fs, ts = m.get("from_span") or [None, None], m.get("to_span") or [None, None]
    span = lambda a: (f"from {a[0]} to {a[1]}" if a[0] and a[1] else f"until {a[1]}" if a[1] else f"from {a[0]}" if a[0] else "(no dates)")
    m["gen"] = f"Wikidata records {m['from']} as a capital of {m['state']} {span(fs)}, and {m['to']} {span(ts)}." if m["basis"] != "added by hand" else m["note"]
    if not m["note"]:
        m["note"] = m["gen"]
        if m["conf"] != "both ends dated":
            m["note"] += {"old capital's end not recorded": f" The end of {m['from']}'s time as capital is not recorded, so the move is dated by the start of {m['to']}'s.",
                          "new capital's start not recorded": f" The start of {m['to']}'s time as capital is not recorded, so the move is dated by the end of {m['from']}'s.",
                          "gap between the two": " There is a gap between the two in Wikidata, so this may not be a direct move."}[m["conf"]]

moves.sort(key=lambda m: (m["year"], lin(m), m["order"]))
for i, m in enumerate(moves):
    m["id"] = f"m{i:03d}"

COLS = ["id", "year", "state", "state_qid", "country", "from", "from_qid", "from_lat", "from_lon", "to", "to_qid", "to_lat", "to_lon",
        "km", "bearing", "direction", "kind", "temporary_why", "confidence", "basis", "checked", "purpose_built", "from_coast_km", "to_coast_km",
        "centre_change_km", "also_recorded_for", "note", "source"]
with open(f"{DATA}/moves.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(COLS)
    for m in moves:
        w.writerow(dash([m["id"], m["year"], m["state"], m["q"], m["country"], m["from"], m["from_q"], m["from_lat"], m["from_lon"], m["to"], m["to_q"],
                         m["to_lat"], m["to_lon"], m["km"], m["bearing"], m["direction"], m["kind"], m["temp"], m["confidence"], m["basis"],
                         "yes" if m["checked"] else "no", "yes" if m["purpose_built"] else "no", m["from_coast_km"], m["to_coast_km"],
                         "" if m["centre_change_km"] is None else m["centre_change_km"], "; ".join(m["also"]), m["note"], m["source"]]))
EC = ["action", "state", "state_qid", "from", "to", "year", "change", "reason", "source"]
with open(f"{DATA}/manual_edits.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, EC)
    w.writeheader()
    for e in edits:
        w.writerow(dash(e))
with open(f"{DATA}/same_place.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, ["state", "state_qid", "from", "to", "year", "km", "why"])
    w.writeheader()
    for e in sorted(same_rows, key=lambda e: e["year"]):
        w.writerow(dash(e))
with open(f"{DATA}/planned.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["state", "from", "from_lat", "from_lon", "to", "to_lat", "to_lon", "km", "status_2026", "sources"])
    for p in O.PLANNED:
        w.writerow(dash([p["state"], p["from"], *p["from_ll"], p["to"], *p["to_ll"], round(gc_km(*p["from_ll"], *p["to_ll"]), 1), p["status"], " ".join(p["sources"])]))
jsave({"moves": moves, "edits": edits, "same": same_rows, "auto_since_1500": n_auto_dups, "st_country": st_country}, f"{WORK}/moves.json")
print("moves", len(moves), "temporary", sum(m["kind"] == "temporary" for m in moves), "edits", Counter(e["action"] for e in edits),
      "same", len(same_rows), "conf", Counter(m["confidence"] for m in moves))
