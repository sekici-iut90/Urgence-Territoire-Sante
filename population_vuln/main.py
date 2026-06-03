#!/usr/bin/env python3
"""
Skill Vulnérabilité Population — Plugin Claude Code "Urgence Territoire & Santé"
Interroge l'API Données Locales INSEE pour caractériser la vulnérabilité d'une commune.
Usage :
    python3 main.py --args "82000"
    python3 main.py --args "Rouen"
    python3 main.py --args "Belfort"
"""

import argparse
import json
import sys
import urllib.request
import urllib.parse
import urllib.error


# ── Constantes ──────────────────────────────────────────────────────────────────
GEO_API_URL    = "https://geo.api.gouv.fr/communes"
INSEE_API_URL  = "https://api.insee.fr/donnees-locales/V0.1/donnees"

# Dataset RP 2020 — répartition par âge (15 tranches de 5 ans + 90+)
DS_AGE         = "geo-AGE15_15_90@GEO2023RP2020"

# Dataset RP 2020 — logements par type d'occupation (suroccupation)
DS_LOGEMENT    = "geo-OCCLOG@GEO2023RP2020"


# ── Résolution géographique ──────────────────────────────────────────────────────

def resoudre_commune(saisie: str) -> tuple[str, str, int]:
    """
    Accepte un code postal (5 chiffres), un code INSEE ou un nom de commune.
    Retourne (code_insee, nom_commune, population).
    """
    saisie = saisie.strip()

    if saisie.isdigit() and len(saisie) == 5:
        # Essai code postal
        url = f"{GEO_API_URL}?codePostal={saisie}&fields=code,nom,population&limit=1"
        data = _get_json(url)
        if data:
            c = data[0]
            return c["code"], c.get("nom", "Inconnue"), c.get("population", 0)

        # Essai code INSEE direct
        url = f"{GEO_API_URL}/{saisie}?fields=code,nom,population"
        try:
            data = _get_json(url)
            if data and isinstance(data, dict):
                return data["code"], data.get("nom", "Inconnue"), data.get("population", 0)
        except Exception:
            pass
    else:
        # Recherche par nom
        params = urllib.parse.urlencode({"nom": saisie, "fields": "code,nom,population", "limit": 1})
        url = f"{GEO_API_URL}?{params}"
        data = _get_json(url)
        if data:
            c = data[0]
            return c["code"], c.get("nom", "Inconnue"), c.get("population", 0)

    raise SystemExit(json.dumps(
        {"erreur": f"Commune introuvable pour la saisie : {saisie}"},
        ensure_ascii=False
    ))


def _get_json(url: str):
    """Effectue un GET et retourne le JSON parsé, ou None en cas d'erreur."""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "UrGeo-Plugin/1.0",
            "Accept": "application/json"
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception:
        return None


# ── Récupération données INSEE ───────────────────────────────────────────────────

def fetch_age_distribution(code_insee: str) -> dict | None:
    """Récupère la répartition par âge via l'API Données Locales INSEE (RP 2020)."""
    url = f"{INSEE_API_URL}/{DS_AGE}/COM-{code_insee}.json"
    data = _get_json(url)
    if not data:
        return None

    cellules = data.get("Cellule", [])
    if not cellules:
        return None

    distribution = {}
    for cellule in cellules:
        modalites = cellule.get("Modalite", [])
        valeur = cellule.get("Mesure", {})
        if isinstance(valeur, dict):
            valeur = valeur.get("#text") or valeur.get("valeur")
        try:
            valeur = float(str(valeur).replace(",", "."))
        except (ValueError, TypeError):
            continue
        for m in modalites:
            if m.get("@variable") == "AGE15_15_90":
                distribution[m.get("@code", "?")] = valeur
                break

    return distribution if distribution else None


def fetch_suroccupation(code_insee: str) -> dict | None:
    """Récupère les données de suroccupation des logements (RP 2020)."""
    url = f"{INSEE_API_URL}/{DS_LOGEMENT}/COM-{code_insee}.json"
    data = _get_json(url)
    if not data:
        return None

    cellules = data.get("Cellule", [])
    suroccupation = {}
    for cellule in cellules:
        modalites = cellule.get("Modalite", [])
        valeur = cellule.get("Mesure", {})
        if isinstance(valeur, dict):
            valeur = valeur.get("#text") or valeur.get("valeur")
        try:
            valeur = float(str(valeur).replace(",", "."))
        except (ValueError, TypeError):
            continue
        for m in modalites:
            if m.get("@variable") == "OCCLOG":
                suroccupation[m.get("@libelle", m.get("@code", "?"))] = valeur
                break

    return suroccupation if suroccupation else None


# ── Calculs indicateurs ──────────────────────────────────────────────────────────

# Codes AGE15_15_90 correspondant aux 65 ans et plus
CODES_SENIORS = {"65", "70", "75", "80", "85", "90"}

def calculer_part_seniors(distribution: dict) -> float | None:
    """Calcule le % de 65+ dans la population totale."""
    if not distribution:
        return None
    total = sum(distribution.values())
    if total == 0:
        return None
    seniors = sum(v for k, v in distribution.items() if k in CODES_SENIORS)
    return round((seniors / total) * 100, 1)


def calculer_part_suroccupation(suroccupation: dict) -> float | None:
    """Calcule le % de logements en suroccupation."""
    if not suroccupation:
        return None
    total = sum(suroccupation.values())
    if total == 0:
        return None
    suroc = sum(v for k, v in suroccupation.items() if "suroccup" in k.lower())
    return round((suroc / total) * 100, 1)


def evaluer_vulnerabilite(part_seniors: float | None, part_suroc: float | None) -> str:
    """Évalue le niveau de vulnérabilité global."""
    score = 0
    if part_seniors is not None:
        if part_seniors >= 25:   score += 2
        elif part_seniors >= 18: score += 1
    if part_suroc is not None:
        if part_suroc >= 10:    score += 2
        elif part_suroc >= 5:   score += 1

    if score >= 3:   return "ÉLEVÉE — Prioriser l'évacuation assistée. Nombreuses personnes dépendantes."
    if score >= 2:   return "MODÉRÉE — Prévoir des ressources d'évacuation adaptées."
    if score >= 1:   return "FAIBLE — Population relativement autonome."
    return "INDÉTERMINÉE — Données insuffisantes pour évaluer."


# ── Point d'entrée ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Skill Vulnérabilité Population — données INSEE par commune"
    )
    parser.add_argument(
        "--args", required=True,
        help="Code postal, code INSEE ou nom de commune (ex: '76000', 'Rouen', '75012')"
    )
    args = parser.parse_args()

    saisie = args.args.strip().replace('"', '').replace("'", "")

    # ── 1. Résolution commune ───────────────────────────────────────────────────
    code_insee, nom_commune, population_legale = resoudre_commune(saisie)

    # ── 2. Données INSEE ────────────────────────────────────────────────────────
    distribution_age  = fetch_age_distribution(code_insee)
    suroccupation_log = fetch_suroccupation(code_insee)

    # ── 3. Calcul indicateurs ───────────────────────────────────────────────────
    part_seniors = calculer_part_seniors(distribution_age)
    part_suroc   = calculer_part_suroccupation(suroccupation_log)

    # ── 4. Statut des données ───────────────────────────────────────────────────
    if distribution_age and suroccupation_log:
        statut = "Données INSEE RP 2020 — temps réel"
    elif distribution_age or suroccupation_log:
        statut = "Données partielles INSEE RP 2020"
    else:
        statut = "Mode dégradé — moyennes nationales (API INSEE indisponible)"
        part_seniors = part_seniors or 21.0
        part_suroc   = part_suroc   or 5.0

    # ── 5. Sortie JSON ──────────────────────────────────────────────────────────
    evacuation_estimee = round(population_legale * (part_seniors or 0) / 100) if population_legale else None

    sortie = {
        "commune":           nom_commune,
        "code_insee":        code_insee,
        "saisie_originale":  saisie,
        "population_legale": population_legale,
        "indicateurs": {
            "part_seniors_65plus_pct":       part_seniors,
            "part_logements_suroccupes_pct": part_suroc,
        },
        "vulnerabilite_globale": evaluer_vulnerabilite(part_seniors, part_suroc),
        "implications_operationnelles": {
            "evacuation_assistee_estimee": evacuation_estimee,
            "message": (
                f"Environ {evacuation_estimee:,} personnes de 65+ à évacuer en priorité."
                if evacuation_estimee else "Estimation impossible sans données de population."
            ),
        },
        "statut_donnees": statut,
        "source": "INSEE Recensement de la Population 2020 (RP2020) + API Géo communes",
    }

    print(json.dumps(sortie, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()