# CA Childcare Facility Spatial Dataset: Implementation Plan

**Date:** 2025-12-23
**Project:** ChildCareAssessment
**Purpose:** Build a geocoded dataset of California licensed childcare facilities

---

## Background: KiddoBot Project

### What is KiddoBot?
KiddoBot is an agentic AI assistant helping California parents navigate childcare subsidies, providers, paperwork, and county logistics. The knowledge base powering KiddoBot lives in the `ChildCareAssessment` repository.

### Repository Location
```
~/Documents/GitHub/gov-ai-dev/kiddobot/ChildCareAssessment/
```

### Project Status (as of 2025-12-23)
| Stage | Status | Notes |
|-------|--------|-------|
| 1. Setup & Initial Assessment | ✅ Complete | Multi-model research methodology established |
| 2. CalWORKs Deep-Dive | ✅ Verified | Eligibility matrix, stages 1-3, county variations |
| 3. Core Subsidies (CCDF, Regional Center) | ✅ Verified | SMI thresholds, 21 Regional Centers |
| 4. Provider Search & Costs | ✅ Verified | Fee schedules, tax credits, CCR&R directory |
| 5. Special Situations & Agencies | ✅ Complete | 7 special situation guides, agency coordination |
| 6. County Infrastructure Dataset | ❌ FAILED | Fabricated data deleted; lesson learned |

### Critical Lesson from Stage 6 Failure
**Research Data Integrity Rule:** NEVER synthesize research data. Extract from authoritative sources ONLY. If you cannot point to the source URL/document for a data value, you fabricated it. This spatial dataset project is the "do-over" using proper extraction methodology.

---

## The Gap We're Filling

### Problem Statement
No comprehensive geocoded dataset of California's ~35,000 licensed childcare facilities exists as open data. This is a real gap that prevents:
- Spatial analysis of childcare deserts
- Distance-based provider recommendations
- Policy research on facility distribution
- Integration with GIS tools

### What Exists Today

| Source | Facilities Covered | Has Lat/Long? | Bulk Download? |
|--------|-------------------|---------------|----------------|
| **data.ca.gov CCL CSVs** | ~28,000 (centers + large FCC) | ❌ No | ✅ Yes |
| **MyChildCare.ca.gov** | All ~35,000 | ❌ No | ❌ Search only |
| **CCR&R Network** | All ~35,000 | Unknown | ❌ Data request required |
| **CDPH Healthcare Facilities** | Healthcare only | ✅ Yes | ✅ Yes |

### What We Can Build
A geocoded dataset of **28,058 active facilities** from data.ca.gov:
- 14,072 Child Care Centers
- 13,986 Family Child Care Homes (capacity >8)

**NOT included** (requires separate effort):
- ~7,000 Small FCC homes (capacity ≤8) — not in bulk download for privacy reasons

---

## Data Sources

### Primary: data.ca.gov Community Care Licensing
**Dataset page:** https://data.ca.gov/dataset/community-care-licensing-facilities

**CSVs to download:**

1. **Child Care Centers**
   - URL: `https://data.chhs.ca.gov/dataset/46ffcbdf-4874-4cc1-92c2-fb715e3ad014/resource/7aed8063-cea7-4367-8651-c81643164ae0/download/tmpwya01y9s.csv`
   - Records: ~19,400 (includes closed; filter to LICENSED)
   - Active: 14,072

2. **Family Child Care Homes** (capacity >8 only)
   - URL: `https://data.chhs.ca.gov/dataset/46ffcbdf-4874-4cc1-92c2-fb715e3ad014/resource/4b5cc48d-03b1-4f42-a7d1-b9816903eb2b/download/tmpghf_prqt.csv`
   - Records: ~19,750 (includes closed; filter to LICENSED)
   - Active: 13,986

### CSV Schema (17 columns)
```
facility_type, facility_number, facility_name, licensee, facility_administrator,
facility_telephone_number, facility_address, facility_city, facility_state,
facility_zip, county_name, regional_office, facility_capacity, facility_status,
license_first_date, closed_date, file_date
```

### Geocoding: Census Geocoder API
- **URL:** https://geocoding.geo.census.gov/geocoder/
- **Batch endpoint:** https://geocoding.geo.census.gov/geocoder/locations/addressbatch
- **Cost:** Free
- **Rate limit:** 10,000 addresses per batch file
- **Expected match rate:** 90-95%

---

## Implementation Steps

### Phase 1: Data Extraction (~30 min)

1. **Download both CSVs**
   ```bash
   curl -o childcare_centers.csv "https://data.chhs.ca.gov/dataset/46ffcbdf-4874-4cc1-92c2-fb715e3ad014/resource/7aed8063-cea7-4367-8651-c81643164ae0/download/tmpwya01y9s.csv"

   curl -o fcc_homes.csv "https://data.chhs.ca.gov/dataset/46ffcbdf-4874-4cc1-92c2-fb715e3ad014/resource/4b5cc48d-03b1-4f42-a7d1-b9816903eb2b/download/tmpghf_prqt.csv"
   ```

2. **Filter to active facilities only**
   - Keep only `facility_status == "LICENSED"`
   - Discard CLOSED, INACTIVE, PENDING, ON PROBATION

3. **Merge into unified dataset**
   - Add `facility_category` column: "CENTER" or "FCC"
   - Standardize column names

4. **Prepare geocoding input**
   - Format: `id,street,city,state,zip`
   - Census Geocoder requires this specific format

### Phase 2: Geocoding (~3-4 hours)

1. **Split into batches of 10,000 addresses**

2. **Submit to Census Geocoder batch API**
   ```bash
   curl --form addressFile=@batch1.csv \
        --form benchmark=Public_AR_Current \
        --form vintage=Current_Current \
        "https://geocoding.geo.census.gov/geocoder/locations/addressbatch" \
        -o batch1_results.csv
   ```

3. **Process results**
   - Match types: Exact, Non_Exact, Tie, No_Match
   - Extract: latitude, longitude, match_type, matched_address

4. **Handle failures**
   - ~5-10% may not geocode
   - Log for manual review or alternative geocoding

### Phase 3: Validation & Output (~1 hour)

1. **Validate geocodes**
   - Check coordinates are within California bounds
   - Verify county assignment matches original data
   - Spot-check random samples on map

2. **Generate output files**

   **Primary output:** `ca_childcare_facilities_geocoded.csv`
   ```
   facility_number, facility_name, facility_type, facility_category,
   licensee, phone, address, city, state, zip, county,
   capacity, license_date, latitude, longitude, geocode_match_type
   ```

   **GeoJSON output:** `ca_childcare_facilities.geojson`
   - For direct use in GIS tools
   - Point geometry with all attributes

3. **Create data dictionary**
   - Document all fields
   - Note data source and extraction date
   - Document geocoding methodology

4. **Generate summary statistics**
   - Facilities by county
   - Facilities by type
   - Geocode success rate
   - Capacity totals

---

## Output Location

All outputs go to:
```
~/Documents/GitHub/gov-ai-dev/kiddobot/ChildCareAssessment/Data/
```

### Files to Create
| File | Description |
|------|-------------|
| `ca_childcare_facilities_geocoded.csv` | Primary geocoded dataset |
| `ca_childcare_facilities.geojson` | GeoJSON for GIS tools |
| `CA_CHILDCARE_FACILITIES_DATA_DICTIONARY.md` | Field documentation |
| `geocoding_log.csv` | Geocoding results and failures |
| `facility_summary_by_county.csv` | County-level aggregates |

---

## Quality Assurance

### Pre-Geocoding Checks
- [ ] Record counts match expected (~14k centers, ~14k FCC)
- [ ] All records have valid addresses
- [ ] Status filter correctly applied

### Post-Geocoding Checks
- [ ] Geocode success rate ≥90%
- [ ] All coordinates within CA bounding box
- [ ] No duplicate facility_numbers
- [ ] County counts are plausible

### Spot Checks
- [ ] Sample 10 random facilities
- [ ] Verify address + coordinates on Google Maps
- [ ] Confirm facility still exists at location

---

## Known Limitations

1. **Small FCC homes excluded** — Homes with capacity ≤8 are not in bulk data (privacy reasons)

2. **Address currency** — Addresses are from license records; facilities may have moved

3. **Geocoding accuracy** — Census geocoder places at street centerline, not parcel

4. **Data freshness** — CCL data updated irregularly; check `file_date` column

5. **Closed facilities in source** — Must filter; ~9,600 closed facilities in raw data

---

## Estimated Effort & Cost

| Task | Time | Cost |
|------|------|------|
| Data extraction & prep | 30 min | $0 |
| Geocoding (28k addresses) | 3-4 hours | $0 (Census Geocoder is free) |
| Validation & output | 1 hour | $0 |
| Documentation | 30 min | $0 |
| **TOTAL** | ~5-6 hours | **$0** |

---

## Future Enhancements

### Small FCC Data
- File formal data request with CCR&R Network (research@rrnetwork.org)
- Or submit California Public Records Act request to CDSS

### Data Enrichment
- Add quality ratings from MyChildCare.ca.gov (would require scraping)
- Add subsidy acceptance from CCR&R
- Add Head Start/CSPP program participation

### Maintenance
- Set up quarterly refresh process
- Compare to previous version for changes
- Track facility openings/closings

---

## Commands for Fresh Session

When starting a fresh session, provide this context:

```
I'm working on the ChildCareAssessment project at:
~/Documents/GitHub/gov-ai-dev/kiddobot/ChildCareAssessment/

Read the spatial dataset plan at:
Data/SPATIAL_DATASET_PLAN.md

Execute the plan to create a geocoded CA childcare facility dataset.
Key constraints:
- Only extract data from authoritative sources (no synthesis)
- Use Census Geocoder API (free, bulk-capable)
- Output to Data/ folder
- Document everything

Start with Phase 1: Download and filter the CCL CSVs.
```

---

*Plan created: 2025-12-23*
*Author: Claude (with human review)*
