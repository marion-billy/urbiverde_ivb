"""Freeze the sensitivity-analysis stability table into a committed CSV.

Reads the reference run (data/outputs/) and every perturbed run under _sandbox/sensitivity/<tag>/,
computes the per-tag stability metrics (corridor overlap, blocked-link Jaccard, relative KPI
change) via utils.sensitivity_metrics.stability_table, and writes one flat
_sandbox/sensitivity/sensitivity_summary.csv. Reproducible: re-run after any new perturbed batch.

Coverage is whatever actually exists on disk (a couple appears only for the tags it was run for):
local sensitivity on Perpignan + La Rochelle, sweep on Perpignan, ecoprofils herisson + lezard.
"""
from __future__ import annotations

# NOTE: the raw per-run sensitivity tree has been consolidated into _sandbox/sensitivity/all_stats.csv
# (one long CSV) and the heavy .tif/.geojson pruned, so sensitivity_summary.csv is now frozen
# (blocked_jaccard needs the pruned corridor geojson). Kept for provenance.

import os
import sys

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "utils"))
from sensitivity_metrics import stability_table  # noqa: E402

BASE = os.path.join(ROOT, "data", "outputs")
SENS = os.path.join(ROOT, "_sandbox", "sensitivity")

COUPLES = [
    ("Perpignan", "ground_mammal"), ("Perpignan", "ground_reptile"),
    ("LaRochelle", "ground_mammal"), ("LaRochelle", "ground_reptile"),
]


def _kind(tag: str) -> str:
    """sweep = wide parameter scan (swd0_*, swfc_*) ; local = single +/- perturbation."""
    return "sweep" if tag.startswith("sw") else "local"


frames = []
for city, guild in COUPLES:
    df = stability_table(BASE, SENS, city, guild)
    if not df.empty:
        frames.append(df)

out = pd.concat(frames, ignore_index=True)
out.insert(1, "kind", out["perturbation"].map(_kind))
dest = os.path.join(SENS, "sensitivity_summary.csv")
out.to_csv(dest, index=False)
print(f"wrote {dest}  shape={out.shape}")
print(out.to_string(max_colwidth=18))
