# gov-ai-dev Shared Resources

Shared utilities and data files used across BizBot, KiddoBot, and WaterBot.

## California Locations Data

### Files

| File | Description |
|------|-------------|
| `data/california-locations.json` | Comprehensive CA counties and cities data (58 counties, 482 cities) |
| `data/california-locations.js` | JavaScript utility module with lookup functions |

### Usage

#### JavaScript/React Import

```javascript
import {
  CA_COUNTIES,
  getCitiesForCounty,
  getCountyForCity,
  searchCities
} from '@/shared/data/california-locations.js'

// Get all 58 counties (sorted)
console.log(CA_COUNTIES)
// ['Alameda', 'Alpine', 'Amador', ...]

// Get cities for a county
const oaklandCities = getCitiesForCounty('Alameda')
// ['Alameda', 'Albany', 'Berkeley', 'Dublin', 'Emeryville', 'Fremont', ...]

// Reverse lookup: find county for a city
const county = getCountyForCity('Oakland')
// 'Alameda'

// Search cities (for autocomplete)
const results = searchCities('oak', 5)
// [{ city: 'Oakland', county: 'Alameda' }, { city: 'Oakdale', county: 'Stanislaus' }, ...]
```

#### React Dropdown Options

```javascript
import { getCountyOptions, getCityOptions } from '@/shared/data/california-locations.js'

// For county <select>
const countyOptions = getCountyOptions()
// [{ value: 'Alameda', label: 'Alameda County' }, ...]

// For city <select> (after county selected)
const cityOptions = getCityOptions('Los Angeles')
// [{ value: 'Agoura Hills', label: 'Agoura Hills' }, ..., { value: '__unincorporated__', label: 'Unincorporated / Other' }]
```

### Data Source

- **Counties:** All 58 California counties
- **Cities:** All 482 incorporated California cities
- **Population:** County population estimates (2023 Census)
- **Source:** California League of Cities, US Census Bureau
- **Last Updated:** January 2026

### Counties Without Incorporated Cities

Three California counties have no incorporated cities:
- Alpine (smallest county, ~1,200 population)
- Mariposa (gateway to Yosemite)
- Trinity (rural northern CA)

For these counties, the dropdown shows "Unincorporated area" option with a manual text field.

### Extending This Data

To add additional data (e.g., zip codes, population by city):

1. Edit `california-locations.json`
2. Add new fields to the county/city objects
3. Create corresponding lookup functions in `california-locations.js`

## Bot-Specific Usage

### BizBot
- Uses city/county for local licensing requirements
- Production form: `/root/vanderdev-website/src/components/bizbot/IntakeForm.jsx`

### KiddoBot
- Uses county for childcare resource lookups
- County-only (childcare in CA is county-administered)
- Reference: `kiddobot/ChildCareAssessment/08_URL_Database/county_welfare_urls.csv`

### WaterBot
- Could use for regional water board jurisdiction lookups
- Currently chat-only (no intake form yet)
