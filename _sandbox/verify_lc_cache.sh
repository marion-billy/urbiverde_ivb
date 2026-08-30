#!/bin/bash
cd /home/jovyan/work/team/marion/corridor_project || exit 1
G=ground_reptile
timeout -k 60 1200 python3 utils/run_pipeline.py Perpignan --ecoprofil $G --lc-cache --refresh-lc --out-tag lcver_fresh  > _sandbox/logs/LC_lcver_fresh.log  2>&1
timeout -k 60 1200 python3 utils/run_pipeline.py Perpignan --ecoprofil $G --lc-cache             --out-tag lcver_cached > _sandbox/logs/LC_lcver_cached.log 2>&1
python3 - > _sandbox/logs/LC_CACHE_VERIFY.txt 2>&1 <<'PY'
import pandas as pd, glob
def stat(d):
    f=glob.glob(f"{d}/ground_reptile/stats_*.csv")
    return pd.read_csv(f[0]).iloc[0] if f else None
base=stat("data/outputs/Perpignan")
fresh=stat("data/sensitivity/lcver_fresh/data/outputs/Perpignan")
cached=stat("data/sensitivity/lcver_cached/data/outputs/Perpignan")
cols=["ec_real_ha","connected_habitat_pct","n_subnetworks","nb_corridors"]
for c in cols:
    print(f"{c:24}: base={None if base is None else base.get(c)}  fresh={None if fresh is None else fresh.get(c)}  cached={None if cached is None else cached.get(c)}")
ok = fresh is not None and cached is not None and all(abs(float(fresh[c])-float(cached[c]))<1e-6 for c in cols if c in fresh and c in cached)
print("VERDICT:", "OK (cache lu == fraîchement téléchargé)" if ok else "DIFFERENCE -> cache NON fidèle")
PY
echo done > _sandbox/logs/LC_VERIFY_DONE.flag
