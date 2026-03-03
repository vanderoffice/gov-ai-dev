# WaterBot Project Handoff Document

**Created:** 2026-01-15
**Purpose:** Complete context for building WaterBot - California Water Boards RAG Chatbot
**Use:** Start a new Claude Code session with this file as context

---

## Project Summary

Build **WaterBot**, a professional-grade RAG chatbot for California Water Boards on vanderdev.net. This is the third chatbot in the series after KiddoBot (childcare assistance) and BizBot (business licensing).

**Target Users:**
- Small business owners needing water permits
- Environmental organizations seeking restoration funding
- Agricultural operations managing compliance
- Local governments seeking infrastructure financing
- Non-profits working with water resources

**Core Features:**
1. RAG-powered chat with source citations
2. "Do I Need a Permit?" decision tree tool
3. Funding Navigator eligibility checker

---

## Existing Architecture (MUST FOLLOW)

All chatbots on vanderdev.net use identical patterns:

| Component | Technology |
|-----------|------------|
| Frontend | React 18 + Vite + Tailwind CSS |
| Hosting | Hostinger FTP via GitHub Actions |
| Backend | n8n webhooks (n8n.vanderdev.net) |
| Vector DB | Supabase PostgreSQL + pgvector |
| Embeddings | OpenAI `text-embedding-3-small` (1536 dim) |
| LLM | Claude Sonnet |
| Similarity | Cosine similarity, threshold > 0.70 |

### Critical n8n Patterns (From KiddoBot Fix)
```
- alwaysOutputData: true  ← On vector search node (CRITICAL)
- Fallback handler for empty results
- escapeBraces() function for LangChain templates
- Top-K retrieval: 8 chunks
```

### Key Reference Files

| File | Purpose |
|------|---------|
| `/Users/slate/Documents/GitHub/vanderdev-website/src/pages/KiddoBot.jsx` | Pattern for WaterBot.jsx (3-mode, chat, intake) |
| `/Users/slate/Documents/GitHub/vanderdev-website/src/pages/BizBot.jsx` | Alternative pattern reference |
| `/Users/slate/Documents/GitHub/vanderdev-website/src/components/kiddobot/IntakeForm.jsx` | Multi-step form pattern |
| `/Users/slate/Documents/GitHub/vanderdev-website/src/components/bizbot/LicenseFinder.jsx` | Pattern for PermitFinder.jsx |
| `/Users/slate/Documents/DEV_RESOURCES/Projects/wisebot/wisebot_knowledge_schema.sql` | Database schema pattern |
| `/Users/slate/Documents/GitHub/vanderdev-website/src/App.jsx` | Router - add WaterBot route |
| `/Users/slate/Documents/GitHub/vanderdev-website/src/components/Sidebar.jsx` | Navigation - add WaterBot NavItem |
| `/Users/slate/Documents/GitHub/vanderdev-website/CLAUDE.md` | Full architecture documentation |

---

## Knowledge Base Repository

**Location:** `gov-ai-dev/waterbot-knowledge` (public GitHub repo)

### Directory Structure
```
waterbot-knowledge/
├── README.md
├── metadata-schema.md
├── 01-overview/
│   ├── swrcb-overview.md
│   ├── regional-boards-overview.md
│   └── jurisdiction-guide.md
├── 02-regional-boards/
│   ├── region1-north-coast/
│   ├── region2-sf-bay/
│   ├── region3-central-coast/
│   ├── region4-los-angeles/
│   ├── region5-central-valley/
│   ├── region6-lahontan/
│   ├── region7-colorado-river/
│   ├── region8-santa-ana/
│   └── region9-san-diego/
├── 03-permits/
│   ├── npdes/
│   ├── wdr/
│   ├── 401-certification/
│   ├── water-rights/
│   └── habitat-restoration/
├── 04-funding/
│   ├── state-programs/
│   └── federal-programs/
├── 05-compliance/
├── 06-forms/
├── 07-decision-trees/
└── 08-glossary/
```

### Document Frontmatter Schema
```yaml
---
title: "Document Title"
document_id: "unique-id"
category: permit|funding|regulation|overview|compliance
permit_types: [npdes_general, construction]
funding_programs: [cwsrf, prop4]
regional_boards: [statewide]
source_url: "https://waterboards.ca.gov/..."
source_agency: "State Water Resources Control Board"
last_verified: "2026-01-15"
keywords: [keyword1, keyword2]
summary: "Brief description for preview"
---
```

---

## Database Schema (Supabase)

**Schema name:** `waterbot` in `n8n` database

### Core Tables
- `documents` - Source tracking with file_hash/content_hash deduplication
- `document_chunks` - Vector embeddings (1536-dim) with denormalized metadata
- `permit_decision_tree` - Permit Finder logic nodes
- `permit_details` - Permit reference data
- `funding_programs` - Funding Navigator data
- `funding_eligibility_rules` - Eligibility logic

### Key ENUM Types
```sql
-- Permit types
CREATE TYPE waterbot.permit_type AS ENUM (
    'npdes_individual', 'npdes_general', 'wdr', 'water_right',
    '401_certification', 'stormwater', 'construction', 'industrial',
    'municipal', 'habitat_restoration', 'recycled_water', 'other'
);

-- Funding programs
CREATE TYPE waterbot.funding_program AS ENUM (
    'cwsrf', 'dwsrf', 'safer', 'wifia', 'prop1', 'prop4', 'prop68',
    'swc', 'recycled_water', 'dac', 'tribal', 'other'
);

-- Regional boards
CREATE TYPE waterbot.regional_board AS ENUM (
    'region1', 'region2', 'region3', 'region4', 'region5',
    'region5s', 'region5f', 'region5r', 'region6v', 'region6s',
    'region7', 'region8', 'region9', 'statewide'
);
```

---

## n8n Workflows

| Workflow | Webhook | Purpose | Status |
|----------|---------|---------|--------|
| WaterBot - Chat | `/webhook/waterbot` | RAG chat (primary) | ✅ Active |
| WaterBot - Permit Lookup | `/webhook/waterbot-permits` | Decision tree tool | ✅ Active |
| WaterBot - Funding Lookup | `/webhook/waterbot-funding` | Eligibility checker | ✅ Active |

> **Note:** All backend workflows are deployed and active on n8n.vanderdev.net. Frontend integration pending.

---

## React Components to Create

```
src/pages/WaterBot.jsx              # Main page (3-mode selection)
src/components/waterbot/
├── IntakeForm.jsx                  # Project questionnaire (5 steps)
├── PermitFinder.jsx                # Decision tree UI
├── FundingNavigator.jsx            # Eligibility checker
├── PermitCard.jsx                  # Result display
└── FundingCard.jsx                 # Result display
```

### IntakeForm Steps
1. **Project Type** - Construction, Agricultural, Municipal, Industrial, Restoration
2. **Location** - County (auto-maps to region), waterbody
3. **Discharge** - Type, volume, pollutants
4. **Water Needs** - Water rights, existing permits, federal nexus
5. **Applicant** - Entity type, DAC status, tribal, budget

### Color Theme
- Primary: `blue-500` (water theme)
- Accent: `cyan-500`
- Dark background (consistent with other bots)

---

## Research Scope

### Primary Sources
| Source | URL |
|--------|-----|
| SWRCB Main | waterboards.ca.gov |
| Regional Boards | waterboards.ca.gov/[region] |
| CIWQS | ciwqs.waterboards.ca.gov |
| eFiling | efiling.waterboards.ca.gov |
| Financial Assistance | waterboards.ca.gov/water_issues/programs/grants_loans |

### The Nine Regional Water Quality Control Boards
| Region | Name | Key Counties |
|--------|------|--------------|
| 1 | North Coast | Humboldt, Mendocino, Del Norte |
| 2 | San Francisco Bay | Alameda, SF, Santa Clara, San Mateo |
| 3 | Central Coast | Monterey, Santa Barbara, San Luis Obispo |
| 4 | Los Angeles | LA, Orange, Ventura |
| 5 | Central Valley | Sacramento, Fresno, Kern (3 sub-offices) |
| 6 | Lahontan | Alpine, Mono, Inyo (2 sub-offices) |
| 7 | Colorado River | Imperial, Riverside (part) |
| 8 | Santa Ana | Riverside, San Bernardino |
| 9 | San Diego | San Diego, Imperial (part) |

### Permit Types to Document
- **NPDES** - Individual, General (Construction, Industrial, Municipal MS4)
- **WDR** - Waste Discharge Requirements (state-only)
- **401 Certification** - Federal project water quality cert
- **Water Rights** - Appropriative, riparian, temporary
- **Habitat Restoration** - SHRO, SRGO, accelerated pathways

### Funding Programs to Document
**State Programs:**
- Clean Water State Revolving Fund (CWSRF)
- Drinking Water State Revolving Fund (DWSRF)
- SAFER Program
- Proposition 1 (2014) - Water quality
- Proposition 68 (2018) - Parks and water
- **Proposition 4 (2024)** - Safe Drinking Water, Wildfire Prevention, Drought Preparedness, and Clean Air Bond Act ($10B bond)
- Small Community Drinking Water
- Disadvantaged Community (DAC) programs
- Tribal water programs

**Federal Programs:**
- WIFIA (Water Infrastructure Finance and Innovation Act)
- EPA water quality grants
- Bureau of Reclamation Title XVI

---

## Proposition 4 (2024) Research Notes

**Full Name:** Safe Drinking Water, Wildfire Prevention, Drought Preparedness, and Clean Air Bond Act of 2024

**Total:** $10 billion general obligation bond

**Key Water-Related Allocations:**
- Safe drinking water programs
- Drought preparedness
- Water recycling and groundwater
- Flood protection
- Watershed and fisheries restoration
- Coastal resilience

**Research URLs:**
- Official ballot measure text
- Legislative Analyst's Office analysis
- State Water Board implementation guidance (when available)
- Eligible project categories
- Application timeline and procedures

**Important:** This is a NEW program (2024) - implementation details may still be developing. Check for latest guidance from SWRCB Division of Financial Assistance.

---

## Implementation Phases

| Phase | Days | Deliverables |
|-------|------|--------------|
| 1. Infrastructure | 1-3 | Schema, n8n workflows, UI skeleton |
| 2. Foundation | 4-7 | 10-12 core docs (SWRCB, regulations, glossary) |
| 3. Regional Boards | 8-14 | 36 docs (4 per region × 9 regions) |
| 4. Permits | 15-25 | 25+ permit documentation |
| 5. Funding | 26-32 | 12+ funding docs, DB populated |
| 6. Tools | 33-40 | Permit Finder, Funding Navigator |
| 7. **Vector DB Tuning** | 41-50 | Test suite, accuracy validation (CRITICAL) |
| 8. QA/Deploy | 51-55 | Final testing, launch |

**Total:** ~11 weeks

---

## Phase 7: Vector DB Tuning (Critical for RAG Accuracy)

This phase dramatically improved KiddoBot accuracy. Do not skip.

### Test Query Suite (50+ queries)
- **Permit queries** (15-20): Coverage across all permit types
- **Funding queries** (10-15): All programs including Prop 4
- **Compliance queries** (5-10): Enforcement, violations
- **Edge cases** (10+): Ambiguous, multi-topic, out-of-scope

### Parameters to Tune

| Parameter | Test Values | Current Default |
|-----------|-------------|-----------------|
| Chunk size | 500-1500 chars | 1000 |
| Chunk overlap | 100-250 chars | 200 |
| Similarity threshold | 0.60-0.80 | 0.70 |
| Top-K retrieval | 5-12 | 8 |

### Accuracy Scoring Matrix

| Score | Criteria |
|-------|----------|
| 5 | Perfect answer with correct sources |
| 4 | Correct answer, minor source issues |
| 3 | Partially correct |
| 2 | Mostly incorrect |
| 1 | Hallucination |
| 0 | Complete failure |

**Target:** Average ≥ 4.0, no scores below 3

### Tuning Process
1. Create test query spreadsheet with expected answers
2. Run baseline with default params, score each
3. Adjust ONE parameter at a time
4. Re-run test suite, compare scores
5. Keep changes that improve, rollback regressions
6. Document final optimal configuration

---

## Disclaimer (Required on All Responses)

```
DISCLAIMER: WaterBot provides general information about California Water Boards
regulations, permits, and funding programs. This information is for educational
purposes only and does not constitute official guidance or legal advice.

Permit requirements vary by project and location. Always confirm requirements
with the appropriate Regional Water Quality Control Board or the State Water
Resources Control Board before proceeding with any project.

For official information:
- State Water Board: (916) 341-5250
- Find your Regional Board: waterboards.ca.gov/waterboards_map.html
```

---

## Starting the Implementation

### To begin Phase 1 (Infrastructure):
1. Create `waterbot` schema in Supabase (execute SQL)
2. Create n8n workflows (Knowledge Gateway, Ingest)
3. Create `src/pages/WaterBot.jsx` following KiddoBot pattern
4. Add route in `App.jsx` and NavItem in `Sidebar.jsx`
5. Deploy skeleton to staging

### Commands to Run:
```bash
# In vanderdev-website directory
cd /Users/slate/Documents/GitHub/vanderdev-website
npm install
npm run dev  # Local testing

# Create knowledge base repo
gh repo create gov-ai-dev/waterbot-knowledge --public --description "Knowledge base for WaterBot - California Water Boards RAG Chatbot"
```

---

## Original Research Document

Full research plan available at:
`/Users/slate/Downloads/water-boards-research-plan.md`

This contains the comprehensive 4-week, 11-subagent research strategy with detailed breakdowns for each permit type, regional board, and funding program.

---

## Session Instructions

When starting a new Claude Code session with this document:

1. **Read this file first** for full context
2. **Check the phase** you're working on
3. **Reference the key files** listed above for patterns
4. **Follow n8n critical patterns** (alwaysOutputData, fallbacks)
5. **Use the document frontmatter schema** for all knowledge base files
6. **Include Prop 4 (2024)** in funding research - this is new and important

**Quality Standard:** This is professional/state-grade work. All content must cite official sources, include disclaimers, and be verifiable.
