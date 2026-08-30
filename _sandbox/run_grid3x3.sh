#!/bin/bash
# JOINT 3x3 sensitivity grid: d0 x friction-contrast, to MEASURE the interaction the OAT sweep cannot see.
# Levels d0 in {0.50,1.00,1.20}, contrast in {0.00,1.00,2.00}. The cross (either factor == baseline) exists
# already; only the 4 corners per couple run here = 6 x 4 x 4 = 96. With the cross -> full 3x3 factorial.
#
# SCHEDULER (2026-08-13): FLAT job list piped to `xargs -P 3` (each corner an independent job; no per-city
# subshell, so no slow city stalls the others). UNIFORM 5h timeout ceiling: a ceiling never slows a fast run
# (Nancy bird = 400s), it only caps a genuinely heavy one (LRSY has a huge habitat graph; even the light
# guilds at d0 x1.20 exceed 30 min there). OUTER retry loop up to MAX_PASS: idempotent skip of finished
# corners, so each pass only re-runs the gaps; stops at 96/96. PYTHONPATH=conda (urllib3-future fork breaks
# Earth Engine). NO --lc-cache (raster cache corrupt).
#   setsid nohup bash _sandbox/run_grid3x3.sh </dev/null >> _sandbox/logs/nohup_grid3x3.out 2>&1 &
export PYTHONPATH=/opt/conda/lib/python3.11/site-packages
cd /home/jovyan/work/team/marion/corridor_project || exit 1
mkdir -p _sandbox/logs
PROG=_sandbox/logs/GRID3x3_progress.log
SELF=/home/jovyan/work/team/marion/corridor_project/_sandbox/run_grid3x3.sh
MAX_PASS=4

if [ "$1" = "--worker" ]; then
  C="$2"; G="$3"; d0="$4"; fc="$5"
  tag="grid_d$(printf '%03d' "$(python3 -c "print(int(round($d0*100)))")")_fc$(printf '%03d' "$(python3 -c "print(int(round($fc*100)))")")"
  sdir="data/sensitivity/$tag/data/outputs/$C/$G"
  if ls "$sdir"/stats_*.csv >/dev/null 2>&1; then exit 0; fi
  TO=18000   # 5h ceiling for every corner; fast ones still finish fast
  t0=$SECONDS
  for attempt in 1 2 3; do
    timeout -k 60 "$TO" python3 utils/run_pipeline.py "$C" --ecoprofil "$G" --out-tag "$tag" \
        --d0-scale "$d0" --friction-contrast "$fc" \
        > "_sandbox/logs/GRID_${C}_${G}_${tag}.log" 2>&1
    find . -maxdepth 1 -name '??????.geojson' -size -2k -delete 2>/dev/null
    if ls "$sdir"/stats_*.csv >/dev/null 2>&1; then
      echo "done  $C $G $tag attempt=$attempt ($((SECONDS-t0))s)" | tee -a "$PROG"; exit 0
    fi
    sleep $((attempt * 90))
  done
  echo "FAIL  $C $G $tag (sans stats) ($((SECONDS-t0))s)" | tee -a "$PROG"
  exit 0
fi

# ---- controller: flat 96-job list, 3 at a time, retried until 96/96 ----
CITIES=(Kourou Perpignan Nancy LaRochelle LRSY Toulouse)
GUILDS=(ground_mammal ground_reptile arboreal_mammal forest_edge_bird)
CORNERS=("0.50:0.00" "0.50:2.00" "1.20:0.00" "1.20:2.00")
for PASS in $(seq 1 $MAX_PASS); do
  echo "=== GRID3x3 (flat xargs -P3) PASS $PASS/$MAX_PASS $(date +'%F %H:%M') ===" | tee -a "$PROG"
  for C in "${CITIES[@]}"; do
    for G in "${GUILDS[@]}"; do
      for p in "${CORNERS[@]}"; do
        echo "$C $G ${p%%:*} ${p##*:}"
      done
    done
  done | xargs -P 3 -n 4 bash "$SELF" --worker
  ndone=$(ls data/sensitivity/grid_d*_fc*/data/outputs/*/*/stats_*.csv 2>/dev/null | wc -l)
  echo "=== PASS $PASS done $(date +'%F %H:%M') : $ndone / 96 ===" | tee -a "$PROG"
  [ "$ndone" -ge 96 ] && break
done
touch _sandbox/logs/GRID3x3_DONE.flag
