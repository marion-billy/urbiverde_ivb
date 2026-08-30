#!/bin/bash
# Per-land-cover-class friction OFAT on Perpignan (fast city): scale ONE class at a time by +/-20 %,
# for the generalist (hedgehog) and the specialist (lizard). Feeds a per-class tornado ranking which
# land-cover assumption drives the connectivity KPI the most.
cd /home/jovyan/work/team/marion/corridor_project || exit 1
mkdir -p _sandbox/logs
CITY=Perpignan
CLASSES="10 20 30 40 50 51 52 53 54 55 60 80 90 95"
for G in ground_mammal ground_reptile; do
  for C in $CLASSES; do
    python3 utils/run_pipeline.py $CITY --ecoprofil $G --friction-scale 0.8 --friction-class $C --out-tag c${C}_m20 \
        > _sandbox/logs/SENS3_${CITY}_${G}_c${C}_m20.log 2>&1
    python3 utils/run_pipeline.py $CITY --ecoprofil $G --friction-scale 1.2 --friction-class $C --out-tag c${C}_p20 \
        > _sandbox/logs/SENS3_${CITY}_${G}_c${C}_p20.log 2>&1
  done
done
echo "SENS3 Perpignan per-class DONE" > _sandbox/logs/SENS3_Perpignan_DONE.flag
