name: meteo_alerte
allowed-tools: Bash(python3 *)
description: Trigger when user asks about météo, vigilance, tempête, pluie, vent, inondation, crue, alerte météo ou nom de commune.
run: python3 ${CLAUDE_SKILL_DIR}/main.py --ville "$ARGUMENTS"
post-process: Le script renvoie un JSON. Reformule les données en une alerte claire et structurée pour l'utilisateur, en signalant tout danger potentiel.
