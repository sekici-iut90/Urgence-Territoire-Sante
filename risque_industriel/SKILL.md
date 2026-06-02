name: risque-industriel
allowed-tools: Bash(python3 *)
description: |
  Déclenche ce skill quand l'utilisateur pose une question sur les risques industriels,
  les sites SEVESO, les ICPE, les matières dangereuses ou les périmètres de sécurité autour d'une zone.

  FONCTIONNEMENT :
  1. Le script interroge ou simule la base Géorisques (data.gouv.fr) pour la zone demandée.
  2. Il liste les établissements ICPE/SEVESO dans un rayon donné avec leur niveau de danger.
  3. Il évalue le risque d'effet domino (plusieurs sites dangereux proches).
  4. La sortie JSON est reformulée avec les périmètres de sécurité à appliquer.

  QUESTIONS TYPE :
  - "Y a-t-il des sites Seveso près de Mulhouse ?"
  - "Quels sont les risques industriels à proximité de Strasbourg ?"
  - "Liste les ICPE autour de Lyon dans un rayon de 5 km."
  - "Y a-t-il des dépôts de matières dangereuses à Belfort ?"
  - "Quel est le périmètre de sécurité à appliquer autour de l'usine de Fessenheim ?"
  - "Risque domino entre les sites industriels de la zone de Mulhouse ?"

  Reformule les résultats en signalant les établissements à risque élevé en priorité
  et les périmètres d'exclusion recommandés.
command: python3 ${CLAUDE_SKILL_DIR}/main.py --adresse "$ARGUMENTS"