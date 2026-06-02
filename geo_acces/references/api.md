# Documentation Technique — Skill 3 : Géo-Accès

## Description

Le skill `geo_acces` calcule l'itinéraire optimal pour un véhicule de secours entre deux points.
En production, il interrogera l'API de routage de l'IGN ou OSRM. En l'état actuel, il utilise
un **moteur de simulation** basé sur la formule de Haversine et un référentiel de coordonnées
GPS des grandes villes françaises.

> **Note** : Le champ `"mock": true` dans chaque réponse indique que les données sont simulées.

---

## API de Référence (Production future)

### Option A — IGN Géoportail Itinéraires (API officielle France)
```
GET https://data.geopf.fr/navigation/itineraire
    ?resource=bdtopo-osrm
    &start={lon_dep},{lat_dep}
    &end={lon_arr},{lat_arr}
    &profile=car
    &optimization=shortest
```

### Option B — OSRM (Open Source Routing Machine)
```
GET https://router.project-osrm.org/route/v1/driving/{lon_dep},{lat_dep};{lon_arr},{lat_arr}
    ?overview=false&steps=false
```

---

## Interface du script `main.py`

### Mode production (Claude Code — `$ARGUMENTS`)
```bash
python3 main.py --query "De Strasbourg à Colmar pour un VSAV"
```

### Mode test CLI direct
```bash
python3 main.py --depart "Strasbourg" --arrivee "Colmar" --vehicule "FPT"
```

### Paramètres
| Paramètre    | Mode         | Description                                              |
|:-------------|:-------------|:---------------------------------------------------------|
| `--query`    | Production   | Requête en langage naturel (reçoit `$ARGUMENTS`)         |
| `--depart`   | Test CLI     | Point de départ (adresse ou nom de ville)                |
| `--arrivee`  | Test CLI     | Point d'arrivée (adresse ou nom de ville)                |
| `--vehicule` | Test CLI     | Profil : `VSAV` (défaut), `FPT`, `Camion Pompier`, `Moto` |

---

## Profils de Véhicules de Secours

| Profil         | Gabarit | Hauteur max | Poids max | Vitesse ref. |
|:---------------|:--------|:------------|:----------|:-------------|
| VSAV           | Léger   | 2,5 m       | 3,5 t     | 50 km/h      |
| FPT / Camion   | Lourd   | 3,8 m       | 16,0 t    | 35 km/h      |
| Moto-secours   | Moto    | 1,5 m       | 0,3 t     | 70 km/h      |

---

## Structure JSON de sortie (`main.py`)

### Réponse success (aucun blocage)
```json
{
  "mock": true,
  "horodatage_utc": "2026-06-02T12:00:00+00:00",
  "depart": "Strasbourg",
  "arrivee": "Colmar",
  "vehicule_profil": "VSAV",
  "contraintes_vehicule": {
    "gabarit": "Léger",
    "hauteur_max_m": 2.5,
    "poids_max_t": 3.5,
    "vitesse_ref_kmh": 50
  },
  "distance_km": 80.9,
  "temps_estime_minutes": 97.1,
  "itineraire_etapes": [
    "Départ : Strasbourg",
    "Rejoindre l'axe de desserte principal",
    "Traversée de zone urbaine — priorité aux feux",
    "Arrivée : Colmar"
  ],
  "itineraire_alternatif": null,
  "alertes_points_blocage": []
}
```

### Réponse avec blocage et itinéraire alternatif
```json
{
  "mock": true,
  "horodatage_utc": "2026-06-02T12:00:00+00:00",
  "depart": "Lyon",
  "arrivee": "Grenoble",
  "vehicule_profil": "VSAV",
  "contraintes_vehicule": { "gabarit": "Léger", "hauteur_max_m": 2.5, "poids_max_t": 3.5, "vitesse_ref_kmh": 50 },
  "distance_km": 120.4,
  "temps_estime_minutes": 144.5,
  "itineraire_etapes": [
    "Départ : Lyon",
    "⚠️  Route principale bloquée — Déviation activée",
    "Emprunter l'itinéraire de délestage balisé",
    "Arrivée : Grenoble"
  ],
  "itineraire_alternatif": {
    "distance_km": 150.5,
    "temps_estime_minutes": 180.6,
    "note": "Itinéraire de délestage via voies secondaires (+25% de distance)"
  },
  "alertes_points_blocage": [
    {
      "zone": "RN 7 — Section Nord",
      "cause": "Verglas — chaussée impraticable",
      "gravite": "Bloquant",
      "delai_levee_estime": "Variable (conditions météo)"
    }
  ]
}
```

### Réponse erreur
```json
{
  "erreur": "[message descriptif de l'erreur]"
}
```

---

## Notes d'implémentation

- **Aucune clé API requise** : simulation locale via Haversine + table de coordonnées.
- **Modules Python utilisés** : `math`, `random`, `re`, `json`, `argparse`, `datetime` (tous standards).
- **Distance routière** : vol d'oiseau (Haversine) × 1,3 (facteur de sinuosité routière empirique).
- **Blocages** : simulation probabiliste déterministe — même requête → même résultat (seed = hash du trajet).
- **Sécurité** : validation regex de toutes les entrées, séparateur `--` dans la commande shell.
