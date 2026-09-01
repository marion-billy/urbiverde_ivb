"""Overall chi-square test of habitat selection per ecoprofil (companion to the Manly ratios).

Reads the pooled selection ratios and coverage produced by gbif_crosstest.py, and tests whether the
focal occurrences distribute across the four classes (core / stepping stone / corridor / matrix)
differently from the target-group background. Two variants, which agree:
  - goodness-of-fit: focal counts vs expected = n_focal * availability (availability treated known);
  - 2xk contingency: focal counts vs target-group counts (honest to the TGB being a finite sample).
Writes chi2_pooled.csv. The p-values are optimistic: spatial thinning does not remove all
dependence between neighbouring occurrences.
"""
import pandas as pd
import numpy as np
from scipy.stats import chi2, chi2_contingency

OUT = "papier/internship_report/figures"
rp = pd.read_csv(f"{OUT}/ratios_pooled.csv")
cov = pd.read_csv(f"{OUT}/coverage.csv")
NOMS = {"ground_mammal": "Hérisson", "arboreal_mammal": "Écureuil",
        "forest_edge_bird": "Fauvette", "ground_reptile": "Lézard"}

rows = []
for g, nom in NOMS.items():
    d = rp[rp.guild == g]
    if d.empty:
        continue
    obs = d["n_c"].to_numpy(float)
    avail = d["avail"].to_numpy(float)
    n_focal = obs.sum()
    n_tgb = int(cov[cov.guild == g]["n_tgb"].sum())
    exp = n_focal * avail
    m = exp > 0
    chi_gof = float(((obs[m] - exp[m]) ** 2 / exp[m]).sum())
    df = int(m.sum() - 1)
    p_gof = float(chi2.sf(chi_gof, df))
    table = np.vstack([obs, avail * n_tgb])
    keep = table.sum(0) > 0
    chi_ind, p_ind, dof_ind, _ = chi2_contingency(table[:, keep])
    rows.append({"guild": g, "espece": nom, "n_focal": int(n_focal), "n_tgb": n_tgb,
                 "chi2_gof": round(chi_gof, 1), "df": df, "p_gof": p_gof,
                 "chi2_contingency": round(float(chi_ind), 1), "p_contingency": p_ind})

res = pd.DataFrame(rows)
res.to_csv(f"{OUT}/chi2_pooled.csv", index=False)
print(res.to_string(index=False))
print(f"\n-> {OUT}/chi2_pooled.csv")
