#!/bin/bash
# freeze_env.sh - releve et fige l'environnement d'execution de la chaine.
#
# Pourquoi : l'annexe A du rapport liste des versions de bibliotheques, mais elles ne sont
# figees dans aucun fichier (requirements.txt ne porte que smoothify). Ce script produit les
# deux artefacts qui rendent l'affirmation exacte, et qui permettent a un tiers de reconstituer
# l'environnement.
#
# A lancer sur la VM, depuis la racine du projet, dans l'environnement qui a produit les sorties :
#   bash env/freeze_env.sh
#
# Produit :
#   env/requirements-lock.txt  - toutes les versions pip, exhaustif (reconstitution a l'identique)
#   env/requirements-core.txt  - les seules bibliotheques importees par la chaine (lisible, annexe A)
#   env/environment.yml        - export conda si conda est disponible
#   env/env_report.txt         - versions relevees a l'execution + contexte (python, OS, commit)

set -u
cd "$(dirname "$0")/.." || exit 1
OUT="env"
mkdir -p "$OUT"

PY="${PYTHON:-python3}"
PIP="${PIP:-$PY -m pip}"

echo "=== 1. pip freeze (exhaustif) ==="
$PIP freeze > "$OUT/requirements-lock.txt" 2>/dev/null \
  && echo "  -> $OUT/requirements-lock.txt ($(wc -l < "$OUT/requirements-lock.txt") paquets)" \
  || echo "  ECHEC pip freeze"

echo "=== 2. versions des bibliotheques effectivement importees ==="
# Liste tenue a la main : correspond aux imports de utils/*.py. La mettre a jour si un
# import est ajoute a la chaine.
$PY - > "$OUT/env_report.txt" <<'PYEOF'
import importlib, platform, subprocess, sys

MODULES = [
    "numpy", "pandas", "scipy", "networkx", "shapely", "geopandas", "xarray", "rioxarray",
    "rasterio", "skimage", "sklearn", "matplotlib", "tqdm", "affine", "requests",
    "osmnx", "ee", "geemap", "xee", "pyarrow", "smoothify",
]

def git(*a):
    try:
        return subprocess.run(["git", *a], capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return "(hors depot Git)"

print("python           :", sys.version.split()[0])
print("plateforme       :", platform.platform())
print("executable       :", sys.executable)
print("commit git       :", git("rev-parse", "HEAD"))
print("arbre modifie    :", "oui" if git("status", "--porcelain") not in ("", "(hors depot Git)") else "non")
print()
print("bibliotheque         version")
print("-" * 40)
core = []
for m in MODULES:
    try:
        mod = importlib.import_module(m)
        v = getattr(mod, "__version__", "?")
        print(f"{m:20s} {v}")
        core.append((m, v))
    except Exception as e:
        print(f"{m:20s} ABSENT ({type(e).__name__})")

# Noms de distribution differant du nom d'import
DIST = {"skimage": "scikit-image", "sklearn": "scikit-learn", "ee": "earthengine-api"}
with open("env/requirements-core.txt", "w") as fh:
    fh.write("# Bibliotheques importees par la chaine, versions relevees a l'execution.\n")
    fh.write("# Genere par env/freeze_env.sh - ne pas editer a la main.\n")
    for m, v in core:
        if v != "?":
            fh.write(f"{DIST.get(m, m)}=={v}\n")
PYEOF
cat "$OUT/env_report.txt"
echo "  -> $OUT/env_report.txt, $OUT/requirements-core.txt"

echo "=== 3. export conda (si disponible) ==="
if command -v conda >/dev/null 2>&1; then
    conda env export --no-builds > "$OUT/environment.yml" 2>/dev/null \
      && echo "  -> $OUT/environment.yml" || echo "  ECHEC conda env export"
else
    echo "  conda absent, etape ignoree"
fi

echo
echo "Termine. Commiter env/ puis corriger la phrase de l'annexe A du rapport"
echo "(les versions sont desormais figees dans env/requirements-lock.txt)."
