#!/bin/bash
# Per-land-cover-class friction OFAT on Perpignan, QUEUED behind the sweeps, RESUMABLE + hang-proof.
# Waits for the sweeps, then scales ONE class at a time by +/-20 % for both profiles. Skips runs
# already done and wraps each in `timeout` so a hung Earth Engine fetch cannot freeze the queue.
cd /home/jovyan/work/team/marion/corridor_project || exit 1
mkdir -p _sandbox/logs
while [ ! -f _sandbox/logs/SWEEP_Perpignan_DONE.flag ]; do sleep 30; done
sleep 10
CITY=Perpignan
CLASSES="10 20 30 40 50 51 52 53 54 55 60 80 90 95"

run() {  # $1=guild $2=tag $3=scale $4=class
  local G="$1" tag="$2" sc="$3" cl="$4"
  if ls data/sensitivity/$tag/data/outputs/$CITY/$G/stats_*.csv >/dev/null 2>&1; then
    echo "skip $G $tag"; return
  fi
  timeout -k 60 900 python3 utils/run_pipeline.py $CITY --ecoprofil $G --lc-cache --friction-scale $sc --friction-class $cl --out-tag $tag \
      > _sandbox/logs/SENS3_${CITY}_${G}_${tag}.log 2>&1
  echo "$G $tag exit=$?"
}

for G in ground_mammal ground_reptile; do
  for C in $CLASSES; do
    run "$G" "c${C}_m20" 0.8 "$C"
    run "$G" "c${C}_p20" 1.2 "$C"
  done
done
echo "SENS3 Perpignan per-class DONE" > _sandbox/logs/SENS3_Perpignan_DONE.flag
