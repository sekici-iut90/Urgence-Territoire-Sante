# Documentation API - Skill Vulnérabilité Population

## Sources de données

| Source                            | URL                                               | Auth   |
| --------------------------------- | ------------------------------------------------- | ------ |
| API Géo (Découpage administratif) | https://geo.api.gouv.fr/communes                  | Aucune |
| API Données Locales INSEE         | https://api.insee.fr/donnees-locales/V0.1/donnees | Aucune |

---

# Endpoints utilisés

## 1. API Géo - Résolution géographique

Permet de traduire la saisie utilisateur (Code Postal, Code INSEE ou Nom de commune) en métadonnées géographiques.

### Paramètres

| Paramètre    | Type   | Description                                               |
| ------------ | ------ | --------------------------------------------------------- |
| `codePostal` | string | Code postal à 5 chiffres (ex : 82000)                     |
| `nom`        | string | Nom de la commune pour recherche textuelle (ex : Rouen)   |
| `fields`     | string | Filtre des champs retournés (`code`, `nom`, `population`) |

### Exemple de requête

```http
GET https://geo.api.gouv.fr/communes?codePostal=82000&fields=code,nom,population&limit=1
```

---

## 2. API INSEE - Données Locales

Interrogée en utilisant le code INSEE (`COM-XXXXX`) récupéré à l'étape précédente.

### Jeux de données (Datasets RP 2020)

| Indicateur               | Dataset                         |
| ------------------------ | ------------------------------- |
| Âge (15 tranches)        | `geo-AGE15_15_90@GEO2023RP2020` |
| Logement (Suroccupation) | `geo-OCCLOG@GEO2023RP2020`      |

### Exemple de requête

```http
GET https://api.insee.fr/donnees-locales/V0.1/donnees/geo-AGE15_15_90@GEO2023RP2020/COM-82121.json
```

---

# Champs retournés (Structure de sortie)

L'outil agrège les données et retourne un objet JSON structuré.

| Champ                                                      | Type   | Description                                                                   |
| ---------------------------------------------------------- | ------ | ----------------------------------------------------------------------------- |
| `commune`                                                  | string | Nom officiel de la commune identifiée                                         |
| `code_insee`                                               | string | Code INSEE officiel de la commune                                             |
| `population_legale`                                        | int    | Population totale (INSEE / API Géo)                                           |
| `indicateurs.part_seniors_65plus_pct`                      | float  | Pourcentage de la population âgée de 65 ans et plus                           |
| `indicateurs.part_logements_suroccupes_pct`                | float  | Pourcentage de logements en situation de suroccupation                        |
| `vulnerabilite_globale`                                    | string | Score de vulnérabilité (ÉLEVÉE, MODÉRÉE, FAIBLE, INDÉTERMINÉE)                |
| `implications_operationnelles.evacuation_assistee_estimee` | int    | Nombre théorique de seniors (65+) potentiellement à évacuer                   |
| `statut_donnees`                                           | string | Qualité des données récupérées ("Temps réel", "Partielles" ou "Mode dégradé") |

---

# Seuils de vulnérabilité et implications

Le niveau de vulnérabilité globale est calculé sur un système de points combinant la part de seniors (65+ ans) et la suroccupation des logements.

| Niveau     | Score   | Seuil indicateurs                                   | Implication opérationnelle                                                                         |
| ---------- | ------- | --------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| 🔴 ÉLEVÉE  | ≥ 3 pts | Seniors ≥ 25 % ou suroccupation ≥ 10 % (si cumulés) | Prioriser l'évacuation assistée. Nombreuses personnes dépendantes ou zones d'habitation denses.    |
| 🟠 MODÉRÉE | 2 pts   | Seniors ≥ 18 % ou suroccupation ≥ 5 %               | Prévoir des ressources d'évacuation adaptées. Logistique et transports médico-sociaux à anticiper. |
| 🟡 FAIBLE  | 1 pt    | Faible cumul des critères précédents                | Population relativement autonome. Suivi standard des consignes de sécurité.                        |

---

# Comportement en cas d'erreur ou d'indisponibilité

| Situation                          | Comportement du script                                                                                                                                                                                                 |
| ---------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Commune ou code postal introuvable | `{"erreur": "Commune introuvable pour la saisie : ..."}` puis `exit 1`                                                                                                                                                 |
| API INSEE indisponible             | Bascule en mode dégradé avec utilisation des moyennes nationales par défaut : Seniors = 21,0 %, Suroccupation = 5,0 %. Le champ `statut_donnees` devient `"Mode dégradé"` et le script termine normalement (`exit 0`). |

---

# Exemples de questions opérationnelles

### Quelle est la vulnérabilité de la population à Rouen ?

```bash
python3 main.py --args "Rouen"
```

### Évaluation des personnes âgées à évacuer en urgence sur le code postal 82000

```bash
python3 main.py --args "82000"
```

### Profil de vulnérabilité pour Belfort

```bash
python3 main.py --args "Belfort"
```

---

# Limites connues

* Le calcul du nombre de seniors à évacuer (`evacuation_assistee_estimee`) est une projection brute basée sur le pourcentage INSEE appliqué à la population légale globale.
* En cas de panne complète de l'API INSEE, le script ne bloque pas mais injecte des constantes nationales statiques afin d'assurer la continuité de service de l'assistant de crise.
* Les données reposent sur le recensement RP 2020 (géographie 2023).
