name: meteo_alerte
allowed-tools: Bash(python3 *)
description: |
  Déclenche ce skill quand l'utilisateur pose une question sur la météo, la vigilance,
  les risques climatiques ou les conditions atmosphériques pour une commune française.

  FONCTIONNEMENT :
  1. Le script géocode la ville (Open-Meteo Geocoding API) pour obtenir ses coordonnées GPS.
  2. Il récupère les conditions météo actuelles en temps réel (Open-Meteo Forecast API).
  3. Il traduit le code WMO en condition lisible et en niveau de vigilance Météo-France.
  4. La sortie JSON est reformulée en alerte claire, en signalant tout danger potentiel.

  QUESTIONS TYPE :
  - "Quelle est la météo à Strasbourg en ce moment ?"
  - "Y a-t-il des alertes de vigilance sur Lyon ?"
  - "Est-ce qu'il y a du vent à Bordeaux aujourd'hui ?"
  - "Quelles sont les conditions météo à Mulhouse pour un déploiement de secours ?"
  - "Y a-t-il un risque de tempête ou d'orage sur Marseille ?"
  - "Vigilance inondation à Nantes ?"

  Utilise le champ "vigilance_meteofrance" (Vert/Jaune/Orange/Rouge) comme référence
  institutionnelle et signale tout niveau Orange ou Rouge comme priorité opérationnelle.
run: python3 -- ${CLAUDE_SKILL_DIR}/main.py --ville "$ARGUMENTS"
