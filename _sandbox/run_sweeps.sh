#!/bin/bash
# Parameter SWEEPS on Perpignan, RESUMABLE + hang-proof:
#   - skip a run whose stats already exist (so a relaunch resumes where it stopped),
#   - wrap each run in `timeout` so a hung Earth Engine fetch is killed (15 min) instead of freezing
#     the whole sequential queue (root cause of the overnight stall).
# d0 sweep (0.50..1.50) and contrast sweep (k=0..2), for hedgehog + lizard. Baseline 1.0 = data/outputs.
cd /home/jovyan/work/team/marion/corridor_project || exit 1
mkdir -p _sandbox/logs
CITY=Perpignan
D0=(0.50 0.60 0.70 0.75 0.80 0.90 1.10 1.25 1.50)
FC=(0.00 0.25 0.50 0.75 1.25 1.50 2.00)

run() {  # $1=guild $2=tag $3..=extra pipeline args
  local G="$1" tag="$2"; shift 2
  if ls data/sensitivity/$tag/data/outputs/$CITY/$G/stats_*.csv >/dev/null 2>&1; then
    echo "skip $G $tag (déjà fait)"; return
  fi
  timeout -k 60 900 python3 utils/run_pipeline.py $CITY --ecoprofil $G --lc-cache "$@" --out-tag $tag \
      > _sandbox/logs/SWEEP_${CITY}_${G}_${tag}.log 2>&1
  echo "$G $tag exit=$?"
}

for G in ground_mammal ground_reptile; do
  for v in "${D0[@]}"; do
    run "$G" "swd0_$(printf '%03d' $(python3 -c "print(int(round($v*100)))"))" --d0-scale $v
  done
  for v in "${FC[@]}"; do
    run "$G" "swfc_$(printf '%03d' $(python3 -c "print(int(round($v*100)))"))" --friction-contrast $v
  done
done
echo "SWEEPS Perpignan DONE" > _sandbox/logs/SWEEP_Perpignan_DONE.flag
