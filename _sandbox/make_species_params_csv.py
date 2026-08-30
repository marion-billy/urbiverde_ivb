"""Export the full ecological-profile parameters (species_params.SPECIES_CONFIG) to a flat CSV.

One row per ecological profile: identity, dispersal distances, reference + representative species,
habitat and barrier codes, and the full friction value for every land-cover code (NaN barriers shown
as 'inf'). Companion, machine-readable form of the README parameter tables.

Run: python3 _sandbox/make_species_params_csv.py  ->  data/outputs/species_params.csv
"""
import sys
import numpy as np
import pandas as pd

sys.path.insert(1, "utils")
import species_params as spp

LC = spp.LC_MAP
CODES = [10, 20, 30, 40, 50, 60, 80, 90, 95, 51, 52, 53, 54, 55]  # WorldCover then OSM
OUT = "data/outputs/species_params.csv"


def fmt_species(pairs):
    return "; ".join(f"{lat} ({fr})" for lat, fr in pairs)


def fric(v):
    return "inf" if isinstance(v, float) and np.isnan(v) else v


rows = []
for key, c in spp.SPECIES_CONFIG.items():
    d0 = c["graph"]["d0"]
    ref = c.get("reference_species_cerema", ("", ""))
    row = {
        "cle": key,
        "profil_ecologique": c.get("label", ""),
        "description": c.get("description", ""),
        "d0_m": d0,
        "lien_max_graphe_m": 2 * d0,          # Gabriel graph max link
        "budget_cout_UC": 3 * d0,             # d0 x 3 dispersal-cost budget
        "espece_reference_latin": ref[0],
        "espece_reference_fr": ref[1],
        "especes_representatives": fmt_species(c.get("representative_species", [])),
        "codes_habitat": ", ".join(map(str, c.get("habitat_codes", []))),
        "codes_barrieres_infranchissables": ", ".join(
            str(k) for k, v in c["friction"].items() if isinstance(v, float) and np.isnan(v)),
    }
    for code in CODES:
        row[f"friction_{code}_{LC.get(code, '?')}"] = fric(c["friction"].get(code))
    row["refs"] = c.get("refs", "")
    rows.append(row)

df = pd.DataFrame(rows)
df.to_csv(OUT, index=False)
print(f"{len(df)} profils x {len(df.columns)} colonnes -> {OUT}")
print(df[["cle", "d0_m", "codes_habitat", "codes_barrieres_infranchissables"]].to_string(index=False))
