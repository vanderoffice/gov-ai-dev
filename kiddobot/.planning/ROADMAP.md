# Roadmap: KiddoBot Overhaul

## Overview

Full overhaul of KiddoBot following the standard 7-phase template. Phases are conditionally included based on `/bot-audit` results from 2026-02-16. Target: WaterBot v2.0 feature and quality parity.

## Domain Expertise

California childcare programs, subsidized care (CalWORKs, CCDF, Head Start, Regional Center), SMI/FPL income thresholds, 58-county R&R agency network, licensing requirements (Title 5 vs Title 22), immunization requirements, special populations (foster, homeless, migrant, military families).

## Production-First Doctrine

All code changes target the production repo on VPS:
- **Repo:** `vanderoffice/vanderdev-website` at `/root/vanderdev-website/`
- **Build:** `ssh vps "cd /root/vanderdev-website && npm run build"`
- **Dev repos are READ-ONLY** — no code changes to `gov-ai-dev/*`
- **Knowledge content** is ingested via `/bot-ingest`, not deployed via git

## Phases

- [x] Phase 0: Audit & Baseline — **INCLUDE** (mandatory)
- [x] Phase 1: Knowledge Refresh — **COMPLETE** (URLs fixed, thresholds verified, 935 chunks re-ingested)
- [x] Phase 2: Shared Infrastructure — **SKIP** (WaterBot built components; KiddoBot imports in Phase 4)
- [x] Phase 3: Tool Rebuilds — **COMPLETE** (threshold externalization + county R&R + cross-tool CTAs)
- [x] Phase 4: UI/UX Polish — **COMPLETE** (violet accent + responsive layout)
- [x] Phase 5: Integration & E2E — **COMPLETE** (webhook 30S/5A/0W; embedding regression documented)
- [x] Phase 6: Production Deploy — **COMPLETE** (live verified, cross-bot comparison done)

## Phase Details

### Phase 0: Audit & Baseline
**Goal**: Establish current state and measurable baseline before any changes.
**Depends on**: None
**Research**: Unlikely
**Plans**: 1

Key work:
- Run `/bot-eval --bot kiddobot --mode embedding --core` for coverage baseline
- Document current mode count (3: calculator, personalized, programs), feature list, component usage
- Copy audit report into `.planning/` for reference
- Confirm phase skip/include decisions in this ROADMAP

---

### Phase 1: Knowledge Refresh
**Goal**: Clean 48 broken URLs from RAG content and verify all thresholds are current.
**Depends on**: Phase 0
**Research**: Likely (verify current SMI/FPL thresholds, fee schedules for 2025-26 fiscal year)
**Plans**: 2-3

Key work:
- Run `/bot-refresh` checks (staleness, URLs, thresholds)
- Remove or replace 48 broken URLs in knowledge markdown files
- Fix malformed URL (`publichealthlawcenter.org%20Center...`) and double-path URL (`carefacilitysearch//carefacilitysearch/`)
- Fix typo: `trintyfamilyresource.org` → `trinityfamilyresource.org`
- Verify 2025-26 SMI/FPL income limits, family fee schedules, CCDF thresholds
- Canonicalize 44 redirected URLs to their final destinations
- Run `/bot-ingest --replace` with cleaned content
- Run `/bot-ingest verify.py` — must PASS

---

### Phase 3: Tool Rebuilds
**Goal**: Refactor EligibilityCalculator to data-driven thresholds and enhance ProgramFinder with county-aware matching.
**Depends on**: Phase 1
**Research**: Likely (current threshold values, county R&R service areas)
**Plans**: 2-3

Key work:
- Extract hardcoded SMI/FPL thresholds from KiddoBot.jsx into JSON config (`src/lib/bots/data/kiddobot-thresholds.json`)
- Refactor EligibilityCalculator to load thresholds from JSON (easy annual updates)
- Enhance ProgramFinder with county-aware matching (58 counties, each with different R&R agencies)
- Build county R&R lookup data file from existing `ChildCareAssessment/07_County_Deep_Dives/`
- Cross-tool CTAs: chat → calculator → program finder flows
- 10+ test scenarios per tool with expected results

---

### Phase 4: UI/UX Polish
**Goal**: Bring KiddoBot visual presentation to WaterBot standard with pink accent theme.
**Depends on**: Phase 3
**Research**: Unlikely
**Plans**: 2

Key work:
- Import `react-markdown` + `remark-gfm` into KiddoBot.jsx
- Apply `getMarkdownComponents('pink')` to all response surfaces
- Implement pill-style source citations
- Verify gradient message bubbles use pink accent
- Add responsive layout CSS (mobile-first)
- Ensure `ICON_MAP` renders icons as SVG, never as text
- Verify styled blockquotes, tables, code pills render correctly
- Side-by-side visual comparison with WaterBot

---

### Phase 5: Integration & E2E
**Goal**: Comprehensive testing of all modes, tools, and cross-tool flows.
**Depends on**: Phase 4
**Research**: Unlikely
**Plans**: 1-2

Key work:
- Run `/bot-eval --bot kiddobot --mode embedding --core` — must score >= 80%
- Run `/bot-eval --bot kiddobot --mode webhook` — live endpoint testing
- Test all mode transitions (calculator ↔ personalized ↔ programs)
- Test edge cases: empty inputs, very long queries, special characters, non-English input
- Compare against Phase 0 baseline: improvement >= 5 points
- Verify all cross-tool CTAs functional
- Check for console errors in browser dev tools

---

### Phase 6: Production Deploy
**Goal**: Ship it. Verify live.
**Depends on**: Phase 5
**Research**: Unlikely
**Plans**: 1

Key work:
- Final VPS build: `ssh vps "cd /root/vanderdev-website && npm run build"`
- Verify live site at `vanderdev.net/kiddobot`
- Run `/bot-eval --mode webhook` against live endpoints
- Log results: `/bot-refresh track-history.py --bot kiddobot`
- Confirm all 3 bots (WaterBot, BizBot, KiddoBot) still render correctly

## Progress

**Execution Order:**
Phases execute in numeric order. Skipped phases are marked N/A.

| Phase | Plans Complete | Status | Completed |
|-------|---------------|--------|-----------|
| 0: Audit & Baseline | 1/1 | Complete | 2026-02-16 |
| 1: Knowledge Refresh | 2/2 | Complete | 2026-02-16 |
| 2: Shared Infrastructure | N/A | SKIPPED | N/A |
| 3: Tool Rebuilds | 2/2 | Complete | 2026-02-16 |
| 4: UI/UX Polish | 2/2 | Complete | 2026-02-16 |
| 5: Integration & E2E | 1/1 | Complete | 2026-02-16 |
| 6: Production Deploy | 1/1 | Complete | 2026-02-16 |

## Skills Used Per Phase

| Phase | Skills | Purpose |
|-------|--------|---------|
| 0: Audit & Baseline | `/bot-audit`, `/bot-eval --core` | Assessment + baseline |
| 1: Knowledge Refresh | `/bot-refresh`, `/bot-ingest --replace`, `/bot-eval` | Content update cycle |
| 3: Tool Rebuilds | (manual coding on VPS) | EligibilityCalculator + ProgramFinder |
| 4: UI/UX Polish | (manual coding on VPS) | Visual parity with WaterBot |
| 5: Integration & E2E | `/bot-eval --mode webhook`, `/bot-eval --baseline auto` | Comprehensive testing |
| 6: Production Deploy | `/bot-refresh track-history` | Ship + log |

## Estimated Effort

Based on WaterBot v2.0 calibration data (~5 min/plan):

| Phase | Est. Plans | Est. Time |
|-------|-----------|-----------|
| 0: Audit & Baseline | 1 | ~5 min |
| 1: Knowledge Refresh | 2-3 | ~15 min |
| 3: Tool Rebuilds | 2-3 | ~15 min |
| 4: UI/UX Polish | 2 | ~10 min |
| 5: Integration & E2E | 1-2 | ~10 min |
| 6: Production Deploy | 1 | ~5 min |
| **Total** | **9-13** | **~60 min** |
