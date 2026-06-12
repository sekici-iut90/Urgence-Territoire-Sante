---
name: health-capacity
description: 'Localize real-time health facilities (hospitals, clinics, nursing homes) within a given radius and retrieve their remaining capacity. Use when: finding available beds, checking facility availability, locating healthcare services in a specific area.'
argument-hint: 'Provide location (address/coordinates) and search radius in km'
user-invocable: true
---

# Health Capacity Localization

Locate hospitals, clinics, and nursing homes in real-time within a specified radius and check their current available capacity.

## When to Use

- Find available hospital beds in a specific area
- Locate clinics with remaining capacity
- Search for nursing homes (EHPAD) with open spots
- Emergency room capacity checks
- Plan healthcare resource allocation
- Real-time healthcare availability assessment

## Quick Start

### 1. Define Search Parameters
- **Location**: Address, city, or GPS coordinates (latitude, longitude)
- **Radius**: Search distance in kilometers
- **Facility Type**: Hospital, clinic, nursing home (EHPAD), or all

### 2. Query Health Facilities
Execute the search via the Python interface:

```bash
python main.py "Find hospitals in Paris within 5 km"
```

### 3. Analyze Results
The script returns a JSON object containing:
- Facility name and type
- Address and distance
- Contact information
- Current bed capacity (total lits)
- Last updated timestamp

## Detailed Procedure

### Step 1: Execute Search
The skill automatically uses OpenStreetMap and Data.gouv.fr. Run the unified [skill script](./main.py):

```bash
python main.py "Find hospitals in Paris"
```

### Step 2: Parse Results
The response includes:
- **Available beds**: Current open beds (when available)
- **Total capacity**: Maximum occupancy
- **Distance**: Calculated from search center

## Troubleshooting
- No results: Increase search radius.
- Slow queries: Specific facility types help.

## References
- [API References](./references/api.md)
- [OpenStreetMap](https://www.openstreetmap.org/)
- [Data.gouv.fr](https://www.data.gouv.fr/)
