"""Merge the internship-report markdown sections into a single PDF, pip-only (no LaTeX).

Pipeline: rapport_*.md -> HTML (+ CSS) -> PDF via xhtml2pdf (pure Python).
Needs: pip install xhtml2pdf

Same markdown subset as build_docx.py / build_latex.py:
- headings, hard-wrapped paragraphs, markdown tables,
- encadré blockquotes -> bordered boxes, brouillon notes dropped,
- [FIGURE : ...] -> embedded image if available else dashed placeholder, numbered caption,
- [TABLEAU : ...] -> numbered caption (+ following table if any),
- **bold** and highlighted placeholders.

Run: python3 build_pdf.py  ->  rapport_complet.pdf
"""

from __future__ import annotations

import glob
import html
import os
import re
import shutil

from xhtml2pdf import pisa

BASE: str = os.path.dirname(os.path.abspath(__file__))
FIG: str = os.path.join(BASE, "figures")
PIPELINE_SRC: str = os.path.normpath(os.path.join(BASE, "..", "..", "data", "outputs", "pipeline.png"))
PIPELINE_DST: str = os.path.join(FIG, "pipeline_chaine.png")

PLACEHOLDER_RE = re.compile(r"\[(?:CHIFFRE|À (?:COMPLÉTER|VÉRIFIER|ADAPTER))[^\]]*\]")
TOKEN_RE = re.compile(r"(\*\*.+?\*\*|\[(?:CHIFFRE|À (?:COMPLÉTER|VÉRIFIER|ADAPTER))[^\]]*\])")

CSS = """
@page { size: a4 portrait; margin: 2.3cm;
  @frame footer { -pdf-frame-content: footerContent; bottom: 1cm; margin-left: 2.3cm; margin-right: 2.3cm; height: 1cm; } }
body { font-family: "Times New Roman", serif; font-size: 11pt; line-height: 1.4; color: #1A1A1A; }
h1 { font-size: 20pt; -pdf-outline: true; -pdf-outline-level: 0; page-break-before: always;
  color: #123F3A; border-bottom: 1.5pt solid #2E8B84; padding-bottom: 3pt; margin-bottom: 10pt; }
h2 { font-size: 14pt; -pdf-outline: true; -pdf-outline-level: 1; color: #1B3A2B; margin-top: 12pt; }
h3 { font-size: 12pt; -pdf-outline: true; -pdf-outline-level: 2; color: #2E5D45; margin-top: 8pt; }
p { text-align: justify; margin: 5pt 0; }
.encadre { background-color: #EAF3EA; border: 1pt solid #6F9C6F; padding: 8pt 10pt; margin: 9pt 0; }
.encadre .etitle { color: #123F3A; margin-bottom: 4pt; }
.figure { text-align: center; margin: 10pt 0; }
.figure img { width: 15cm; }
.placeholder { border: 1pt dashed #AAAAAA; background-color: #F4F4F4; color: #888888;
  text-align: center; padding: 16pt; margin: 4pt 0; }
.caption { font-size: 9pt; font-style: italic; text-align: center; color: #444444; margin-top: 3pt; }
.tcaption { font-size: 9pt; font-style: italic; color: #444444; margin-top: 8pt; }
table { -pdf-keep-with-next: true; margin: 6pt 0; }
th { background-color: #2E8B84; color: #FFFFFF; font-weight: bold; border: 0.5pt solid #2E8B84; padding: 4pt; font-size: 9.5pt; }
td { border: 0.5pt solid #9CB89C; padding: 4pt; font-size: 9.5pt; }
.hl { background-color: #FFF176; }
.cover-title { text-align: center; font-size: 25pt; font-weight: bold; color: #123F3A; margin-top: 5cm; }
.cover-rule { border-top: 2pt solid #2E8B84; margin: 16pt 3cm; }
.cover-sub { text-align: center; font-size: 13pt; font-style: italic; color: #333333; }
.cover-meta { text-align: center; font-size: 12pt; margin-top: 5pt; }
"""


def figure_image(caption: str) -> str | None:
    m = re.match(r"\s*([\w-]+\.png)\b", caption)
    if m and os.path.exists(os.path.join(FIG, m.group(1))):
        return os.path.join(FIG, m.group(1))
    c = caption.lower()
    if "arborescence" in c:
        return os.path.join(FIG, "arborescence_sorties.png")
    if "comparaison sur la rochelle" in c:
        return os.path.join(FIG, "comparaison_larochelle.png")
    if "gabriel" in c:
        return os.path.join(FIG, "gabriel_criterion.png")
    if "réseau écologique" in c:
        return os.path.join(FIG, "reseau_ecologique.png")
    if "synoptique de la chaîne" in c:
        return PIPELINE_DST if os.path.exists(PIPELINE_DST) else None
    if "segmentation morphologique" in c:
        return os.path.join(FIG, "mspa_example.png")
    if "complet de sorties" in c:
        return os.path.join(FIG, "sorties_perpignan.png")
    if "dispersion compar" in c:
        return os.path.join(FIG, "dispersion_comparee.png")
    if "occupation du sol de toulouse" in c:
        return os.path.join(FIG, "landcover_toulouse.png")
    if "localisation" in c:
        return os.path.join(FIG, "localisation_territoires_osm.png")
    if "côte à côte" in c:
        return os.path.join(FIG, "territoires_comparees.png")
    if "scénario de végétalisation" in c:
        return os.path.join(FIG, "scenario_local.png")
    if "poolés sur les cinq territoires" in c:
        return os.path.join(FIG, "gbif_ratios_pooled.png")
    if "par territoire et poolés" in c:
        return os.path.join(FIG, "gbif_recap_par_ville.png")
    if "fauvette à toulouse" in c:
        return os.path.join(FIG, "gbif_carte_Toulouse_fauvette.png")
    if "cartes d'occurrences" in c and "oiseaux de lisière" in c:
        return os.path.join(FIG, "gbif_cartes_forest_edge_bird.png")
    if "cartes d'occurrences" in c and "mammifères arboricoles" in c:
        return os.path.join(FIG, "gbif_cartes_arboreal_mammal.png")
    if "cartes d'occurrences" in c and "mammifères terrestres" in c:
        return os.path.join(FIG, "gbif_cartes_ground_mammal.png")
    if "cartes d'occurrences" in c and "reptiles terrestres" in c:
        return os.path.join(FIG, "gbif_cartes_ground_reptile.png")
    if "tornade" in c and "hérisson" in c:
        return os.path.join(FIG, "tornado_ground_mammal_connected_habitat_pct.png")
    if "tornade" in c and "lézard" in c:
        return os.path.join(FIG, "tornado_ground_reptile_connected_habitat_pct.png")
    if "courbe de réponse" in c and "distance de dispersion" in c and "lézard" in c:
        return os.path.join(FIG, "response_d0_ground_reptile.png")
    if "courbe de réponse" in c and "distance de dispersion" in c and "hérisson" in c:
        return os.path.join(FIG, "response_d0_ground_mammal.png")
    if "courbe de réponse" in c and "contraste" in c and "lézard" in c:
        return os.path.join(FIG, "response_contrast_ground_reptile.png")
    if "courbe de réponse" in c and "contraste" in c and "hérisson" in c:
        return os.path.join(FIG, "response_contrast_ground_mammal.png")
    return None


def inline(text: str) -> str:
    out: list[str] = []
    for tok in TOKEN_RE.split(text):
        if not tok:
            continue
        if tok.startswith("**") and tok.endswith("**"):
            out.append("<b>" + html.escape(tok[2:-2]) + "</b>")
        elif PLACEHOLDER_RE.fullmatch(tok):
            out.append('<span class="hl">' + html.escape(tok) + "</span>")
        else:
            out.append(html.escape(tok))
    return "".join(out)


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


def encadre_html(content: list[str]) -> str:
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
    inner = f'<p class="etitle">{inline(title)}</p>' + "".join(f"<p>{inline(p)}</p>" for p in body)
    return f'<div class="encadre">{inner}</div>'


def classify_quote(content: list[str]) -> str:
    """Encadré (title line, blank, body) vs plain quote (e.g. the problématique) vs meta note."""
    firstne = next((ln for ln in content if ln.strip()), "").strip()
    if firstne.startswith(("Brouillon", "Front matter", "Travaux cités", "Références fournies")):
        return "drop"
    idx = next((i for i, ln in enumerate(content) if ln.strip()), None)
    if idx is not None and idx + 1 < len(content) and content[idx + 1].strip() == "" \
            and any(ln.strip() for ln in content[idx + 2:]):
        return "encadre"
    return "quote"


def table_html(block: list[str], caption: str | None, ntab: int) -> str:
    parsed = [[c.strip() for c in r.strip().strip("|").split("|")] for r in block]
    header, body = parsed[0], parsed[2:]
    rows = ["<tr>" + "".join(f"<th>{inline(h)}</th>" for h in header) + "</tr>"]
    for row in body:
        rows.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in row) + "</tr>")
    cap = f'<p class="tcaption">Tableau {ntab}. {inline(caption)}</p>' if caption else ""
    return cap + "<table>" + "".join(rows) + "</table>"


def figure_html(caption: str, nfig: int) -> str:
    img = figure_image(caption)
    if img and os.path.exists(img):
        inner = f'<div class="figure"><img src="{img}"/></div>'
    else:
        inner = '<div class="placeholder">[Figure à insérer]</div>'
    return inner + f'<p class="caption">Figure {nfig}. {inline(caption)}</p>'


def title_page() -> str:
    return (
        '<div class="cover-title">Conception d\'un outil reproductible de connectivité écologique urbaine</div>'
        '<div class="cover-rule"></div>'
        '<p class="cover-sub">à partir de l\'observation de la Terre et de données ouvertes</p>'
        '<p class="cover-meta">&nbsp;</p><p class="cover-meta">&nbsp;</p>'
        '<p class="cover-meta">Rapport de stage, Master 2 SIGMA</p>'
        '<p class="cover-meta"><b>Marion Billy</b></p>'
        '<p class="cover-meta">Structure d\'accueil : Murmuration</p>'
        '<p class="cover-meta">Tuteur de stage : Hugo Poupard &nbsp;·&nbsp; Responsable pédagogique : Laurent Jégou</p>'
        '<p class="cover-meta">Stage du 16 février au 14 août 2026</p>'
    )


def main() -> None:
    os.makedirs(FIG, exist_ok=True)

    blocks: list[list[str]] = []
    for fp in sorted(glob.glob(os.path.join(BASE, "rapport_*.md"))):
        blocks.extend(parse_blocks(open(fp, encoding="utf-8").read()))

    parts: list[str] = [title_page()]
    nfig = ntab = 0
    i = 0
    while i < len(blocks):
        block = blocks[i]
        first = block[0].lstrip()
        if first.startswith("#"):
            m = re.match(r"(#+)\s+(.*)", first)
            lvl = min(len(m.group(1)), 3)
            parts.append(f"<h{lvl}>{html.escape(m.group(2).strip())}</h{lvl}>")
        elif first.startswith(">"):
            content = [re.sub(r"^>\s?", "", ln) for ln in block]
            kind = classify_quote(content)
            if kind == "encadre":
                parts.append(encadre_html(content))
            elif kind == "quote":
                parts.append('<blockquote style="margin:6pt 1.2cm; font-style:italic; '
                             'border-left:3pt solid #6F9C6F; padding-left:8pt;">'
                             + inline(" ".join(ln.strip() for ln in content if ln.strip())) + "</blockquote>")
        elif is_table_block(block):
            ntab += 1
            parts.append(table_html(block, None, ntab))
        else:
            joined = " ".join(ln.strip() for ln in block).strip()
            joined = re.sub(r"\s*\(objet\s*:[^)]*\)\s*$", "", joined)  # drop "(objet : ...)" reading aid
            mfig = re.match(r"\[FIGURE\s*:\s*(.*)\]$", joined)
            mtab = re.match(r"\[TABLEAU\s*:\s*(.*)\]$", joined)
            if mfig:
                nfig += 1
                parts.append(figure_html(mfig.group(1).strip(), nfig))
            elif mtab:
                cap = mtab.group(1).strip()
                nxt = blocks[i + 1] if i + 1 < len(blocks) else None
                ntab += 1
                if nxt and is_table_block(nxt):
                    parts.append(table_html(nxt, cap, ntab))
                    i += 1
                else:
                    parts.append(f'<p class="tcaption">Tableau {ntab}. {inline(cap)}</p>'
                                 '<div class="placeholder">[Tableau à compléter après le re-run]</div>')
            else:
                parts.append(f"<p>{inline(joined)}</p>")
        i += 1

    doc = (f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>"
           '<div id="footerContent">Page <pdf:pagenumber> / <pdf:pagecount></div>'
           + "".join(parts) + "</body></html>")

    out = os.path.join(BASE, "rapport_complet.pdf")
    with open(out, "w+b") as f:
        status = pisa.CreatePDF(doc, dest=f, encoding="utf-8")
    print("PDF écrit :", out, "| erreurs:", status.err)
    print(f"  figures : {nfig} ; tableaux : {ntab}")


if __name__ == "__main__":
    main()
