#!/usr/bin/env python3
"""
Skill 5 — Alerte Météo
Récupère les conditions météo actuelles pour une ville via Open-Meteo (sans clé API).
Usage : python3 main.py --ville "Strasbourg"
"""

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from typing import NoReturn

# ---------------------------------------------------------------------------
# Correspondance codes WMO → (condition lisible, niveau d'alerte Météo-France)
# Référentiel : Vert / Jaune / Orange / Rouge (conforme Météo-France)
# ---------------------------------------------------------------------------
WMO_CODES = {
    0:  ("Ciel dégagé",               "Vert"),
    1:  ("Principalement dégagé",     "Vert"),
    2:  ("Partiellement nuageux",     "Vert"),
    3:  ("Couvert",                   "Vert"),
    45: ("Brouillard",                "Jaune"),
    48: ("Brouillard givrant",        "Jaune"),
    51: ("Bruine légère",             "Vert"),
    53: ("Bruine modérée",            "Jaune"),
    55: ("Bruine dense",              "Jaune"),
    56: ("Bruine verglaçante",        "Orange"),
    57: ("Bruine verglaçante forte",  "Orange"),
    61: ("Pluie légère",              "Vert"),
    63: ("Pluie modérée",             "Jaune"),
    65: ("Pluie forte",               "Orange"),
    66: ("Pluie verglaçante",         "Orange"),
    67: ("Pluie verglaçante forte",   "Rouge"),
    71: ("Neige légère",              "Jaune"),
    73: ("Neige modérée",             "Orange"),
    75: ("Neige forte",               "Rouge"),
    77: ("Grésil",                    "Orange"),
    80: ("Averses légères",           "Jaune"),
    81: ("Averses modérées",          "Orange"),
    82: ("Averses violentes",         "Rouge"),
    85: ("Averses de neige",          "Orange"),
    86: ("Averses de neige fortes",   "Rouge"),
    95: ("Orage",                     "Orange"),
    96: ("Orage avec grêle",          "Rouge"),
    99: ("Orage violent avec grêle",  "Rouge"),
}

# Regex d'acceptation des noms de villes (lettres latines étendues, tirets, apostrophes, espaces)
_VILLE_RE = re.compile(r"^[\w\s\-\''\u00C0-\u024F]{1,100}$")


def erreur(message: str) -> NoReturn:
    """Affiche un JSON d'erreur et quitte avec le code 1."""
    print(json.dumps({"erreur": message}, ensure_ascii=False))
    sys.exit(1)


def fetch_json(url: str, timeout: int = 10, context: str = "API") -> dict:
    """Effectue un GET HTTP et retourne le JSON parsé.

    Args:
        url:     URL complète à appeler.
        timeout: Délai maximum en secondes avant abandon.
        context: Libellé de l'étape (ex: "Géocodage", "Météo") pour les messages d'erreur.
    """
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        erreur(f"[{context}] Erreur HTTP {exc.code} : {exc.reason}")
    except urllib.error.URLError as exc:
        erreur(f"[{context}] Impossible de joindre l'API : {exc.reason}")
    except json.JSONDecodeError:
        erreur(f"[{context}] Réponse API invalide (JSON malformé).")


def geocode(ville: str) -> tuple[str, float, float]:
    """Convertit un nom de ville en (nom_validé, latitude, longitude)."""
    params = urllib.parse.urlencode({
        "name": ville,
        "count": 1,
        "language": "fr",
        "format": "json",
    })
    url = f"https://geocoding-api.open-meteo.com/v1/search?{params}"
    data = fetch_json(url, timeout=5, context="Géocodage")

    results = data.get("results")
    if not results:
        erreur(f"Ville introuvable : '{ville}'")

    r = results[0]
    return r["name"], float(r["latitude"]), float(r["longitude"])


def get_meteo(lat: float, lon: float) -> dict:
    """Récupère les conditions météo actuelles pour des coordonnées données."""
    params = urllib.parse.urlencode({
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,wind_speed_10m,weather_code,precipitation",
        "timezone": "auto",
    })
    url = f"https://api.open-meteo.com/v1/forecast?{params}"
    data = fetch_json(url, timeout=10, context="Météo")

    current = data.get("current")
    if not current:
        erreur("Données météo indisponibles pour ces coordonnées.")

    return current


def decode_wmo(code: int) -> tuple[str, str]:
    """Retourne (condition, niveau_alerte_meteofrance) pour un code WMO."""
    if code in WMO_CODES:
        return WMO_CODES[code]
    # Fallback : cherche la borne inférieure la plus proche
    for threshold in sorted(WMO_CODES.keys(), reverse=True):
        if code >= threshold:
            return WMO_CODES[threshold]
    return ("Condition inconnue", "Inconnu")


def main():
    parser = argparse.ArgumentParser(
        description="Alerte Météo — récupère les conditions actuelles pour une ville."
    )
    parser.add_argument(
        "--ville",
        required=True,
        help="Nom de la ville (ex: Strasbourg, Lyon, Bordeaux)",
    )
    args = parser.parse_args()

    ville_query = args.ville.strip()

    # Validation de l'entrée : longueur et caractères autorisés
    if not ville_query:
        erreur("Le paramètre --ville ne peut pas être vide.")
    if not _VILLE_RE.match(ville_query):
        erreur("Nom de ville invalide (caractères non autorisés ou trop long).")

    # Étape 1 : Géocodage
    nom_ville, lat, lon = geocode(ville_query)

    # Étape 2 : Données météo
    current = get_meteo(lat, lon)

    weather_code = int(current.get("weather_code", 0))
    condition, niveau_alerte = decode_wmo(weather_code)

    # Étape 3 : Construction et affichage du JSON de sortie
    resultat = {
        "horodatage_utc": datetime.now(timezone.utc).isoformat(),
        "ville": nom_ville,
        "latitude": lat,
        "longitude": lon,
        "temperature_c": current.get("temperature_2m"),
        "precipitation_mm": current.get("precipitation"),
        "vent_kmh": current.get("wind_speed_10m"),
        "weather_code": weather_code,
        "condition": condition,
        "vigilance_meteofrance": niveau_alerte,
    }

    print(json.dumps(resultat, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
