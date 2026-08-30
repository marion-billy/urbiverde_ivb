#!/bin/bash
# Sensitivity grid for La Rochelle (morcele) : 2 guilds x 4 perturbations, mirrors the Perpignan grid.
cd /home/jovyan/work/team/marion/corridor_project || exit 1
mkdir -p _sandbox/logs
CITY=LaRochelle
for G in ground_mammal ground_reptile; do
  python3 utils/run_pipeline.py $CITY --ecoprofil $G --friction-scale 0.8  --out-tag fric_m20 > _sandbox/logs/SENS2_${CITY}_${G}_fric_m20.log 2>&1
  python3 utils/run_pipeline.py $CITY --ecoprofil $G --friction-scale 1.2  --out-tag fric_p20 > _sandbox/logs/SENS2_${CITY}_${G}_fric_p20.log 2>&1
  python3 utils/run_pipeline.py $CITY --ecoprofil $G --d0-scale 0.75       --out-tag d0_m25   > _sandbox/logs/SENS2_${CITY}_${G}_d0_m25.log 2>&1
  python3 utils/run_pipeline.py $CITY --ecoprofil $G --d0-scale 1.25       --out-tag d0_p25   > _sandbox/logs/SENS2_${CITY}_${G}_d0_p25.log 2>&1
done
echo "SENS2 LaRochelle DONE" > _sandbox/logs/SENS2_LaRochelle_DONE.flag
