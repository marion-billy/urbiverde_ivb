"""Generate the §4.2 figure: connected habitat by territory and ecological profile.

Reads the re-run stats CSVs and plots, for the six territories (ordered by total
vegetated cover), the connected-habitat share of each of the four ecological profiles.
It makes visible both the coverage gradient (connectivity rises with vegetated cover)
and the woodland-profile anomaly (La Roche-sur-Yon: high total green but low arboreal
connectivity because forest is sparse in an agricultural matrix).

Run: python3 make_territory_connectivity.py
"""

from __future__ import annotations

import csv
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUTROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", "data", "outputs"))

# territory key -> display name
TERR = {
    "LRSY": "La Roche-sur-Yon",
    "Nancy": "Nancy",
    "Perpignan": "Perpignan",
    "Kourou": "Kourou",
    "Toulouse": "Toulouse",
    "LaRochelle": "La Rochelle",
}
# profile key -> (display, colour)
PROF = [
    ("ground_mammal", "Petit mammifère terrestre", "#2E7D32"),
    ("arboreal_mammal", "Mammifère arboricole", "#8D6E63"),
    ("forest_edge_bird", "Oiseau de lisière", "#1565C0"),
    ("ground_reptile", "Reptile terrestre", "#F5A623"),
]


def stat(city: str, prof: str, field: str) -> float | None:
    p = f"{OUTROOT}/{city}/{prof}/stats_{prof}_{city}.csv"
    if not os.path.exists(p):
        return None
    with open(p) as fh:
        rows = list(csv.DictReader(fh))
    return float(rows[0][field]) if rows else None


def main() -> None:
    # total vegetated cover per territory (ground_mammal habitat = trees+shrub+grass)
    cover = {k: stat(k, "ground_mammal", "habitat_coverage_pct") for k in TERR}
    order = sorted(TERR, key=lambda k: cover[k] if cover[k] is not None else 0)

    fig, ax = plt.subplots(figsize=(11, 5.5))
    n_prof = len(PROF)
    width = 0.19
    x = np.arange(len(order))

    for i, (pk, plabel, colour) in enumerate(PROF):
        vals = [stat(k, pk, "connected_habitat_pct") or 0 for k in order]
        ax.bar(x + (i - (n_prof - 1) / 2) * width, vals, width, label=plabel, color=colour)

    # annotate total vegetated cover above each territory group
    ymax = 100
    for xi, k in zip(x, order):
        c = cover[k]
        if c is not None:
            ax.text(xi, ymax * 0.97, f"couvert végétal {c:.0f} %", ha="center", va="top",
                    fontsize=8.5, color="#455A64", style="italic")

    ax.set_xticks(x)
    ax.set_xticklabels([TERR[k] for k in order], fontsize=10)
    ax.set_ylabel("Part d'habitat fonctionnellement connecté (%)", fontsize=10)
    ax.set_ylim(0, ymax)
    ax.set_title("Connectivité par territoire et par profil écologique\n"
                 "(territoires classés par couverture végétale croissante)", fontsize=11)
    ax.legend(fontsize=9, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.09),
              framealpha=0.9, frameon=False)
    ax.grid(axis="y", linestyle=":", alpha=0.5)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()

    out = os.path.join(HERE, "territoire_connectivite.png")
    fig.savefig(out, dpi=200, bbox_inches="tight")
    print("wrote", out)


if __name__ == "__main__":
    main()
