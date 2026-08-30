"""Gantt du stage : planning PRÉVISIONNEL vs RÉALISÉ (Figure du chapitre 6).

Source du prévisionnel : planning_stage_Marion_010326.xlsx (axes, tâches, jalons).
Source du réalisé : daté juin-août (decision_log, logs de session /team/agents, mémoires projet) ;
février-mai reconstruit à partir du prévu + des divergences documentées. --> À FAIRE VALIDER PAR
MARION : ajuster les semaines de la colonne `real` ci-dessous (elle a vécu le calendrier réel).

Semaines : S1 = lundi 16/02/2026 ; le stage court du 16/02 au 14/08 (~26 semaines).
Run : python3 make_gantt.py  ->  gantt_stage.png
"""
from __future__ import annotations

import os
from datetime import date, timedelta

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

HERE = os.path.dirname(os.path.abspath(__file__))
START = date(2026, 2, 16)  # S1, lundi
PREVU = "#B7C4C2"          # prévu : gris-vert clair
REAL = "#123F3A"           # réalisé : vert foncé Murmuration
DIVERG = "#BE842A"         # tâche dont le réalisé diverge nettement du prévu (ambre)

# (axe, tâche, prévu (s0,s1), réalisé (s0,s1) ou None si non réalisé, diverge?)
# semaines en numéro S (1..27). None réalisé = planifié mais non fait.
TASKS = [
    ("0", "Cadrage : problématique, périmètre, planning",        (1, 2),  (1, 3),  False),
    ("1", "État de l'art (connectivité, guildes, réglementaire)", (1, 6),  (1, 8),  False),
    ("1", "Mise en place technique (VM, Python, GEE)",           (3, 6),  (2, 5),  False),
    ("1", "Occupation du sol : prévu U-Net/Sentinel-2 → réalisé WorldCover 10 m + OSM",
                                                                 (4, 9),  (3, 6),  True),
    ("1", "Méthode connectivité : MSPA → graphe de Gabriel → PC → LCP (circuit theory écarté)",
                                                                 (6, 9),  (5, 12), True),
    ("2", "Implémentation du pipeline + 1er test ville pilote",  (8, 13), (6, 16), False),
    ("2", "Stabilisation / optimisation (smoothing, PC, ruptures)", (0, 0), (16, 20), True),
    ("2", "Extension aux 6 territoires (prévu : 4 villes)",      (0, 0),  (15, 21), True),
    ("2", "Validation : occurrences GBIF + comparaison Cerema",  (8, 12), (18, 23), True),
    ("2", "Analyse de sensibilité (balayage d₀ × contraste)",    (7, 9),  (20, 26), True),
    ("3", "Co-bénéfices (LST, 3-30-300, bruit/carbone) — non réalisé, reporté en perspective",
                                                                 (14, 20), None,   False),
    ("4", "Rédaction état de l'art + méthode",                   (1, 22), (2, 26), False),
    ("4", "Rédaction résultats + discussion + conclusion",       (14, 23), (22, 26), False),
    ("4", "Production des figures et cartes (conventions carto)", (6, 24), (24, 26), False),
    ("4", "Bibliographie, corrections finales, mise en forme",   (24, 26), (23, 26), False),
]

# jalons prévisionnels (semaine approx, libellé)
MILESTONES = [
    (2, "24/02\nplanning"), (3, "02/03\ncorpus"), (9, "mi-avr.\nAxe 1"),
    (11, "fin avr.\n1er test"), (18, "mi-juin\nAxe 2"), (20, "fin juin\nrestitution"),
    (25, "début août\ndraft"), (26.4, "mi-août\nfinal"),
]
AXE_LABEL = {"0": "Axe 0 · Cadrage", "1": "Axe 1 · Cadre & méthode",
             "2": "Axe 2 · Dev & validation", "3": "Axe 3 · Co-bénéfices",
             "4": "Axe 4 · Rédaction"}


def wk(w: float) -> float:
    """Semaine S -> jours depuis START (pour l'axe des x en dates)."""
    return (w - 1) * 7


def main() -> None:
    n = len(TASKS)
    fig, ax = plt.subplots(figsize=(12.5, 0.5 * n + 2.2))
    y = n
    prev_axe = None
    yticks, ylabels = [], []
    for axe, label, prevu, real, diverg in TASKS:
        y -= 1
        if axe != prev_axe:
            ax.axhline(y + 0.6, color="#999", lw=0.6, alpha=0.5)
            ax.text(wk(1) - 3, y + 0.5, AXE_LABEL[axe], fontsize=8.5, fontweight="bold",
                    va="center", ha="right", color="#123F3A")
            prev_axe = axe
        # barre prévue (au-dessus)
        if prevu and prevu != (0, 0):
            ax.barh(y + 0.18, wk(prevu[1] + 1) - wk(prevu[0]), left=wk(prevu[0]), height=0.3,
                    color=PREVU, zorder=2)
        # barre réalisée (en-dessous)
        if real:
            ax.barh(y - 0.18, wk(real[1] + 1) - wk(real[0]), left=wk(real[0]), height=0.3,
                    color=DIVERG if diverg else REAL, zorder=3)
        else:  # planifié, non réalisé
            ax.text(wk(prevu[0]), y - 0.18, "  non réalisé", fontsize=7, style="italic",
                    va="center", color="#C0392B")
        yticks.append(y)
        ylabels.append(label)
    ax.set_yticks(yticks)
    ax.set_yticklabels(ylabels, fontsize=8)
    ax.set_ylim(-0.8, n + 0.3)

    # axe x en mois
    months = []
    d = date(START.year, START.month, 1)
    while d <= date(2026, 8, 31):
        months.append(d)
        d = date(d.year + (d.month == 12), (d.month % 12) + 1, 1)
    for m in months:
        xd = (m - START).days
        if 0 <= xd <= wk(27):
            ax.axvline(xd, color="#ccc", lw=0.6, ls=":", zorder=1)
    ax.set_xticks([(m - START).days for m in months if 0 <= (m - START).days <= wk(27)])
    ax.set_xticklabels([m.strftime("%b").capitalize() for m in months
                        if 0 <= (m - START).days <= wk(27)], fontsize=9)
    ax.set_xlim(wk(1) - 3, wk(27))

    # jalons prévisionnels
    for w, lab in MILESTONES:
        ax.axvline(wk(w), color=DIVERG, lw=0.8, ls="--", alpha=0.6, zorder=1)
        ax.plot(wk(w), n + 0.05, marker="D", color=DIVERG, markersize=6, zorder=5, clip_on=False)
        ax.text(wk(w), n + 0.35, lab, fontsize=6.5, ha="center", va="bottom", color=DIVERG)

    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.legend(handles=[Patch(color=PREVU, label="Prévisionnel"),
                       Patch(color=REAL, label="Réalisé"),
                       Patch(color=DIVERG, label="Réalisé divergent du prévu / jalon"),
                       ],
              loc="upper center", bbox_to_anchor=(0.5, -0.02), ncol=3, fontsize=8, frameon=False)
    ax.set_title("Planning du stage : prévisionnel et réalisé", fontsize=13, pad=26)
    fig.tight_layout()
    out = os.path.join(HERE, "gantt_stage.png")
    fig.savefig(out, dpi=160, bbox_inches="tight")
    plt.close(fig)
    print("gantt_stage.png OK")


if __name__ == "__main__":
    main()
