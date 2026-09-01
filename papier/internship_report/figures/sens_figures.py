"""Grouped sensitivity figures (small multiples), all profiles x all territories with data.
Two composite PNGs per axis (d0, friction-contrast), each = 2 metric rows (part connectee, nb
sous-reseaux) x N territory columns, one coloured line per ecological profile. Read-only inputs.
Output: papier/internship_report/figures/sens_curves_d0.png and sens_curves_contrast.png
"""
import glob, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..")
OUT = os.path.dirname(os.path.abspath(__file__)); os.makedirs(OUT, exist_ok=True)
CITIES = ["Kourou", "Perpignan", "Nancy", "LaRochelle", "LRSY", "Toulouse"]
CITY_FR = {"LaRochelle": "La Rochelle", "LRSY": "La Roche-sur-Yon"}
# profil -> (label, colour)
PROF = {"ground_mammal": ("profil hérisson", "#CC79A7"),
        "arboreal_mammal": ("profil écureuil", "#D55E00"),
        "forest_edge_bird": ("profil fauvette", "#0072B2"),
        "ground_reptile": ("profil lézard", "#5D3A9B")}
METRICS = [("connected_habitat_pct", "Part d'habitat connecté (%)"),
           ("n_subnetworks", "Nombre de sous-réseaux")]
AXES = {"swd0": ("d₀ (% de la référence)", [50, 60, 70, 80, 90, 110, 120], 100),
        "swfc": ("Contraste de friction (%)", [0, 25, 50, 75, 125, 150, 200], 100)}


# All perturbed sensitivity runs live in one long CSV (perturbation, city, guild + stat cols),
# instead of a deep _sandbox/sensitivity/<tag>/<city>/<guild>/stats.csv tree.
ALL = pd.read_csv(os.path.join(ROOT, "_sandbox", "sensitivity", "all_stats.csv"))


def series(city, guild, metric, prefix, scales, ref_x):
    pts = {}
    sub = ALL[(ALL["city"] == city) & (ALL["guild"] == guild)]
    for m in scales:
        row = sub[sub["perturbation"] == f"{prefix}_{m:03d}"]
        if not row.empty:
            pts[m] = float(row.iloc[0][metric])
    fb = glob.glob(f"{ROOT}/data/outputs/{city}/{guild}/stats_*.csv")   # baseline stays in data/outputs
    if fb:
        pts[ref_x] = float(pd.read_csv(fb[0]).iloc[0][metric])
    xs, ys = [], []
    for x in sorted(pts):
        xs.append(x); ys.append(pts[x])
    return xs, ys


def make_figure(prefix):
    xlabel, scales, ref_x = AXES[prefix]
    tag0 = f"{prefix}_{scales[0]:03d}"
    cities = [c for c in CITIES
              if not ALL[(ALL["city"] == c) & (ALL["perturbation"] == tag0)].empty]
    # 1,80 pouce par ligne et non 2,15 : posee par sa hauteur dans le rapport, une figure
    # plus elancee serait davantage reduite et son texte deviendrait illisible.
    # villes en lignes, indicateurs en colonnes : figure verticale, lisible en page portrait.
    # sharey par colonne, pour que les territoires se comparent sur un même indicateur.
    nrow, ncol = len(cities), len(METRICS)
    fig, axs = plt.subplots(nrow, ncol, figsize=(3.6 * ncol, 1.80 * nrow), squeeze=False,
                            sharex=True, sharey="col")
    for i, city in enumerate(cities):
        for j, (mcol, mlab) in enumerate(METRICS):
            ax = axs[i][j]
            for guild, (plab, col) in PROF.items():
                xs, ys = series(city, guild, mcol, prefix, scales, ref_x)
                if xs:
                    ax.plot(xs, ys, "o-", ms=3.5, lw=1.5, color=col,
                            label=plab if (i == 0 and j == 0) else None)
            ax.axvline(ref_x, color="0.4", ls="--", lw=0.8)
            if i == 0:
                ax.set_title(mlab, fontsize=11.5, fontweight="bold")
            if j == 0:
                ax.set_ylabel(CITY_FR.get(city, city), fontsize=11.5, fontweight="bold")
            if i == nrow - 1:
                ax.set_xlabel(xlabel, fontsize=10)
            ax.grid(ls=":", alpha=0.4); ax.tick_params(labelsize=9)
    # pas de titre : la légende du rapport porte déjà l'axe balayé et le sens de la
    # ligne pointillée
    fig.tight_layout(rect=[0, 0.035, 1, 1])
    # légende centrée sur la zone tracée, non sur la figure (qui inclut la marge de gauche)
    fig.canvas.draw()
    bas = min(a.get_tightbbox(fig.canvas.get_renderer()).y0 for a in axs.ravel())
    y = fig.transFigure.inverted().transform((0, bas))[1] - 0.012
    g, d = axs[-1][0].get_position(), axs[-1][-1].get_position()
    fig.legend(loc="upper center", ncol=4, fontsize=10.5, frameon=False,
               bbox_to_anchor=((g.x0 + d.x1) / 2, y))
    dest = os.path.join(OUT, f"sens_curves_{ {'swd0':'d0','swfc':'contrast'}[prefix] }.png")
    fig.savefig(dest, dpi=140, bbox_inches="tight"); plt.close(fig)
    print(f"-> {os.path.relpath(dest, ROOT)}  ({nrow} territoires x {ncol} indicateurs)")


for p in ("swd0", "swfc"):
    make_figure(p)
