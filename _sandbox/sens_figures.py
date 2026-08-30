"""Grouped sensitivity figures (small multiples), all profiles x all territories with data.
Two composite PNGs per axis (d0, friction-contrast), each = 2 metric rows (part connectee, nb
sous-reseaux) x N territory columns, one coloured line per ecological profile. Read-only inputs.
Output: _sandbox/figures_sens/sens_curves_d0.png and sens_curves_contrast.png
"""
import glob, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "_sandbox", "figures_sens"); os.makedirs(OUT, exist_ok=True)
CITIES = ["Kourou", "Perpignan", "Nancy", "LaRochelle", "LRSY", "Toulouse"]
# profil -> (label, colour)
PROF = {"ground_mammal": ("petit mammifère (hérisson)", "#2E8B84"),
        "arboreal_mammal": ("mammifère arboricole (écureuil)", "#BE842A"),
        "forest_edge_bird": ("oiseau de lisière (fauvette)", "#3B6EA5"),
        "ground_reptile": ("reptile (lézard)", "#B23A48")}
METRICS = [("connected_habitat_pct", "Part d'habitat connecté (%)"),
           ("n_subnetworks", "Nombre de sous-réseaux")]
AXES = {"swd0": ("d₀ (% de la référence)", [50, 60, 70, 80, 90, 110, 120], 100),
        "swfc": ("Contraste de friction (%)", [0, 25, 50, 75, 125, 150, 200], 100)}


def series(city, guild, metric, prefix, scales, ref_x):
    xs, ys = [], []
    pts = {}
    for m in scales:
        f = glob.glob(f"{ROOT}/data/sensitivity/{prefix}_{m:03d}/data/outputs/{city}/{guild}/stats_*.csv")
        if f:
            pts[m] = float(pd.read_csv(f[0]).iloc[0][metric])
    fb = glob.glob(f"{ROOT}/data/outputs/{city}/{guild}/stats_*.csv")
    if fb:
        pts[ref_x] = float(pd.read_csv(fb[0]).iloc[0][metric])
    for x in sorted(pts):
        xs.append(x); ys.append(pts[x])
    return xs, ys


def make_figure(prefix):
    xlabel, scales, ref_x = AXES[prefix]
    cities = [c for c in CITIES
              if glob.glob(f"{ROOT}/data/sensitivity/{prefix}_{scales[0]:03d}/data/outputs/{c}/*/stats_*.csv")]
    nrow, ncol = len(METRICS), len(cities)
    fig, axs = plt.subplots(nrow, ncol, figsize=(3.1 * ncol, 3.0 * nrow), squeeze=False)
    for i, (mcol, mlab) in enumerate(METRICS):
        for j, city in enumerate(cities):
            ax = axs[i][j]
            for guild, (plab, col) in PROF.items():
                xs, ys = series(city, guild, mcol, prefix, scales, ref_x)
                if xs:
                    ax.plot(xs, ys, "o-", ms=3, lw=1.3, color=col, label=plab if (i == 0 and j == 0) else None)
            ax.axvline(ref_x, color="0.4", ls="--", lw=0.8)
            if i == 0:
                ax.set_title(city, fontsize=10, fontweight="bold")
            if j == 0:
                ax.set_ylabel(mlab, fontsize=8)
            if i == nrow - 1:
                ax.set_xlabel(xlabel, fontsize=8)
            ax.grid(ls=":", alpha=0.4); ax.tick_params(labelsize=7)
    fig.legend(loc="lower center", ncol=4, fontsize=8, frameon=False, bbox_to_anchor=(0.5, -0.02))
    fig.suptitle(f"Courbes de réponse de la sensibilité, axe : {xlabel.split(' (')[0]}\n"
                 "(ligne pointillée = référence)", fontsize=11)
    fig.tight_layout(rect=[0, 0.04, 1, 0.94])
    dest = os.path.join(OUT, f"sens_curves_{ {'swd0':'d0','swfc':'contrast'}[prefix] }.png")
    fig.savefig(dest, dpi=140, bbox_inches="tight"); plt.close(fig)
    print(f"-> {os.path.relpath(dest, ROOT)}  ({ncol} territoires)")


for p in ("swd0", "swfc"):
    make_figure(p)
