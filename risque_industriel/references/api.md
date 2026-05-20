# Documentation API — Skill Risque Industriel

## Sources de données

| Source | URL | Auth |
|--------|-----|------|
| Géorisques ICPE | `https://georisques.gouv.fr/api/v1/icpe` | Aucune |
| BAN (géocodage) | `https://api-adresse.data.gouv.fr/search/` | Aucune |

---

## Endpoint ICPE — Géorisques

### Paramètres

| Paramètre | Type | Description |
|-----------|------|-------------|
| `latlon` | string | Coordonnées `lat,lon` en WGS84 |
| `rayon` | int | Rayon en mètres (max recommandé : 10 000) |
| `page` | int | Numéro de page (commence à 1) |
| `page_size` | int | Résultats par page (max : 100) |

### Exemple de requête

```
GET https://georisques.gouv.fr/api/v1/icpe?latlon=48.8566,2.3522&rayon=3000&page=1&page_size=50
```

### Champs retournés (principaux)

| Champ | Description |
|-------|-------------|
| `raisonSociale` | Nom de l'établissement |
| `statutSeveso` | `"Seveso seuil haut"`, `"Seveso seuil bas"`, ou null |
| `regime` | Régime ICPE : Autorisation, Enregistrement, Déclaration |
| `activitePrincipale` | Activité principale de l'installation |
| `adresse`, `commune`, `codePostal` | Localisation |
| `latitude`, `longitude` | Coordonnées GPS de l'établissement |
| `distance` | Distance en mètres depuis le point de recherche |
| `codeS3ic` | Identifiant national de l'installation |

### Codes Seveso

| Statut | Risque | Implication opérationnelle |
|--------|--------|---------------------------|
| Seveso seuil haut | 🔴 CRITIQUE | Plan de Prévention des Risques Technologiques (PPRT) obligatoire. Périmètre de danger Z1/Z2. Contact DREAL immédiat. |
| Seveso seuil bas | 🟠 ÉLEVÉ | Surveillance renforcée. Risque d'effet domino en cas d'incident voisin. |
| ICPE (non Seveso) | 🟡 MODÉRÉ | Surveiller en cas d'incendie ou explosion à proximité. |

---

## Endpoint BAN — Géocodage d'adresse

```
GET https://api-adresse.data.gouv.fr/search/?q=Place+de+la+République+Paris&limit=1
```

Retourne les coordonnées GPS de l'adresse.

---

## Comportement en cas d'erreur

| Situation | Comportement du script |
|-----------|----------------------|
| Adresse introuvable | JSON `{"erreur": "..."}` + exit 1 |
| API Géorisques down | JSON `{"erreur": "API Géorisques inaccessible : ..."}` + exit 1 |
| HTTP 403/429 | JSON `{"erreur": "API Géorisques HTTP 4xx"}` + exit 1 |
| 0 résultat | Sortie normale avec `total_icpe: 0` et `niveau_alerte: FAIBLE` |

---

## Exemples de questions opérationnelles

```
"Y a-t-il des sites Seveso dans un rayon de 5 km autour de Rouen ?"
→ python3 main.py --adresse "Rouen" --rayon 5000 --seveso-only

"Risque industriel autour du 48.85, 2.35 ?"
→ python3 main.py --lat 48.85 --lon 2.35

"Dépôts dangereux à moins de 2 km de la préfecture du Rhône ?"
→ python3 main.py --adresse "Préfecture du Rhône, Lyon" --rayon 2000
```

---

## Limites connues

- Le rayon est calculé à partir du centroïde de l'établissement, pas de son emprise réelle.
- Les établissements en cessation d'activité ne sont pas inclus.
- Pagination limitée à 50 résultats par défaut (augmentable via `PAGE_SIZE` dans le code).
- Latence typique : 300–800 ms selon la charge de l'API.