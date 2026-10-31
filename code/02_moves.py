"""Derive capital moves automatically from the Wikidata statements (before any hand edits).

For each state, every capital statement that is not deprecated and names a known, located city becomes a spell with a
start year and an end year (either may be missing). A move is read from the spells in two ways:

  A. A spell B starts in year t. The old capital A is the other city whose spell ends within two years of t ("both ends
     dated"), or, failing that, the city whose spell began before t and has no end ("old capital's end not recorded").
     Failing both, the city whose spell ended most recently before t, within 30 years ("gap between the two").
     A city whose spell runs on more than two years past t is a co-capital, not a capital that was left.
  B. A spell A ends in year t and no move was found at t. The new capital is a city with no start date that runs on
     past t, the preferred-rank one if there are several ("new capital's start not recorded").

Moves under SAME_PLACE_KM (renamings such as Edo to Tokyo, or a city and its own district) are kept apart as
"same place". Statements with no dates at all cannot be placed in time; states with several capitals but no dates are
counted. Writes WORK/auto_moves.json, WORK/auto_log.json."""
from collections import defaultdict
from common import *

S = jload(f"{WORK}/states.json")
T = jload(f"{WORK}/statements.json")
by = defaultdict(list)
for t in T:
    by[t["s"]].append(t)

alive = lambda s: not (isinstance(s["dis"], int) and s["dis"] < FIRST_YEAR)
iy = lambda v: v if isinstance(v, int) else None
moves, same, log = [], [], {"undated_multi": [], "ambiguous_end": [], "unknown_cap": 0, "deprecated": 0, "no_coord": 0}

for q, ts in by.items():
    s = S[q]
    if not alive(s):
        continue
    sp = []
    for t in ts:
        if t["cap"] == "?":
            log["unknown_cap"] += 1; continue
        if t["rank"] == "deprecated":
            log["deprecated"] += 1; continue
        if t["lat"] is None:
            log["no_coord"] += 1; continue
        sp.append({**t, "a": iy(t["start"]), "b": iy(t["end"])})
    caps = {x["cap"] for x in sp}
    if len(caps) < 2:
        continue
    if all(x["a"] is None and x["b"] is None for x in sp):
        log["undated_multi"].append({"q": q, "label": s["label"], "caps": sorted({x["capL"] for x in sp})})
        continue
    dist = lambda A, B: gc_km(A["lat"], A["lon"], B["lat"], B["lon"])
    found = []
    for B in sp:
        t = B["a"]
        if t is None:
            continue
        others = [A for A in sp if A["cap"] != B["cap"] and dist(A, B) >= 0]
        c1 = [A for A in others if A["b"] is not None and abs(A["b"] - t) <= 2 and (A["a"] is None or A["a"] < t)]
        c2 = [A for A in others if A["b"] is None and A["a"] is not None and A["a"] < t]
        c3 = [A for A in others if A["b"] is not None and t - 30 <= A["b"] < t - 2]
        if c1:
            A, conf = min(c1, key=lambda A: (abs(A["b"] - t), -(A["a"] or -9999))), "both ends dated"
        elif c2:
            A, conf = max(c2, key=lambda A: A["a"]), "old capital's end not recorded"
        elif c3:
            A, conf = max(c3, key=lambda A: A["b"]), "gap between the two"
        else:
            continue
        found.append((A, B, t, conf))
    used = {(A["cap"], t) for A, B, t, _ in found}
    for A in sp:
        t = A["b"]
        if t is None or any(c == A["cap"] and abs(y - t) <= 2 for c, y in used):
            continue
        if any(B["a"] is not None and abs(B["a"] - t) <= 2 and B["cap"] != A["cap"] for B in sp):
            continue
        cand = [B for B in sp if B["cap"] != A["cap"] and B["a"] is None and (B["b"] is None or B["b"] > t + 2)]
        if len(cand) > 1:
            pref = [B for B in cand if B["rank"] == "preferred"]
            if len(pref) == 1:
                cand = pref
            else:
                log["ambiguous_end"].append({"q": q, "label": s["label"], "from": A["capL"], "year": t, "cands": [B["capL"] for B in cand]})
                continue
        if cand:
            found.append((A, cand[0], t, "new capital's start not recorded"))
    for A, B, t, conf in found:
        d = dist(A, B)
        m = {"q": q, "state": s["label"] or q, "types": s["types"], "inc": s["inc"], "dis": s["dis"],
             "from_q": A["cap"], "from": A["capL"], "from_lat": A["lat"], "from_lon": A["lon"],
             "to_q": B["cap"], "to": B["capL"], "to_lat": B["lat"], "to_lon": B["lon"],
             "year": t, "km": round(d, 1), "conf": conf, "from_rank": A["rank"], "to_rank": B["rank"],
             "from_span": [A["a"], A["b"]], "to_span": [B["a"], B["b"]]}
        if A["cap"] == B["cap"]:
            continue
        (same if d < SAME_PLACE_KM else moves).append(m)

moves.sort(key=lambda m: (m["year"], m["state"]))
jsave(moves, f"{WORK}/auto_moves.json")
jsave(same, f"{WORK}/auto_same.json")
jsave(log, f"{WORK}/auto_log.json")
post = [m for m in moves if m["year"] >= FIRST_YEAR]
print("auto moves", len(moves), "since 1500", len(post), "same place", len(same), "undated multi-capital states", len(log["undated_multi"]),
      "ambiguous", len(log["ambiguous_end"]), {k: v for k, v in log.items() if isinstance(v, int)})
