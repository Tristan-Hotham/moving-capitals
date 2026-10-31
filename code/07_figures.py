"""Header card, paper figures (release/paper/f_*.png) and blog figures (release/blog/b_*.png). Numbers from results.json."""
import shutil
import matplotlib.patheffects as pe
from figstyle import *

R = jload(f"{DATA}/results.json")
M = jload(f"{WORK}/moves.json")["moves"]
PAP = os.path.join(ROOT, "release", "paper"); BLOG = os.path.join(ROOT, "release", "blog")
for d in (PAP, BLOG):
    os.makedirs(d, exist_ok=True)
HALO = [pe.withStroke(linewidth=3, foreground=BG)]
short = lambda s: s.replace(" (New Delhi from 1931)", "").replace("Calcutta (Kolkata)", "Calcutta").replace("Zanzibar (Stone Town)", "Zanzibar").replace("Kyoto (Heian-kyō)", "Kyoto")


def both(fig, name):
    fig.savefig(f"{PAP}/f_{name}.png", dpi=200, facecolor=fig.get_facecolor())
    fig.savefig(f"{BLOG}/b_{name}.png", dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)


def legend_cent(ax, x, y, dy, fs=10, temp=True):
    for i, (c, n, col) in enumerate(CENTURIES):
        ax.plot([x, x + .03], [y - i * dy] * 2, color=col, lw=3, transform=ax.transAxes, solid_capstyle="round")
        ax.text(x + .04, y - i * dy, n, transform=ax.transAxes, va="center", fontsize=fs, color=FG)
    if temp:
        k = len(CENTURIES)
        ax.plot([x, x + .03], [y - k * dy] * 2, color=MUT, lw=2, transform=ax.transAxes, linestyle=(0, (3, 2)))
        ax.text(x + .04, y - k * dy, "temporary seat", transform=ax.transAxes, va="center", fontsize=fs, color=FG)


# ---------- world map ----------
def world_map(ax, lw=1.4):
    world(ax)
    for m in sorted(M, key=lambda m: (m["kind"] == "lasting", m["year"])):
        arc(ax, m, lw=lw, alpha=.92, dot=10)


fig = plt.figure(figsize=(12, 6.4), facecolor=BG)
ax = fig.add_axes([0, 0, 1, .93]); world_map(ax)
fig.text(.02, .955, f"Every capital move since 1500: {R['n']} moves, coloured by century", fontproperties=DISP6, fontsize=17, color=FG)
legend_cent(ax, .015, .40, .04)
ax.text(.015, .04, "Wikidata, checked and corrected by hand. Great-circle arcs; hollow dot old capital, filled dot new.", transform=ax.transAxes, fontsize=8.5, color=MUT)
both(fig, "map")

# ---------- Europe ----------
x0, y0 = xy(-11, 35); x1, y1 = xy(42, 61)
ext = (x0 - 2e5, x1, y0, y1 + 1e5)
fig = plt.figure(figsize=(10, 10 * (ext[3] - ext[2]) / (ext[1] - ext[0]) / .93), facecolor=BG)
ax = fig.add_axes([0, 0, 1, .93])
world(ax, ext, lw=.5)
EU = [m for m in M if ext[0] < xy(m["to_lon"], m["to_lat"])[0] < ext[1] and ext[2] < xy(m["to_lon"], m["to_lat"])[1] < ext[3]]
for m in sorted(EU, key=lambda m: (m["kind"] == "lasting", m["year"])):
    arc(ax, m, lw=2, dot=22)
fig.canvas.draw(); rend = fig.canvas.get_renderer(); boxes = []
for m in sorted(EU, key=lambda m: -m["km"]):
    if m["kind"] != "lasting" or m["km"] < 60:
        continue
    X, Y = xy(m["to_lon"], m["to_lat"])
    for dx, dy, ha, va in ((9, 0, "left", "center"), (-9, 0, "right", "center"), (0, 9, "center", "bottom"), (0, -9, "center", "top")):
        t = ax.annotate(f"{short(m['to'])} {m['year']}", (X, Y), xytext=(dx, dy), textcoords="offset points", ha=ha, va=va, fontsize=8.6, color=FG, path_effects=HALO, zorder=20)
        bb = t.get_window_extent(rend).expanded(1.05, 1.1)
        if any(bb.overlaps(b) for b in boxes) or not ax.get_window_extent(rend).contains(bb.x0, bb.y0) or not ax.get_window_extent(rend).contains(bb.x1, bb.y1):
            t.remove(); continue
        boxes.append(bb); break
fig.text(.02, .962, f"Europe: {len(EU)} moves since 1500, labelled at the new capital", fontproperties=DISP6, fontsize=17, color=FG)
legend_cent(ax, .015, .97, .032, fs=9)
both(fig, "europe")

# ---------- centuries ----------
fig, ax = plt.subplots(figsize=(9, 4.6), facecolor=BG); ax.set_facecolor(BG)
C = R["by_century"]
for i, c in enumerate(C):
    ax.bar(i, c["lasting"], color=c["col"], width=.72)
    ax.bar(i, c["temp"], bottom=c["lasting"], color=c["col"], alpha=.42, width=.72)
    ax.text(i, c["n"] + 1, str(c["n"]), ha="center", fontsize=12, color=FG, fontweight="medium")
ax.set_xticks(range(len(C))); ax.set_xticklabels([c["name"].replace(" century", "\ncentury") for c in C], fontsize=10.5)
ax.set_ylim(0, 66); ax.spines[["top", "right", "left"]].set_visible(False); ax.yaxis.grid(color=RULE); ax.set_axisbelow(True); ax.tick_params(left=False)
ax.bar(0, 0, color=FG, label="lasting"); ax.bar(0, 0, color=FG, alpha=.42, label="temporary")
ax.legend(frameon=False, loc="upper left", fontsize=10)
ax.set_title("Capital moves by century since 1500", fontproperties=DISP6, fontsize=15, loc="left", color=FG, pad=12)
fig.tight_layout(); both(fig, "century")

# ---------- decades ----------
fig, ax = plt.subplots(figsize=(11, 3.8), facecolor=BG); ax.set_facecolor(BG)
for d in R["by_decade"]:
    ax.bar(d["d"] + 5, d["lasting"], width=8.6, color=CC[century(d["d"])])
    ax.bar(d["d"] + 5, d["n"] - d["lasting"], bottom=d["lasting"], width=8.6, color=CC[century(d["d"])], alpha=.42)
for yy, t, row, ha in ((1712, "St Petersburg", 0, "center"), (1808, "Lisbon to Rio", 1, "center"), (1918, "Petrograd to Moscow", 0, "right"), (1949, "Nanjing to Taipei", 2, "center"), (1960, "Brasília", 1, "center"), (2026, "Ciudad de la Paz", 0, "right")):
    top = 21 - row * 2.2
    ax.plot([yy, yy], [0, top - .6], color=MUT, lw=.7, zorder=0)
    ax.text(yy, top, f"{t} {yy}", ha=ha, fontsize=8.5, color=FG)
ax.set_xlim(1495, 2035); ax.set_ylim(0, 23); ax.spines[["top", "right", "left"]].set_visible(False); ax.yaxis.grid(color=RULE); ax.set_axisbelow(True); ax.tick_params(left=False)
ax.set_ylabel("moves per decade", fontsize=10)
ax.set_title("Every move, decade by decade (pale: temporary)", fontproperties=DISP6, fontsize=15, loc="left", color=FG, pad=10)
fig.tight_layout(); both(fig, "decade")

# ---------- longest ----------
fig, ax = plt.subplots(figsize=(10, 5.6), facecolor=BG); ax.set_facecolor(BG)
D = R["longest"][:10][::-1]
for i, d in enumerate(D):
    col = CC[century(d["year"])]
    if d["kind"] == "temporary":
        ax.barh(i, d["km"], color=col, alpha=.4, edgecolor=col, linestyle=(0, (3, 2)), lw=1.2, height=.62)
    else:
        ax.barh(i, d["km"], color=col, height=.62)
    ax.text(d["km"] + 70, i, f"{d['km']:,} km", va="center", fontsize=10, color=FG)
ax.set_yticks(range(len(D))); ax.set_yticklabels([f"{short(d['from'])} to {short(d['to'])}, {d['year']}" for d in D], fontsize=10)
ax.set_xlim(0, 8900); ax.spines[["top", "right", "left"]].set_visible(False); ax.xaxis.grid(color=RULE); ax.set_axisbelow(True); ax.tick_params(left=False)
ax.set_title("The ten longest capital moves since 1500 (pale, dashed: temporary)", fontproperties=DISP6, fontsize=14.5, loc="right", color=FG, pad=10)
fig.tight_layout(); both(fig, "longest")

# ---------- purpose-built ----------
fig, ax = plt.subplots(figsize=(10, 6.2), facecolor=BG); ax.set_facecolor(BG)
P = sorted(R["purpose_built"], key=lambda p: p["year"])[::-1]
for i, p in enumerate(P):
    col = CC[century(p["year"])]
    ax.plot([p["founded"], p["year"]], [i, i], color=col, lw=3, solid_capstyle="round")
    ax.scatter([p["founded"]], [i], s=40, facecolor=BG, edgecolor=col, lw=1.6, zorder=3)
    ax.scatter([p["year"]], [i], s=55, color=col, zorder=4)
ax.set_yticks(range(len(P))); ax.set_yticklabels([f"{short(p['to']).replace('Delhi', 'New Delhi')}, {p['country']}" for p in P], fontsize=9.5)
ax.set_xlim(1570, 2040); ax.spines[["top", "right", "left"]].set_visible(False); ax.xaxis.grid(color=RULE); ax.set_axisbelow(True); ax.tick_params(left=False)
ax.set_title("Capitals built for the purpose: begun (hollow), occupied (filled)", fontproperties=DISP6, fontsize=14.5, loc="right", color=FG, pad=10)
fig.tight_layout(); both(fig, "purpose")

# ---------- the sea ----------
fig, ax = plt.subplots(figsize=(8.5, 7.2), facecolor=BG); ax.set_facecolor(BG)
mod = [m for m in M if m["kind"] == "lasting" and m["year"] >= 1900]
f = lambda v: np.sqrt(min(v, 2000))
isin = lambda m: m["from_coast_km"] <= 50 and m["to_coast_km"] - m["from_coast_km"] >= 50
for v in (0, 10, 50, 200, 500, 1000, 2000):
    ax.axhline(f(v), color=RULE, lw=.8, zorder=0); ax.text(.5, f(v), f"{v:,} km", ha="center", va="bottom", fontsize=8.5, color=MUT)
labs = []
for m in sorted(mod, key=isin):
    hi = isin(m); col = CC[century(m["year"])] if hi else MUT
    ax.plot([0, 1], [f(m["from_coast_km"]), f(m["to_coast_km"])], color=col, lw=2.2 if hi else .9, alpha=1 if hi else .45, zorder=3 if hi else 1)
    ax.scatter([0, 1], [f(m["from_coast_km"]), f(m["to_coast_km"])], color=col, s=18 if hi else 8, zorder=4)
    if hi:
        yr = f(m["to_coast_km"]); nm = short(m["to"]).replace("Ciudad de la Paz", "Ciudad de la Paz")
        near = next((l for l in labs if abs(l[0] - yr) < 1.1), None)
        if near: near[1].append(nm)
        else: labs.append([yr, [nm]])
for yr, names in labs:
    ax.text(1.03, yr, ", ".join(names), va="center", fontsize=9, color=FG)
ax.set_xlim(-.25, 1.62); ax.invert_yaxis(); ax.axis("off")
ax.text(0, -2.5, "old capital", ha="center", fontsize=10.5, fontweight="medium"); ax.text(1, -2.5, "new capital", ha="center", fontsize=10.5, fontweight="medium")
ax.text(-.02, f(25), "coastal\ncapitals", ha="right", va="center", fontsize=9, color=MUT)
fig.suptitle(f"Distance from the sea, lasting moves since 1900: {R['sea']['inland_n']} of {R['sea']['modern_n']} left the coast for the interior", fontproperties=DISP6, fontsize=13.5, x=.03, ha="left", color=FG)
fig.tight_layout(rect=(0, 0, 1, .95)); both(fig, "sea")

# ---------- countries ----------
fig, ax = plt.subplots(figsize=(9, 5.6), facecolor=BG); ax.set_facecolor(BG)
D = R["countries"][:12][::-1]
for i, d in enumerate(D):
    ax.barh(i, d["lasting"], color=HOT, height=.64); ax.barh(i, d["n"] - d["lasting"], left=d["lasting"], color=HOT, alpha=.38, height=.64)
    ax.text(d["n"] + .25, i, str(d["n"]), va="center", fontsize=10)
ax.set_yticks(range(len(D))); ax.set_yticklabels([d["name"] for d in D], fontsize=10.5)
ax.barh(0, 0, color=HOT, label="lasting"); ax.barh(0, 0, color=HOT, alpha=.38, label="temporary"); ax.legend(frameon=False, loc="lower right", fontsize=10)
ax.spines[["top", "right", "left"]].set_visible(False); ax.xaxis.grid(color=RULE); ax.set_axisbelow(True); ax.tick_params(left=False)
ax.set_title("Most capital moves since 1500, by present-day country", fontproperties=DISP6, fontsize=14.5, loc="right", color=FG, pad=10)
fig.tight_layout(); both(fig, "countries")

# ---------- header card 1200 x 630 ----------
fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=BG)
ax = fig.add_axes([.30, .02, .72, .94]); world(ax, ext=(-1.25e7, 1.62e7, -5.0e6, 8.0e6), lw=.25)
for m in sorted(M, key=lambda m: (m["kind"] == "lasting", m["km"])):
    arc(ax, m, lw=1.5 if m["km"] < 2000 else 2.4, dot=8)
fig.text(.035, .80, "Capitals", fontproperties=DISP, fontsize=54, color=FG)
fig.text(.035, .68, "that", fontproperties=DISP, fontsize=54, color=HOT)
fig.text(.035, .56, "moved", fontproperties=DISP, fontsize=54, color=COOL)
fig.text(.037, .44, f"{R['n']} moves of a capital since 1500.\nThe longest: Lisbon to Rio de Janeiro,\n{R['lisbon_rio']['km']:,} km, in 1808.", fontsize=12.5, color=FG, va="top", linespacing=1.5)
fig.text(.037, .07, "Dr Tristan Hotham · maps.tristanhotham.com", fontsize=10, color=MUT)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=BG); plt.close(fig)
from PIL import Image
im = Image.open(os.path.join(ROOT, "header.png")); assert im.size == (1200, 630), im.size
print("figures:", sorted(os.listdir(PAP)), sorted(os.listdir(BLOG)))
