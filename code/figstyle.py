"""House style for static figures: fonts (a static Fraunces Black cut from the variable font, written to memory), colours,
and a light world map in the Equal Earth projection with great-circle arcs."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MPoly
import numpy as np
from pyproj import Transformer
from shapely.geometry import shape, box
from common import *

FONTS = "/home/claude/ref/fonts"
FD = os.path.join(WORK, "fonts"); os.makedirs(FD, exist_ok=True)
if not os.path.exists(f"{FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    instancer.instantiateVariableFont(TTFont(f"{FONTS}/FrauncesVar.ttf"), {"wght": 900, "opsz": 144, "SOFT": 0, "WONK": 0}).save(f"{FD}/Fraunces-Black.ttf")
    instancer.instantiateVariableFont(TTFont(f"{FONTS}/FrauncesVar.ttf"), {"wght": 600, "opsz": 48, "SOFT": 0, "WONK": 0}).save(f"{FD}/Fraunces-Semibold.ttf")
DISP = fm.FontProperties(fname=f"{FD}/Fraunces-Black.ttf")
DISP6 = fm.FontProperties(fname=f"{FD}/Fraunces-Semibold.ttf")
SERP = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Regular.ttf")
SERI = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-It.ttf")
SERB = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Semibold.ttf")
fm.fontManager.addfont(f"{FONTS}/IBMPlexMono-Regular.ttf")
fm.fontManager.addfont(f"{FONTS}/IBMPlexMono-Medium.ttf")
MONO = "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 12, "axes.edgecolor": "#646875", "axes.labelcolor": "#1E2430",
                     "xtick.color": "#646875", "ytick.color": "#646875"})
BG, FG, MUT, LAND, RULE, HOT, COOL, GOLD, SEA = "#F7F3EA", "#1E2430", "#646875", "#E6DECD", "#E2DACA", "#B8452A", "#23408E", "#C99A06", "#F7F3EA"
CC = {c: col for c, _, col in CENTURIES}
CN = {c: n for c, n, _ in CENTURIES}
tr = Transformer.from_crs(4326, 8857, always_xy=True)
_LAND = None


def land_parts(clip=(-180, -58, 180, 84), tol=.04):
    global _LAND
    if _LAND is None:
        out = []
        for f in jload(LAND50)["features"]:
            g = shape(f["geometry"]).intersection(box(*clip)).simplify(tol, preserve_topology=True)
            for p in (g.geoms if hasattr(g, "geoms") else [g]):
                if p.geom_type != "Polygon" or p.is_empty:
                    continue
                a = np.array(p.exterior.coords)
                x, y = tr.transform(a[:, 0], a[:, 1])
                out.append(np.column_stack([x, y]))
        _LAND = out
    return _LAND


_BORD = None


def borders():
    global _BORD
    if _BORD is None:
        out = []
        for f in jload(NE50)["features"]:
            g = shape(f["geometry"]).intersection(box(-180, -58, 180, 84)).simplify(.04, preserve_topology=True)
            for p in (g.geoms if hasattr(g, "geoms") else [g]):
                if p.geom_type != "Polygon" or p.is_empty:
                    continue
                a = np.array(p.exterior.coords)
                x, y = tr.transform(a[:, 0], a[:, 1])
                out.append(np.column_stack([x, y]))
        _BORD = out
    return _BORD


def world(ax, ext=None, land=LAND, ec="#FFFFFF", lw=.35, bord=True):
    for p in land_parts():
        ax.add_patch(MPoly(p, closed=True, fc=land, ec="none", zorder=1))
    if bord:
        for p in borders():
            ax.plot(p[:, 0], p[:, 1], color=ec, lw=lw, zorder=2, solid_joinstyle="round")
    ax.set_aspect("equal"); ax.axis("off")
    if ext:
        ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])
    else:
        ax.set_xlim(-1.62e7, 1.62e7); ax.set_ylim(-6.3e6, 8.4e6)


def xy(lon, lat):
    return tr.transform(np.asarray(lon), np.asarray(lat))


def arc(ax, m, lw=1.6, alpha=.95, z=5, col=None, dots=True, dot=14):
    g = np.array(gc_points(m["from_lat"], m["from_lon"], m["to_lat"], m["to_lon"], max(8, min(80, int(m["km"] / 50)))))
    lon = ((g[:, 1] + 180) % 360) - 180
    x, y = xy(lon, g[:, 0])
    c = col or CC[century(m["year"])]
    ls = (0, (3.2, 2.2)) if m["kind"] == "temporary" else "-"
    ax.plot(x, y, color=c, lw=lw if m["kind"] == "lasting" else lw * .75, alpha=alpha, zorder=z, solid_capstyle="round", linestyle=ls)
    if dots:
        ax.scatter([x[0]], [y[0]], s=dot, facecolor=BG, edgecolor=c, lw=1.1, zorder=z + 1, alpha=alpha)
        ax.scatter([x[-1]], [y[-1]], s=dot * 1.3, facecolor=c, edgecolor="white", lw=.6, zorder=z + 2, alpha=alpha)
    return x, y


def mix(a, b, t):
    A = [int(a[i:i + 2], 16) for i in (1, 3, 5)]; B = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(A, B))


def save(fig, name, dpi=200):
    fig.savefig(name, dpi=dpi, facecolor=fig.get_facecolor())
    plt.close(fig)
