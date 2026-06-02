name: geo_acces
allowed-tools: Bash(python3 *)
description: |
  Trigger when user asks about routing, access times, blocked roads, or itinerary
  for emergency vehicles between two locations.
  Le script renvoie un JSON. Reformule les résultats : distance, temps de trajet,
  obstacles détectés et itinéraire alternatif si route bloquée.
run: python3 -- ${CLAUDE_SKILL_DIR}/main.py --query "$ARGUMENTS"
