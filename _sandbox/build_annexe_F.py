"""Rebuild Annexe F (sensitivity synthesis) to match the retained approach: SWEEP-only (no local
+/-25 %). Per (territory, profil), reference value + sweep range on each axis (d0 50-120 %, contrast
0-200 %) for the two headline indicators, plus the d0 connexity margin. Prints markdown to paste.
Read-only inputs. Covers whatever complete cities are on disk."""
import glob, os
import pandas as pd

ROOT = os.path.join(os.path.dirname(__file__), "..")
CITY_FR = {"Kourou": "Kourou", "Perpignan": "Perpignan", "Nancy": "Nancy",
           "LaRochelle": "La Rochelle", "LRSY": "La Roche-sur-Yon", "Toulouse": "Toulouse"}
GUILD_FR = {"ground_mammal": "Petit mammifère terrestre", "arboreal_mammal": "Mammifère arboricole",
            "forest_edge_bird": "Oiseau de lisière", "ground_reptile": "Reptile terrestre"}
ORDER = ["Kourou", "Perpignan", "Nancy", "LaRochelle", "LRSY", "Toulouse"]
GORDER = ["ground_mammal", "arboreal_mammal", "forest_edge_bird", "ground_reptile"]
D0 = [50, 60, 70, 80, 90, 110, 120]
FC = [0, 25, 50, 75, 125, 150, 200]


def stat(city, guild, tag=None):
    p = (f"{ROOT}/data/outputs/{city}/{guild}/stats_*.csv" if tag is None
         else f"{ROOT}/data/sensitivity/{tag}/data/outputs/{city}/{guild}/stats_*.csv")
    f = glob.glob(p)
    if not f:
        return None
    s = pd.read_csv(f[0]).iloc[0]
    return float(s["connected_habitat_pct"]), int(s["n_subnetworks"])


def rng(city, guild, prefix, scales, idx):
    ref = stat(city, guild)
    vals = [ref[idx]] if ref else []
    for m in scales:
        v = stat(city, guild, f"{prefix}_{m:03d}")
        if v:
            vals.append(v[idx])
    if not vals:
        return None
    return min(vals), max(vals)


def margin(city, guild):
    """d0 connexity margin: connexe on all / connexe >= X% / never."""
    connexe = []
    ref = stat(city, guild)
    for m in D0:
        v = stat(city, guild, f"swd0_{m:03d}")
        if v and v[1] == 1:
            connexe.append(m)
    if ref and ref[1] == 1:
        connexe.append(100)
    if not connexe:
        return "morcelé (jamais connexe)"
    lo = min(connexe)
    return f"connexe ≥ {lo} %" if lo > 50 else "connexe sur toute la plage"


rows = []
for city in ORDER:
    for guild in GORDER:
        ref = stat(city, guild)
        if ref is None:
            continue
        # garde-fou : n'inclure que les couples aux DEUX balayages reellement faits (>= 5 points sur 7)
        if (sum(1 for m in D0 if stat(city, guild, f"swd0_{m:03d}")) < 5
                or sum(1 for m in FC if stat(city, guild, f"swfc_{m:03d}")) < 5):
            continue
        cd0 = rng(city, guild, "swd0", D0, 0)
        cfc = rng(city, guild, "swfc", FC, 0)
        nd0 = rng(city, guild, "swd0", D0, 1)
        nfc = rng(city, guild, "swfc", FC, 1)
        fmt = lambda r, suf="": ("n. d." if r is None else
                                 (f"{r[0]:.0f}{suf}" if round(r[0]) == round(r[1]) else f"{r[0]:.0f}–{r[1]:.0f}{suf}"))
        rows.append([CITY_FR[city], GUILD_FR[guild], f"{ref[0]:.0f} %",
                     fmt(cd0, " %"), fmt(cfc, " %"), f"{ref[1]}",
                     fmt(nd0), fmt(nfc)])

cols = ["Territoire", "Profil écologique", "Connecté réf.", "Connecté (d₀)", "Connecté (contraste)",
        "Sous-rés. réf.", "Sous-rés. (d₀)", "Sous-rés. (contraste)"]
print(f"couples: {len(rows)}\n")
print("| " + " | ".join(cols) + " |")
print("|" + "|".join("---" for _ in cols) + "|")
for r in rows:
    print("| " + " | ".join(r) + " |")
