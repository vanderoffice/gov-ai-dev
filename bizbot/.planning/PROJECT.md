# BizBot Overhaul

## What This Is

California business licensing chatbot with 3 specialized modes (Just Chat, Guided Setup, License Finder) — rebuilt to WaterBot v2.0 standard with refreshed knowledge base, wizard-style LicenseFinder, shared UI pipeline, and 17-agency license database.

## Core Value

**BizBot users get accurate, current California business licensing information through an intuitive multi-mode interface with deterministic license matching and styled markdown responses.**

## Requirements

### Validated

- Audit report produced by `/bot-audit` on 2026-02-14 — v1.0
- Eval baseline captured by `/bot-eval` (94.3% → 100% coverage) — v1.0
- Phase skip/include decisions documented — v1.0
- Wire up shared markdown rendering pipeline (`getMarkdownComponents`, `react-markdown`, `remark-gfm`) — v1.0
- Fix broken/dead URLs in knowledge base (6 dead replaced, 2 redirects updated) — v1.0
- Add pill-style source citations to all response surfaces — v1.0
- Rebuild LicenseFinder with wizard pattern and deterministic matching — v1.0
- Achieve UI parity with WaterBot standard (42% → ~90%) — v1.0
- All webhook endpoints returning structured responses (100/100 webhook score) — v1.0

- ✓ ISS-002: Cross-industry general licenses auto-included (DBA, SOI, BPP) — v1.1
- ✓ ISS-003: City/county-specific license data seeded (25 CA metros) — v1.1
- ✓ ISS-004: External POST auth fixed (X-Bot-Token in audit tooling) — v1.1
- ✓ Metadata enrichment on all 387 chunks (topic + industry_category) — v1.1
- ✓ Timestamp columns for chunk-level staleness tracking — v1.1

### Active

- [ ] KiddoBot audit and overhaul (next bot in pipeline)
- [ ] Expand city-specific license data beyond top 25 metros
- [ ] Filtered RAG retrieval using topic metadata (e.g., industry-only for License Finder)

### Out of Scope

- New bot modes beyond existing 3 (Chat, Guided Setup, License Finder) — current modes cover all use cases
- Database migration or restructuring (DB health is 100/100) — no need
- Custom ML model training — RAG + LLM approach sufficient
- Mobile native app — web-first, responsive design works
- Shared component refactoring (WaterBot established patterns; BizBot imports them)

## Context

### Current State (v1.1 shipped 2026-02-16)

**Overall Score:** ~97/100

| Category | Pre-Overhaul | v1.0 | v1.1 |
|----------|-------------|------|------|
| Database Health | 100/100 | 100/100 | 100/100 |
| URL Validation | 60/100 | ~88/100 | ~88/100 (bot-blocking WAF unchanged) |
| Webhook Health | 70/100 | 100/100 | 100/100 (external access fixed) |
| Knowledge Freshness | 100/100 | 100/100 | 100/100 |
| UI Parity | 42/100 | ~90/100 | ~90/100 |
| Data Coverage | N/A | N/A | Expanded (25 metros + 728 CDPs) |

**Eval Metrics:**

| Metric | Baseline | v1.0 Final | v1.1 Final |
|--------|----------|------------|------------|
| Coverage | 94.3% | 100.0% | 100.0% |
| STRONG | 29 | 29 | 29 |
| ACCEPTABLE | 4 | 6 | 6 |
| WEAK | 2 | 0 | 0 |

**Production LOC:** 1,948 lines across 3 JSX files (BizBot.jsx, IntakeForm.jsx, LicenseFinder.jsx)

**License Database:** 19 agencies (17 state + 2 county), 36 industry licenses across 9 categories + 25 city-specific licenses

**RAG Metadata:** 387 chunks — 100% topic coverage (8 categories), 142 industry subcategory annotations, TIMESTAMPTZ staleness tracking

**City Dropdown:** 1,210 entries (482 incorporated + 728 CDPs)

### Bot Registry

| Property | Value |
|----------|-------|
| DB Table | `public.bizbot_documents` |
| Content Column | `content` |
| Embedding Column | `embedding` |
| Webhooks | `/bizbot`, `/bizbot-licenses`, `/bizbot-license-finder` |
| Knowledge Dir | `~/Documents/GitHub/gov-ai-dev/bizbot/BizAssessment/` |
| Accent Color | orange |
| Production File | `/root/vanderdev-website/src/pages/BizBot.jsx` |

### Technical Stack

- **Production repo:** `vanderoffice/vanderdev-website` at `/root/vanderdev-website/`
- **Framework:** React + Vite
- **RAG:** Supabase pgvector (1536-dim, OpenAI text-embedding-3-small)
- **Orchestration:** n8n webhooks at `n8n.vanderdev.net/webhook/`
- **Shared components:** `ChatMessage.jsx`, `WizardStepper.jsx`, `autoLinkUrls.js`, `getMarkdownComponents()`

## Constraints

- **Production-first:** All code changes on VPS via SSH. Dev repos are read-only.
- **Shared components:** Changes to `src/lib/bots/` affect all 3 bots.
- **Regulatory accuracy:** Fee/threshold/eligibility changes require human verification against authoritative sources (DCA, ABC, CSLB, DRE, CalGOLD).
- **Build pipeline:** `ssh vps "cd /root/vanderdev-website && npm run build"` — nginx serves `dist/`.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Production-first doctrine | Dev repo divergence cost WaterBot a full reconciliation phase | All code work on VPS |
| Skip Phase 2 (Shared Infra) | WaterBot already built all shared components; BizBot just imports them | Phase 4 handles wiring |
| Include Phase 1 despite fresh content | URL health at 60% — 34 broken + 44 redirects need remediation | URL-focused knowledge refresh |
| Both WEAK eval scores acceptable | injection_03 and offtopic_03 are intentionally off-domain; handled by LLM, not RAG | No knowledge gaps |
| FTB /index.html URLs left as-is | FTB serves directly (200); removing index.html returns 503 | Documented |
| Deduplicated 2 preamble chunks | 3 BizInterviews files shared same Perplexity header; kept 1 copy | 392 → 387 chunks |
| Bot-blocking 403s documented | ftb (29) + sos (3) = 32 URLs with WAF blocking; valid in browser | Known limitation |
| PHASE_CONFIG constants | Reusable color/icon config across dashboard, progress bar, groups | Clean pattern |
| ISS-001 resolved: DB tables created | license_requirements/license_agencies seeded (17 agencies, 31 licenses) | Wizard functional |
| Industry subcategory → parent category | Frontend subcategory codes didn't match DB parent codes | Fixed data contract |
| Entity type value alignment | sole_proprietor → sole_proprietorship to match n8n workflow | Fixed data contract |
| WAF 403 is infrastructure | VPS hardening blocks external POST; internal access fine | ISS-004 logged |
| TEXT types in DB functions | Production schema uses text, not varchar — function return types must match | ✓ Good |
| General licenses all conditional | DBA/SOI/BPP marked conditional to avoid false positives for sole props | ✓ Good |
| city_biz_lic_ prefix convention | All city-specific license codes use this prefix for dedup detection | ✓ Good |
| hasCityLicense check before generic | Prevents generic $50-$500 from polluting cost accumulators when real city data exists | ✓ Good |
| Santa Clarita → LA County TTC | City doesn't issue own business license; mapped to county agency | ✓ Good |
| TIMESTAMPTZ over TIMESTAMP | Timezone-aware timestamps for chunk staleness tracking | ✓ Good |
| No indexes on timestamp cols | Staleness queries are batch (bot-refresh), not real-time | ✓ Good |
| CDP pop >= 1000 threshold | Keeps dropdown manageable; special counties exempt (all CDPs) | ✓ Good |
| (Unincorporated) suffix on CDPs | Distinguishes from incorporated cities; n8n fallback handles unknown names | ✓ Good |
| infer_topic_metadata returns {} for unknown dirs | Safe no-op for WaterBot/KiddoBot — only matches NN_ prefix convention | ✓ Good |
| ISS-004 was X-Bot-Token, not WAF | Nginx vhost requires auth header on /webhook/ — fix in tooling, not infra | ✓ Good |

---
*Last updated: 2026-02-16 after v1.1 milestone*
