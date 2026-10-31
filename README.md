# Capitals that moved

Every move of a state's capital since 1500 that can be read from Wikidata, checked, corrected and extended by hand against cited sources: 184 moves by 114 states, with the year, the great-circle distance, the direction, whether the move lasted, how confident the record is, and every manual edit with its source.

Interactive page: https://maps.tristanhotham.com/moving-capitals/
Paper: https://doi.org/10.5281/zenodo.23847842
Blog post: https://blog.tristanhotham.com/2026/10/31/moving-capitals/

## Headline results

- 184 moves since 1500: 136 lasting and 48 temporary (wartime or crisis seats, or moves that went back within ten years). The 20th century has the most, 59 (44 lasting); the busiest decade is the 1940s (18).
- The longest move is the Portuguese court's flight from Lisbon to Rio de Janeiro in 1808: 7,716 km. The longest lasting move is Muscat to Zanzibar in 1840 (3,924 km). The median lasting move is 177 km.
- 17 moves went to a capital built for the purpose (St Petersburg, Karlsruhe, Washington, Canberra, Brasília, Islamabad, Abuja, Naypyidaw, Ciudad de la Paz and others), 12 of them after 1900.
- Since 1900, 27% of lasting moves left a coastal capital for the interior (13 of 48), against 8% before 1900.
- By present-day country the United States has the most moves (17, 11 of them the Continental Congress and early federal government), then Germany (12, from 8 states).
- The record is thin: only 21.3% of Wikidata's 2,978 capital statements have a date, and 81% of present-day sovereign states have one recorded capital. 45 automatic moves were removed, 5 corrected, 22 confirmed and 42 added by hand.
- Indonesia's move to Nusantara has not been made as of 2026 (no presidential decree; the Constitutional Court confirmed in May 2026 that Jakarta remains the capital). It is shown as planned, not counted.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/06_build_site.py`); loads `data/site.json`, `data/cities.json`, `data/borders_today.json`. |
| `header.png` | Social card, 1200 x 630. |
| `data/moves.csv` | The 184 moves: year, state and Wikidata item, present-day country, old and new capital with items and coordinates, km, bearing, direction, lasting or temporary (and why), confidence, basis, purpose-built, distance from the sea, change in distance to the country's centre, other items recording the same move, note and source (59 KB). |
| `data/moves.geojson` | The same moves as great-circle lines. |
| `data/manual_edits.csv` | Every hand edit (158 rows): removals, corrections, confirmations, additions, merges, same-place pairs and display labels, each with a reason and a source. |
| `data/same_place.csv` | Renamings and redefinitions of the same city, not counted as moves. |
| `data/planned.csv` | Planned moves not made (Nusantara), with status as of 2026 and sources. |
| `data/results.json` | Every number used in the page, paper, blog and collage. |
| `data/site.json`, `data/cities.json`, `data/borders_today.json` | Page data; Natural Earth city names and present-day borders. |
| `code/` | Scripts, run in order (below), the page, paper and blog templates, and `overrides.py` (all manual choices). |
| `release/` | Paper PDF and LaTeX source with figures, blog post and figures, Zenodo files. |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |

## Method in brief

- Input: every capital (P36) statement in Wikidata of items that are countries, sovereign states, historical countries, kingdoms, realms, republics, empires, ancient civilisations or constitutional monarchies, with start and end times, rank, coordinates, inception and dissolution (QLever). States that existed after 1500.
- Reading moves: a new capital's start within two years of an old one's end; or a start with the old capital undated at its end; or an end with the new capital undated at its start (preferred rank first). Overlaps of more than two years are joint capitals. Deprecated statements, unknown values and states with no dates are left out. Renamings and moves under 2 km are not moves. The same move on several items (ends within 10 km, years within three) is counted once.
- Hand edits (`code/overrides.py`, logged in `data/manual_edits.csv`): wrong orders, institutions' seats, duplicates and wrong items removed; years and cities corrected; famous moves confirmed; missing moves added (Istanbul to Ankara, Kyoto to Tokyo, Karachi to Rawalpindi, the Continental Congress, the Province of Canada, the Republic of China 1912 to 1949, France 1879 and 1940 to 1944 and others).
- Measures: haversine distance (radius 6,371 km), initial bearing, present-day country where most of the state's capitals lie, distance to the nearest ocean coast (Natural Earth 1:50m land). Temporary: new seat held under a year, back where it started within ten years, or a listed wartime or exile seat.
- Confidence: checked (against a cited source), high (both ends dated in Wikidata), medium (one end dated).
- Caveats: a reading of an open database, not a complete history; much richer for Europe; "capital" often means the court for older monarchies; several countries split capital functions; some moves transferred the title before the ministries.

## How to rerun

Needs Python 3 with numpy, shapely, pyproj, matplotlib, fontTools and Pillow; mapshaper (npm); xelatex and pdftotext; node with playwright for QA. Raw inputs are read in place (paths in `code/common.py`): `/home/claude/newdata/raw3/capitals.tsv` (the QLever dump) and Natural Earth files in `/home/claude/newdata/raw/geo/`. Intermediate files go to `/dev/shm/capitals` (set `CAPSTMP` to change).

```
python3 code/01_parse.py        # statements and states from the dump
python3 code/02_moves.py        # automatic moves
python3 code/03_clean.py        # hand edits, merges, classification, measures
python3 code/04_results.py      # results.json, page data
python3 code/05_geo.py          # borders and city names for the page
python3 code/06_build_site.py   # index.html
python3 code/07_figures.py      # header, paper and blog figures
python3 code/08_paper.py        # paper PDF (set DOI=... to fill the DOI)
python3 code/09_readme.py       # README and LICENSE
python3 code/10_release.py      # blog post, Zenodo files
python3 reddit/collage.py       # collage
node code/12_qa.js              # screenshots and console check
```

## Sources and licences

- Wikidata, via QLever (https://qlever.cs.uni-freiburg.de/wikidata), retrieved 2026. CC0.
- Hand checks cite English Wikipedia articles (CC BY-SA 4.0; cited, not copied), africanews (Equatorial Guinea) and The Star and The Jakarta Post (Nusantara), each linked in `data/manual_edits.csv`.
- Natural Earth countries, land and populated places. Public domain.
- Base map tiles on the page: © Esri.

## Citation

Hotham, T. (2026) Capitals that moved: every capital move since 1500 in Wikidata, checked and corrected. Zenodo. https://doi.org/10.5281/zenodo.23847842

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
