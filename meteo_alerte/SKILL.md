name: meteo_alerte
allowed-tools: Bash(python3 *)
description: |
  Déclenche ce skill quand l'utilisateur demande des informations sur la météo, vigilance, tempête,
  pluie, vent, inondation, crue, alerte météo ou un nom de commune.
  Le script renvoie un JSON. Reformule les données en une alerte claire et structurée pour
  l'utilisateur, en signalant tout danger potentiel. Utilise le champ "vigilance_meteofrance"
  (Vert / Jaune / Orange / Rouge) comme référence de niveau d'alerte institutionnel.
run: python3 -- ${CLAUDE_SKILL_DIR}/main.py --ville "$ARGUMENTS"
