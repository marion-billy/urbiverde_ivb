"""Item 5 biblio cleanup on rapport_8_references.md, with backup + printed journal (deletion guard).
1) Remove the 10 clearly-non-relevant orphan entries (validated by Marion), by (surname, year).
   KEEP the 8 'espèces' orphans (flagged for §2.3) and the 2 borderline (Boakes, El-Gabbas).
2) Strip the verified-moot [⚠ corps : ...] flags from every entry.
Prints every removed line and the strip count. Idempotent-ish (skips already-absent)."""
import re
import shutil

F = "rapport_8_references.md"
REMOVE = {("Audebert", "2018"), ("Herold", "2004"), ("Dickson", "2019"), ("Baguette", "2013"),
          ("Phillips", "2009"), ("Clark", "1999"), ("Lumia", "2023"), ("Kwon", "2021"),
          ("Aliabad", "2024"), ("Merkens", "2023")}
CORPS_FLAG = re.compile(r"\s*\[⚠ corps[^\]]*\]")

shutil.copyfile(F, F + ".bak")
out, removed, stripped = [], [], 0
for ln in open(F, encoding="utf-8"):
    m = re.match(r"^([A-ZÉÈÀ][A-Za-zÉÈÀ'’-]+)\b.*\((\d{4})", ln)
    if m and (m.group(1), m.group(2)) in REMOVE:
        removed.append(ln.strip()[:95])
        continue
    new = CORPS_FLAG.sub("", ln)
    if new != ln:
        stripped += 1
    out.append(new)

open(F, "w", encoding="utf-8").write("".join(out))
print(f"SUPPRIMÉES ({len(removed)}/10) :")
for r in removed:
    print("  -", r, "…")
print(f"\nflags [⚠ corps] retirés : {stripped}")
print(f"sauvegarde : {F}.bak")
