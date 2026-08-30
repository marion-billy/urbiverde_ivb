#!/bin/bash
# SOLO sweep of ground_mammal (herisson, d0=3000, heaviest profile) for ONE big city given as $1.
# Full resources (no parallel city), timeout 6h/run, single attempt, idempotent, detached.
#   setsid nohup bash _sandbox/run_hedgehog_solo.sh LRSY </dev/null >> _sandbox/logs/nohup_hh_LRSY.out 2>&1 &
export PYTHONPATH=/opt/conda/lib/python3.11/site-packages
cd /home/jovyan/work/team/marion/corridor_project || exit 1
C="$1"; G=ground_mammal
[ -z "$C" ] && { echo "usage: run_hedgehog_solo.sh <City>"; exit 1; }
mkdir -p _sandbox/logs
PROG="_sandbox/logs/SENS_${C}_${G}_solo.log"
D0=(0.50 0.60 0.70 0.80 0.90 1.10 1.20)
FC=(0.00 0.25 0.50 0.75 1.25 1.50 2.00)

run() {  # $1=tag ; $2.. = extra pipeline args
  local tag="$1"; shift
  local sdir="data/sensitivity/$tag/data/outputs/$C/$G"
  if ls "$sdir"/stats_*.csv >/dev/null 2>&1; then echo "skip  $tag (deja fait)" | tee -a "$PROG"; return; fi
  local t0=$SECONDS
  timeout -k 120 21600 python3 utils/run_pipeline.py "$C" --ecoprofil "$G" --out-tag "$tag" "$@" \
      > "_sandbox/logs/SENSFULL_${C}_${G}_${tag}.log" 2>&1
  find . -maxdepth 1 -name '??????.geojson' -size -2k -mmin +5 -delete 2>/dev/null
  if ls "$sdir"/stats_*.csv >/dev/null 2>&1; then
    echo "done  $tag ($((SECONDS-t0))s)" | tee -a "$PROG"
  else
    echo "FAIL  $tag (sans stats, $((SECONDS-t0))s)" | tee -a "$PROG"
  fi
}

echo "=== SOLO $C $G START $(date +'%F %H:%M') (timeout 6h/run, 1 essai) ===" | tee -a "$PROG"
for v in "${D0[@]}"; do run "swd0_$(printf '%03d' "$(python3 -c "print(int(round($v*100)))")")" --d0-scale "$v"; done
for v in "${FC[@]}"; do run "swfc_$(printf '%03d' "$(python3 -c "print(int(round($v*100)))")")" --friction-contrast "$v"; done
echo "=== SOLO $C $G DONE $(date +'%F %H:%M') ===" | tee -a "$PROG"
