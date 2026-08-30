"""Append an explicit '(source : ...)' to every [FIGURE : ...] / [TABLEAU : ...] caption of the
report (SIGMA hard rule: figures numbered + sourced + called in text). Deterministic mapping keyed
by a distinctive substring of each caption, NOT a heuristic. Idempotent (skips captions already
carrying a '(source'). Prints every assignment for review. Edits the markdown in place."""
import glob
import os
import re

BASE = os.path.join(os.path.dirname(__file__), "..", "papier", "internship_report")

PERSO = "(source personnelle, 2026)"
WC = "(source personnelle, d'après ESA WorldCover et OpenStreetMap, 2026)"
CEREMA = "(source personnelle, d'après Cerema Dter Sud-Ouest, 2025)"
GBIF = "(source personnelle, d'après les données GBIF, 2026)"
OSMBG = "(source personnelle, fond de carte OpenStreetMap, 2026)"

# distinctive substring (lowercased) -> source string. First match wins.
MAP = [
    ("réseau écologique", PERSO),
    ("localisation des six territoires", OSMBG),
    ("les six territoires d'étude", PERSO),
    ("occupation du sol de toulouse", WC),
    ("caractéristiques des quatre profils", CEREMA),
    ("schéma synoptique de la chaîne", PERSO),
    ("segmentation morphologique", PERSO),
    ("graphe de gabriel", PERSO),
    ("arborescence normalisée", PERSO),
    ("tableau de bord interactif", PERSO),
    ("exemple de sorties sur un territoire", PERSO),
    ("récapitulatif des indicateurs", PERSO),
    ("surfaces de dispersion comparées", PERSO),
    ("courbes de réponse à la distance", PERSO),
    ("courbes de réponse au contraste", PERSO),
    ("ratios de sélection des occurrences gbif", GBIF),
    ("occurrences gbif de l'oiseau de lisière", GBIF),
    ("comparaison sur le secteur de salles-sur-mer", CEREMA),
    ("scénario de végétalisation", PERSO),
    ("part d'habitat connecté par territoire", PERSO),
    ("diagramme de gantt comparant", PERSO),
    ("optimisations des étapes coûteuses", PERSO),
    ("effectifs d'occurrences focales gbif", GBIF),
    ("ratios de sélection gbif par territoire", GBIF),
    ("cartes d'occurrences du profil des oiseaux", GBIF),
    ("cartes d'occurrences du profil des mammifères arboricoles", GBIF),
    ("cartes d'occurrences du profil des petits mammifères", GBIF),
    ("cartes d'occurrences du profil des reptiles", GBIF),
    ("diagramme de gantt du stage", PERSO),
    ("synthèse de sensibilité par territoire", PERSO),
]

CAP_RE = re.compile(r"\[(FIGURE|TABLEAU)\s*:\s*(.*?)\]", re.DOTALL)


def pick(caption: str) -> str | None:
    low = " ".join(caption.lower().split())
    for key, src in MAP:
        if key in low:
            return src
    return None


def main() -> None:
    total, sourced, skipped, unmatched = 0, 0, 0, []
    for path in sorted(glob.glob(os.path.join(BASE, "rapport_*.md"))):
        text = open(path, encoding="utf-8").read()
        name = os.path.basename(path)

        def repl(m):
            nonlocal sourced, skipped
            kind, cap = m.group(1), m.group(2)
            capf = " ".join(cap.split())
            if "(source" in cap:
                skipped += 1
                return m.group(0)
            src = pick(cap)
            if src is None:
                unmatched.append(f"{name}: {capf[:70]}")
                return m.group(0)
            sourced += 1
            body = cap.rstrip()
            sep = " " if body.endswith((".", "?", "!", ")")) else ". "
            print(f"  {name:34s} {capf[:58]:60s} -> {src}")
            return f"[{kind} : {body}{sep}{src}]"

        new = CAP_RE.sub(repl, text)
        total += len(CAP_RE.findall(text))
        if new != text:
            open(path, "w", encoding="utf-8").write(new)
    print(f"\ncaptions vues: {total} | sourcées: {sourced} | déjà sourcées (sautées): {skipped} "
          f"| non mappées: {len(unmatched)}")
    for u in unmatched:
        print("  NON MAPPÉE:", u)


if __name__ == "__main__":
    main()
