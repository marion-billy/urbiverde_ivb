#!/bin/bash
# Sweep runner for ONE city, serial internally (safe to run several in parallel: one per city,
# each writing to its own data/sensitivity/<tag>/.../<city>/ dirs). Same structure as the proven
# serial runner. Usage: bash run_city.sh <City>
export PYTHONPATH=/opt/conda/lib/python3.11/site-packages
cd /home/jovyan/work/team/marion/corridor_project || exit 1
C="$1"
[ -z "$C" ] && { echo "usage: run_city.sh <City> [\"guild1 guild2 ...\"]"; exit 1; }
mkdir -p _sandbox/logs
PROG="_sandbox/logs/SENS_${C}.log"
# 2e argument optionnel : liste de profils a traiter (defaut = les 4)
if [ -n "$2" ]; then GUILDS=($2); else GUILDS=(ground_mammal ground_reptile arboreal_mammal forest_edge_bird); fi
D0=(0.50 0.60 0.70 0.80 0.90 1.10 1.20)
FC=(0.00 0.25 0.50 0.75 1.25 1.50 2.00)

run() {  # $1=guild $2=tag $3..=extra pipeline args
  local G="$1" tag="$2"; shift 2
  local sdir="data/sensitivity/$tag/data/outputs/$C/$G"
  if ls $sdir/stats_*.csv >/dev/null 2>&1; then return; fi
  local t0=$SECONDS attempt
  # timeout monte a 3600s (grandes AOI LRSY/Toulouse : reptile ~3000s, swd0_120 depassait 1500s).
  # 2 essais seulement : un vrai timeout ne se rattrape pas, inutile de bruler 3x3600s dessus.
  for attempt in 1 2; do
    timeout -k 120 3600 python3 utils/run_pipeline.py "$C" --ecoprofil "$G" --out-tag "$tag" "$@" \
        > "_sandbox/logs/SENSFULL_${C}_${G}_${tag}.log" 2>&1
    # concurrency-safe cleanup: only tiles older than 5 min (never a run's in-use tile)
    find . -maxdepth 1 -name '??????.geojson' -size -2k -mmin +5 -delete 2>/dev/null
    if ls $sdir/stats_*.csv >/dev/null 2>&1; then
      echo "done  $C $G $tag attempt=$attempt ($((SECONDS-t0))s)" | tee -a "$PROG"; return
    fi
    sleep $((attempt * 60))
  done
  echo "FAIL  $C $G $tag (sans stats) ($((SECONDS-t0))s)" | tee -a "$PROG"
}

for PASS in 1 2; do
  echo "=== $C PASS $PASS/2 $(date +%H:%M) ===" | tee -a "$PROG"
  for G in "${GUILDS[@]}"; do
    for v in "${D0[@]}"; do
      run "$G" "swd0_$(printf '%03d' $(python3 -c "print(int(round($v*100)))"))" --d0-scale "$v"
    done
    for v in "${FC[@]}"; do
      run "$G" "swfc_$(printf '%03d' $(python3 -c "print(int(round($v*100)))"))" --friction-contrast "$v"
    done
  done
done
echo "=== $C DONE $(date +%H:%M) ===" | tee -a "$PROG"
