#!/usr/bin/env python3
"""Two-way ANOVA variance decomposition on the joint 3x3 (d0 x friction-contrast) grid.

For each couple (city x guild) and each output, build the 3x3 table of one output value per
cell (levels d0 in {0.50,1.00,1.20}, contrast in {0.00,1.00,2.00}) and decompose its total
sum of squares into the main effect of d0, the main effect of contrast, and their interaction.
With one replicate per cell the interaction absorbs the residual, so no significance test is
possible; the point is the SHARE of variance carried by the interaction (finite-grid analogue
of the gap between a first-order and a total sensitivity index). A large interaction share is
exactly what a one-factor-at-a-time (OAT) reading cannot see.

Reads the 5 cross cells from the existing OAT outputs and the 4 corners from the grid_* tags.
Writes data/sensitivity/grid3x3_anova.csv and prints a human summary.
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd

ROOT = "/home/jovyan/work/team/marion/corridor_project"
CITIES = ["Kourou", "Perpignan", "Nancy", "LaRochelle", "LRSY", "Toulouse"]
GUILDS = ["ground_mammal", "ground_reptile", "arboreal_mammal", "forest_edge_bird"]
OUTPUTS = ["connected_habitat_pct", "n_subnetworks", "ec_real_ha"]
D0 = [0.50, 1.00, 1.20]      # rows
FC = [0.00, 1.00, 2.00]      # cols

def cell_path(city: str, guild: str, d0: float, fc: float) -> str:
    """Return the stats CSV path for one (d0, contrast) cell of a couple."""
    d, f = int(round(d0 * 100)), int(round(fc * 100))
    if abs(d0 - 1.0) < 1e-9 and abs(fc - 1.0) < 1e-9:
        base = os.path.join(ROOT, "data", "outputs")                       # baseline
    elif abs(fc - 1.0) < 1e-9:
        base = os.path.join(ROOT, "data", "sensitivity", f"swd0_{d:03d}", "data", "outputs")
    elif abs(d0 - 1.0) < 1e-9:
        base = os.path.join(ROOT, "data", "sensitivity", f"swfc_{f:03d}", "data", "outputs")
    else:
        base = os.path.join(ROOT, "data", "sensitivity", f"grid_d{d:03d}_fc{f:03d}", "data", "outputs")
    return os.path.join(base, city, guild, f"stats_{guild}_{city}.csv")

def read_value(path: str, col: str) -> float | None:
    """Read a single output value from a one-row stats CSV, or None if unavailable."""
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    if col not in df.columns or df.empty:
        return None
    return float(df[col].iloc[0])

def anova2(matrix: np.ndarray) -> dict:
    """Balanced two-way ANOVA sum-of-squares decomposition (one replicate per cell)."""
    grand = matrix.mean()
    ss_total = float(((matrix - grand) ** 2).sum())
    row_means = matrix.mean(axis=1)   # d0 effect
    col_means = matrix.mean(axis=0)   # contrast effect
    ss_d0 = float(matrix.shape[1] * ((row_means - grand) ** 2).sum())
    ss_fc = float(matrix.shape[0] * ((col_means - grand) ** 2).sum())
    ss_int = ss_total - ss_d0 - ss_fc
    if ss_total <= 0:
        return dict(ss_total=0.0, pct_d0=np.nan, pct_fc=np.nan, pct_int=np.nan, grand=grand)
    return dict(ss_total=ss_total, pct_d0=100 * ss_d0 / ss_total, pct_fc=100 * ss_fc / ss_total,
                pct_int=100 * ss_int / ss_total, grand=grand)

def main() -> None:
    rows = []
    for city in CITIES:
        for guild in GUILDS:
            grid = {out: np.full((3, 3), np.nan) for out in OUTPUTS}
            missing = 0
            for i, d0 in enumerate(D0):
                for j, fc in enumerate(FC):
                    p = cell_path(city, guild, d0, fc)
                    vals = {out: read_value(p, out) for out in OUTPUTS}
                    if any(v is None for v in vals.values()):
                        missing += 1
                    for out in OUTPUTS:
                        if vals[out] is not None:
                            grid[out][i, j] = vals[out]
            complete = missing == 0
            for out in OUTPUTS:
                m = grid[out]
                if np.isnan(m).any():
                    rows.append(dict(city=city, guild=guild, output=out, complete=False,
                                     n_cells=int(9 - np.isnan(m).sum())))
                    continue
                res = anova2(m)
                rows.append(dict(city=city, guild=guild, output=out, complete=complete, n_cells=9,
                                 ref_value=round(float(m[1, 1]), 3), grand=round(res["grand"], 3),
                                 pct_d0=round(res["pct_d0"], 1), pct_contrast=round(res["pct_fc"], 1),
                                 pct_interaction=round(res["pct_int"], 1)))
    out_df = pd.DataFrame(rows)
    out_csv = os.path.join(ROOT, "data", "sensitivity", "grid3x3_anova.csv")
    out_df.to_csv(out_csv, index=False)
    try:
        os.chmod(out_csv, 0o666)
    except OSError:
        pass
    print(f"written: {out_csv}  ({len(out_df)} rows)")

    ok = out_df[out_df.get("complete", False) == True].copy()  # noqa: E712
    print(f"\ncomplete couples/outputs: {len(ok)} / {len(out_df)}")
    if len(ok):
        for out in OUTPUTS:
            sub = ok[ok["output"] == out]
            if len(sub):
                print(f"\n=== {out} : interaction share of variance (pct_interaction) ===")
                print(f"  median={sub['pct_interaction'].median():.1f}%  "
                      f"max={sub['pct_interaction'].max():.1f}%  "
                      f"n>20%={int((sub['pct_interaction'] > 20).sum())}/{len(sub)}")
                top = sub.sort_values("pct_interaction", ascending=False).head(6)
                print(top[["city", "guild", "ref_value", "pct_d0", "pct_contrast",
                           "pct_interaction"]].to_string(index=False))

if __name__ == "__main__":
    main()
