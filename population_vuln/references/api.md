# Documentation Technique - API Vulnérabilité Population (INSEE)

## Description
Ce document décrit le fonctionnement et l'intégration future avec l'API INSEE pour récupérer les indicateurs de vulnérabilité de la population.

## Paramètres d'entrée
Le skill s'attend à recevoir en argument de la ligne de commande un paramètre unique qui correspond au **Code Postal** ou au **Code Commune INSEE**.

- `args` : Chaîne de caractères (String), typiquement un code postal à 5 chiffres (ex: `75001`).

## Schéma de sortie (JSON)
L'outil retourne un objet JSON avec les clés suivantes :
- `postal_code` (String) : Le code postal interrogé.
- `population_total` (Integer) : Population totale de la zone.
- `seniors_percentage` (Float) : Pourcentage de la population âgée de plus de 65 ans.
- `overcrowding_percentage` (Float) : Pourcentage de logements en situation de suroccupation.

## Codes d'erreur potentiels
- `400 Bad Request` : Le code postal fourni est invalide ou mal formaté.
- `404 Not Found` : Aucune donnée trouvée pour ce territoire.
- `500 Internal Server Error` : Indisponibilité du service INSEE.

## Note d'implémentation
Actuellement, le script `main.py` utilise des données simulées (mock). Lors de l'intégration réelle, il faudra rajouter la gestion du token Bearer pour s'authentifier auprès de l'API INSEE.
