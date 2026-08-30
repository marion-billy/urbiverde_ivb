"""Sensitivity-analysis metrics for the connectivity pipeline.

Compares a perturbed run (friction / d0 scaled, produced under data/sensitivity/<tag>/) to the
reference run (data/outputs/), per (city, ecoprofil), and quantifies how much the CONCLUSIONS move:
corridor overlap, blocked-link Jaccard, and relative KPI change. Also a tornado plot per KPI.

Message sought: even if absolute values shift, do the corridors, the black points and the ranking
of ecoprofils hold under a reasonable parameter change? Standard robustness check for a least-cost
connectivity model (Beier 2008, Spear 2010, Zeller 2012, Rayfield 2011).

Usage (after the perturbed runs exist):
    from sensitivity_metrics import stability_table, tornado_plot
    df = stability_table("data/outputs", "data/sensitivity", "Perpignan", "ground_mammal")
    tornado_plot(df, "connected_habitat_pct", "tornado.png")
"""
from __future__ import annotations

import glob
import os

import geopandas as gpd
import pandas as pd

KPIS = ["ec_real_ha", "connected_habitat_pct", "n_subnetworks", "nb_corridors", "nb_failed_corridors"]


def _lcp(d: str, city: str, guild: str) -> gpd.GeoDataFrame | None:
    f = glob.glob(f"{d}/{city}/{guild}/lcp_*.geojson")
    return gpd.read_file(f[0]) if f else None


def _failed(d: str, city: str, guild: str) -> gpd.GeoDataFrame | None:
    f = glob.glob(f"{d}/{city}/{guild}/failed_links_*.geojson")
    return gpd.read_file(f[0]) if f else None


def _stats(d: str, city: str, guild: str) -> pd.Series | None:
    f = glob.glob(f"{d}/{city}/{guild}/stats_*.csv")
    return pd.read_csv(f[0]).iloc[0] if f else None


def _blocked_pairs(gdf: gpd.GeoDataFrame | None) -> set:
    """Order-independent set of node pairs that are blocked."""
    if gdf is None or gdf.empty:
        return set()
    col = "fail_reason" if "fail_reason" in gdf.columns else "reason"
    if col not in gdf.columns:
        return set()
    bl = gdf[gdf[col] == "blocked"]
    return {frozenset((int(a), int(b))) for a, b in zip(bl["node_1"], bl["node_2"])}


def _jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b) if (a | b) else 1.0


def compare_pair(baseline_dir: str, perturbed_dir: str, city: str, guild: str,
                 corridor_buffer_m: float = 20.0) -> dict:
    """Stability metrics of a perturbed (city, guild) run vs the reference run."""
    out: dict = {"city": city, "guild": guild}

    lb, lp = _lcp(baseline_dir, city, guild), _lcp(perturbed_dir, city, guild)
    if lb is not None and lp is not None and len(lb) and len(lp):
        lp_utm = lp.to_crs(lb.crs)
        buf = lp_utm.buffer(corridor_buffer_m).union_all()
        out["corridor_overlap_pct"] = round(
            float(lb.intersection(buf).length.sum() / lb.length.sum() * 100), 1)
        out["nb_corridors_delta_pct"] = round((len(lp) - len(lb)) / len(lb) * 100, 1) if len(lb) else None

    out["blocked_jaccard"] = round(
        _jaccard(_blocked_pairs(_failed(baseline_dir, city, guild)),
                 _blocked_pairs(_failed(perturbed_dir, city, guild))), 2)

    sb, sp = _stats(baseline_dir, city, guild), _stats(perturbed_dir, city, guild)
    if sb is not None and sp is not None:
        for k in KPIS:
            if k in sb and k in sp and pd.notna(sb[k]) and float(sb[k]) != 0:
                out[f"{k}_delta_pct"] = round((float(sp[k]) - float(sb[k])) / float(sb[k]) * 100, 1)
    return out


def stability_table(baseline_dir: str, sensitivity_root: str, city: str, guild: str) -> pd.DataFrame:
    """One row per perturbation tag found under sensitivity_root, compared to the baseline."""
    tags = sorted(d for d in os.listdir(sensitivity_root)
                  if os.path.isdir(os.path.join(sensitivity_root, d, "data", "outputs", city, guild)))
    rows = []
    for tag in tags:
        r = compare_pair(baseline_dir, os.path.join(sensitivity_root, tag, "data", "outputs"), city, guild)
        r = {"perturbation": tag, **r}
        rows.append(r)
    return pd.DataFrame(rows)


PARAM_LABELS = {"fric": "Friction (±20 %)", "d0": "Distance d₀ (±25 %)", "c10": "Arbres (10)", "c20": "Arbustes (20)", "c30": "Prairies (30)", "c40": "Cultures (40)", "c50": "Bâti (50)", "c51": "Bâtiments (51)", "c52": "Routes princ. (52)", "c53": "Voirie sec. (53)", "c54": "Chemins (54)", "c55": "Voies ferrées (55)", "c60": "Sols nus (60)", "c80": "Eau (80)", "c90": "Z. humides (90)", "c95": "Mangroves (95)"}
KPI_LABELS = {
    "connected_habitat_pct": "part d'habitat connectée",
    "ec_real_ha": "surface équivalente connectée",
    "n_subnetworks": "nombre de sous-réseaux",
    "nb_corridors": "nombre de corridors",
}
POLARITY = {  # +1: higher KPI = better connectivity ; -1: higher = worse (fragmentation)
    "connected_habitat_pct": 1, "ec_real_ha": 1, "nb_corridors": 1,
    "n_subnetworks": -1, "nb_failed_corridors": -1,
}


def _parse_tag(tag: str) -> tuple[str, str]:
    """Split a perturbation tag into (parameter, sign): 'fric_m20' -> ('fric', '-')."""
    import re
    m = re.match(r"(.+?)_(m|p)\d+", tag)
    if not m:
        return tag, "+"
    return m.group(1), ("-" if m.group(2) == "m" else "+")


def tornado_plot(df: pd.DataFrame, kpi_col: str, out_png: str, title: str | None = None) -> None:
    """Proper tornado diagram: one bar per parameter, spanning its minus and plus effect.

    Each parameter (friction, d0) is perturbed down and up; the bar runs from the KPI change under
    the reduced value (left, red) to the change under the increased value (right, green), centred on
    the reference (0). Parameters are sorted by total swing, the widest on top.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    col = f"{kpi_col}_delta_pct" if not kpi_col.endswith("_delta_pct") else kpi_col
    d = df.dropna(subset=[col]).copy()
    d["param"], d["sign"] = zip(*d["perturbation"].map(_parse_tag))

    effect = {}  # param -> {'-': delta, '+': delta}
    for p, sub in d.groupby("param"):
        effect[p] = {s: float(sub[sub["sign"] == s][col].iloc[0]) for s in sub["sign"].unique()}
    params = sorted(effect, key=lambda p: abs(effect[p].get("+", 0.0) - effect[p].get("-", 0.0)))

    import re as _re

    def _pct(tag: str) -> str:
        m = _re.search(r"_(m|p)(\d+)", tag)
        return f"{'-' if m.group(1) == 'm' else '+'}{m.group(2)} %" if m else ""

    inp = {}  # param -> {sign: input-change label}
    for _p, _sub in d.groupby("param"):
        inp[_p] = {s: _pct(_sub[_sub["sign"] == s]["perturbation"].iloc[0]) for s in _sub["sign"].unique()}

    pol = POLARITY.get(kpi_col, 1)  # colour by effect on connectivity, not raw KPI sign
    fig, ax = plt.subplots(figsize=(7.6, max(1.8, 0.95 * len(params))))
    for i, p in enumerate(params):
        lo = effect[p].get("-", 0.0)
        hi = effect[p].get("+", 0.0)
        ax.barh(i, lo, color=("#2E7D32" if lo * pol >= 0 else "#C62828"), height=0.55, zorder=3,
                label="paramètre réduit" if i == 0 else None)
        ax.barh(i, hi, color=("#2E7D32" if hi * pol >= 0 else "#C62828"), height=0.55, zorder=3,
                label="paramètre augmenté" if i == 0 else None)
        ax.text(lo, i, f" {inp[p].get('-', '')} : {lo:+.1f} % ", va="center",
                ha="right" if lo < 0 else "left", fontsize=8)
        ax.text(hi, i, f" {inp[p].get('+', '')} : {hi:+.1f} % ", va="center",
                ha="left" if hi >= 0 else "right", fontsize=8)
    ax.set_yticks(range(len(params)))
    ax.set_yticklabels([PARAM_LABELS.get(p, p) for p in params])
    ax.axvline(0, color="black", linewidth=0.9, zorder=2)
    ax.set_xlabel(f"{KPI_LABELS.get(kpi_col, kpi_col)} : variation (%) vs référence")
    ax.set_title(title or f"Sensibilité de {kpi_col}", fontsize=10)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color="#2E7D32", label="connectivité renforcée"),
                       Patch(color="#C62828", label="connectivité dégradée")],
              fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=2, frameon=False)
    xmax = max(max((abs(v) for e in effect.values() for v in e.values()), default=1.0), 1.0) * 1.6
    ax.set_xlim(-xmax, xmax)
    fig.savefig(out_png, dpi=150, bbox_inches="tight")
    plt.close(fig)


def rank_stability(baseline_dir: str, perturbed_dir: str, city: str, guilds: list[str],
                   kpi: str = "connected_habitat_pct") -> float:
    """Spearman correlation of the ecoprofil ranking (by KPI) baseline vs perturbed (1 = identical order)."""
    from scipy.stats import spearmanr
    b = {g: float(_stats(baseline_dir, city, g)[kpi]) for g in guilds if _stats(baseline_dir, city, g) is not None}
    p = {g: float(_stats(perturbed_dir, city, g)[kpi]) for g in guilds if _stats(perturbed_dir, city, g) is not None}
    common = [g for g in guilds if g in b and g in p]
    if len(common) < 2:
        return float("nan")
    return round(float(spearmanr([b[g] for g in common], [p[g] for g in common]).correlation), 3)


def response_curve(baseline_dir: str, sensitivity_root: str, city: str, guild: str, prefix: str,
                   kpis: list[tuple[str, str, str]], out_png: str, xlabel: str,
                   title: str | None = None, baseline_x: float = 1.0) -> "pd.DataFrame":
    """Sweep response curve: plot one or two KPIs against a swept parameter to locate tipping points.

    Reads every tag directory named ``<prefix>_<int>`` under sensitivity_root (the int is the swept
    value times 100), adds the reference run at baseline_x, and plots each KPI versus the parameter.
    A parameter SWEEP answers "at what value does the diagnosis break", unlike the local tornado.

    Parameters
    ----------
    kpis : list of (column, label, colour); one or two entries (a second uses a twin y-axis).
    """
    import re
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    pts = []
    for d in sorted(os.listdir(sensitivity_root)):
        m = re.match(rf"{prefix}_(\d+)$", d)
        if not m:
            continue
        s = _stats(os.path.join(sensitivity_root, d, "data", "outputs"), city, guild)
        if s is not None:
            pts.append((int(m.group(1)) / 100.0, s))
    sb = _stats(baseline_dir, city, guild)
    if sb is not None:
        pts.append((baseline_x, sb))
    pts = sorted({round(x, 4): s for x, s in pts}.items())
    xs = [x for x, _ in pts]

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    axes = [ax] + [ax.twinx() for _ in kpis[1:]]
    for a, (col, lab, colour) in zip(axes, kpis):
        ys = [float(s[col]) if col in s and pd.notna(s[col]) else float("nan") for _, s in pts]
        a.plot(xs, ys, "o-", color=colour, label=lab)
        a.set_ylabel(lab, color=colour)
        a.tick_params(axis="y", labelcolor=colour)
    ax.axvline(baseline_x, color="black", linestyle="--", linewidth=0.9)
    ax.text(baseline_x, ax.get_ylim()[1], " référence", fontsize=8, va="top")
    ax.set_xlabel(xlabel)
    ax.set_title(title or f"{city}, {guild} : courbe de réponse", fontsize=10)
    fig.savefig(out_png, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return pd.DataFrame([{"x": x, **{c: (float(s[c]) if c in s else None) for c, _, _ in kpis}}
                         for x, s in pts])
