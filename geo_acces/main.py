#!/usr/bin/env python3
"""
Skill 3 — Géo-Accès
Calcule l'itinéraire de secours pour un véhicule entre un point de départ et d'arrivée.

Modes d'utilisation :
  - Production (Claude) : python3 main.py --query "De Strasbourg à Colmar pour un VSAV"
  - Test CLI direct     : python3 main.py --depart "Strasbourg" --arrivee "Colmar" --vehicule "VSAV"
"""

import argparse
import json
import math
import random
import re
import sys
from datetime import datetime, timezone
from typing import NoReturn

# ---------------------------------------------------------------------------
# Base de coordonnées GPS des grandes villes françaises (WGS84)
# Utilisée pour le calcul Haversine → distance routière réaliste
# ---------------------------------------------------------------------------
COORDONNEES_VILLES = {
    "paris":       (48.8566,  2.3522),
    "lyon":        (45.7496,  4.8467),
    "marseille":   (43.2965,  5.3698),
    "bordeaux":    (44.8378, -0.5792),
    "toulouse":    (43.6047,  1.4442),
    "nice":        (43.7102,  7.2620),
    "nantes":      (47.2184, -1.5536),
    "strasbourg":  (48.5734,  7.7521),
    "montpellier": (43.6110,  3.8767),
    "rennes":      (48.1173, -1.6778),
    "grenoble":    (45.1885,  5.7245),
    "lille":       (50.6292,  3.0573),
    "dijon":       (47.3220,  5.0415),
    "metz":        (49.1193,  6.1727),
    "nancy":       (48.6921,  6.1844),
    "caen":        (49.1829, -0.3707),
    "colmar":      (48.0786,  7.3580),
    "mulhouse":    (47.7508,  7.3359),
    "reims":       (49.2583,  4.0317),
    "rouen":       (49.4431,  1.0993),
    "brest":       (48.3904, -4.4861),
    "tours":       (47.3941,  0.6848),
    "clermont":    (45.7772,  3.0870),
    "belfort":     (47.6384,  6.8628),
    "saint-etienne": (45.4397,  4.3872),
    "angers":      (47.4784, -0.5632),
    "le mans":     (48.0061,  0.1996),
    "perpignan":   (42.6986,  2.8956),
    "limoges":     (45.8315,  1.2578),
    "toulon":      (43.1242,  5.9280),
    "besancon":    (47.2380,  6.0243),
    "orleans":     (47.9030,  1.9093),
    "poitiers":    (46.5802,  0.3404),
    "troyes":      (48.2973,  4.0744),
    "chartres":    (48.4469,  1.4885),
}

# ---------------------------------------------------------------------------
# Points de blocage simulés (scénarios d'urgence réalistes)
# ---------------------------------------------------------------------------
BLOCAGES_SIMULES = [
    {
        "zone": "Avenue du Rhin",
        "cause": "Inondation de la chaussée (crue)",
        "gravite": "Bloquant",
        "delai_levee_estime": "4-6 heures",
    },
    {
        "zone": "RD 101 — Pont des Lilas",
        "cause": "Chute d'arbre suite aux vents violents",
        "gravite": "Bloquant",
        "delai_levee_estime": "1-2 heures",
    },
    {
        "zone": "Traversée centre-ville",
        "cause": "Accident de la route en cours (secours présents)",
        "gravite": "Ralentissement majeur",
        "delai_levee_estime": "30-60 minutes",
    },
    {
        "zone": "RN 7 — Section Nord",
        "cause": "Verglas — chaussée impraticable",
        "gravite": "Bloquant",
        "delai_levee_estime": "Variable (conditions météo)",
    },
    {
        "zone": "Tunnel sous-fluvial",
        "cause": "Fermeture pour fumée détectée",
        "gravite": "Bloquant",
        "delai_levee_estime": "2-3 heures",
    },
]

# ---------------------------------------------------------------------------
# Profils de véhicules de secours : gabarit, poids, vitesse de référence
# ---------------------------------------------------------------------------
PROFILS_VEHICULES = {
    "vsav":           {"gabarit": "Léger", "hauteur_max_m": 2.5, "poids_max_t": 3.5,  "vitesse_ref_kmh": 50},
    "fpt":            {"gabarit": "Lourd", "hauteur_max_m": 3.8, "poids_max_t": 16.0, "vitesse_ref_kmh": 35},
    "camion pompier": {"gabarit": "Lourd", "hauteur_max_m": 3.8, "poids_max_t": 16.0, "vitesse_ref_kmh": 35},
    "camion":         {"gabarit": "Lourd", "hauteur_max_m": 3.8, "poids_max_t": 16.0, "vitesse_ref_kmh": 35},
    "moto":           {"gabarit": "Moto",  "hauteur_max_m": 1.5, "poids_max_t": 0.3,  "vitesse_ref_kmh": 70},
}

_ENTREE_RE = re.compile(r"^[\w\s\-\,\'\u00C0-\u024F\.\/\?\!]{1,200}$")


def erreur(message: str) -> NoReturn:
    """Affiche un JSON d'erreur et quitte avec le code 1."""
    print(json.dumps({"erreur": message}, ensure_ascii=False))
    sys.exit(1)


def valider_entree(texte: str, nom_champ: str) -> str:
    """Valide et nettoie un paramètre textuel."""
    texte = texte.strip()
    if not texte:
        erreur(f"Le paramètre {nom_champ} ne peut pas être vide.")
    if not _ENTREE_RE.match(texte):
        erreur(f"Le paramètre {nom_champ} contient des caractères non autorisés.")
    return texte


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance à vol d'oiseau en km entre deux points GPS (formule de Haversine)."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def resoudre_ville(texte: str) -> tuple[str, tuple[float, float]] | tuple[None, None]:
    """Recherche la première ville connue dans une chaîne de texte."""
    texte_norm = texte.lower()
    for ville, coords in COORDONNEES_VILLES.items():
        if ville in texte_norm:
            return ville.capitalize(), coords
    return None, None


def calculer_distance(depart: str, arrivee: str) -> tuple[float, str | None, str | None]:
    """
    Calcule la distance routière estimée entre deux lieux.
    - Si les deux villes sont reconnues → Haversine × 1.3 (facteur sinuosité routière).
    - Sinon → distance intra-urbaine plausible (5–25 km) déterministe par requête.
    Retourne (distance_km, nom_départ_résolu, nom_arrivée_résolu).
    """
    nom_dep, coord_dep = resoudre_ville(depart)
    nom_arr, coord_arr = resoudre_ville(arrivee)

    if coord_dep and coord_arr:
        dist_vol = haversine(*coord_dep, *coord_arr)
        return round(dist_vol * 1.3, 1), nom_dep, nom_arr

    # Fallback déterministe (pas de coordonnées connues)
    rng = random.Random(hash(depart.lower() + arrivee.lower()))
    return round(rng.uniform(5.0, 25.0), 1), None, None


def detecter_profil_vehicule(vehicule: str) -> dict:
    """Retourne le profil de contraintes du véhicule, avec fallback VSAV."""
    v_lower = vehicule.lower()
    for cle, profil in PROFILS_VEHICULES.items():
        if cle in v_lower:
            return profil
    return PROFILS_VEHICULES["vsav"]


def detecter_blocages(depart: str, arrivee: str) -> list[dict]:
    """
    Simulation probabiliste DÉTERMINISTE des blocages (seed = hash du trajet).
    Même requête → même résultat. Probabilité de blocage : 30%.
    """
    rng = random.Random(hash(depart.lower() + arrivee.lower()))
    if rng.random() < 0.30:
        return rng.sample(BLOCAGES_SIMULES, k=rng.randint(1, 2))
    return []


def generer_etapes(depart: str, arrivee: str, alertes: list[dict]) -> list[str]:
    """Génère des étapes d'itinéraire contextualisées selon les alertes."""
    etapes = [f"Départ : {depart}"]
    if any(a["gravite"] == "Bloquant" for a in alertes):
        etapes.append("⚠️  Route principale bloquée — Déviation activée")
        etapes.append("Emprunter l'itinéraire de délestage balisé")
    else:
        etapes.append("Rejoindre l'axe de desserte principal")
        if alertes:
            etapes.append(f"⚠️  Ralentissement signalé : {alertes[0]['zone']}")
        etapes.append("Traversée de zone urbaine — priorité aux feux")
    etapes.append(f"Arrivée : {arrivee}")
    return etapes


def extraire_lieux(query: str) -> tuple[str, str, str]:
    """
    Extrait départ, arrivée et véhicule depuis une requête en langage naturel.
    Gère les patterns courants en français.
    """
    vehicule = "VSAV"
    if re.search(r"camion|fpt|fourgon|pompe.tonne", query, re.IGNORECASE):
        vehicule = "Camion Pompier"
    elif re.search(r"moto", query, re.IGNORECASE):
        vehicule = "Moto"

    patterns = [
        r"de\s+(.+?)\s+(?:à|vers|jusqu'à)\s+(.+?)(?:\s+pour|\s+avec|\s+en|\s*\??\s*$)",
        r"depuis\s+(.+?)\s+(?:vers|à|jusqu'à)\s+(.+?)(?:\s+pour|\s+avec|\s*\??\s*$)",
        r"entre\s+(.+?)\s+et\s+(.+?)(?:\s+pour|\s+avec|\s*\??\s*$)",
    ]
    for pattern in patterns:
        m = re.search(pattern, query, re.IGNORECASE)
        if m:
            return m.group(1).strip(), m.group(2).strip(), vehicule

    return query[:60], "Destination non précisée", vehicule


def main():
    parser = argparse.ArgumentParser(
        description="Géo-Accès — Calcul d'itinéraire d'urgence.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Exemples :\n"
            "  Production : python3 main.py --query \"De Strasbourg à Lyon pour un VSAV\"\n"
            "  Dev        : python3 main.py --depart Strasbourg --arrivee Lyon --vehicule VSAV"
        ),
    )
    parser.add_argument("--query",    help="Requête en langage naturel (mode Claude Code, reçoit $ARGUMENTS)")
    parser.add_argument("--depart",   help="Point de départ (mode test CLI direct)")
    parser.add_argument("--arrivee",  help="Point d'arrivée (mode test CLI direct)")
    parser.add_argument("--vehicule", default="VSAV", help="Profil véhicule (VSAV, FPT, Camion Pompier, Moto)")
    args = parser.parse_args()

    # Résolution du mode d'invocation
    if args.query:
        depart, arrivee, vehicule = extraire_lieux(valider_entree(args.query, "--query"))
    elif args.depart and args.arrivee:
        depart   = valider_entree(args.depart,   "--depart")
        arrivee  = valider_entree(args.arrivee,  "--arrivee")
        vehicule = valider_entree(args.vehicule, "--vehicule")
    else:
        erreur("Fournir --query (mode Claude) ou --depart + --arrivee (mode test).")

    # Calcul distance et résolution des noms de villes
    distance_km, nom_dep, nom_arr = calculer_distance(depart, arrivee)
    depart_affiche  = nom_dep  or depart
    arrivee_affiche = nom_arr or arrivee

    # Profil véhicule et temps de trajet
    profil      = detecter_profil_vehicule(vehicule)
    vitesse_kmh = profil["vitesse_ref_kmh"]
    temps_min   = round((distance_km / vitesse_kmh) * 60, 1)

    # Détection probabiliste déterministe des blocages
    alertes = detecter_blocages(depart_affiche, arrivee_affiche)

    # Itinéraire alternatif si blocage bloquant
    itineraire_alt = None
    if any(a["gravite"] == "Bloquant" for a in alertes):
        dist_alt  = round(distance_km * 1.25, 1)
        temps_alt = round((dist_alt / vitesse_kmh) * 60, 1)
        itineraire_alt = {
            "distance_km": dist_alt,
            "temps_estime_minutes": temps_alt,
            "note": "Itinéraire de délestage via voies secondaires (+25% de distance)",
        }

    resultat = {
        "mock": True,
        "horodatage_utc": datetime.now(timezone.utc).isoformat(),
        "depart": depart_affiche,
        "arrivee": arrivee_affiche,
        "vehicule_profil": vehicule,
        "contraintes_vehicule": profil,
        "distance_km": distance_km,
        "temps_estime_minutes": temps_min,
        "itineraire_etapes": generer_etapes(depart_affiche, arrivee_affiche, alertes),
        "itineraire_alternatif": itineraire_alt,
        "alertes_points_blocage": alertes,
    }

    print(json.dumps(resultat, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
