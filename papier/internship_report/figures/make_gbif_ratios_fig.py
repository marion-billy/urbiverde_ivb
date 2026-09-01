# -*- coding: utf-8 -*-
"""Figure des ratios de sélection GBIF, agreges sur les cinq territoires temperes.

Source  : papier/internship_report/figures/ratios_pooled.csv (produit par gbif_crosstest.py)
Sortie  : papier/internship_report/figures/gbif_ratios_pooled.png

Un ratio superieur a 1 signale une classe frequentee plus souvent que sa part de surface ne
le laisserait attendre, un ratio inferieur a 1 l'inverse. L'axe est logarithmique de sorte
qu'une preference d'un facteur deux et un evitement du meme facteur s'ecartent visuellement
d'autant de la ligne de reference.

Representation en points et non en barres : une barre part de zero et suggere une quantite
accumulee, alors qu'un ratio de sélection est une position sur une echelle dont l'origine
utile est 1, la fréquentation proportionnelle a la surface disponible. Le point donne cette
position, la moustache donne l'intervalle de confiance.

Deux jeux de couleurs cohabitent sans se confondre : les points prennent la couleur de la
classe d'espace, celle des cartes du rapport, et chaque profil est encadre dans la couleur de
son espece repere, celle des autres figures. Les profils suivent l'ordre du rapport.

Usage :
    python _sandbox/make_gbif_ratios_fig.py                 # echelle log (defaut)
    python _sandbox/make_gbif_ratios_fig.py --echelle lin   # echelle lineaire
"""
import argparse
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.ticker import FixedFormatter, FixedLocator

RACINE = Path(__file__).resolve().parents[3]
CSV = RACINE / "papier" / "internship_report" / "figures" / "ratios_pooled.csv"
SORTIE = RACINE / "papier" / "internship_report" / "figures" / "gbif_ratios_pooled.png"

# profils dans l'ordre du rapport, avec la couleur de leur espece repere
PROFILS = [
    ("ground_mammal",    "Profil hérisson", "#CC79A7"),
    ("arboreal_mammal",  "Profil écureuil", "#D55E00"),
    ("forest_edge_bird", "Profil fauvette", "#0072B2"),
    ("ground_reptile",   "Profil lézard",   "#5D3A9B"),
]
# classes d'espaces, de gauche a droite dans chaque profil ; couleurs des cartes du rapport
CLASSES = [
    ("core",           "Noyau de biodiversité", "#206c2c"),
    ("stepping_stone", "Espace relais",         "#b2df8a"),
    ("corridor",       "Tracé de moindre coût", "#f5ad04"),
    ("matrix",         "Matrice",               "#9e9e9e"),
]
ECART = 0.19    # ecart horizontal entre deux classes d'un meme profil
DEMI = 0.44     # demi-largeur du cadre de profil


def charger():
    table, effectifs = {}, {}
    for r in csv.DictReader(CSV.open(encoding="utf-8")):
        table[(r["guild"], r["class"])] = (float(r["ratio"]), float(r["ci_lo"]),
                                           float(r["ci_hi"]))
        effectifs[r["guild"]] = int(r["n_focal_tot"])
    manquants = [(g, c) for g, _, _ in PROFILS for c, _, _ in CLASSES if (g, c) not in table]
    if manquants:
        raise SystemExit(f"couples absents du CSV : {manquants}")
    return table, effectifs


def main(echelle):
    table, effectifs = charger()
    fig, ax = plt.subplots(figsize=(7.0, 4.1))

    if echelle == "log":
        ax.set_yscale("log")
        ax.set_ylim(0.14, 4.2)
    else:
        ax.set_ylim(0, 3.4)

    x = np.arange(len(PROFILS), dtype=float)

    # cadre de profil, dans la couleur de l'espece repere
    for xi, (_, _, coul_prof) in zip(x, PROFILS):
        ax.axvspan(xi - DEMI, xi + DEMI, facecolor=coul_prof, alpha=0.06, zorder=0)
        ax.axvspan(xi - DEMI, xi + DEMI, facecolor="none", edgecolor=coul_prof,
                   linewidth=1.1, alpha=0.55, zorder=4)

    for xi, (guild, _, _) in zip(x, PROFILS):
        for k, (cle, _, couleur) in enumerate(CLASSES):
            r, lo, hi = table[(guild, cle)]
            xk = xi + (k - (len(CLASSES) - 1) / 2) * ECART
            ax.plot([xk, xk], [lo, hi], color=couleur, linewidth=1.7, alpha=0.8,
                    solid_capstyle="round", zorder=2)
            ax.plot(xk, r, marker="o", markersize=8.5, markerfacecolor=couleur,
                    markeredgecolor="#2b2b2b", markeredgewidth=0.9, zorder=3)

    # la ligne de reference se repere par sa graduation en gras ; le sens de lecture
    # (au-dessus recherche, au-dessous evite) est dit dans le texte du rapport
    ax.axhline(1.0, color="#333333", linewidth=1.0, linestyle="--", zorder=1)

    if echelle == "log":
        ax.yaxis.set_major_locator(FixedLocator([0.25, 0.5, 1, 2, 4]))
        ax.yaxis.set_minor_locator(FixedLocator([]))
        ax.yaxis.set_major_formatter(FixedFormatter(["0,25", "0,5", "1", "2", "4"]))
        for etiq, val in zip(ax.get_yticklabels(), [0.25, 0.5, 1, 2, 4]):
            if val == 1:
                etiq.set_fontweight("bold")   # la reference se repere sur l'axe
    else:
        ax.set_yticks([0, 0.5, 1, 1.5, 2, 2.5, 3])
        ax.set_yticklabels(["0", "0,5", "1", "1,5", "2", "2,5", "3"])

    ax.set_xticks(x)
    ax.set_xticklabels([f"{lib}\n(n = {effectifs[g]})" for g, lib, _ in PROFILS], fontsize=10)
    for etiq, (_, _, coul_prof) in zip(ax.get_xticklabels(), PROFILS):
        etiq.set_color(coul_prof)
        etiq.set_fontweight("bold")
    ax.set_xlim(-DEMI - 0.14, len(PROFILS) - 1 + DEMI + 0.14)
    ax.set_ylabel("Ratio de sélection\n(usage observé / disponibilité)", fontsize=9.5)
    ax.tick_params(axis="both", length=0, labelsize=9)
    ax.grid(axis="y", color="#dddddd", linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)
    for cote in ("top", "right", "bottom"):
        ax.spines[cote].set_visible(False)

    fig.tight_layout()
    # legende en bas, centree sur la zone tracee et non sur la figure entiere
    # (laquelle inclut la marge des etiquettes de profil, a gauche)
    boite = ax.get_position()
    fig.legend(handles=[Line2D([], [], linestyle="none", marker="o", markersize=8.5,
                               markerfacecolor=c, markeredgecolor="#2b2b2b",
                               markeredgewidth=0.9, label=lib)
                        for _, lib, c in CLASSES],
               frameon=False, fontsize=9, ncol=4, loc="upper center",
               bbox_to_anchor=((boite.x0 + boite.x1) / 2, boite.y0 - 0.10),
               handletextpad=0.3, columnspacing=1.6)
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(SORTIE, dpi=300, bbox_inches="tight", facecolor="white")
    print(f"OK -> {SORTIE}  (echelle {echelle}, moustaches = IC 95 % bootstrap)")
    for guild, lib, _ in PROFILS:
        bouts = " | ".join(f"{nom.split(' ')[0].lower()} {table[(guild, cle)][0]:.2f}"
                           for cle, nom, _ in CLASSES)
        print(f"   {lib:16s} n={effectifs[guild]:4d}  {bouts}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--echelle", choices=["log", "lin"], default="log")
    main(p.parse_args().echelle)
