name: risque-industriel
description: >
  Liste les sites ICPE/SEVESO autour d'une zone pour évaluer le risque domino.
  Trigger when user asks: "sites Seveso près de", "risque industriel à", "ICPE autour de", "danger usine", "périmètre de sécurité", "dépôts dangereux".
allowed-tools: Bash(python3 *)
command: python3 ${CLAUDE_SKILL_DIR}/main.py --adresse "$ARGUMENTS"