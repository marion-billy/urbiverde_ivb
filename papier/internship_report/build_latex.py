"""Merge the internship-report markdown sections into a single compilable LaTeX file.

Produces rapport_complet.tex (class report, babel french). No LaTeX engine is required to
GENERATE it; compile it on Overleaf (upload this file + the figures/ folder) or with a local
TeX Live (pdflatex rapport_complet.tex, twice for the TOC/LOF/LOT).

Mapping of the markdown subset used in rapport_0..7:
- # / ## / ### -> \\chapter / \\section / \\subsection (leading manual numbers stripped, LaTeX renumbers);
  the Résumé chapter is unnumbered (\\chapter*).
- hard-wrapped paragraphs joined; **bold** -> \\textbf; placeholders -> \\hl (highlighted).
- encadré blockquotes -> tcolorbox; brouillon notes dropped.
- [FIGURE : ...] -> figure with \\includegraphics if the image exists, else a framed placeholder; always \\caption.
- [TABLEAU : ...] -> caption attached to the following markdown table, or a placeholder table.
- markdown tables -> tabularx + booktabs.

Run: python3 build_latex.py
"""

from __future__ import annotations

import glob
import os
import re
import shutil

BASE: str = os.path.dirname(os.path.abspath(__file__))
FIG: str = os.path.join(BASE, "figures")
PIPELINE_SRC: str = os.path.normpath(os.path.join(BASE, "..", "..", "data", "outputs", "pipeline.png"))
PIPELINE_DST: str = os.path.join(FIG, "pipeline_chaine.png")

PLACEHOLDER_RE = re.compile(r"\[(?:CHIFFRE|À (?:COMPLÉTER|VÉRIFIER|ADAPTER)|réf[^\]]*compléter)[^\]]*\]")
TOKEN_RE = re.compile(r"(\*\*.+?\*\*|\*[^*\n]+?\*|\[(?:CHIFFRE|À (?:COMPLÉTER|VÉRIFIER|ADAPTER)|réf[^\]]*compléter)[^\]]*\])")

SPECIAL = {"&": r"\&", "%": r"\%", "#": r"\#", "_": r"\_", "$": r"\$",
           "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}

# Mathematical / technical Unicode used in the markdown (d₀, ≥, √, ...) that pdflatex does not
# know out of the box. Applied AFTER the SPECIAL escaping, so the LaTeX we inject stays literal.
UNICODE_MATH = {
    "≥": r"$\geq$", "≤": r"$\leq$", "≠": r"$\neq$", "≈": r"$\approx$",
    "×": r"$\times$", "·": r"$\cdot$", "−": r"$-$", "√": r"$\surd$", "∞": r"$\infty$",
    "Σ": r"$\sum$",
    "→": r"$\rightarrow$", "←": r"$\leftarrow$", "≃": r"$\simeq$", "≡": r"$\equiv$",
    "₀": r"$_{0}$", "₁": r"$_{1}$", "₂": r"$_{2}$", "₃": r"$_{3}$", "₄": r"$_{4}$",
    "₅": r"$_{5}$", "₆": r"$_{6}$", "₇": r"$_{7}$", "₈": r"$_{8}$", "₉": r"$_{9}$",
    "ₙ": r"$_{n}$", "ᵢ": r"$_{i}$", "ⱼ": r"$_{j}$",
    # text Unicode absent de Computer Modern / T1 : ligatures, ponctuation, grec
    "œ": r"\oe{}", "Œ": r"\OE{}", "æ": r"\ae{}", "Æ": r"\AE{}", "…": r"\ldots{}",
    "–": "--", "’": "'", "‘": "`", "“": "``", "”": "''", "•": r"$\bullet$",
    "α": r"$\alpha$", "β": r"$\beta$", "γ": r"$\gamma$", "μ": r"$\mu$",
    "ρ": r"$\rho$", "σ": r"$\sigma$", "Δ": r"$\Delta$",
}


def esc(s: str) -> str:
    s = s.replace("\\", r"\textbackslash{}")
    for k, v in SPECIAL.items():
        s = s.replace(k, v)
    for k, v in UNICODE_MATH.items():
        s = s.replace(k, v)
    return s


def inline(text: str) -> str:
    out: list[str] = []
    for tok in TOKEN_RE.split(text):
        if not tok:
            continue
        if tok.startswith("**") and tok.endswith("**"):
            out.append(r"\textbf{" + esc(tok[2:-2]) + "}")
        elif len(tok) > 2 and tok.startswith("*") and tok.endswith("*"):
            out.append(r"\textit{" + esc(tok[1:-1]) + "}")
        elif PLACEHOLDER_RE.fullmatch(tok):
            out.append(r"\hl{" + esc(tok) + "}")
        else:
            out.append(esc(tok))
    return "".join(out)


def figure_image(caption: str) -> str | None:
    m = re.search(r"([\w-]+\.png)", caption)  # règle générale : fichier cité dans la légende
    if m and os.path.exists(os.path.join(FIG, m.group(1))):
        return f"figures/{m.group(1)}"
    c = caption.lower()
    if "arborescence" in c:
        return "figures/arborescence_sorties.png"
    if "salles" in c:
        return "figures/comparaison_salles.png"
    if "gabriel" in c:
        return "figures/gabriel_criterion.png"
    if "principe du chemin de moindre coût" in c:
        return "figures/lcp_principe.png"
    if "familles de modèles de connectivité" in c:
        return "figures/diniz_connectivity_models.png"
    if "tableau de bord interactif" in c:
        return "figures/dashboard_capture.png"
    if "courbes de réponse à la distance" in c:
        return "figures/sens_curves_d0.png"
    if "courbes de réponse au contraste" in c:
        return "figures/sens_curves_contrast.png"
    if "part d'habitat connecté par territoire" in c:
        return "figures/territoire_connectivite.png"
    if "réseau écologique" in c:
        return "figures/reseau_ecologique.png"
    if "synoptique de la chaîne" in c:
        return "figures/pipeline_chaine.png" if os.path.exists(PIPELINE_DST) else None
    if "segmentation morphologique" in c:
        return "figures/mspa_example.png"
    if "complet de sorties" in c or "sorties de la chaîne sur perpignan" in c:
        return "figures/sorties_perpignan.png"
    if "dispersion compar" in c:
        return "figures/dispersion_comparee.png"
    if "occupation du sol" in c and "toulouse" in c:
        return "figures/landcover_toulouse.png"
    if "localisation" in c:
        return "figures/localisation_territoires_osm.png"
    if "gantt" in c:
        return "figures/gantt_stage.png"
    if "côte à côte" in c:
        return "figures/territoires_comparees.png"
    if "scénario de végétalisation" in c:
        return "figures/scenario_local.png"
    if "poolés sur les cinq territoires" in c or "agrégés sur les cinq territoires" in c:
        return "figures/gbif_ratios_pooled.png"
    if "par territoire et poolés" in c or "par territoire et agrégés" in c:
        return "figures/gbif_recap_par_ville.png"
    if "fauvette à toulouse" in c or "oiseau de lisière à toulouse" in c:
        return "figures/gbif_carte_Toulouse_fauvette.png"
    if "cartes d'occurrences" in c and "oiseaux de lisière" in c:
        return "figures/gbif_cartes_forest_edge_bird.png"
    if "cartes d'occurrences" in c and "mammifères arboricoles" in c:
        return "figures/gbif_cartes_arboreal_mammal.png"
    if "cartes d'occurrences" in c and "mammifères terrestres" in c:
        return "figures/gbif_cartes_ground_mammal.png"
    if "cartes d'occurrences" in c and "reptiles terrestres" in c:
        return "figures/gbif_cartes_ground_reptile.png"
    if "tornade" in c:
        return "figures/tornado_sensibilite_perpignan.png"
    if "courbe de réponse" in c and "distance de dispersion" in c and "lézard" in c:
        return "figures/response_d0_ground_reptile.png"
    if "courbe de réponse" in c and "distance de dispersion" in c and "hérisson" in c:
        return "figures/response_d0_ground_mammal.png"
    if "courbe de réponse" in c and "contraste" in c and "lézard" in c:
        return "figures/response_contrast_ground_reptile.png"
    if "courbe de réponse" in c and "contraste" in c and "hérisson" in c:
        return "figures/response_contrast_ground_mammal.png"
    return None


def strip_num(title: str) -> str:
    return re.sub(r"^\d+(?:\.\d+)*\.?\s*", "", title).strip()


def is_table_block(block: list[str]) -> bool:
    return len(block) >= 2 and all("|" in ln for ln in block) and re.match(r"^\|?\s*-", block[1].strip()) is not None


def parse_blocks(text: str) -> list[list[str]]:
    blocks: list[list[str]] = []
    cur: list[str] = []
    for line in text.splitlines():
        if line.strip() == "":
            if cur:
                blocks.append(cur); cur = []
        else:
            if line.lstrip().startswith("#") and cur:
                blocks.append(cur); cur = []
            cur.append(line)
    if cur:
        blocks.append(cur)
    return blocks


def render_heading(first: str) -> str:
    m = re.match(r"(#+)\s+(.*)", first)
    level, title = len(m.group(1)), m.group(2).strip()
    numm = re.match(r"(\d+(?:\.\d+)*)\.", title)          # leading manual number "2.4."
    annm = re.match(r"Annexe\s+([A-Z])\b", title)         # "Annexe A."
    if level == 1:
        low = title.lower()
        if "résumé" in low:
            return "\\chapter*{Résumé / Abstract}\n\\addcontentsline{toc}{chapter}{Résumé / Abstract}"
        if "références" in low or "bibliographie" in low:
            return ("\\chapter*{" + esc(title) + "}\n\\addcontentsline{toc}{chapter}{" + esc(title) + "}"
                    "\n\\phantomsection\\label{sec:bibliographie}")
        lab = ("\\label{chap:" + numm.group(1) + "}") if numm else ""
        return "\\chapter{" + esc(strip_num(title)) + "}" + lab
    if level == 2:
        if title in ("Résumé", "Abstract"):
            return "\\section*{" + esc(title) + "}"
        if annm:
            return "\\section{" + esc(title) + "}\\label{annexe:" + annm.group(1) + "}"
        lab = ("\\label{sec:" + numm.group(1) + "}") if numm else ""
        return "\\section{" + esc(strip_num(title)) + "}" + lab
    if annm:
        return "\\subsection{" + esc(title) + "}\\label{annexe:" + annm.group(1) + "}"
    lab = ("\\label{sec:" + numm.group(1) + "}") if numm else ""
    return "\\subsection{" + esc(strip_num(title)) + "}" + lab


def render_encadre(content: list[str]) -> str:
    paras: list[str] = []
    cur: list[str] = []
    for ln in content:
        if ln.strip() == "":
            if cur:
                paras.append(" ".join(cur)); cur = []
        else:
            cur.append(ln.strip())
    if cur:
        paras.append(" ".join(cur))
    title = paras[0] if paras else ""
    body = paras[1:]
    out = ["\\begin{tcolorbox}[colback=green!4,colframe=green!45!black,breakable]"]
    parts: list[str] = []
    if title:
        parts.append("\\textbf{" + inline(title) + "}")  # encadré title in bold
    parts.extend(inline(p) for p in body if p)
    out.append("\n\n".join(parts))
    out.append("\\end{tcolorbox}")
    return "\n".join(out)


def classify_quote(content: list[str]) -> str:
    """Encadré (title line, blank, body) vs plain quote (e.g. the problématique) vs meta note."""
    firstne = next((ln for ln in content if ln.strip()), "").strip()
    if firstne.startswith(("Brouillon", "Front matter", "Travaux cités", "Références fournies",
                           "**Références encore", "Références encore")):
        return "drop"
    idx = next((i for i, ln in enumerate(content) if ln.strip()), None)
    if idx is not None and idx + 1 < len(content) and content[idx + 1].strip() == "" \
            and any(ln.strip() for ln in content[idx + 2:]):
        return "encadre"
    return "quote"


def render_table(block: list[str], caption: str | None) -> str:
    parsed = [[c.strip() for c in r.strip().strip("|").split("|")] for r in block]
    header, body = parsed[0], parsed[2:]
    n = len(header)
    wide = n >= 7  # gros tableaux : page paysage, police reduite, colonnes a largeur naturelle
    out: list[str] = []
    if wide:
        out.append("\\begin{landscape}")
    out.append("\\begin{table}[H]")
    out.append("\\centering")
    if wide:
        out.append("\\footnotesize")
    if caption:
        out.append("\\caption{" + inline(caption) + "}")
    if wide:
        ncol = min(2, n)  # 1 ou 2 premieres colonnes de texte a gauche, le reste centre
        out.append("\\begin{tabular}{" + "l" * ncol + "c" * (n - ncol) + "}")
    else:
        cols = " ".join([">{\\raggedright\\arraybackslash}X"] * n)
        out.append(f"\\begin{{tabularx}}{{\\textwidth}}{{{cols}}}")
    out.append("\\toprule")
    out.append(" & ".join("\\textbf{" + inline(h) + "}" for h in header) + " \\\\")
    out.append("\\midrule")
    for row in body:
        cells = (row + [""] * n)[:n]
        out.append(" & ".join(inline(c) for c in cells) + " \\\\")
    out.append("\\bottomrule")
    out.append("\\end{tabular}" if wide else "\\end{tabularx}")
    out.append("\\end{table}")
    if wide:
        out.append("\\end{landscape}")
    return "\n".join(out)


def render_placeholder_table(caption: str) -> str:
    return ("\\begin{table}[H]\n\\centering\n\\caption{" + inline(caption) + "}\n"
            "\\fbox{\\parbox{0.9\\textwidth}{\\centering\\textcolor{gray}{[Tableau à compléter après le re-run]}}}\n"
            "\\end{table}")


def render_figure(caption: str, num: int | None = None) -> str:
    img = figure_image(caption)
    out = ["\\begin{figure}[H]", "\\centering"]
    if img and os.path.exists(os.path.join(BASE, img)):
        out.append(f"\\includegraphics[width=0.98\\textwidth]{{{img}}}")
    else:
        out.append("\\fbox{\\parbox[c][3.2cm][c]{0.9\\textwidth}{\\centering\\textcolor{gray}{[Figure à insérer]}}}")
    out.append("\\caption{" + inline(caption) + "}")
    if num is not None:
        out.append("\\label{fig:" + str(num) + "}")
    out.append("\\end{figure}")
    return "\n".join(out)


PREAMBLE = r"""\documentclass[a4paper,11pt]{report}
% Compiled with tectonic (XeTeX): use fontspec with Latin Modern, loaded by OTF filename
% (font-by-name lookup fails here, no fontconfig). fontenc+inputenc+lmodern under XeTeX
% mis-renders « » § ² (they showed as ń ż ğ š); fontspec renders all Unicode natively.
\usepackage{fontspec}
\setmainfont{Latin Modern Roman}[Extension=.otf, UprightFont=lmroman10-regular, BoldFont=lmroman10-bold, ItalicFont=lmroman10-italic, BoldItalicFont=lmroman10-bolditalic]
\setsansfont{Latin Modern Sans}[Extension=.otf, UprightFont=lmsans10-regular, BoldFont=lmsans10-bold, ItalicFont=lmsans10-oblique]
\setmonofont{Latin Modern Mono}[Extension=.otf, UprightFont=lmmono10-regular, BoldFont=lmmonolt10-bold, ItalicFont=lmmono10-italic]
\usepackage[french]{babel}
\usepackage{graphicx}
\usepackage{float}
\usepackage{amsmath}
\usepackage{booktabs}
\usepackage{tabularx}
\usepackage{array}
% Numérotation plate des figures/tableaux (Figure 1..N, pas 2.1) : la classe report réinitialise
% et préfixe les compteurs par chapitre ; chngcntr les détache pour une numérotation continue,
% cohérente avec les renvois « Figure N » du texte et le rendu docx.
\usepackage{chngcntr}
\counterwithout{figure}{chapter}
\counterwithout{table}{chapter}
\usepackage[most]{tcolorbox}
\usepackage{soul}
% Titre de chapitre sur la même ligne que « Chapitre N » (au lieu du numéro seul au-dessus du titre)
\usepackage{titlesec}
\titleformat{\chapter}[hang]{\normalfont\LARGE\bfseries}{\chaptertitlename\ \thechapter.}{0.6em}{}
\titlespacing*{\chapter}{0pt}{0pt}{1.5em}
% Légendes : séparateur deux-points à la française (« Figure 1 : ... », format demandé),
% et non « Figure 1 – » (le tiret de babel-french) ni « Figure 1. »
\usepackage{caption}
\DeclareCaptionLabelSeparator{frcolon}{~: }
\captionsetup{labelsep=frcolon, font=small, labelfont=bf}
\usepackage{geometry}
\geometry{margin=2.5cm}
% Grands tableaux (>= 7 colonnes) tournés en page paysage pour rester lisibles
\usepackage{pdflscape}
\usepackage{hyperref}
\hypersetup{hidelinks}
% URL / DOI cassables n'importe ou (bibliographie), dans la police du corps
\usepackage{xurl}
\urlstyle{same}
\sethlcolor{yellow}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0.5em}
\renewcommand{\arraystretch}{1.2}

\begin{document}

\begin{titlepage}
\centering
% Bandeau institutionnel
\begin{minipage}[c]{0.32\textwidth}\centering\includegraphics[height=1.2cm]{figures/logo_univ_toulouse.png}\end{minipage}\hfill
\begin{minipage}[c]{0.32\textwidth}\centering\includegraphics[height=0.95cm]{figures/logo_utjj.png}\end{minipage}\hfill
\begin{minipage}[c]{0.32\textwidth}\centering\includegraphics[height=1.2cm]{figures/logo_inp_agro.png}\end{minipage}

\vspace{1.1cm}
{\large Master Géomatique SIGMA\par}
{\normalsize ScIences Géomatiques en environneMent et Aménagement\par}
\vspace{0.15cm}
{\small Université de Toulouse\,\textperiodcentered\,\href{http://sigma.univ-toulouse.fr}{sigma.univ-toulouse.fr}\par}

\vspace{1.0cm}
{\normalsize\bfseries RAPPORT DE MASTER 2\par}
\vspace{0.5cm}
\rule{0.55\textwidth}{0.4pt}\par
\vspace{0.6cm}
{\LARGE\bfseries Conception d'un outil d'identification\\
des continuités écologiques urbaines potentielles\par}
\vspace{0.45cm}
{\Large à partir de l'observation de la Terre\\
et de données ouvertes\par}
\vspace{0.6cm}
\rule{0.55\textwidth}{0.4pt}\par

\vspace{1.6cm}
{\Large\bfseries Marion Billy\par}
\vspace{0.5cm}
{\small Structure d'accueil\par}
\vspace{0.2cm}
{\normalsize\bfseries Murmuration\par}
\vspace{0.12cm}
\includegraphics[height=1.0cm]{figures/logo_murmuration.png}\par

\vspace{1.4cm}
{\small\begin{tabular}{r@{\ }l}
Tuteur de stage : & Hugo Poupard\\
Enseignant-référent : & Laurent Jégou\\
Période : & du 16 février au 14 août 2026\\
\end{tabular}\par}
\vfill
\end{titlepage}

\tableofcontents
\listoffigures
\listoftables
\clearpage
{\noindent\Large\bfseries Liste des équations}\par\medskip
\begin{tabular}{@{}ll@{}}
(1) & Probabilité de déplacement entre deux taches ($p_{ij}$)\\
(2) & Probability of Connectivity (PC)\\
(3) & Budget de déplacement\\
(4) & Surface équivalente connectée (EC)\\
\end{tabular}
\clearpage
"""


def linkify(text: str) -> str:
    """Turn plain-text cross-references in already-escaped body text into clickable hyperlinks.

    Sections/subsections (§X.Y), chapters, figures and annexes point to their target; author-year
    citations point to the bibliography. Never applied to the bibliography itself. Structural links
    are inserted first, then the citation wrap skips any parenthesis that already holds a link (the
    negative lookahead on "hyperref"), which avoids nesting \\hyperref inside \\hyperref.
    """
    text = re.sub(r"§\s?(\d+(?:\.\d+)+)", r"\\hyperref[sec:\1]{§\1}", text)
    text = re.sub(r"\bchapitre\s+(\d+)\b", r"\\hyperref[chap:\1]{chapitre \1}", text)
    text = re.sub(
        r"\b(Figures?)\s+(\d+)((?:\s+et\s+\d+)?)",
        lambda m: "\\hyperref[fig:" + m.group(2) + "]{" + m.group(1) + " " + m.group(2) + m.group(3) + "}",
        text,
    )
    text = re.sub(r"\bannexe\s+([A-Z])\b", r"\\hyperref[annexe:\1]{annexe \1}", text)
    text = re.sub(
        r"\((?![^()]*hyperref)([^()]*(?:19|20)\d{2}[a-z]?[^()]*)\)",
        r"\\hyperref[sec:bibliographie]{(\1)}",
        text,
    )
    return text


URL_RE = re.compile(r"(https?://[^\s)]+)")


def render_bib_line(text: str) -> str:
    """Render a bibliography line, wrapping URLs in \\url{} so long DOIs break (xurl)."""
    out: list[str] = []
    for i, part in enumerate(URL_RE.split(text)):
        if i % 2 == 1:
            out.append("\\url{" + part + "}")
        elif part:
            out.append(inline(part))
    return "".join(out)


def main() -> None:
    os.makedirs(FIG, exist_ok=True)

    blocks: list[list[str]] = []
    for fp in sorted(glob.glob(os.path.join(BASE, "rapport_*.md"))):
        blocks.extend(parse_blocks(open(fp, encoding="utf-8").read()))

    body: list[str] = []
    nfig = ntab = 0
    in_bib = False
    i = 0
    while i < len(blocks):
        block = blocks[i]
        first = block[0].lstrip()
        if first.startswith("#"):
            hm = re.match(r"(#+)\s+(.*)", first)
            if hm and len(hm.group(1)) == 1:  # a chapter: bibliography chapter turns linkify off
                lw = hm.group(2).lower()
                in_bib = "bibliographie" in lw or "références" in lw
            body.append(render_heading(first))
        elif first.startswith(">"):
            content = [re.sub(r"^>\s?", "", ln) for ln in block]
            kind = classify_quote(content)
            if kind == "encadre":
                body.append(render_encadre(content))
            elif kind == "quote":
                q = inline(" ".join(ln.strip() for ln in content if ln.strip()))
                body.append("\\begin{quote}\n" + (q if in_bib else linkify(q)) + "\n\\end{quote}")
        elif is_table_block(block):
            body.append(render_table(block, None))
            ntab += 1
        else:
            joined = " ".join(ln.strip() for ln in block).strip()
            joined = re.sub(r"\s*\(objet\s*:[^)]*\)", "", joined)  # drop "(objet : ...)" reading aid
            joined = re.sub(r"\s*\[(?:non revérifiée|⚠|URL)[^\]]*\]", "", joined)  # working annotations
            mfig = re.match(r"\[FIGURE\s*:\s*(.*)\]$", joined)
            mtab = re.match(r"\[TABLEAU\s*:\s*(.*)\]$", joined)
            meq = re.match(r"\[EQUATION\s+(\d+)\s*:\s*(.*)\]$", joined)
            if meq:
                body.append("\\begin{equation*}\n" + meq.group(2).strip()
                            + "\n\\tag{" + meq.group(1) + "}\n\\end{equation*}")
            elif mfig:
                body.append(render_figure(mfig.group(1).strip(), nfig + 1))
                nfig += 1
            elif mtab:
                cap = mtab.group(1).strip()
                nxt = blocks[i + 1] if i + 1 < len(blocks) else None
                if nxt and is_table_block(nxt):
                    body.append(render_table(nxt, cap))
                    ntab += 1
                    i += 1
                else:
                    body.append(render_placeholder_table(cap))
                    ntab += 1
            elif in_bib:
                body.append(render_bib_line(joined))
            else:
                body.append(linkify(inline(joined)))
        i += 1

    tex = PREAMBLE + "\n\n".join(body) + "\n\n\\end{document}\n"
    out = os.path.join(BASE, "rapport_complet.tex")
    with open(out, "w", encoding="utf-8") as f:
        f.write(tex)
    print("TEX écrit :", out)
    print(f"  figures : {nfig} ; tableaux : {ntab}")


if __name__ == "__main__":
    main()
