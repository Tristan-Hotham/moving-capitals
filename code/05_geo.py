"""Page geometry: present-day borders (Natural Earth 50m, simplified with mapshaper to TopoJSON) and city names
(Natural Earth populated places with at least 250,000 people, or national capitals)."""
import subprocess
from common import *

out = f"{DATA}/borders_today.json"
subprocess.run(["mapshaper", NE50, "-filter-fields", "ADMIN", "-simplify", "8%", "keep-shapes", "-o", "format=topojson", "precision=0.01", out], check=True, capture_output=True)
P = jload(PLACES)["features"]
cities = []
for f in P:
    p = f["properties"]
    if (p["pop_max"] or 0) >= 250000 or p["adm0cap"] == 1:
        cities.append({"name": p["name"], "lat": round(p["latitude"], 3), "lon": round(p["longitude"], 3), "pop": int(p["pop_max"] or 0), "cap": int(p["adm0cap"] or 0)})
cities.sort(key=lambda c: -c["pop"])
jsave(cities, f"{DATA}/cities.json")
print("borders", os.path.getsize(out) // 1024, "KB; cities", len(cities))
