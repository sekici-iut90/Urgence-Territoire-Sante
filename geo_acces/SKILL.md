name: geo_acces
allowed-tools: Bash(python3 *)
description: |
  Déclenche ce skill quand l'utilisateur pose une question sur l'accès routier, le temps de trajet,
  les routes bloquées ou l'itinéraire d'un véhicule de secours entre deux points.

  FONCTIONNEMENT :
  1. Le script extrait automatiquement le départ, l'arrivée et le type de véhicule depuis ta question.
  2. Il calcule la distance via GPS (formule de Haversine) et le temps de trajet selon le profil du véhicule.
  3. Il simule des points de blocage éventuels et propose un itinéraire alternatif si nécessaire.
  4. La sortie est un JSON structuré que tu reformules en langage naturel.

  QUESTIONS TYPE :
  - "Est-ce que c'est possible d'aller de Belfort à Mulhouse ?"
  - "Quel est le temps de trajet d'un VSAV de Lyon à Grenoble ?"
  - "Y a-t-il des routes bloquées entre Strasbourg et Colmar pour un camion pompier ?"
  - "Combien de temps faut-il pour aller de Bordeaux à Toulouse en urgence ?"
  - "Accès de la caserne de Metz à l'hôpital de Nancy, avec quel véhicule ?"

  Reformule le JSON en précisant : distance, temps estimé, obstacles détectés et itinéraire de repli si besoin.
run: python3 -- ${CLAUDE_SKILL_DIR}/main.py --query "$ARGUMENTS"
