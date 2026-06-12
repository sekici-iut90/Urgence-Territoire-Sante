#!/usr/bin/env python3

"""
Health Capacity Skill - Unified Claude Skill
Locates hospitals, clinics, and nursing homes and retrieves their capacity.
"""

import json
import sys
import re
import os
import math
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, List
import requests

# Configuration
CACHE_FILE = os.path.join(os.path.dirname(__file__), 'facilities_cache.json')
CACHE_EXPIRY_HOURS = 24

class HealthDataFetcher:
    """Fetch and cache real healthcare facility data from OSM and data.gouv.fr"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'HealthCapacitySkill/1.0 (Claude Health Facility Locator)'
        })
        self.timeout = 15
    
    def get_facilities(self, lat: float, lon: float, radius_km: float = 15, 
                       facility_types: list = None, force_refresh: bool = False, location_name: str = None) -> list:
        # Try cache first
        if not force_refresh:
            cached = self._load_cache()
            if cached:
                nearby = [f for f in cached if self._distance(lat, lon, f['lat'], f['lon']) <= radius_km + 5]
                if nearby:
                    return cached
        
        facilities = self._fetch_from_osm(lat, lon, radius_km, facility_types)
        
        # French data enrichment
        if 41 <= lat <= 51 and -8 <= lon <= 8:
            facilities_fr = self._fetch_from_annuaire_sante(lat, lon, radius_km, location_name)
            facilities = self._merge_facilities(facilities, facilities_fr)
        
        self._save_cache(facilities)
        return facilities
    
    def _fetch_from_osm(self, lat: float, lon: float, radius_km: float, facility_types: list = None) -> list:
        radius_m = int(radius_km * 1000)
        filters = []
        
        # Tags OSM plus larges pour inclure les hôpitaux, cliniques et EHPAD
        if not facility_types or 'hospital' in facility_types:
            filters.extend([
                f'node["amenity"="hospital"](around:{radius_m},{lat},{lon});',
                f'way["amenity"="hospital"](around:{radius_m},{lat},{lon});',
                f'relation["amenity"="hospital"](around:{radius_m},{lat},{lon});'
            ])
        if not facility_types or 'clinic' in facility_types:
            filters.extend([
                f'node["amenity"="clinic"](around:{radius_m},{lat},{lon});',
                f'way["amenity"="clinic"](around:{radius_m},{lat},{lon});',
                f'node["healthcare"="clinic"](around:{radius_m},{lat},{lon});'
            ])
        if not facility_types or 'nursing_home' in facility_types:
            filters.extend([
                f'node["amenity"="social_facility"]["social_facility"="nursing_home"](around:{radius_m},{lat},{lon});',
                f'way["amenity"="social_facility"]["social_facility"="nursing_home"](around:{radius_m},{lat},{lon});',
                f'node["amenity"="nursing_home"](around:{radius_m},{lat},{lon});'
            ])
        
        query = f"[out:json];(\n  {chr(10).join(filters)}\n);out center;"
        
        for attempt in range(3):
            try:
                response = self.session.post('https://overpass-api.de/api/interpreter', data=query, timeout=self.timeout)
                response.raise_for_status()
                return self._parse_osm_response(response.json())
            except Exception as e:
                if attempt == 2: print(f"  ✗ OSM Error: {e}", file=sys.stderr)
                time.sleep(1)
        return []

    def _parse_osm_response(self, data: dict) -> list:
        facilities = []
        for element in data.get('elements', []):
            if 'tags' not in element or 'center' not in element: continue
            tags = element['tags']
            lat, lon = element['center']['lat'], element['center']['lon']
            
            # Recherche de nom très exhaustive
            name = (tags.get('name') or 
                    tags.get('official_name') or 
                    tags.get('operator') or 
                    tags.get('brand') or
                    tags.get('description') or 
                    f"Établissement de santé ({tags.get('amenity', 'médical')})")
            
            # Récupération de la capacité depuis OSM si disponible
            osm_capacity = (self._parse_int(tags.get('beds')) or 
                           self._parse_int(tags.get('capacity')) or 
                           self._parse_int(tags.get('capacity:persons')))

            # Reconstruction de l'adresse plus robuste
            address = self._build_address(tags)
            if not address:
                city = tags.get('addr:city') or tags.get('is_in:city')
                if city: address = city

            facilities.append({
                'id': f"osm_{element['id']}",
                'name': name,
                'type': self._map_osm_type(tags),
                'address': address,
                'lat': float(lat), 'lon': float(lon),
                'phone': tags.get('phone') or tags.get('contact:phone') or tags.get('operator:phone'),
                'website': tags.get('website') or tags.get('url') or tags.get('contact:website'),
                'source': 'OpenStreetMap',
                'capacity': {
                    'total_beds': osm_capacity,
                    'available_beds': None,
                    'occupancy_rate': None
                }
            })
        return facilities

    def _fetch_from_annuaire_sante(self, lat: float, lon: float, radius_km: float, location_name: str = None) -> list:
        """Récupère les données officielles françaises (FINESS) via data.gouv.fr"""
        try:
            # On utilise le dataset Annuaire Santé qui contient les capacités
            params = {
                'q': location_name if location_name else 'Hôpital',
                'limit': 100
            }
            
            response = self.session.get(
                'https://www.data.gouv.fr/api/1/datasets/5ea6ddb0634df442df1de1be/records/',
                params=params, 
                timeout=10
            )
            
            if response.status_code == 200:
                return self._parse_gouv_records(response.json().get('records', []), lat, lon, radius_km)
            return []
        except Exception:
            return []

    def _parse_gouv_records(self, records: list, c_lat: float, c_lon: float, radius: float) -> list:
        facilities = []
        for r in records:
            try:
                f = r.get('fields', {})
                geo = r.get('geometry', {}) or f.get('geolocalisation', {})
                if not geo: continue
                coords = geo.get('coordinates', [])
                if not coords: continue
                
                # Inversion lat/lon selon le format de data.gouv.fr
                lat, lon = float(coords[1]), float(coords[0])
                dist = self._distance(c_lat, c_lon, lat, lon)
                
                if dist > radius + 5: continue
                
                # Recherche de capacité dans divers champs possibles
                capacity = (self._parse_int(f.get('nb_lits_total')) or 
                           self._parse_int(f.get('capacite_totale')) or 
                           self._parse_int(f.get('capacite_accueil')) or
                           self._parse_int(f.get('nb_places_total')))
                
                # if capacity: print(f"DEBUG: Found capacity {capacity} for {f.get('nom_etablissement')}", file=sys.stderr)

                facilities.append({
                    'id': f"finess_{r.get('recordid') or f.get('num_finess')}",
                    'name': f.get('nom_etablissement') or f.get('rs') or f.get('raison_sociale'),
                    'type': self._map_to_standard_type(f.get('libelle_categorie_etablissement', '')),
                    'address': f.get('adresse_etablissement') or f.get('adresse') or f"{f.get('num_voie', '')} {f.get('nom_voie', '')}, {f.get('code_postal', '')} {f.get('libelle_commune', '')}",
                    'lat': lat, 'lon': lon,
                    'phone': f.get('telephone'),
                    'website': f.get('site_internet') or f.get('url'),
                    'source': 'FINESS',
                    'capacity': {
                        'total_beds': capacity,
                        'available_beds': None,
                        'occupancy_rate': None
                    }
                })
            except: continue
        return facilities

    def _merge_facilities(self, osm: list, gouv: list) -> list:
        """Fusionne les données OSM et Gouv en privilégiant les infos officielles"""
        merged = {f['id']: f for f in osm}
        
        for g in gouv:
            matched = False
            for o_id, o in list(merged.items()):
                # Si les établissements sont à moins de 300 mètres, on considère que c'est le même
                if self._distance(g['lat'], g['lon'], o['lat'], o['lon']) < 0.3:
                    # On enrichit OSM avec les données Gouv
                    if g['name']: merged[o_id]['name'] = g['name']
                    if g['address']: merged[o_id]['address'] = g['address']
                    if g['phone']: merged[o_id]['phone'] = g['phone']
                    merged[o_id]['capacity'] = g['capacity']
                    merged[o_id]['source'] = f"{merged[o_id]['source']} + FINESS"
                    matched = True
                    break
            
            if not matched:
                merged[g['id']] = g
                
        return list(merged.values())

    @staticmethod
    def _parse_int(v) -> Optional[int]:
        """Safely parse integer values"""
        try:
            if v is None: return None
            # Handle string with decimals or other formats
            if isinstance(v, str):
                v = v.replace(' ', '').replace(',', '.')
                return int(float(v))
            return int(v)
        except (ValueError, TypeError):
            return None

    def _save_cache(self, data: list):
        try:
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump({'timestamp': datetime.now(timezone.utc).isoformat(), 'facilities': data}, f, ensure_ascii=False, indent=2)
        except: pass

    def _load_cache(self) -> list:
        try:
            if not os.path.exists(CACHE_FILE): return None
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                d = json.load(f)
            ts = datetime.fromisoformat(d['timestamp'].replace('Z', '+00:00'))
            if datetime.now(timezone.utc) - ts > timedelta(hours=CACHE_EXPIRY_HOURS): return None
            return d['facilities']
        except: return None

    @staticmethod
    def _distance(lat1, lon1, lat2, lon2):
        R = 6371
        dLat, dLon = math.radians(lat2-lat1), math.radians(lon2-lon1)
        a = math.sin(dLat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dLon/2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    @staticmethod
    def _map_osm_type(t):
        if t.get('amenity') == 'hospital': return 'hospital'
        if t.get('amenity') in ['clinic', 'nursing_home']: return t.get('amenity')
        return 'clinic'

    @staticmethod
    def _map_to_standard_type(t):
        l = t.lower()
        if 'hôpital' in l or 'hospital' in l: return 'hospital'
        if 'ehpad' in l or 'maison' in l: return 'nursing_home'
        return 'clinic'

    @staticmethod
    def _build_address(t):
        p = [t.get(f'addr:{k}') for k in ['housenumber', 'street', 'postcode', 'city'] if t.get(f'addr:{k}')]
        return ', '.join(p)

class SkillParser:
    def __init__(self):
        self.fetcher = HealthDataFetcher()
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'HealthCapacitySkill/1.0'})

    def execute(self, text: str) -> Dict:
        text_l = text.lower()
        loc = self._extract_location(text_l)
        if not loc: return {'success': False, 'error': 'Lieu non trouvé'}
        
        rad = 5
        m = re.search(r'(\d+)\s*km', text_l)
        if m: rad = float(m.group(1))
        
        types = []
        if any(w in text_l for w in ['hôpital', 'hopital', 'hospital']): types.append('hospital')
        if 'clinique' in text_l or 'clinic' in text_l: types.append('clinic')
        if any(w in text_l for w in ['ehpad', 'maison', 'nursing']): types.append('nursing_home')

        try:
            resp = self.session.get('https://nominatim.openstreetmap.org/search', 
                                    params={'q': f"{loc}, France", 'format': 'json', 'limit': 1}, timeout=10)
            if not resp.ok or not resp.json(): return {'success': False, 'error': 'Géocodage échoué'}
            lat, lon = float(resp.json()[0]['lat']), float(resp.json()[0]['lon'])
            
            facilities = self.fetcher.get_facilities(lat, lon, radius_km=rad, facility_types=types, location_name=loc)
            results = []
            for f in facilities:
                d = self.fetcher._distance(lat, lon, f['lat'], f['lon'])
                if d <= rad:
                    f['distance_km'] = round(d, 2)
                    results.append(f)
            
            results.sort(key=lambda x: x['distance_km'])
            return {'success': True, 'count': len(results), 'facilities': results}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _extract_location(self, text):
        # Liste de villes connues
        cities = ['paris', 'lyon', 'marseille', 'toulouse', 'nice', 'nantes', 'strasbourg', 'bordeaux', 'lille', 'rennes', 'belfort', 'montbéliard']
        for c in cities:
            if c in text: return c.capitalize()
        
        # Capture après les prépositions courantes
        m = re.search(r'(?:à|in|en|near|vers|de|sur)\s+([a-zàâäéèêëïîôöùûüç\-]+)', text)
        if m:
            loc = m.group(1).capitalize()
            # Nettoyage si la capture prend un mot inutile
            if loc.lower() in ['un', 'une', 'des', 'les', 'le', 'la']:
                return None
            return loc
        return None

if __name__ == '__main__':
    query = ' '.join(sys.argv[1:]) or sys.stdin.read().strip()
    if not query: print(json.dumps({'error': 'No query'})); sys.exit(1)
    print(json.dumps(SkillParser().execute(query), indent=2, ensure_ascii=False))
