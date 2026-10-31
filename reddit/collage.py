"""Reddit collage (r/dataisbeautiful style, light): world map of every capital move since 1500 with labels on open sea,
a decade timeline strip and a ranking of the longest moves. Labels are checked automatically: no label box may touch
land (Natural Earth 1:50m) or another label, and no leader line may cross another label. Run: python3 reddit/collage.py"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code"))
from figstyle import *
import matplotlib.patheffects as pe
from shapely.geometry import box as sbox, LineString
from shapely.ops import unary_union

R = jload(f"{DATA}/results.json")
M = jload(f"{WORK}/moves.json")["moves"]
OUT = os.path.join(ROOT, "reddit", "capitals_that_moved.png")
W_IN, H_IN, DPI = 28, 19.6, 100
fig = plt.figure(figsize=(W_IN, H_IN), dpi=DPI, facecolor="#FBF8F1")
PAPER = "#FBF8F1"
HALO = [pe.withStroke(linewidth=6, foreground=PAPER)]

# ---------- title ----------
fig.text(.03, .955, "Capitals that moved", fontproperties=DISP, fontsize=64, color=FG, va="top")
fig.text(.03, .895, f"Every move of a country's capital since 1500 that the open record knows about, famous ones checked by hand: {R['n']} moves by {R['n_states']} states.\n"
         f"Each arc runs from the old capital (hollow dot) to the new one (filled dot), coloured by century.", fontsize=20, color=FG, va="top", linespacing=1.45)

# ---------- map ----------
ax = fig.add_axes([0.0, .245, 1.0, .60]); ax.set_facecolor(PAPER)
EXT = (-1.45e7, 1.62e7, -5.6e6, 9.7e6)
world(ax, ext=EXT, land="#E8E0CF", ec="#FBF8F1", lw=.5)
for m in sorted(M, key=lambda m: (m["kind"] == "lasting", m["km"])):
    arc(ax, m, lw=2.6 if m["km"] < 3000 else 3.4, dot=34, alpha=.95)
P = R["planned"][0]
nus = next(p for p in jload(f"{DATA}/site.json")["planned"])
g = np.array(nus["g"]); x, y = xy(g[:, 1], g[:, 0]); ax.plot(x, y, color="#8A8378", lw=2.2, linestyle=(0, (1, 2.5)), zorder=4)

# Calcutta, Karachi, Istanbul, Quebec City and Yangon were tried too, but there is no open sea near enough for their labels.
LAB = [  # (from, to, label lon, lat, text lines, ha)
    ("Lisbon", "Rio de Janeiro", -33, 15, ["Lisbon → Rio de Janeiro 1808", "7,716 km, the longest:", "the court flees Napoleon"], "center"),
    ("St Petersburg", "Moscow", 45, 86, ["Moscow → St Petersburg 1712", "St Petersburg → Moscow 1918"], "center"),
    ("Dar es Salaam", "Dodoma", 50, -27, ["Dar es Salaam →", "Dodoma 1996"], "center"),
    ("Muscat", "Zanzibar (Stone Town)", 67, -12, ["Muscat → Zanzibar 1840", "longest lasting: 3,924 km"], "center"),
    ("Philadelphia", "Washington", -56, 33, ["Philadelphia →", "Washington 1800"], "center"),
    ("Rio de Janeiro", "Brasília", -26, -30, ["Rio de Janeiro → Brasília", "1960 · built in four years"], "center"),
    ("Chengdu", "Taipei", 145, 15, ["Chengdu → Taipei", "1949"], "center"),
    ("Melbourne", "Canberra", 165, -42, ["Melbourne → Canberra", "1927"], "center"),
    ("Lagos", "Abuja", -20, 2, ["Lagos → Abuja", "1991"], "center"),
    ("Malabo", "Ciudad de la Paz", 0, -12, ["Malabo → Ciudad", "de la Paz, 2026"], "center"),
    ("Kyoto (Heian-kyō)", "Tokyo", 158, 37, ["Kyoto → Tokyo", "1868"], "center"),
    ("Belize City", "Belmopan", -100, 12, ["Belize City → Belmopan", "1970"], "center"),
]
us_cities = {c for mm in M if mm["state"] == "United States" for c in (mm["from"], mm["to"])} - {"Washington"}
assert len(us_cities) == 8, us_cities
assert R["longest"][0]["km"] == 7716 and R["longest"][1]["km"] == 3924 and R["ex"]["delhi"]["km"] == 1305
fig.canvas.draw(); rend = fig.canvas.get_renderer()
inv = ax.transData.inverted()
from shapely.geometry import Polygon as SPoly
_LP = [SPoly(p).buffer(0) for p in land_parts()]
LANDU = unary_union([q.buffer(1.6e5) for q in _LP if q.area > 5e9] + [q.buffer(5e4) for q in _LP if q.area <= 5e9])   # 160 km margin round large land, 50 km round small islands
ARCS = []
for mm in M:
    gg = np.array(gc_points(mm["from_lat"], mm["from_lon"], mm["to_lat"], mm["to_lon"], 30)); ax_, ay_ = xy(gg[:, 1], gg[:, 0])
    ARCS.append((mm["id"], LineString(list(zip(ax_, ay_))).buffer(1.5e5)))
lw_, ly_ = .015, .40
(lgx0, lgy0) = inv.transform(ax.transAxes.transform((0, ly_ - 7.6 * .055)))
(lgx1, lgy1) = inv.transform(ax.transAxes.transform((.235, ly_ + .03)))
placed = [(sbox(lgx0, lgy0, lgx1, lgy1), "legend", LineString([(0, 0), (1, 1)]))]
NUS = (84, -22)
nx, ny = xy(*NUS); placed.append((sbox(nx - 1.9e6, ny - 4.5e5, nx + 1.9e6, ny + 4.5e5), "nusantara", LineString([(0, 0), (1, 1)])))
problems = []
TEXTS = []
for f, t, lo, la, lines, ha in LAB:
    m = next(mm for mm in M if mm["from"] == f and mm["to"] == t)
    X, Y = xy(lo, la)
    t1 = ax.text(X, Y, "\n".join(lines), ha="center", va="center", fontsize=13, color=FG, zorder=30, linespacing=1.22, path_effects=HALO)
    bb = t1.get_window_extent(rend)
    (x0, y0), (x1, y1) = inv.transform((bb.x0, bb.y0)), inv.transform((bb.x1, bb.y1))
    w2, h2 = (x1 - x0) / 2 + 6e4, (y1 - y0) / 2 + 6e4
    g = np.array(gc_points(m["from_lat"], m["from_lon"], m["to_lat"], m["to_lon"], 40)); gx, gy = xy(g[:, 1], g[:, 0])
    ARCLINE = LineString(list(zip(gx, gy)))
    best = None
    ARCU = unary_union([a for i, a in ARCS if i != m["id"]])
    for dx in np.arange(-7e6, 7.01e6, 1.6e5):
        for dy in np.arange(-4.4e6, 4.41e6, 1.2e5):
            cx, cy = X + dx, Y + dy
            if cx - w2 < EXT[0] or cx + w2 > EXT[1] or cy - h2 < EXT[2] or cy + h2 > EXT[3] - 2e5:
                continue
            B = sbox(cx - w2, cy - h2, cx + w2, cy + h2)
            if B.intersects(LANDU) or B.intersects(ARCU) or any(B.intersects(o[0]) for o in placed):
                continue
            from shapely.ops import nearest_points
            q = nearest_points(ARCLINE, sbox(cx - w2, cy - h2, cx + w2, cy + h2))
            ex, ey = q[0].x, q[0].y
            px, py = min(max(ex, cx - w2), cx + w2), min(max(ey, cy - h2), cy + h2)
            L = LineString([(px, py), (ex, ey)])
            if L.length > 2.2e6 or L.intersection(LANDU).length > 1.5e6:
                continue
            if any(L.crosses(o[0]) or L.within(o[0]) for o in placed) or any(L.intersects(o[2]) and L.length > 1.5e5 and o[2].length > 1.5e5 for o in placed):
                continue
            cost = L.length + .3 * np.hypot(cx - X, cy - Y) + (2e6 if L.length > 1.2e5 and L.intersects(ARCU) else 0)
            if best is None or cost < best[0]:
                best = (cost, cx, cy, B, L, px, py)
    if best is None:
        problems.append("no free spot for " + lines[0]); t1.remove(); continue
    _, cx, cy, B, L, px, py = best; ex, ey = L.coords[1]
    t1.set_position((cx, cy))
    if L.length > 1.2e5:
        ax.plot([px, ex], [py, ey], color="#8A8378", lw=1.1, zorder=25)
    placed.append((B, lines[0], L)); TEXTS.append((lines[0], t1))
TEXTS.append(("Nusantara note", ax.text(*xy(*NUS), "Jakarta → Nusantara (dotted):\nplanned, not made; Jakarta is\nstill the capital in 2026", ha="center", va="center", fontsize=12.5, color="#6F685E", style="italic", zorder=30, path_effects=HALO)))

# legend (on the sea, south Pacific)
lx, ly = .015, .40
for i, (c, n, col) in enumerate(CENTURIES):
    yy = ly - i * .055
    ax.plot([lx, lx + .03], [yy, yy], color=col, lw=6, transform=ax.transAxes, solid_capstyle="round")
    ax.text(lx + .038, yy, n, transform=ax.transAxes, va="center", fontsize=16, color=FG, path_effects=HALO)
yy = ly - 6 * .055
ax.plot([lx, lx + .03], [yy, yy], color=MUT, lw=3.5, transform=ax.transAxes, linestyle=(0, (2.5, 1.6)))
ax.text(lx + .038, yy, "temporary seat (war, crisis,\nor back within 10 years)", transform=ax.transAxes, va="center", fontsize=14, color=FG, path_effects=HALO)
yy -= .055
ax.scatter([lx + .008], [yy], s=90, facecolor=PAPER, edgecolor=FG, lw=1.8, transform=ax.transAxes)
ax.scatter([lx + .024], [yy], s=110, color=FG, transform=ax.transAxes)
ax.text(lx + .038, yy, "old capital, new capital", transform=ax.transAxes, va="center", fontsize=14, color=FG, path_effects=HALO)

# ---------- timeline strip ----------
bx = fig.add_axes([.04, .085, .50, .13]); bx.set_facecolor(PAPER)
for d in R["by_decade"]:
    col = CC[century(d["d"])]
    bx.bar(d["d"] + 5, d["lasting"], width=8.4, color=col)
    bx.bar(d["d"] + 5, d["n"] - d["lasting"], bottom=d["lasting"], width=8.4, color=col, alpha=.4)
bx.set_xlim(1497, 2032); bx.set_ylim(0, 20); bx.spines[["top", "right", "left"]].set_visible(False); bx.tick_params(left=False, labelsize=14)
bx.set_yticks([5, 10, 15]); bx.yaxis.grid(color=RULE); bx.set_axisbelow(True)
for yy, t in ((1712, "St Petersburg"), (1808, "Rio"), (1918, "Moscow")):
    bx.annotate(t, (yy, 0), xytext=(yy, 17), ha="center", fontsize=12.5, color=FG, arrowprops=dict(arrowstyle="-", color=MUT, lw=.8))
bx.text(1500, 21.5, f"Moves per decade (pale: temporary). Busiest century: the 20th, {R['c20']['n']} moves; busiest decade: the {R['busiest_decade']['d']}s, mostly wartime", fontsize=15.5, color=FG, fontweight="medium")

# ---------- ranking ----------
rx = fig.add_axes([.71, .085, .25, .13]); rx.set_facecolor(PAPER)
D = R["longest"][:7][::-1]
short = lambda s: s.replace(" (New Delhi from 1931)", "").replace("Calcutta (Kolkata)", "Calcutta").replace("Zanzibar (Stone Town)", "Zanzibar")
for i, d in enumerate(D):
    col = CC[century(d["year"])]
    if d["kind"] == "temporary":
        rx.barh(i, d["km"], color=col, alpha=.4, edgecolor=col, linestyle=(0, (3, 2)), lw=1.3, height=.66)
    else:
        rx.barh(i, d["km"], color=col, height=.66)
    rx.text(d["km"] + 90, i, f"{d['km']:,} km", va="center", fontsize=13)
rx.set_yticks(range(len(D))); rx.set_yticklabels([f"{short(d['from'])} → {short(d['to'])} {d['year']}" for d in D], fontsize=13.5)
rx.set_xlim(0, 9300); rx.set_xticks([]); rx.spines[["top", "right", "left", "bottom"]].set_visible(False); rx.tick_params(left=False)
rx.text(-0.02, 1.06, "The longest moves", transform=rx.transAxes, fontsize=15.5, ha="right", fontweight="medium")

# ---------- footer ----------
fig.text(.03, .018, "Source: Wikidata capital statements (CC0) via QLever, with the famous and doubtful moves checked, corrected or added by hand against cited sources (every edit listed in the data); Natural Earth. "
         "Great-circle distances.\nIt is a map of what the record knows: much richer for Europe than elsewhere. Data, code and interactive map: maps.tristanhotham.com/moving-capitals  ·  Dr Tristan Hotham",
         fontsize=13.5, color=MUT, va="bottom", linespacing=1.45)
fig.savefig(OUT, dpi=DPI, facecolor=fig.get_facecolor())
# ---------- independent pixel check: each label box (with its halo) against drawn land, and against arcs and dots ----------
fig.canvas.draw(); H = fig.canvas.get_renderer().height
boxes = {n: t.get_window_extent(fig.canvas.get_renderer()).expanded(1, 1) for n, t in TEXTS}
def mask(what):
    f2 = plt.figure(figsize=(W_IN, H_IN), dpi=DPI, facecolor="white")
    a2 = f2.add_axes(ax.get_position().bounds); a2.set_facecolor("white")
    if what == "land":
        for p_ in land_parts():
            a2.add_patch(MPoly(p_, closed=True, fc="black", ec="none"))
    else:
        for mm in M:
            arc(a2, mm, lw=2.6 if mm["km"] < 3000 else 3.4, dot=34, alpha=1, col="black")
        a2.plot(x, y, color="black", lw=2.2)
    a2.set_aspect("equal"); a2.axis("off"); a2.set_xlim(ax.get_xlim()); a2.set_ylim(ax.get_ylim())
    f2.canvas.draw(); arr = np.asarray(f2.canvas.buffer_rgba())[:, :, 0]; plt.close(f2)
    return arr < 128
for what in ("land", "data"):
    mk = mask(what)
    for n, bb in boxes.items():
        r0, r1 = int(H - bb.y1) - 4, int(H - bb.y0) + 4
        c0, c1 = int(bb.x0) - 4, int(bb.x1) + 4
        k = int(mk[max(r0, 0):r1, max(c0, 0):c1].sum())
        if k:
            problems.append(f"{n}: {k} {what} pixels under the label")
plt.close(fig)
from PIL import Image
print(OUT, Image.open(OUT).size, "problems:", problems or "none")
