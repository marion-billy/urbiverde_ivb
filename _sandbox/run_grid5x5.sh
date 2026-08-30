#!/bin/bash
# 5x5 DENSIFICATION (targeted): fill the INTERIOR of the d0 x contrast grid for the 3 most-fragmented
# reptile couples, to draw a smooth response surface of the fragmentation metric where the 3x3 showed
# the interaction is least negligible. Levels d0 in {0.50,0.70,1.00,1.10,1.20}, contrast in
# {0.00,0.50,1.00,1.50,2.00}. The cross (either factor==baseline) already exists from the OAT sweep, and
# the 4 corners from the 3x3. Only the 12 interior points per couple are new: 3 couples x 12 = 36 runs.
# Same robust scheduler as run_grid3x3.sh: flat list -> xargs -P3, uniform 5h ceiling, retry loop.
#   setsid nohup bash _sandbox/run_grid5x5.sh </dev/null >> _sandbox/logs/nohup_grid5x5.out 2>&1 &
export PYTHONPATH=/opt/conda/lib/python3.11/site-packages
cd /home/jovyan/work/team/marion/corridor_project || exit 1
mkdir -p _sandbox/logs
PROG=_sandbox/logs/GRID5x5_progress.log
SELF=/home/jovyan/work/team/marion/corridor_project/_sandbox/run_grid5x5.sh
MAX_PASS=4

if [ "$1" = "--worker" ]; then
  C="$2"; G="$3"; d0="$4"; fc="$5"
  tag="grid_d$(printf '%03d' "$(python3 -c "print(int(round($d0*100)))")")_fc$(printf '%03d' "$(python3 -c "print(int(round($fc*100)))")")"
  sdir="data/sensitivity/$tag/data/outputs/$C/$G"
  if ls "$sdir"/stats_*.csv >/dev/null 2>&1; then exit 0; fi
  t0=$SECONDS
  for attempt in 1 2 3; do
    timeout -k 60 18000 python3 utils/run_pipeline.py "$C" --ecoprofil "$G" --out-tag "$tag" \
        --d0-scale "$d0" --friction-contrast "$fc" \
        > "_sandbox/logs/GRID5_${C}_${G}_${tag}.log" 2>&1
    find . -maxdepth 1 -name '??????.geojson' -size -2k -delete 2>/dev/null
    if ls "$sdir"/stats_*.csv >/dev/null 2>&1; then
      echo "done  $C $G $tag attempt=$attempt ($((SECONDS-t0))s)" | tee -a "$PROG"; exit 0
    fi
    sleep $((attempt * 60))
  done
  echo "FAIL  $C $G $tag (sans stats) ($((SECONDS-t0))s)" | tee -a "$PROG"
  exit 0
fi

# ---- controller ----
COUPLES=("LaRochelle ground_reptile" "Toulouse ground_reptile" "Nancy ground_reptile")
# 12 interior points: d0 in {0.50,0.70,1.10,1.20} x fc in {0.00,0.50,1.50,2.00} MINUS the 4 corners
INTERIOR=(\
  "0.50 0.50" "0.50 1.50" \
  "0.70 0.00" "0.70 0.50" "0.70 1.50" "0.70 2.00" \
  "1.10 0.00" "1.10 0.50" "1.10 1.50" "1.10 2.00" \
  "1.20 0.50" "1.20 1.50")
for PASS in $(seq 1 $MAX_PASS); do
  echo "=== GRID5x5 (flat xargs -P3) PASS $PASS/$MAX_PASS $(date +'%F %H:%M') ===" | tee -a "$PROG"
  for cpl in "${COUPLES[@]}"; do
    for pt in "${INTERIOR[@]}"; do
      echo "$cpl $pt"
    done
  done | xargs -P 3 -n 4 bash "$SELF" --worker
  ndone=$(for cpl in "${COUPLES[@]}"; do set -- $cpl; for t in $(ls -d data/sensitivity/grid_d*_fc*/ 2>/dev/null); do :; done; done; ls data/sensitivity/grid_d*_fc*/data/outputs/{LaRochelle,Toulouse,Nancy}/ground_reptile/stats_*.csv 2>/dev/null | wc -l)
  echo "=== PASS $PASS done $(date +'%F %H:%M') : reptile grid cells present $ndone ===" | tee -a "$PROG"
  # 3 couples x 25 cells = 75 total when the full 5x5 is assembled from all tag sources; here we only
  # gate on the 36 interior runs being done (12 x 3), detected by re-running xargs which skips finished.
  gaps=0
  for cpl in "${COUPLES[@]}"; do set -- $cpl; C=$1; G=$2
    for pt in "${INTERIOR[@]}"; do set -- $pt; d0=$1; fc=$2
      tag="grid_d$(printf '%03d' "$(python3 -c "print(int(round($d0*100)))")")_fc$(printf '%03d' "$(python3 -c "print(int(round($fc*100)))")")"
      ls data/sensitivity/$tag/data/outputs/$C/$G/stats_*.csv >/dev/null 2>&1 || gaps=$((gaps+1))
    done
  done
  echo "    interior gaps remaining: $gaps / 36" | tee -a "$PROG"
  [ "$gaps" -eq 0 ] && break
done
echo "=== GRID5x5 DONE $(date +'%F %H:%M') ===" | tee -a "$PROG"
touch _sandbox/logs/GRID5x5_DONE.flag
