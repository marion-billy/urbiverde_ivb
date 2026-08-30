"""Complete the 24 'et al.'-truncated bibliography entries with full author lists from Crossref.
Query by title, verify (year exact + first-author surname match) before applying. Only confident
matches are patched into rapport_8_references.md; uncertain ones are printed for manual check.
Makes a .bak2 backup first. Never guesses an author list."""
import json, re, time, urllib.request, urllib.parse, shutil

F = "rapport_8_references.md"
MAIL = "research@murmuration-sas.com"


def initials(given: str) -> str:
    out = []
    for tok in given.replace(".", " ").split():
        parts = tok.split("-")
        out.append("-".join(p[0].upper() + "." for p in parts if p))
    return " ".join(out)


def apa_authors(auths: list) -> str:
    names = []
    for a in auths:
        fam = a.get("family", "").strip()
        giv = a.get("given", "").strip()
        names.append(f"{fam}, {initials(giv)}".strip().rstrip(",") if giv else fam)
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + ", & " + names[-1]


def crossref(title: str):
    q = urllib.parse.urlencode({"query.bibliographic": title, "rows": 3})
    url = f"https://api.crossref.org/works?{q}&mailto={MAIL}"
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)["message"]["items"]


lines = open(F, encoding="utf-8").read().splitlines(keepends=True)
shutil.copyfile(F, F + ".bak2")
patched, flagged = 0, []

for i, ln in enumerate(lines):
    if ", et al. (" not in ln:
        continue
    myr = re.search(r"\((\d{4})\)", ln)
    mtit = re.search(r"\(\d{4}\)\.\s*(?:\*)?([^*.]{15,140})", ln)
    msurn = re.match(r"^([A-ZÉÈ][A-Za-zÉÈ'’\-]+)", ln)
    if not (myr and mtit and msurn):
        flagged.append((i, "parsing", ln[:60])); continue
    year, title, surn = myr.group(1), mtit.group(1).strip(), msurn.group(1)
    try:
        items = crossref(title)
    except Exception as e:
        flagged.append((i, f"réseau {type(e).__name__}", f"{surn} {year}")); time.sleep(1); continue
    time.sleep(0.5)
    best = None
    for it in items:
        iy = str((it.get("issued", {}).get("date-parts", [[None]]) or [[None]])[0][0])
        fam0 = (it.get("author", [{}]) or [{}])[0].get("family", "")
        if iy == year and fam0 and (fam0.split()[-1].lower() == surn.lower() or surn.lower() in fam0.lower()):
            best = it; break
    if not best or not best.get("author"):
        flagged.append((i, "pas de match sûr (année/auteur)", f"{surn} {year} — {title[:45]}")); continue
    full = apa_authors(best["author"])
    # remplace le segment auteurs (tout avant ' (YEAR).') par la liste complète
    new = re.sub(r"^.*? \(" + year + r"\)\.", f"{full} ({year}).", ln, count=1)
    if new != ln and "et al." not in new.split(f"({year})")[0]:
        lines[i] = new; patched += 1
        print(f"OK  [{surn} {year}] {len(best['author'])} auteurs")
    else:
        flagged.append((i, "remplacement non appliqué", f"{surn} {year}"))

open(F, "w", encoding="utf-8").write("".join(lines))
print(f"\n=== {patched} entrées complétées / 24 ; {len(flagged)} à vérifier à la main ===")
for i, why, what in flagged:
    print(f"  L{i+1} [{why}] {what}")
print(f"sauvegarde : {F}.bak2")
