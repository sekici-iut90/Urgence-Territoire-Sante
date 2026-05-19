#!/usr/bin/env python3
"""
Skill 5 — Alerte Météo
Récupère les conditions météo actuelles pour une ville via Open-Meteo (sans clé API).
Usage : python3 main.py --ville "Strasbourg"
"""

import argparse
import json
import sys
import urllib.request
import urllib.parse

# ---------------------------------------------------------------------------
# Correspondance codes WMO → (condition lisible, niveau d'alerte)
# ---------------------------------------------------------------------------
WMO_CODES = {
    0:  ("Ciel dégagé",            "Aucun"),
    1:  ("Principalement dégagé",  "Aucun"),
    2:  ("Partiellement nuageux",  "Aucun"),
    3:  ("Couvert",                "Aucun"),
    45: ("Brouillard",             "Vigilance"),
    48: ("Brouillard givrant",     "Vigilance"),
    51: ("Bruine légère",          "Faible"),
    53: ("Bruine modérée",         "Faible"),
    55: ("Bruine dense",           "Faible"),
    56: ("Bruine verglaçante",     "Modéré"),
    57: ("Bruine verglaçante forte","Modéré"),
    61: ("Pluie légère",           "Faible"),
    63: ("Pluie modérée",          "Faible"),
    65: ("Pluie forte",            "Modéré"),
    66: ("Pluie verglaçante",      "Modéré"),
    67: ("Pluie verglaçante forte","Élevé"),
    71: ("Neige légère",           "Faible"),
    73: ("Neige modérée",          "Modéré"),
    75: ("Neige forte",            "Élevé"),
    77: ("Grésil",                 "Modéré"),
    80: ("Averses légères",        "Faible"),
    81: ("Averses modérées",       "Modéré"),
    82: ("Averses violentes",      "Élevé"),
    85: ("Averses de neige",       "Modéré"),
    86: ("Averses de neige fortes","Élevé"),
    95: ("Orage",                  "Élevé"),
    96: ("Orage avec grêle",       "Critique"),
    99: ("Orage violent avec grêle","Critique"),
}


def erreur(message: str) -> None:
    """Affiche un JSON d'erreur et quitte avec le code 1."""
    print(json.dumps({"erreur": message}, ensure_ascii=False))
    sys.exit(1)


def fetch_json(url: str) -> dict:
    """Effectue un GET HTTP et retourne le JSON parsé."""
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        erreur(f"Impossible de joindre l'API : {exc.reason}")
    except json.JSONDecodeError:
        erreur("Réponse API invalide (JSON malformé).")


def geocode(ville: str) -> tuple[str, float, float]:
    """Convertit un nom de ville en (nom_validé, latitude, longitude)."""
    params = urllib.parse.urlencode({
        "name": ville,
        "count": 1,
        "language": "fr",
        "format": "json",
    })
    url = f"https://geocoding-api.open-meteo.com/v1/search?{params}"
    data = fetch_json(url)

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
    data = fetch_json(url)

    current = data.get("current")
    if not current:
        erreur("Données météo indisponibles pour ces coordonnées.")

    return current


def decode_wmo(code: int) -> tuple[str, str]:
    """Retourne (condition, niveau_alerte) pour un code WMO."""
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
    if not ville_query:
        erreur("Le paramètre --ville ne peut pas être vide.")

    # Étape 1 : Géocodage
    nom_ville, lat, lon = geocode(ville_query)

    # Étape 2 : Données météo
    current = get_meteo(lat, lon)

    weather_code = int(current.get("weather_code", 0))
    condition, niveau_alerte = decode_wmo(weather_code)

    # Étape 3 : Construction et affichage du JSON de sortie
    resultat = {
        "ville": nom_ville,
        "latitude": lat,
        "longitude": lon,
        "temperature_c": current.get("temperature_2m"),
        "precipitation_mm": current.get("precipitation"),
        "vent_kmh": current.get("wind_speed_10m"),
        "weather_code": weather_code,
        "condition": condition,
        "niveau_alerte": niveau_alerte,
    }

    print(json.dumps(resultat, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
