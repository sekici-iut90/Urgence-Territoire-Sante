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

## Codes météo WMO (weather_code) — Niveaux de vigilance Météo-France

> Les niveaux sont conformes au référentiel institutionnel Météo-France : **Vert / Jaune / Orange / Rouge**.

| Code  | Condition                        | Vigilance Météo-France |
|-------|----------------------------------|------------------------|
| 0     | Ciel dégagé                      | Vert                   |
| 1     | Principalement dégagé            | Vert                   |
| 2     | Partiellement nuageux            | Vert                   |
| 3     | Couvert                          | Vert                   |
| 45    | Brouillard                       | Jaune                  |
| 48    | Brouillard givrant               | Jaune                  |
| 51    | Bruine légère                    | Vert                   |
| 53    | Bruine modérée                   | Jaune                  |
| 55    | Bruine dense                     | Jaune                  |
| 56    | Bruine verglaçante               | Orange                 |
| 57    | Bruine verglaçante forte         | Orange                 |
| 61    | Pluie légère                     | Vert                   |
| 63    | Pluie modérée                    | Jaune                  |
| 65    | Pluie forte                      | Orange                 |
| 66    | Pluie verglaçante                | Orange                 |
| 67    | Pluie verglaçante forte          | Rouge                  |
| 71    | Neige légère                     | Jaune                  |
| 73    | Neige modérée                    | Orange                 |
| 75    | Neige forte                      | Rouge                  |
| 77    | Grésil                           | Orange                 |
| 80    | Averses légères                  | Jaune                  |
| 81    | Averses modérées                 | Orange                 |
| 82    | Averses violentes                | Rouge                  |
| 85    | Averses de neige                 | Orange                 |
| 86    | Averses de neige fortes          | Rouge                  |
| 95    | Orage                            | Orange                 |
| 96    | Orage avec grêle                 | Rouge                  |
| 99    | Orage violent avec grêle         | Rouge                  |

---

## Structure du JSON de sortie (main.py)

```json
{
  "horodatage_utc": "2026-06-02T12:00:00+00:00",
  "ville": "Strasbourg",
  "latitude": 48.5734,
  "longitude": 7.7521,
  "temperature_c": 18.4,
  "precipitation_mm": 0.0,
  "vent_kmh": 22.5,
  "weather_code": 95,
  "condition": "Orage",
  "vigilance_meteofrance": "Orange"
}
```

**En cas d'erreur :**
```json
{
  "erreur": "[Géocodage] Ville introuvable : 'XYZ'"
}
```

---

## Notes d'implémentation
- **Aucune clé API requise** : Open-Meteo est entièrement gratuit.
- **Modules Python utilisés** : `urllib.request`, `urllib.parse`, `json`, `argparse`, `re`, `datetime` (tous standards).
- **Pas de dépendances tierces** (`requests` non requis).
- **Timeouts différenciés** : 5 s pour le géocodage, 10 s pour la prévision météo.
- **Validation d'entrée** : le nom de ville est validé par regex avant tout appel réseau.
