"""Generate the sensitivity annexe table (markdown) from the frozen sensitivity_summary.csv.

For each (city, guild) present, reports the reference value and the range under perturbation of the
two headline KPIs (part d'habitat connectee, nombre de sous-reseaux), separately for the LOCAL
perturbations (d0 +/-25 %, friction +/-20 %) and the SWEEP (d0 0.50..1.50). Absolute values are
reconstructed from the reference stats and the relative deltas in the summary, so the table reads in
the report's own units. Re-run whenever the campaign advances; paste the printed markdown into
rapport_9 Annexe F.
"""
from __future__ import annotations

import glob
import os

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SUMMARY = os.path.join(ROOT, "data", "sensitivity", "sensitivity_summary.csv")
BASE = os.path.join(ROOT, "data", "outputs")

CITY_FR = {"Perpignan": "Perpignan", "LaRochelle": "La Rochelle", "Nancy": "Nancy",
           "LRSY": "La Roche-sur-Yon", "Toulouse": "Toulouse", "Kourou": "Kourou"}
GUILD_FR = {"ground_mammal": "Petit mammifère terrestre", "ground_reptile": "Reptile terrestre",
            "arboreal_mammal": "Mammifère arboricole", "forest_edge_bird": "Oiseau de lisière"}
LOCAL = {"d0_m25", "d0_p25", "fric_m20", "fric_p20"}


def _ref(city: str, guild: str) -> pd.Series | None:
    f = glob.glob(f"{BASE}/{city}/{guild}/stats_*.csv")
    return pd.read_csv(f[0]).iloc[0] if f else None


def _range(sub: pd.DataFrame, ref_val: float, col: str) -> str:
    """Absolute min..max of a KPI reconstructed from reference value and the % deltas in `sub`."""
    d = sub[col].dropna()
    if d.empty or ref_val is None:
        return "n. d."
    vals = [ref_val * (1 + x / 100.0) for x in d]
    lo, hi = min(vals + [ref_val]), max(vals + [ref_val])
    return f"{lo:.0f}" if round(lo) == round(hi) else f"{lo:.0f}–{hi:.0f}"


df = pd.read_csv(SUMMARY)
rows = []
for (city, guild), sub in df.groupby(["city", "guild"]):
    ref = _ref(city, guild)
    if ref is None:
        continue
    ch, ns = float(ref["connected_habitat_pct"]), float(ref["n_subnetworks"])
    loc = sub[sub["perturbation"].isin(LOCAL)]
    swp = sub[sub["kind"] == "sweep"]
    rows.append({
        "Territoire": CITY_FR.get(city, city),
        "Profil écologique": GUILD_FR.get(guild, guild),
        "Hab. connecté réf.": f"{ch:.0f} %",
        "Hab. connecté (local)": _range(loc, ch, "connected_habitat_pct_delta_pct") + " %",
        "Hab. connecté (balayage)": (_range(swp, ch, "connected_habitat_pct_delta_pct") + " %") if len(swp) else "n. d.",
        "Sous-réseaux réf.": f"{ns:.0f}",
        "Sous-réseaux (local)": _range(loc, ns, "n_subnetworks_delta_pct"),
        "Sous-réseaux (balayage)": _range(swp, ns, "n_subnetworks_delta_pct") if len(swp) else "n. d.",
    })

out = pd.DataFrame(rows)
n_couples = out.shape[0]
print(f"# couples couverts: {n_couples} / 24\n")
# markdown table
cols = list(out.columns)
print("| " + " | ".join(cols) + " |")
print("|" + "|".join("---" for _ in cols) + "|")
for _, r in out.iterrows():
    print("| " + " | ".join(str(r[c]) for c in cols) + " |")
dest = os.path.join(ROOT, "data", "sensitivity", "sensitivity_annexe.md")
with open(dest, "w") as fh:
    fh.write(f"Couverture: {n_couples}/24 couples (ville x profil).\n\n")
    fh.write("| " + " | ".join(cols) + " |\n")
    fh.write("|" + "|".join("---" for _ in cols) + "|\n")
    for _, r in out.iterrows():
        fh.write("| " + " | ".join(str(r[c]) for c in cols) + " |\n")
print(f"\nwrote {dest}")
