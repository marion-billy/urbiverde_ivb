# -*- coding: utf-8 -*-
"""Schéma de la segmentation morphologique, avec les paramètres réellement employés.

Sortie : papier/internship_report/figures/schema_mspa.png

Le schéma n'illustre pas une érosion-dilatation : la chaîne ne fait qu'une **érosion** d'un
pixel avec un élément structurant 3x3 (utils/connectivity.py, fast_mspa), puis classe les
taches d'origine d'après la surface de cœur qui subsiste. La géométrie exportée reste la
tache entière, lisière comprise.

L'érosion dessinée est calculée par le même appel scipy que la chaîne, sur une grille
synthétique dont chaque pixel vaut 10 m, soit 0,01 ha. Les quatre taches couvrent les quatre
issues possibles du classement ; leurs surfaces sont exactes, mais l'étiquette de chacune
énonce la règle appliquée plutôt que la valeur mesurée.

Le commentaire est volontairement réduit : les paramètres et le sens de lecture sont dans la
légende de la figure, dans le rapport.

Usage : python _sandbox/make_schema_mspa.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import ndimage

RACINE = Path(__file__).resolve().parents[3]
SORTIE = RACINE / "papier" / "internship_report" / "figures" / "schema_mspa.png"

PIXEL_M = 10.0                      # résolution WorldCover
HA_PAR_PIXEL = PIXEL_M ** 2 / 1e4   # 0,01 ha
SEUIL_NOYAU_HA = 1.0                # core_min_ha
SEUIL_RELAIS_HA = 0.1               # islet_min_ha

C_FOND = "#f4f4f2"
C_HABITAT = "#b2df8a"    # habitat brut, couleur des espaces relais du rapport
C_NOYAU = "#206c2c"      # cœur conservé, couleur des noyaux du rapport
C_ECARTE = "#c9c9c9"
C_GRILLE = "#ffffff"


def grille():
    """Quatre taches synthétiques, une par issue du classement."""
    g = np.zeros((22, 40), dtype=np.uint8)
    g[3:15, 2:14] = 1      # 12x12 px  -> cœur 10x10 = 1,00 ha  -> noyau
    g[4:12, 17:25] = 1     #  8x8  px  -> cœur  6x6  = 0,36 ha  -> espace relais
    g[5:7, 28:38] = 1      # 10x2  px  -> aucun cœur            -> écartée
    g[13:16, 30:33] = 1    #  3x3  px  -> cœur 1 px, 0,09 ha    -> écartée
    return g


def classer(g):
    """Reproduit utils/connectivity.py : érosion 3x3 d'un pixel, puis seuils de surface."""
    coeur = ndimage.binary_erosion(g, structure=np.ones((3, 3)), iterations=1)
    etiquettes, n = ndimage.label(g)
    fiches = []
    for e in range(1, n + 1):
        tache = etiquettes == e
        surface = tache.sum() * HA_PAR_PIXEL
        coeur_ha = (tache & coeur).sum() * HA_PAR_PIXEL
        # le motif énonce la règle appliquée, non la valeur mesurée : le schéma sert à
        # faire comprendre le critère, pas à donner un exemple chiffré
        if coeur_ha >= SEUIL_NOYAU_HA:
            classe = "Noyau de biodiversité"
            motif = f"cœur ≥ {SEUIL_NOYAU_HA:g} ha"
        elif surface >= SEUIL_RELAIS_HA and coeur_ha > 0:
            classe = "Espace relais"
            motif = (f"cœur non nul, tache ≥ {SEUIL_RELAIS_HA:g} ha".replace(".", ","))
        elif coeur_ha == 0:
            classe = "Écartée"
            motif = "sans cœur"
        else:
            classe = "Écartée"
            motif = f"tache < {SEUIL_RELAIS_HA:g} ha".replace(".", ",")
        fiches.append({"masque": tache, "surface": surface, "coeur_ha": coeur_ha,
                       "classe": classe, "motif": motif})
    # l'ordre des lettres suit le classement, non la géométrie : le déduire des
    # coordonnées donnait un ordre différent à chaque changement de disposition
    def rang(f):
        if f["classe"] == "Noyau de biodiversité":
            return 0
        if f["classe"] == "Espace relais":
            return 1
        return 2 if "tache" in f["motif"] else 3
    fiches.sort(key=rang)
    for lettre, f in zip("ABCD", fiches):
        f["lettre"] = lettre
    return coeur, fiches


def dessiner(ax, g, image, palette, titre):
    ax.imshow(image, cmap=matplotlib.colors.ListedColormap(palette),
              vmin=0, vmax=len(palette) - 1, interpolation="nearest")
    ax.set_xlim(-0.5, g.shape[1] - 0.5)
    ax.set_ylim(g.shape[0] - 0.5, -0.5)
    ax.set_xticks([])
    ax.set_yticks([])
    for cote in ax.spines.values():
        cote.set_visible(False)
    for x in range(g.shape[1] + 1):
        ax.axvline(x - 0.5, color=C_GRILLE, linewidth=0.5, zorder=3)
    for y in range(g.shape[0] + 1):
        ax.axhline(y - 0.5, color=C_GRILLE, linewidth=0.5, zorder=3)
    ax.set_title(titre, fontsize=18, loc="left", fontweight="bold", color="#222222", pad=6)


def main():
    g = grille()
    coeur, fiches = classer(g)
    # les trois panneaux sur une ligne : empilés, la figure sortait en portrait de
    # 4 x 7,5 pouces et ne tenait pas dans la page une fois posée sur la justification
    fig, axs = plt.subplots(1, 3, figsize=(11.0, 2.9))

    dessiner(axs[0], g, np.where(g == 1, 1, 0), [C_FOND, C_HABITAT],
             "(a)  Habitat binaire")
    dessiner(axs[1], g, np.where(coeur & (g == 1), 2, np.where(g == 1, 1, 0)),
             [C_FOND, C_HABITAT, C_NOYAU], "(b)  Érosion")

    rendu = np.zeros_like(g, dtype=int)
    for f in fiches:
        rendu[f["masque"]] = {"Noyau de biodiversité": 3,
                              "Espace relais": 2}.get(f["classe"], 1)
    dessiner(axs[2], g, rendu, [C_FOND, C_ECARTE, C_HABITAT, C_NOYAU], "(c)  Classement")

    # la lettre est posée SOUS la tache, sur le seul panneau que la clé commente
    for f in fiches:
        ys, xs = np.where(f["masque"])
        axs[2].text(xs.mean(), ys.max() + 1.2, f"{f['lettre']}.", ha="center", va="top",
                    fontsize=16, fontweight="bold", color="black")

    # la règle de classement, à position fixe sous le panneau (c)
    cle = "\n".join(f"{f['lettre']}.  {f['classe']}, {f['motif']}"
                    for f in fiches)
    axs[2].text(0.0, -0.05, cle, transform=axs[2].transAxes, ha="left", va="top",
                fontsize=12, color="#444444", linespacing=1.25)

    fig.tight_layout()
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(SORTIE, dpi=300, bbox_inches="tight", facecolor="white")

    print(f"OK -> {SORTIE}")
    for f in fiches:
        print(f"   {f['surface']:.2f} ha, cœur {f['coeur_ha']:.2f} ha -> {f['classe']}")


if __name__ == "__main__":
    main()
