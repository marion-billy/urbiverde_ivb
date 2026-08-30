"""Build the sweep response curves (d0 + friction contrast) for Perpignan once the runs are done.

Run after _sandbox/logs/SWEEP_Perpignan_DONE.flag appears:
    python3 _sandbox/make_response_curves.py
Produces figures/response_{d0,contrast}_{guild}.png and prints the KPI-vs-parameter tables so the
tipping-point values can be read off and written into rapport_5 (section 5.5.2).
"""
import os
import sys

sys.path.insert(1, "utils")
import sensitivity_metrics as sm

FIG = "papier/internship_report/figures"
KPIS = [
    ("connected_habitat_pct", "part d'habitat connectée (%)", "#2E7D32"),
    ("n_subnetworks", "nombre de sous-réseaux", "#C62828"),
]
NOMS = {"ground_mammal": "Hérisson", "ground_reptile": "Lézard"}
SWEEPS = [
    ("swd0", "response_d0", "facteur appliqué à la distance de dispersion d₀", "de d₀"),
    ("swfc", "response_contrast", "facteur de contraste des frictions k", "du contraste de friction"),
]

for g, nom in NOMS.items():
    for prefix, stem, xlabel, what in SWEEPS:
        df = sm.response_curve("data/outputs", "data/sensitivity", "Perpignan", g, prefix,
                               KPIS, f"{FIG}/{stem}_{g}.png", xlabel,
                               f"Perpignan, {nom} : réponse au balayage {what}")
        print(f"\n=== {nom} ({g}) — balayage {what} ===")
        print(df.to_string(index=False))

os.system(f"chmod a+rwX {FIG}/response_*.png")
print("\nfigures response_*.png écrites.")
