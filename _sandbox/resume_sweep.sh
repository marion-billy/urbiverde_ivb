#!/bin/bash
# (Re)lance le balayage de sensibilite, DETACHE de la session (setsid + nohup) : survit a une
# deconnexion tant que le conteneur tourne. Idempotent (jeux deja calcules = sautes) et SUR :
# saute une ville deja terminee (56 jeux) ou dont un run est encore frais (< 20 min = suppose actif),
# pour ne jamais faire tourner deux runners sur la meme ville. A relancer tel quel au retour :
#   bash _sandbox/resume_sweep.sh
cd /home/jovyan/work/team/marion/corridor_project || exit 1
mkdir -p _sandbox/logs
TAGS="swd0_050 swd0_060 swd0_070 swd0_080 swd0_090 swd0_110 swd0_120 swfc_000 swfc_025 swfc_050 swfc_075 swfc_125 swfc_150 swfc_200"
for C in Nancy LaRochelle LRSY Toulouse; do
  # deja fini ?
  n=0; for G in ground_mammal ground_reptile arboreal_mammal forest_edge_bird; do for t in $TAGS; do
    ls data/sensitivity/$t/data/outputs/$C/$G/stats_*.csv >/dev/null 2>&1 && n=$((n+1)); done; done
  if [ "$n" -ge 56 ]; then echo "$C : deja complet (56/56), saute"; continue; fi
  # un run frais (< 20 min) ? => suppose encore actif, on ne relance pas
  if [ -n "$(find _sandbox/logs -name "SENSFULL_${C}_*.log" -mmin -20 2>/dev/null | head -1)" ]; then
    echo "$C : run recent (< 20 min), suppose actif, saute"; continue
  fi
  # LRSY (502 km2) et Toulouse (461 km2) : profil herisson trop lourd (timeout), on l'ecarte (option c)
  case "$C" in
    LRSY|Toulouse) GLIST="ground_reptile arboreal_mammal forest_edge_bird" ;;
    *) GLIST="" ;;
  esac
  setsid nohup bash _sandbox/run_city.sh "$C" "$GLIST" </dev/null >> "_sandbox/logs/nohup_${C}.out" 2>&1 &
  disown 2>/dev/null || true
  echo "$C : (re)lance detache ($n/56 deja faits${GLIST:+, sans herisson})"
done
echo "Suivi : compter les stats_*.csv sous data/sensitivity/ ou lire _sandbox/logs/SENS_<Ville>.log"
