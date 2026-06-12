# API References for Health Capacity Skill

This skill integrates multiple data sources to provide accurate healthcare facility information in France.

## Data Sources

### 1. OpenStreetMap (OSM)
- **Endpoint**: `https://overpass-api.de/api/interpreter`
- **Purpose**: Global location of hospitals, clinics, and nursing homes.
- **Documentation**: [Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API)

### 2. Data.gouv.fr (FINESS)
- **Endpoint**: `https://www.data.gouv.fr/api/1/datasets/5ea6ddb0634df442df1de1be/records/`
- **Purpose**: Official French healthcare registry (FINESS) for capacity (beds) and contact info.
- **Documentation**: [Annuaire Santé on data.gouv.fr](https://www.data.gouv.fr/fr/datasets/annuaire-sante-repertoire-national-des-professionnels-de-sante-et-des-etablissements-de-sante-finess/)

### 3. Nominatim (OpenStreetMap Geocoding)
- **Endpoint**: `https://nominatim.openstreetmap.org/search`
- **Purpose**: Converting city names and addresses into GPS coordinates.
- **Documentation**: [Nominatim API](https://nominatim.org/release-docs/latest/api/Search/)

## Technical Details
- **Protocol**: HTTPS REST
- **Authentication**: None required (Public APIs)
- **Format**: JSON
