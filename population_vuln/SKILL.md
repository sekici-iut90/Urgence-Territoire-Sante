name: population-vuln
allowed-tools: Bash(python3 *)
description: |
  Déclenche ce skill quand l'utilisateur pose une question sur la vulnérabilité d'une population,
  les données démographiques, les personnes âgées, le surpeuplement ou les données INSEE d'une commune.

  FONCTIONNEMENT :
  1. Le script interroge ou simule les données INSEE pour la commune demandée.
  2. Il calcule les indicateurs de vulnérabilité : part de +65 ans, logements surpeuplés, isolement.
  3. La sortie JSON est reformulée pour dimensionner les besoins d'évacuation ou de secours.

  QUESTIONS TYPE :
  - "Combien de personnes âgées de plus de 65 ans vivent à Mulhouse ?"
  - "Quelle est la population vulnérable à évacuer à Strasbourg ?"
  - "Donne-moi les données INSEE sur la vulnérabilité de la commune de Belfort."
  - "Combien de logements surpeuplés y a-t-il à Lyon ?"
  - "Quel pourcentage de seniors vit seul à Bordeaux ?"

  Reformule les indicateurs en termes opérationnels : nombre de personnes à mobilité réduite
  à prendre en charge, capacité d'évacuation nécessaire, etc.
run: python3 ${CLAUDE_SKILL_DIR}/main.py --args "$ARGUMENTS"
