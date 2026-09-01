# -*- coding: utf-8 -*-
"""Diagramme en tornade de la sensibilité locale (fig:tornade du rapport).

Source : _sandbox/sensitivity/sensitivity_summary.csv, lignes kind == "local", produites par le
dispositif de perturbation locale décrit en 2.7.1 : plus ou moins 25 % sur la distance de
dispersion, plus ou moins 20 % sur l'ensemble des frictions, puis sur chaque coefficient de
friction pris isolément.

Sortie : papier/internship_report/figures/tornado_sensibilite.png

Lecture : chaque barre part de la référence (0) et s'étend jusqu'à la variation de la part
d'habitat connecté observée sous perturbation. Les paramètres sont rangés du plus influent au
moins influent, dans un ordre commun aux panneaux afin qu'ils se comparent ligne à ligne.

Les libellés des classes d'occupation du sol reprennent ceux de species_params.py, qui fait
foi, et que l'annexe A du rapport reprend à l'identique. Le territoire ne figure pas dans les
titres de panneaux : il est dit dans la légende de la figure, les deux panneaux portant le
même.

Ce que la figure ne dit pas et que le corps du rapport doit dire : les classes sans effet
mesurable, et le résultat des couples de La Rochelle, qui ne portent que les perturbations
globales. Le script les imprime en fin d'exécution pour que le texte reste synchronisé.

Usage : python _sandbox/make_tornado_fig.py
"""
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import to_rgba
from matplotlib.patches import Patch

RACINE = Path(__file__).resolve().parents[3]
CSV = RACINE / "_sandbox" / "sensitivity" / "sensitivity_summary.csv"
SORTIE = RACINE / "papier" / "internship_report" / "figures" / "tornado_sensibilite.png"

METRIQUE = "connected_habitat_pct_delta_pct"
SEUIL_PANNEAU = 5   # nb minimal de paramètres pour mériter un panneau plutôt qu'une note

# libellés de species_params.py, repris à l'identique par l'annexe A du rapport
LC_LIBELLE = {
    10: "Couvert arboré", 20: "Arbustes", 30: "Prairies, herbacées", 40: "Cultures",
    50: "Urbain diffus", 51: "Bâtiments", 52: "Routes principales",
    53: "Routes secondaires, voirie", 54: "Chemins et sentiers", 55: "Voies ferrées",
    60: "Sols nus", 80: "Eaux permanentes", 90: "Zones humides herbacées", 95: "Mangroves",
}
# palette des espèces, convention du rapport ; les profils sont nommés par l'espèce repère
PROFILS = {
    "ground_mammal":    ("Profil hérisson", "#CC79A7"),
    "arboreal_mammal":  ("Profil écureuil", "#D55E00"),
    "forest_edge_bird": ("Profil fauvette", "#0072B2"),
    "ground_reptile":   ("Profil lézard",   "#5D3A9B"),
}
VILLES = {"Perpignan": "Perpignan", "LaRochelle": "La Rochelle", "Nancy": "Nancy",
          "Toulouse": "Toulouse", "LRSY": "La Roche-sur-Yon", "Kourou": "Kourou"}

GLOBAUX = ("Distance de dispersion (± 25 %)", "Toutes frictions ensemble (± 20 %)")


def etiquette(perturbation):
    """« c53_m20 » -> (« Routes secondaires, voirie (± 20 %) », signe de la perturbation)."""
    base, _, direction = perturbation.rpartition("_")
    signe = -1 if direction.startswith("m") else +1
    if base == "d0":
        return GLOBAUX[0], signe
    if base == "fric":
        return GLOBAUX[1], signe
    code = int(base.lstrip("c"))
    return f"{LC_LIBELLE.get(code, f'code {code}')} (± 20 %)", signe


def charger():
    brut = [r for r in csv.DictReader(CSV.open(encoding="utf-8")) if r["kind"] == "local"]
    if not brut:
        raise SystemExit(f"aucune ligne kind=local dans {CSV}")
    donnees = defaultdict(dict)
    for r in brut:
        if r[METRIQUE] in ("", "nan", "NaN"):
            continue
        lib, signe = etiquette(r["perturbation"])
        donnees[(r["city"], r["guild"], lib)][signe] = float(r[METRIQUE])
    return donnees


def main():
    donnees = charger()

    par_couple = defaultdict(set)
    for ville, profil, lib in donnees:
        par_couple[(ville, profil)].add(lib)
    panneaux = sorted(c for c, libs in par_couple.items() if len(libs) >= SEUIL_PANNEAU)
    resumes = sorted(c for c, libs in par_couple.items() if len(libs) < SEUIL_PANNEAU)
    if not panneaux:
        raise SystemExit("aucun couple ne porte la perturbation détaillée")

    influence = defaultdict(list)
    for (ville, profil, lib), v in donnees.items():
        if (ville, profil) in panneaux:
            influence[lib].append(max(abs(x) for x in v.values()))
    ordre = sorted(influence, key=lambda k: -float(np.mean(influence[k])))
    nuls = [k for k in ordre if max(influence[k]) == 0]
    ordre = [k for k in ordre if k not in nuls]

    limite = max(abs(x) for (ville, profil, _), v in donnees.items()
                 if (ville, profil) in panneaux for x in v.values()) * 1.18
    # panneaux empilés plutôt que côte à côte : la colonne des étiquettes de paramètres
    # n'est plus payée deux fois, et la figure tient sur 16 cm sans réduction notable
    fig, axs = plt.subplots(len(panneaux), 1, squeeze=False,
                            figsize=(7.0, 0.9 + 0.30 * len(ordre) * len(panneaux)),
                            sharex=True, sharey=True)
    y = np.arange(len(ordre))[::-1]

    for ax, (ville, profil) in zip(axs.ravel(), panneaux):
        lib_prof, couleur = PROFILS[profil]
        for yi, lib in zip(y, ordre):
            v = donnees.get((ville, profil, lib), {})
            for signe, alpha in ((-1, 1.0), (+1, 0.45)):
                if signe in v:
                    ax.barh(yi + 0.19 * signe, v[signe], height=0.34, color=couleur,
                            alpha=alpha, edgecolor="white", linewidth=0.4, zorder=2)
        ax.axvline(0, color="#333333", linewidth=1.0, zorder=3)
        ax.set_title(lib_prof, fontsize=11, color="#222222", fontweight="bold", pad=9)
        ax.set_xlim(-limite, limite)
        ax.set_ylim(-0.8, len(ordre) - 0.2)
        ax.set_xlabel("Variation de la part d'habitat connecté (%)", fontsize=9)
        ax.grid(axis="x", color="#e4e4e4", linewidth=0.6, zorder=0)
        ax.set_axisbelow(True)
        ax.tick_params(axis="y", length=0, labelsize=8.5)
        # cadre du profil, dans sa couleur, comme sur la figure des ratios GBIF
        ax.set_facecolor(to_rgba(couleur, 0.06))
        for cote in ax.spines.values():
            cote.set_visible(True)
            cote.set_edgecolor(couleur)
            cote.set_alpha(0.55)
            cote.set_linewidth(1.1)

    for ax in axs.ravel():
        ax.set_yticks(y)
        ax.set_yticklabels(ordre, fontsize=8.5)

    fig.tight_layout(rect=[0, 0.02, 1, 1])
    # La legende se pose sous la boite REELLE des axes, intitule d'abscisse compris,
    # mesuree par le moteur de rendu : un decalage fixe la collait a l'axe des x.
    # Elle est par ailleurs centree sur la zone tracee et non sur la figure, qui
    # inclut la marge des etiquettes de parametres, a gauche.
    fig.canvas.draw()
    rendu = fig.canvas.get_renderer()
    bas = min(ax.get_tightbbox(rendu).y0 for ax in axs.ravel())
    y = fig.transFigure.inverted().transform((0, bas))[1] - 0.035
    gauche, droite = axs[-1][0].get_position(), axs[-1][-1].get_position()
    fig.legend(handles=[Patch(facecolor="#777777", alpha=1.0, label="paramètre diminué"),
                        Patch(facecolor="#777777", alpha=0.45, label="paramètre augmenté")],
               loc="upper center", ncol=2, frameon=False, fontsize=9,
               bbox_to_anchor=((gauche.x0 + droite.x1) / 2, y))
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(SORTIE, dpi=300, bbox_inches="tight", facecolor="white")

    # --- ce qui doit figurer dans le corps du rapport, la figure ne le porte plus
    print(f"OK -> {SORTIE}")
    print(f"   panneaux : {[f'{VILLES.get(v, v)} / {PROFILS[p][0]}' for v, p in panneaux]}")
    print(f"   {len(ordre)} paramètres influents\n")
    print("À DIRE DANS LE TEXTE DU RAPPORT (plus porté par la figure) :")
    print(f"   sans effet mesurable ({len(nuls)}) : "
          + ", ".join(sorted(n.split(" (")[0] for n in nuls)))
    for ville, profil in resumes:
        bouts = [f"{lib.split(' (')[0].lower()} {min(donnees[(ville, profil, lib)].values()):+.1f}"
                 f" / {max(donnees[(ville, profil, lib)].values()):+.1f} %"
                 for lib in GLOBAUX if (ville, profil, lib) in donnees]
        print(f"   {VILLES.get(ville, ville)}, {PROFILS[profil][0].lower()} "
              f"(perturbations globales seules) : " + " ; ".join(bouts))
    print("\n   4 premiers paramètres :")
    for lib in ordre[:4]:
        vals = [x for (v, p, l), d in donnees.items() if l == lib for x in d.values()]
        print(f"     {lib:38s} {min(vals):+6.1f} à {max(vals):+6.1f} %")


if __name__ == "__main__":
    main()
