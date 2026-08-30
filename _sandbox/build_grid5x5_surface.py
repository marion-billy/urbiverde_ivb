#!/usr/bin/env python3
"""Assemble the full 5x5 (d0 x contrast) grid for the 3 targeted reptile couples, decompose the
variance (refined vs the 3x3), and draw the response surfaces.

Levels d0 in {0.50,0.70,1.00,1.10,1.20} (rows), contrast in {0.00,0.50,1.00,1.50,2.00} (cols).
Cells come from: baseline (data/outputs), the OAT axes (swd0_* / swfc_*), the 3x3 corners and the
5x5 interior (grid_d*_fc*). One replicate per cell, so the interaction absorbs the residual; the
point is the SHARE of variance and the SHAPE of the surface (separable -> axis-aligned gradients;
interaction -> twisted contours).
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = "/home/jovyan/work/team/marion/corridor_project"
COUPLES = [("LaRochelle", "ground_reptile"), ("Toulouse", "ground_reptile"), ("Nancy", "ground_reptile")]
CITY_FR = {"LaRochelle": "La Rochelle", "Toulouse": "Toulouse", "Nancy": "Nancy"}
D0 = [0.50, 0.70, 1.00, 1.10, 1.20]
FC = [0.00, 0.50, 1.00, 1.50, 2.00]
OUT = "_sandbox/figures_sens"

def cell_path(city, guild, d0, fc):
    d, f = int(round(d0 * 100)), int(round(fc * 100))
    b = abs(d0 - 1.0) < 1e-9, abs(fc - 1.0) < 1e-9
    if b[0] and b[1]:
        base = os.path.join(ROOT, "data", "outputs")
    elif b[1]:
        base = os.path.join(ROOT, "data", "sensitivity", f"swd0_{d:03d}", "data", "outputs")
    elif b[0]:
        base = os.path.join(ROOT, "data", "sensitivity", f"swfc_{f:03d}", "data", "outputs")
    else:
        base = os.path.join(ROOT, "data", "sensitivity", f"grid_d{d:03d}_fc{f:03d}", "data", "outputs")
    return os.path.join(base, city, guild, f"stats_{guild}_{city}.csv")

def read_val(path, col):
    if not os.path.exists(path):
        return np.nan
    df = pd.read_csv(path)
    return float(df[col].iloc[0]) if (col in df.columns and len(df)) else np.nan

def grid(city, guild, col):
    m = np.full((5, 5), np.nan)
    for i, d0 in enumerate(D0):
        for j, fc in enumerate(FC):
            m[i, j] = read_val(cell_path(city, guild, d0, fc), col)
    return m

def anova2(m):
    grand = m.mean()
    sst = float(((m - grand) ** 2).sum())
    ss_d0 = float(m.shape[1] * ((m.mean(1) - grand) ** 2).sum())
    ss_fc = float(m.shape[0] * ((m.mean(0) - grand) ** 2).sum())
    ss_int = sst - ss_d0 - ss_fc
    if sst <= 0:
        return dict(pd0=np.nan, pfc=np.nan, pint=np.nan)
    return dict(pd0=100 * ss_d0 / sst, pfc=100 * ss_fc / sst, pint=100 * ss_int / sst)

def main():
    rows = []
    metrics = [("n_subnetworks", "Nombre de sous-réseaux", "YlOrRd"),
               ("connected_habitat_pct", "Part connectée (%)", "viridis")]
    fig, axes = plt.subplots(len(metrics), len(COUPLES), figsize=(13, 8))
    for r, (col, label, cmap) in enumerate(metrics):
        for c, (city, guild) in enumerate(COUPLES):
            m = grid(city, guild, col)
            a = anova2(m)
            rows.append(dict(city=city, guild=guild, output=col, n_cells=int(25 - np.isnan(m).sum()),
                             ref=round(float(m[2, 2]), 2), pct_d0=round(a["pd0"], 1),
                             pct_contrast=round(a["pfc"], 1), pct_interaction=round(a["pint"], 1)))
            ax = axes[r, c]
            im = ax.imshow(m, origin="lower", aspect="auto", cmap=cmap)
            ax.set_xticks(range(5)); ax.set_xticklabels([f"{x:.2f}" for x in FC], fontsize=8)
            ax.set_yticks(range(5)); ax.set_yticklabels([f"{x:.2f}" for x in D0], fontsize=8)
            cmap_obj = matplotlib.colormaps[cmap]
            vmin, vmax = np.nanmin(m), np.nanmax(m)
            span = (vmax - vmin) or 1.0
            for i in range(5):
                for j in range(5):
                    v = m[i, j]
                    if not np.isnan(v):
                        rgba = cmap_obj((v - vmin) / span)
                        lum = 0.299 * rgba[0] + 0.587 * rgba[1] + 0.114 * rgba[2]
                        ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=7,
                                color="white" if lum < 0.5 else "black")
            if r == 0:
                ax.set_title(f"{CITY_FR[city]} — reptile\ninteraction {a['pint']:.0f} %", fontsize=10)
            else:
                ax.set_title(f"interaction {a['pint']:.0f} %", fontsize=9)
            if c == 0:
                ax.set_ylabel(f"{label}\n\nd₀ (× référence)", fontsize=9)
            if r == len(metrics) - 1:
                ax.set_xlabel("contraste de friction (×)", fontsize=9)
            fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.suptitle("Surfaces de réponse d₀ × contraste (grille 5×5), profil reptile",
                 fontsize=12, y=0.99)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    png = os.path.join(ROOT, OUT, "sens_surface_5x5_reptile.png")
    fig.savefig(png, dpi=150, bbox_inches="tight")
    try: os.chmod(png, 0o666)
    except OSError: pass
    print("figure:", png)
    df = pd.DataFrame(rows)
    csv = os.path.join(ROOT, "data", "sensitivity", "grid5x5_anova.csv")
    df.to_csv(csv, index=False)
    try: os.chmod(csv, 0o666)
    except OSError: pass
    print("csv:", csv, "\n")
    print(df.to_string(index=False))

if __name__ == "__main__":
    main()
