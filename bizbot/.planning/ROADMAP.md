# Roadmap: BizBot Overhaul

## Milestones

- ✅ [v1.0 Overhaul](milestones/v1.0-ROADMAP.md) (Phases 0-6) — SHIPPED 2026-02-15
- ✅ [v1.1 Data Completeness](milestones/v1.1-ROADMAP.md) (Phases 7-9) — SHIPPED 2026-02-16

## Production-First Doctrine

All code changes target the production repo on VPS:
- **Repo:** `vanderoffice/vanderdev-website` at `/root/vanderdev-website/`
- **Build:** `ssh vps "cd /root/vanderdev-website && npm run build"`
- **Dev repos are READ-ONLY** — no code changes to `gov-ai-dev/*`
- **Knowledge content** is ingested via `/bot-ingest`, not deployed via git

## Completed Phases

<details>
<summary>v1.0 Overhaul (Phases 0-6) — SHIPPED 2026-02-15</summary>

- [x] Phase 0: Audit & Baseline (1/1 plans) — completed 2026-02-14
- [x] Phase 1: Knowledge Refresh (2/2 plans) — completed 2026-02-15
- [x] ~~Phase 2: Shared Infrastructure~~ — SKIPPED (WaterBot patterns exist)
- [x] Phase 3: Tool Rebuilds (2/2 plans) — completed 2026-02-15
- [x] Phase 4: UI/UX Polish (1/1 plan) — completed 2026-02-15
- [x] Phase 5: Integration & E2E (1/1 plan) — completed 2026-02-15
- [x] Phase 6: Production Deploy (1/1 plan) — completed 2026-02-15

**Stats:** 6 phases (1 skipped), 8 plans, ~280 min active build time
**Audit score:** 74/100 → ~95/100
**Full details:** [v1.0-ROADMAP.md](milestones/v1.0-ROADMAP.md)

</details>

<details>
<summary>✅ v1.1 Data Completeness (Phases 7-9) — SHIPPED 2026-02-16</summary>

- [x] Phase 7: License Data Expansion (2/2 plans) — completed 2026-02-16
- [x] Phase 8: RAG Pipeline Improvements (3/3 plans) — completed 2026-02-16
- [x] Phase 9: Tooling & Verification (1/1 plan) — completed 2026-02-16

**Stats:** 3 phases, 6 plans, ~85 min active build time
**Eval:** 29S/6A/0W — zero regressions from data expansion
**Full details:** [v1.1-ROADMAP.md](milestones/v1.1-ROADMAP.md)

</details>

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|---------------|--------|-----------|
| 0: Audit & Baseline | v1.0 | 1/1 | Complete | 2026-02-14 |
| 1: Knowledge Refresh | v1.0 | 2/2 | Complete | 2026-02-15 |
| 2: Shared Infra | v1.0 | N/A | SKIPPED | N/A |
| 3: Tool Rebuilds | v1.0 | 2/2 | Complete | 2026-02-15 |
| 4: UI/UX Polish | v1.0 | 1/1 | Complete | 2026-02-15 |
| 5: Integration & E2E | v1.0 | 1/1 | Complete | 2026-02-15 |
| 6: Production Deploy | v1.0 | 1/1 | Complete | 2026-02-15 |
| 7: License Data Expansion | v1.1 | 2/2 | Complete | 2026-02-16 |
| 8: RAG Pipeline Improvements | v1.1 | 3/3 | Complete | 2026-02-16 |
| 9: Tooling & Verification | v1.1 | 1/1 | Complete | 2026-02-16 |

## Domain Expertise

California business licensing, DCA/ABC/CSLB/DRE regulations, CalGOLD local permitting, entity formation (LLC/Corp/Sole Prop), industry-specific licensing (food service, alcohol, construction, cannabis, healthcare, manufacturing, retail, professional services), compliance/renewal cycles, fee schedules.

## Skills Used Per Phase

| Phase | Skills | Purpose |
|-------|--------|---------|
| 0: Audit & Baseline | `/bot-audit`, `/bot-eval --core` | Assessment + baseline |
| 1: Knowledge Refresh | `/bot-refresh`, `/bot-ingest --replace`, `/bot-eval` | URL remediation + re-ingest |
| 3: Tool Rebuilds | (manual coding via SSH) | License data model + finder rebuild |
| 4: UI/UX Polish | (manual coding via SSH) | Markdown pipeline + source pills |
| 5: Integration & E2E | `/bot-eval --mode webhook`, `/bot-eval --baseline auto` | Comprehensive testing |
| 6: Production Deploy | `/bot-refresh track-history` | Ship + log |
| 7: License Data Expansion | (SQL + SSH), `/bot-ingest` | Cross-industry + city/county data |
| 8: RAG Pipeline Improvements | `/bot-ingest`, (SQL via SSH) | Metadata enrichment + timestamps |
| 9: Tooling & Verification | `/bot-eval`, (nginx config) | WAF fix + final eval |
