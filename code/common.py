"""Shared paths and helpers for the moving-capitals project.

Raw inputs (read in place, never copied into the repo):
  CAPS    /home/claude/newdata/raw3/capitals.tsv  QLever (Wikidata) results: every capital (P36) statement of every item
          that is an instance of country (Q6256), sovereign state (Q3624078), historical country (Q3024240), kingdom
          (Q417175), realm (Q1250464), republic (Q7270), empire (Q48349), ancient civilisation (Q28171280) or constitutional
          monarchy (Q41614), with the statement's start time (P580), end time (P582) and rank, the capital's coordinates
          (P625), the state's inception (P571) and dissolution (P576) and English labels. One row per combination, so a
          statement repeats for each type, coordinate and inception value. Blank nodes (.well-known/genid) are Wikidata's
          "unknown value". Wikidata is CC0.
  GEO     /home/claude/newdata/raw/geo/  Natural Earth 50m countries and land, 10m populated places (public domain).
"""
import json, gzip, os, re, math, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAPS = "/home/claude/newdata/raw3/capitals.tsv"
GEO = "/home/claude/newdata/raw/geo"
NE50 = f"{GEO}/ne_50m_admin_0_countries.geojson"
LAND50 = f"{GEO}/ne_50m_land.geojson"
PLACES = f"{GEO}/ne_10m_populated_places_simple.geojson"
DATA = os.path.join(ROOT, "data")
WORK = os.environ.get("CAPSTMP", "/dev/shm/capitals")   # intermediates live in memory, not in the repo
for d in (DATA, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "moving-capitals"
URL = "https://maps.tristanhotham.com/moving-capitals/"
REPO = "https://github.com/Tristan-Hotham/moving-capitals"
RETRIEVED = "2026"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
FIRST_YEAR = 1500
SAME_PLACE_KM = 2       # a "move" shorter than this is the same site under another name, not a move

CENTURIES = [(1500, "16th century", "#9C6B30"), (1600, "17th century", "#C2452D"), (1700, "18th century", "#8E2F6B"),
             (1800, "19th century", "#2F5DA8"), (1900, "20th century", "#1E8C88"), (2000, "21st century", "#D49A00")]


def century(y):
    return max(c for c, _, _ in CENTURIES if c <= y)


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    """Remove em and en dashes and double hyphens from text taken from Wikidata (house style)."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def jsave(obj, path, indent=None):
    if os.path.abspath(path).startswith(DATA):
        obj = dash(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))


def norm(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    return re.sub(r"[\W_]+", " ", s).strip()


def gc_km(lat1, lon1, lat2, lon2):
    """Great-circle distance (haversine, mean Earth radius 6,371.0088 km)."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371.0088 * math.asin(min(1, math.sqrt(a)))


def bearing(lat1, lon1, lat2, lon2):
    """Initial great-circle bearing in degrees from north."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    x = math.sin(dl) * math.cos(p2)
    y = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


COMPASS = ["north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west"]
COMPASS_SHORT = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]


def compass(b):
    return COMPASS[int((b + 22.5) // 45) % 8]


def gc_points(lat1, lon1, lat2, lon2, n=48):
    """Points along the great circle (for arcs), as [lat, lon] with longitudes unwrapped to avoid jumps at 180."""
    p1, l1, p2, l2 = map(math.radians, (lat1, lon1, lat2, lon2))
    d = 2 * math.asin(math.sqrt(math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin((l2 - l1) / 2) ** 2))
    if d < 1e-9:
        return [[lat1, lon1], [lat2, lon2]]
    out, prev = [], None
    for i in range(n + 1):
        f = i / n
        A, B = math.sin((1 - f) * d) / math.sin(d), math.sin(f * d) / math.sin(d)
        x = A * math.cos(p1) * math.cos(l1) + B * math.cos(p2) * math.cos(l2)
        y = A * math.cos(p1) * math.sin(l1) + B * math.cos(p2) * math.sin(l2)
        z = A * math.sin(p1) + B * math.sin(p2)
        lat, lon = math.degrees(math.atan2(z, math.hypot(x, y))), math.degrees(math.atan2(y, x))
        if prev is not None:
            while lon - prev > 180: lon -= 360
            while lon - prev < -180: lon += 360
        prev = lon
        out.append([round(lat, 3), round(lon, 3)])
    return out


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "yr": return str(int(v))
    if f == "pc": return f"{round(float(v))}%"
    if f == "f1": return f"{float(v):.1f}"
    raise ValueError(f)


def fill(text, R, f=fmt):
    return re.sub(r"\{\{(?!IMG|DOI|BLOG_URL|DOI_URL|TABLE_)([^}|]+)(\|(\w+))?\}\}", lambda m: f(get(R, m.group(1)), m.group(3)), text)


def check_dashes(text, where):
    for bad in ("—", "–", "--"):
        assert bad not in text, (where, bad, text[max(0, text.find(bad) - 80):text.find(bad) + 80])
