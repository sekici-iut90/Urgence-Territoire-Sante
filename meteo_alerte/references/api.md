# Documentation Technique - API Météo (Open-Meteo)

## Description
Le script utilise deux API gratuites et sans clé d'Open-Meteo :
1. **Geocoding API** : convertit un nom de ville en coordonnées GPS.
2. **Forecast API** : récupère les conditions météo actuelles à partir de ces coordonnées.

---

## Étape 1 — Géocodage

**URL :**
```
GET https://geocoding-api.open-meteo.com/v1/search?name={VILLE}&count=1&language=fr&format=json
```

**Paramètres :**
| Paramètre  | Type   | Description                          |
|------------|--------|--------------------------------------|
| `name`     | string | Nom de la ville (ex : `Strasbourg`)  |
| `count`    | int    | Nombre de résultats (toujours `1`)   |
| `language` | string | Langue des labels (`fr`)             |

**Réponse JSON (extrait) :**
```json
{
  "results": [
    {
      "name": "Strasbourg",
      "latitude": 48.5734,
      "longitude": 7.7521,
      "country": "France"
    }
  ]
}
```

---

## Étape 2 — Prévisions météo actuelles

**URL :**
```
GET https://api.open-meteo.com/v1/forecast
    ?latitude={LAT}
    &longitude={LON}
    &current=temperature_2m,wind_speed_10m,weather_code,precipitation
    &timezone=auto
```

**Paramètres :**
| Paramètre   | Type   | Description                                       |
|-------------|--------|---------------------------------------------------|
| `latitude`  | float  | Latitude obtenue via le géocodage                 |
| `longitude` | float  | Longitude obtenue via le géocodage                |
| `current`   | string | Champs actuels séparés par virgule (voir ci-bas)  |
| `timezone`  | string | `auto` pour détecter le fuseau horaire local      |

**Champs `current` utilisés :**
| Champ               | Unité  | Description                     |
|---------------------|--------|---------------------------------|
| `temperature_2m`    | °C     | Température à 2 m du sol        |
| `wind_speed_10m`    | km/h   | Vitesse du vent à 10 m          |
| `weather_code`      | WMO    | Code météo WMO (voir tableau)   |
| `precipitation`     | mm     | Précipitations de l'heure       |

---

## Codes météo WMO (weather_code) — Sélection des niveaux d'alerte

| Code  | Condition                        | Niveau d'alerte |
|-------|----------------------------------|-----------------|
| 0     | Ciel dégagé                      | Aucun           |
| 1–3   | Partiellement nuageux            | Aucun           |
| 45–48 | Brouillard givrant               | Vigilance       |
| 51–67 | Bruine / Pluie                   | Faible          |
| 71–77 | Neige / Grésil                   | Modéré          |
| 80–82 | Averses fortes                   | Modéré          |
| 85–86 | Averses de neige                 | Modéré          |
| 95    | Orage                            | Élevé           |
| 96–99 | Orage avec grêle                 | Critique        |

---

## Structure du JSON de sortie (main.py)

```json
{
  "ville": "Strasbourg",
  "latitude": 48.5734,
  "longitude": 7.7521,
  "temperature_c": 18.4,
  "precipitation_mm": 0.0,
  "vent_kmh": 22.5,
  "weather_code": 95,
  "condition": "Orage",
  "niveau_alerte": "Élevé"
}
```

**En cas d'erreur :**
```json
{
  "erreur": "Ville introuvable : 'XYZ'"
}
```

---

## Notes d'implémentation
- **Aucune clé API requise** : Open-Meteo est entièrement gratuit.
- **Modules Python utilisés** : `urllib.request`, `urllib.parse`, `json`, `argparse` (tous standards).
- **Pas de dépendances tierces** (`requests` non requis).
