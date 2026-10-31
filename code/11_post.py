"""reddit/post.md, numbers from results.json."""
from common import *

R = jload(f"{DATA}/results.json")
post = f"""## Title

[OC] Every capital city move since 1500: {R['n']} moves. The longest was a royal escape, Lisbon to Rio de Janeiro in 1808 ({R['lisbon_rio']['km']:,} km)

## Body

I pulled every capital statement with start and end dates from Wikidata and turned them into arcs from the old capital to the new one, then checked the famous moves by hand against sources, fixing or adding what was wrong or missing (Wikidata has no Istanbul to Ankara, no Kyoto to Tokyo, and no record of Canada's parliament wandering between Kingston, Montreal, Toronto and Quebec City). Every edit is listed with its source in the data.

Some things I found: the 20th century is the busiest, with {R['c20']['n']} moves. The median lasting move is only {R['median_km_lasting']} km, but the Portuguese court fled Napoleon all the way to Rio, and the Sultan of Oman moved his capital {R['ex']['zanzibar']['km']:,} km to Zanzibar in 1840. {R['n_purpose_built']} moves went to a capital built for the purpose, {R['n_pb_since_1900']} of them after 1900, and since 1900 {R['sea']['inland_pct']}% of lasting moves left a coastal city for the interior (Brasília, Abuja, Dodoma, Naypyidaw, and Equatorial Guinea's new Ciudad de la Paz in 2026). Indonesia's move to Nusantara has not happened yet: Jakarta is still the capital.

Caveat: this is what the open record knows, which is far richer for Europe than for Africa, Asia or the Americas before colonial rule. Interactive map with a time slider and the story of every move: https://maps.tristanhotham.com/moving-capitals/

## Source comment

Source: Wikidata capital (P36) statements with start and end times (CC0), via QLever; {R['edits']['drop']} automatic moves removed, {R['edits']['fix']} corrected, {R['edits']['check']} confirmed and {R['edits']['add']} added by hand, each with a cited source (mostly English Wikipedia; africanews for Equatorial Guinea; The Star and The Jakarta Post for Nusantara). Borders, coastline and places: Natural Earth (public domain). Distances along the great circle.

Tools: Python (shapely, pyproj, matplotlib); Leaflet for the interactive map.

Interactive version: https://maps.tristanhotham.com/moving-capitals/
Paper: https://doi.org/{{10.5281/zenodo.23847842}}
Data and code: https://github.com/Tristan-Hotham/moving-capitals
"""
check_dashes(post, "post")
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
print(post[:200])
