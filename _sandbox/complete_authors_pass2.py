"""2nd pass on the still-truncated 'et al.' entries: DOI-first, else fuzzy title match (year ±1 +
normalized-title containment). Applies only confident matches; prints candidates for the rest.
Never guesses."""
import json, re, time, urllib.request, urllib.parse, shutil

F = "rapport_8_references.md"
MAIL = "research@murmuration-sas.com"
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())


def initials(given):
    out = []
    for tok in given.replace(".", " ").split():
        out.append("-".join(p[0].upper() + "." for p in tok.split("-") if p))
    return " ".join(out)


def apa(auths):
    n = [f"{a.get('family','').strip()}, {initials(a.get('given','').strip())}".rstrip(", ").strip()
         if a.get("given") else a.get("family", "").strip() for a in auths]
    return n[0] if len(n) == 1 else ", ".join(n[:-1]) + ", & " + n[-1]


def fetch(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)


lines = open(F, encoding="utf-8").read().splitlines(keepends=True)
shutil.copyfile(F, F + ".bak3")
patched, manual = 0, []

for i, ln in enumerate(lines):
    if ", et al. (" not in ln:
        continue
    year = re.search(r"\((\d{4})\)", ln).group(1)
    surn = re.match(r"^([A-ZÉÈ][A-Za-zÉÈ'’\-]+)", ln).group(1)
    tit = re.search(r"\(\d{4}\)\.\s*(?:\*)?([^*.]{12,140})", ln)
    title = tit.group(1).strip() if tit else ""
    doi = re.search(r"https://doi\.org/(\S+?)(?:\s|\)|$)", ln)
    item = None
    try:
        if doi:
            item = fetch(f"https://api.crossref.org/works/{urllib.parse.quote(doi.group(1))}?mailto={MAIL}")["message"]
        else:
            q = urllib.parse.urlencode({"query.bibliographic": title, "rows": 6})
            cands = fetch(f"https://api.crossref.org/works?{q}&mailto={MAIL}")["message"]["items"]
            nt = norm(title)[:40]
            for it in cands:
                ct = norm((it.get("title") or [""])[0])
                iy = str((it.get("issued", {}).get("date-parts", [[None]]) or [[None]])[0][0])
                if it.get("author") and (nt in ct or ct[:40] in norm(title)) and abs(int(iy or 0) - int(year)) <= 1:
                    item = it; break
    except Exception as e:
        manual.append((i + 1, surn, year, f"réseau {type(e).__name__}")); time.sleep(1); continue
    time.sleep(0.5)
    if not item or not item.get("author"):
        # affiche les candidats pour décision manuelle
        cand_txt = ""
        try:
            cand_txt = " | ".join(f"{(c.get('title') or ['?'])[0][:35]}~{(c.get('issued',{}).get('date-parts',[['?']]) or [['?']])[0][0]}" for c in cands[:3])
        except Exception:
            pass
        manual.append((i + 1, surn, year, cand_txt or "aucun candidat")); continue
    full = apa(item["author"])
    new = re.sub(r"^.*? \(" + year + r"\)\.", f"{full} ({year}).", ln, count=1)
    if "et al." not in new.split(f"({year})")[0]:
        lines[i] = new; patched += 1
        print(f"OK  [{surn} {year}] {len(item['author'])} auteurs" + (" (via DOI)" if doi else " (via titre)"))
    else:
        manual.append((i + 1, surn, year, "remplacement KO"))

open(F, "w", encoding="utf-8").write("".join(lines))
print(f"\n=== 2e passe : {patched} complétées ; {len(manual)} à la main ===")
for i, s, y, info in manual:
    print(f"  L{i} [{s} {y}] {info}")
