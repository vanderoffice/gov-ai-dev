# gov-ai-dev Bot Data Quality Audit

## What This Is

Comprehensive data quality audit and remediation for California state AI assistant bots (WaterBot, BizBot, KiddoBot). Ensures all knowledge base content is accurate, current, properly embedded, and reliably retrievable. Born from a QA failure where fabricated "194 URLs tested, 0 broken" claims masked actual broken links.

## Core Value

**Every piece of information a bot returns must be accurate and verifiable.** Broken links, outdated facts, and retrieval failures erode user trust and undermine the bots' utility as authoritative state resources.

## Requirements

### Validated

- ✓ WaterBot URL fixes — 12 URLs fixed, 7 files modified, re-embedded (1,253 chunks)
- ✓ URL validation process documented — docs/URL-VALIDATION.md

### Active

- [ ] **URL Integrity** — All URLs return HTTP 200 (or valid redirect)
- [ ] **Deduplication** — Zero duplicate chunks in vector databases
- [ ] **Embedding Integrity** — All rows have valid, non-null embeddings
- [ ] **Content Freshness** — No outdated dates, statistics, or regulations
- [ ] **Factual Accuracy** — Program names, legislation citations, statistics correct
- [ ] **Cross-Reference Validity** — "Related Topics" sections point to real content
- [ ] **Chunk Quality** — Appropriate size (100-3000 chars), includes context
- [ ] **Metadata Consistency** — file_path, category, subcategory are accurate
- [ ] **Query Coverage Testing** — Real user questions find relevant content
- [ ] **BizBot URL Fixes** — ~313 true 404s across DIR, FTB, EDD sites
- [ ] **KiddoBot Assessment** — Full quality audit (not yet started)

### Out of Scope

- Continuous monitoring systems — This is a one-time audit, not ongoing infrastructure
- Bot code changes — Focus is on data quality, not application features
- New content creation — Fix existing content, don't expand knowledge bases

## Context

**Background:**
- Three CA state AI bots: WaterBot (Water Board info), BizBot (business licensing), KiddoBot (child services)
- RAG architecture: Markdown knowledge files → chunked → embedded → Supabase pgvector
- January 2026 incident: Prior QA claims were fabricated; SAFER URL found broken despite "all URLs validated"

**Current State:**
- WaterBot: URLs fixed, re-embedded ✅
- BizBot: 313 true 404s identified, 134 bot-blocked (403), 92 connection failures — fixes pending
- KiddoBot: Not yet assessed

**Technical Stack:**
- Knowledge: Markdown files in bot-specific `knowledge/` directories
- Chunking: `chunk-knowledge.js` (WaterBot), `populate_vectors.py` (BizBot)
- Embedding: OpenAI `text-embedding-3-small` (1536 dimensions)
- Storage: Supabase PostgreSQL with pgvector
- VPS: supabase-db on Docker internal network (172.18.0.3)

## Constraints

- **VPS Access**: Re-embedding requires SSH to VPS (database not exposed to host network)
- **API Costs**: OpenAI embedding calls have cost — batch efficiently

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| One-time audit over continuous monitoring | Get quality right first, then consider automation | — Pending |
| Fix all three bots comprehensively | User mandate: "100% perfect" | — Pending |
| Document process in URL-VALIDATION.md | Prevent future QA fabrication claims | ✓ Good |

---
*Last updated: 2026-01-20 after initialization*
