"""Demo tornado (one-way sensitivity) from the real sweep outputs, on the two retained axes:
d0 (reach) and friction-contrast (structure). Two output metrics: connected habitat % and the
number of subnetworks (graduated count). Throwaway demo -> _sandbox/tornado_demo_*.png.
"""
import glob
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = os.path.join(os.path.dirname(__file__), "..")

PANELS = [
    ("Kourou", "ground_mammal", "Kourou / hérisson"),
    ("Kourou", "ground_reptile", "Kourou / lézard"),
    ("Perpignan", "ground_mammal", "Perpignan / hérisson"),
    ("Perpignan", "ground_reptile", "Perpignan / lézard"),
]


def val(city, guild, metric, tag=None):
    """metric value for a (city, guild), baseline if tag is None else a sensitivity tag."""
    if tag is None:
        p = f"{ROOT}/data/outputs/{city}/{guild}/stats_*.csv"
    else:
        p = f"{ROOT}/data/sensitivity/{tag}/data/outputs/{city}/{guild}/stats_*.csv"
    f = glob.glob(p)
    return float(pd.read_csv(f[0]).iloc[0][metric]) if f else None


def avail(city, guild, prefix):
    """available sweep tags for an axis, sorted by numeric scale (swd0_050 -> 50)."""
    tags = []
    for d in glob.glob(f"{ROOT}/data/sensitivity/{prefix}_*"):
        t = os.path.basename(d)
        if glob.glob(f"{d}/data/outputs/{city}/{guild}/stats_*.csv"):
            tags.append((int(t.split("_")[1]), t))
    return sorted(tags)


def make_figure(metric, xlabel, outfile, as_int=False):
    fmt = (lambda x: f"{x:.0f}") if as_int else (lambda x: f"{x:.0f}%")
    fig, axes = plt.subplots(2, 2, figsize=(11, 6.5))
    for ax, (city, guild, title) in zip(axes.ravel(), PANELS):
        base = val(city, guild, metric)
        d0, fc = avail(city, guild, "swd0"), avail(city, guild, "swfc")
        bars = []  # (label, low_value, high_value, low_txt, high_txt)
        if d0:
            bars.append(("d₀ (portée)", val(city, guild, metric, d0[0][1]),
                         val(city, guild, metric, d0[-1][1]), f"{d0[0][0]}%", f"{d0[-1][0]}%"))
        if fc:
            # contrast max -> harshest matrix: put it as the "low connectivity" end
            bars.append(("contraste friction", val(city, guild, metric, fc[-1][1]),
                         val(city, guild, metric, fc[0][1]), f"{fc[-1][0]}%", f"{fc[0][0]}%"))
        bars.sort(key=lambda b: abs(b[2] - b[1]))
        for i, (lab, lo, hi, lo_txt, hi_txt) in enumerate(bars):
            left, right = min(lo, hi), max(lo, hi)
            ax.barh(i, right - left, left=left, height=0.55, color="#2E8B84", alpha=0.85)
            ax.text(left, i + 0.34, lo_txt, va="bottom", ha="center", fontsize=7.5, color="#444")
            ax.text(right, i + 0.34, hi_txt, va="bottom", ha="center", fontsize=7.5, color="#444")
        ax.axvline(base, color="#B23A48", ls="--", lw=1.2)
        ax.text(base, -0.7, f"réf. {fmt(base)}", color="#B23A48", fontsize=7.5, va="top", ha="center")
        ax.set_ylim(-0.9, len(bars) - 0.1)
        ax.set_yticks(range(len(bars)))
        ax.set_yticklabels([b[0] for b in bars], fontsize=9)
        ax.set_title(title, fontsize=10, fontweight="bold")
        ax.set_xlabel(xlabel, fontsize=8)
        ax.margins(x=0.18)
        ax.grid(axis="x", ls=":", alpha=0.4)
    fig.suptitle(f"Tornado de sensibilité (une variable à la fois) : {xlabel.lower()}\n"
                 "d₀ et contraste de friction, amplitude = balayage bas -> haut, "
                 "ligne rouge = calage de référence", fontsize=10.5)
    fig.tight_layout(rect=[0, 0, 1, 0.92])
    fig.savefig(f"{ROOT}/{outfile}", dpi=140)
    print("figure ->", os.path.abspath(f"{ROOT}/{outfile}"))


make_figure("connected_habitat_pct", "Part d'habitat connecté (%)", "_sandbox/tornado_demo_connected.png")
make_figure("n_subnetworks", "Nombre de sous-réseaux", "_sandbox/tornado_demo_nsub.png", as_int=True)

# numbers for the record
for city, guild, title in PANELS:
    d0, fc = avail(city, guild, "swd0"), avail(city, guild, "swfc")
    c, n = val(city, guild, "connected_habitat_pct"), val(city, guild, "n_subnetworks")
    line = f"{title:22s} réf: {c:5.1f}% / {n:.0f} ss-rés."
    if d0:
        line += (f" | d0 {d0[0][0]}-{d0[-1][0]}%: sous-rés "
                 f"{val(city,guild,'n_subnetworks',d0[0][1]):.0f}->{val(city,guild,'n_subnetworks',d0[-1][1]):.0f}")
    if fc:
        line += (f" | contraste 0-200%: sous-rés "
                 f"{val(city,guild,'n_subnetworks',fc[0][1]):.0f}->{val(city,guild,'n_subnetworks',fc[-1][1]):.0f}")
    print(line)
