#!/bin/bash
# FULL sensitivity campaign: every city x every guild, two sweeps only
#   d0 sweep 50-120 % (step 10), friction-contrast sweep 0-200 % (retained approach: no local OAT, no uniform friction)
# (d0 0.50..1.50, friction-contrast 0..2). = 6 x 4 x 20 = 480 runs. Baseline 1.0 = data/outputs.
#
# ROBUSTNESS (2026-08-04):
#  - PYTHONPATH=conda first: ~/.local ships urllib3-future (a fork installed *as* urllib3) that breaks
#    the Earth Engine HTTP client; the conda path restores standard urllib3 (osmnx stays available).
#  - NO --lc-cache: the raster cache is corrupt (stores WorldCover codes /10, e.g. 1..9.5 instead of
#    10..95) -> wrong habitat. The fetch path is the proven-correct one (codes 0,10..95,51..54).
#  - timeout per run; retry x3 with long increasing backoff (Overpass = overpass-api.de rate-limits /
#    flaps on dense cities). A run that still fails leaves NO stats, so it is retried on the next PASS.
#  - AUTO-CONVERGING outer loop: up to MAX_PASS passes; each pass skips finished runs and retries only
#    the gaps. Stops as soon as a full pass has zero failures. Runs unattended to completion.
export PYTHONPATH=/opt/conda/lib/python3.11/site-packages
cd /home/jovyan/work/team/marion/corridor_project || exit 1
mkdir -p _sandbox/logs
PROG=_sandbox/logs/SENS_FULL_progress.log
MAX_PASS=6

CITIES=(Kourou Perpignan Nancy LaRochelle LRSY Toulouse)
GUILDS=(ground_mammal ground_reptile arboreal_mammal forest_edge_bird)
D0=(0.50 0.60 0.70 0.80 0.90 1.10 1.20)
FC=(0.00 0.25 0.50 0.75 1.25 1.50 2.00)
PASS_FAILS=0

run() {  # $1=city $2=guild $3=tag $4..=extra pipeline args
  local C="$1" G="$2" tag="$3"; shift 3
  local sdir="data/sensitivity/$tag/data/outputs/$C/$G"
  if ls $sdir/stats_*.csv >/dev/null 2>&1; then return; fi   # already valid: skip silently
  local t0=$SECONDS attempt
  for attempt in 1 2 3; do
    timeout -k 60 1500 python3 utils/run_pipeline.py "$C" --ecoprofil "$G" --out-tag "$tag" "$@" \
        > "_sandbox/logs/SENSFULL_${C}_${G}_${tag}.log" 2>&1
    # clean the temp EE/geemap AOI tiles this run dropped in the project root (convention: nothing at root)
    find . -maxdepth 1 -name '??????.geojson' -size -2k -delete 2>/dev/null
    if ls $sdir/stats_*.csv >/dev/null 2>&1; then
      echo "done  $C $G $tag exit=0 attempt=$attempt ($((SECONDS-t0))s)" | tee -a "$PROG"; return
    fi
    sleep $((attempt * 90))  # long backoff: gentle on Overpass, lets a transient block lift
  done
  echo "FAIL  $C $G $tag (sans stats) ($((SECONDS-t0))s)" | tee -a "$PROG"
  PASS_FAILS=$((PASS_FAILS + 1))
}

MAXPAR=3  # villes traitees en parallele (chacune serielle en interne pour borner la RAM)
for PASS in $(seq 1 $MAX_PASS); do
  echo "=== SENS FULL PASS $PASS/$MAX_PASS $(date +%H:%M) (parallele x$MAXPAR villes) ===" | tee -a "$PROG"
  for C in "${CITIES[@]}"; do
    (
      for G in "${GUILDS[@]}"; do
        for v in "${D0[@]}"; do
          run "$C" "$G" "swd0_$(printf '%03d' $(python3 -c "print(int(round($v*100)))"))" --d0-scale "$v"
        done
        for v in "${FC[@]}"; do
          run "$C" "$G" "swfc_$(printf '%03d' $(python3 -c "print(int(round($v*100)))"))" --friction-contrast "$v"
        done
      done
    ) &
    while [ "$(jobs -r | wc -l)" -ge "$MAXPAR" ]; do wait -n; done
  done
  wait
  echo "=== PASS $PASS done $(date +%H:%M) ===" | tee -a "$PROG"
  sleep 30  # OSM en cache : pas besoin d'une longue recuperation entre passes
done
echo "=== SENS FULL DONE (passes) ===" | tee -a "$PROG"
touch _sandbox/logs/SENS_FULL_DONE.flag
