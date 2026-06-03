#!/usr/bin/env python3
"""
Skill Risque Industriel — Plugin Claude Code "Urgence Territoire & Santé"
Interroge l'API Géorisques pour lister les sites ICPE/SEVESO à proximité d'une zone.
Usage :
    python3 main.py --adresse "Place de la République, Paris"
    python3 main.py --lat 48.8566 --lon 2.3522
    python3 main.py --lat 48.8566 --lon 2.3522 --rayon 5000
    python3 main.py --lat 48.8566 --lon 2.3522 --seveso-only
"""

import argparse
import json
import math
import sys
import urllib.request
import urllib.parse
import urllib.error


# ── Constantes ─────────────────────────────────────────────────────────────────
BAN_URL   = "https://api-adresse.data.gouv.fr/search/"
ICPE_URL  = "https://georisques.gouv.fr/api/v1/installations_classees"
RAYON_DEF = 3000  # mètres par défaut
PAGE_SIZE = 100   # résultats max par page (100 est le maximum autorisé par l'API)

SEVESO_LABELS = {
    "Seveso seuil haut": "🔴 SEVESO SEUIL HAUT",
    "Seveso seuil bas":  "🟠 Seveso seuil bas",
}


# ── Fonctions utilitaires ───────────────────────────────────────────────────────

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> int:
    """Calcule la distance en mètres entre deux points GPS."""
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi    = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return round(2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a)))


def geocode_adresse(adresse: str) -> tuple[float, float, str]:
    """Convertit une adresse en coordonnées GPS via l'API BAN (Base Adresse Nationale)."""
    params = urllib.parse.urlencode({"q": adresse, "limit": 1})
    url = f"{BAN_URL}?{params}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        raise SystemExit(json.dumps({"erreur": f"Géocodage impossible : {e}"}, ensure_ascii=False))

    features = data.get("features", [])
    if not features:
        raise SystemExit(json.dumps({"erreur": f"Adresse introuvable : {adresse}"}, ensure_ascii=False))

    props = features[0]["properties"]
    lon, lat = features[0]["geometry"]["coordinates"]
    label = props.get("label", adresse)
    return lat, lon, label


def fetch_icpe(lat: float, lon: float, rayon: int) -> list[dict]:
    """Interroge l'API Géorisques ICPE et retourne la liste brute des établissements (avec pagination)."""
    all_data = []
    page = 1
    max_pages = 5  # Sécurité contre les requêtes infinies
    
    while page <= max_pages:
        params = urllib.parse.urlencode({
            "latlon":    f"{lon},{lat}",
            "rayon":     rayon,
            "page":      page,
            "page_size": PAGE_SIZE,
        })
        url = f"{ICPE_URL}?{params}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "UrGeo-Plugin/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            raise SystemExit(json.dumps({"erreur": f"API Géorisques HTTP {e.code} : {e.reason}"}, ensure_ascii=False))
        except Exception as e:
            raise SystemExit(json.dumps({"erreur": f"API Géorisques inaccessible : {e}"}, ensure_ascii=False))

        batch = data.get("data", [])
        if not batch:
            break
        all_data.extend(batch)
        if len(batch) < PAGE_SIZE:
            break
        page += 1

    return all_data


def classer_seveso(statut: str | None) -> str:
    """Retourne un label lisible pour le statut Seveso."""
    if not statut:
        return "Non Seveso"
    return SEVESO_LABELS.get(statut, statut)


def calculer_niveau_alerte(etablissements: list[dict]) -> str:
    """Évalue le niveau d'alerte global selon les sites présents."""
    niveaux = [e.get("statutSeveso", "") or "" for e in etablissements]
    if any("seuil haut" in n.lower() for n in niveaux):
        return "CRITIQUE — Site(s) Seveso seuil haut détecté(s). Risque d'effet domino élevé."
    if any("seuil bas" in n.lower() for n in niveaux):
        return "ÉLEVÉ — Site(s) Seveso seuil bas détecté(s). Maintenir périmètre de sécurité."
    if etablissements:
        return "MODÉRÉ — ICPE présentes sans statut Seveso. Surveiller évolution."
    return "FAIBLE — Aucun site ICPE recensé dans le périmètre."


def formater_etablissement(e: dict, index: int, lat_centre: float, lon_centre: float) -> dict:
    """Formate un établissement ICPE pour la sortie JSON."""
    lat_e = e.get("latitude")
    lon_e = e.get("longitude")
    distance = haversine(lat_centre, lon_centre, lat_e, lon_e) if lat_e and lon_e else None

    # Construire l'adresse depuis adresse1/adresse2 (ignorer les "--" vides)
    adresse = " ".join(
        part for part in [e.get("adresse1"), e.get("adresse2")]
        if part and part.strip() not in ("", "--")
    ) or "N/A"

    # Déduire le type d'activité depuis les flags booléens de l'API
    types = []
    if e.get("industrie"):  types.append("Industrie")
    if e.get("carriere"):   types.append("Carrière")
    if e.get("eolienne"):   types.append("Éolienne")
    if e.get("bovins"):     types.append("Élevage bovins")
    if e.get("porcs"):      types.append("Élevage porcs")
    if e.get("volailles"):  types.append("Élevage volailles")
    activite = ", ".join(types) if types else "N/A"

    code = e.get("codeAIOT", "")
    url_fiche = (
        f"https://www.georisques.gouv.fr/risques/installations/donnees#{code}"
        if code else None
    )

    return {
        "rang":          index + 1,
        "nom":           e.get("raisonSociale") or "Inconnu",
        "statut_seveso": classer_seveso(e.get("statutSeveso")),
        "regime":        e.get("regime") or "N/A",
        "activite":      activite,
        "adresse":       adresse,
        "commune":       e.get("commune") or "N/A",
        "code_postal":   e.get("codePostal") or "N/A",
        "distance_m":    distance,
        "coordonnees":   {"lat": lat_e, "lon": lon_e},
        "url_fiche":     url_fiche,
    }


# ── Point d'entrée ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Skill Risque Industriel — sites ICPE/SEVESO autour d'une zone"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--adresse", type=str,   help="Adresse textuelle (géocodage automatique via BAN)")
    group.add_argument("--lat",     type=float, help="Latitude GPS (WGS84)")

    parser.add_argument("--lon",         type=float, help="Longitude GPS (requis si --lat)")
    parser.add_argument("--rayon",       type=int,   default=RAYON_DEF,
                        help=f"Rayon de recherche en mètres (défaut : {RAYON_DEF})")
    parser.add_argument("--seveso-only", action="store_true",
                        help="Ne retourner que les sites classés Seveso")

    args = parser.parse_args()

    # ── Résolution des coordonnées ──────────────────────────────────────────────
    if args.adresse:
        print(f"[Débug] Géocodage de l'adresse : {args.adresse}...", file=sys.stderr, flush=True)
        lat, lon, label_lieu = geocode_adresse(args.adresse)
        print(f"[Débug] Coordonnées trouvées : Lat {lat}, Lon {lon}", file=sys.stderr, flush=True)
    else:
        if args.lon is None:
            parser.error("--lon est requis quand --lat est utilisé")
        lat, lon = args.lat, args.lon
        label_lieu = f"{lat}, {lon}"

    # ── Appel API Géorisques ────────────────────────────────────────────────────
    print(f"[Débug] Interrogation de Géorisques pour {label_lieu} (Rayon : {args.rayon}m)...", file=sys.stderr, flush=True)
    etablissements_bruts = fetch_icpe(lat, lon, args.rayon)
    print(f"[Débug] API Géorisques a répondu ! Nombre de sites bruts : {len(etablissements_bruts)}", file=sys.stderr, flush=True)

    # ── Filtrage optionnel Seveso uniquement ────────────────────────────────────
    if args.seveso_only:
        etablissements_bruts = [
            e for e in etablissements_bruts
            if e.get("statutSeveso") and e["statutSeveso"].lower() in ["seveso seuil haut", "seveso seuil bas"]
        ]

    # ── Tri par distance calculée ───────────────────────────────────────────────
    def distance_sort(e):
        lat_e = e.get("latitude")
        lon_e = e.get("longitude")
        return haversine(lat, lon, lat_e, lon_e) if lat_e and lon_e else 9_999_999

    etablissements_bruts.sort(key=distance_sort)

    # ── Formatage ───────────────────────────────────────────────────────────────
    sites = [formater_etablissement(e, i, lat, lon) for i, e in enumerate(etablissements_bruts)]
    seveso_haut = [s for s in sites if "seuil haut" in s["statut_seveso"].lower()]
    seveso_bas  = [s for s in sites if "seuil bas"  in s["statut_seveso"].lower()]

    sortie = {
        "zone_analysee":       label_lieu,
        "coordonnees_centre":  {"lat": lat, "lon": lon},
        "rayon_m":             args.rayon,
        "niveau_alerte":       calculer_niveau_alerte(etablissements_bruts),
        "resume": {
            "total_icpe":              len(sites),
            "dont_seveso_seuil_haut":  len(seveso_haut),
            "dont_seveso_seuil_bas":   len(seveso_bas),
        },
        "sites_prioritaires": seveso_haut + seveso_bas,
        "autres_icpe":        [s for s in sites if s not in seveso_haut and s not in seveso_bas],
    }

    print(json.dumps(sortie, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()