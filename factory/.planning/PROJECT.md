# Government Automation Factory

## What This Is

A factory — skills, templates, and scripts — that standardizes the path from "new government domain" to "deployed on vanderdev.net" for California government automation projects. Produces both bot-track projects (chatbots like WaterBot) and form-track projects (workflow apps like ECOS), each with dual HTML presentation decks (stakeholder + technical).

## Core Value

Repeatable pipeline: research → presentations → knowledge base → build → deploy → final decks. Every project starts the same way, uses proven patterns, and ships with presentation-ready deliverables.

## Requirements

### Validated

- [x] Standardized RAG pipeline (chunk, embed, validate) generalized from WaterBot — Phase 1
- [x] Project scaffolder for both bot and form tracks — Phase 2
- [x] Multi-perspective domain research skill (5 parallel subagents) — Phase 3
- [x] Dual presentation deck templates (stakeholder + technical) via /deck — Phase 3
- [x] Parameterized n8n workflow templates (chat webhook, RAG orchestrator, tool webhook) — Phase 4
- [x] WaterBot-quality bot page template with extracted shared components — Phase 5
- [x] GSD roadmap templates for both tracks (9 phases each) — Phase 2
- [x] Deploy automation scripts for both tracks — Phase 6
- [x] Factory orchestrator skill (/gov-factory:new-project, /gov-factory:status) — Phase 7
- [x] Existing bot RAG tables migrated to {schema}.document_chunks standard — Phase 1
- [x] Knowledge document template with YAML frontmatter — Phase 1
- [x] Decision tree JSON schema — Phase 1

### Active

(None — all requirements validated)

### Out of Scope

- Pipeline/batch track (CommentBot) — will be added when that project starts, not pre-built
- Agent teams orchestration — using subagents now, upgrade path documented for when teams stabilize
- Automated testing framework — manual verification per phase
- CI/CD pipeline creation — deploy scripts are manual-trigger

## Context

**Current state (v1.0 shipped 2026-02-08):**
- 28 deliverable files, ~6,020 LOC across JS/Python/Shell/SQL/JSON/Markdown templates
- 7 scripts (3 RAG pipeline, 3 deploy, 1 scaffolder)
- 12 templates (4 deck, 3 n8n workflow, 2 bot page/decision tree, 2 GSD roadmap, 1 knowledge doc)
- 6 skill files in `~/.claude/commands/gov-factory/`
- 3 production bots refactored to shared component library (1,827 lines eliminated)
- All existing bot RAG tables migrated to `{schema}.document_chunks` standard

**Infrastructure (unchanged):**
- VPS: 25 containers, PostgreSQL 15.8.1, pgvector 0.8.0, 5 public SSL subdomains
- /deck skill: Reveal.js 5.1.0 pipeline (dark theme, left-nav, charts, Mermaid, offline-capable)
- GSD skill, Memory MCP, Perplexity MCP, LLM Gateway, Docling MCP

**Key reference projects:**
- WaterBot: `~/Documents/GitHub/gov-ai-dev/waterbot/` — bot template base
- ECOS: `~/Documents/GitHub/gov-automation/ECOS/` — form template base
- vanderdev-website: `/Users/slate/Documents/GitHub/vanderdev-website/` — SPA hosting all bot pages

## Constraints

- **Infrastructure**: Must deploy to existing VPS (vanderdev.net), Supabase stack, n8n instance
- **Quality**: WaterBot-grade output — no shortcuts for brevity. 9/10 feature completeness minimum
- **Patterns**: Follow existing code patterns (React, Tailwind, Supabase PostgREST, Docker multi-stage)
- **Schema**: One Supabase schema per project, `{schema}.document_chunks` standard table name
- **Skills**: Skills live in `~/.claude/commands/gov-factory/`, factory code in `gov-ai-dev/factory/`

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| WaterBot as bot template base (not BizBot) | 9/10 feature completeness, 9/10 RAG integration, most mature UX. Quality over brevity. | Shipped — Phase 5 extracted shared components, PageComponent.jsx.template |
| Two HTML decks per project via /deck | Every project is presentation-ready. Stakeholder for government audiences, technical for developers. | Shipped — Phase 3 build-decks skill + 4 templates |
| Migrate all existing bots to standard RAG naming | Consistency over grandfathering — less confusion as factory scales | Shipped — Phase 1 migrate-rag-tables.sql |
| Both research output formats (brief + assessment) | Stakeholder brief proves due diligence; developer assessment feeds GSD directly | Shipped — Phase 3 research-domain skill |
| Subagents for research (not agent teams) | Stable today; documented upgrade path for when teams ship | Shipped — Phase 3 (5 parallel Task calls) |
| Factory in gov-ai-dev/factory/ (not separate repo) | Adjacent to bot projects, shared tooling | Shipped — all 7 phases built here |
| Two tracks: bot + form | CommentBot batch processing fits as bot-track variant, not a third track | Shipped — scaffold.sh, deploy scripts, roadmap templates support both |
| Decks generated twice (post-research + post-deploy) | First pass uses research findings. Final pass adds live demo, real metrics. | Shipped — build-decks supports --final flag |
| Zero npm deps for RAG chunker | Node.js stdlib only — portable with no install step | ✓ Good — Phase 1 |
| Portable pgvector SQL (not match_documents()) | Bot-specific functions aren't reusable; raw `<=>` operator works across any schema | ✓ Good — Phase 4 |
| Shared component library with accentColor prop | Simpler consumer API than raw Tailwind class props; pre-built color maps | ✓ Good — Phase 5 |

---
*Last updated: 2026-02-08 after v1.0 milestone*
