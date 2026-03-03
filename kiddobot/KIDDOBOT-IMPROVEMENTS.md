# KiddoBot Improvement Plan

**Date:** 2026-01-14
**Status:** ✅ Complete
**Live URL:** https://vanderdev.net/kiddobot

---

## Overview

KiddoBot is a California childcare assistance chatbot on vanderdev.net. It helps parents find subsidies, providers, and navigate childcare programs. The bot uses an n8n workflow with an AI agent to generate responses.

## Architecture

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│  React Frontend │────▶│  n8n Webhook         │────▶│  AI Agent       │
│  KiddoBot.jsx   │     │  /webhook/kiddobot   │     │  (Claude/GPT)   │
└─────────────────┘     └──────────────────────┘     └─────────────────┘
                                                              │
                                                              ▼
                                                     ┌─────────────────┐
                                                     │  Knowledge Base │
                                                     │  (System Prompt)│
                                                     └─────────────────┘
```

### Key Files

| Component | Location |
|-----------|----------|
| Frontend | `vps:/root/vanderdev-website/src/pages/KiddoBot.jsx` |
| Intake Form | `vps:/root/vanderdev-website/src/components/kiddobot/IntakeForm.jsx` |
| Eligibility Calculator | `vps:/root/vanderdev-website/src/components/kiddobot/EligibilityCalculator.jsx` |
| n8n Workflow | https://n8n.vanderdev.net (workflow: "KiddoBot" or similar) |
| Research Docs | https://github.com/vanderoffice/gov-ai-dev/tree/main/kiddobot/ChildCareAssessment |

### Infrastructure

- **Frontend:** React + Vite on VPS (`vps` SSH alias)
- **Backend:** n8n workflow at `https://n8n.vanderdev.net/webhook/kiddobot`
- **n8n Access:** Both local (`n8n.local:5678`) and public (`n8n.vanderdev.net`) instances exist

---

## Completed Work (2026-01-14)

### ✅ Hyperlink Detection Fix

**Problem:** AI responses mentioned URLs like "MyChildCare.ca.gov" as plain text instead of clickable links.

**Solution:** Updated `processLinks()` in KiddoBot.jsx to detect:
1. Markdown links `[text](url)` (already worked)
2. Full URLs `https://...` (already worked)
3. **NEW:** Bare domain names like `MyChildCare.ca.gov`, `cde.ca.gov`
4. **NEW:** Phone numbers like `(209) 723-1707` → `tel:` links

**Regex used:**
```javascript
/\[([^\]]+)\]\(([^)]+)\)|(https?:\/\/[^\s<>\[\]()]+)|(?<![/@])\b((?:[a-zA-Z0-9][-a-zA-Z0-9]*\.)+(?:gov|com|org|net|edu|io|ca\.gov)(?:\/[^\s<>\[\]()]*)?)\b|(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})/gi
```

**Status:** Deployed and working.

---

### ✅ Knowledge Base Population & Rural County Support (2026-01-14)

**Problem:** Bot responses were generic because the RAG vector database was nearly empty (only 3 placeholder documents).

**Root Cause:** The n8n workflow had a proper RAG architecture (embeddings → pgvector search → context injection), but the knowledge base contained almost no data. The system was falling back to "general knowledge" because vector search returned nothing useful.

**Solution Implemented (Option C from proposals):**

1. **Ingested full research repository** into Supabase pgvector:
   - 68 markdown files from `ChildCareAssessment/`
   - 1,216 chunks covering subsidies, providers, applications, special situations, county info

2. **Created comprehensive 58-county R&R directory:**
   - New file: `07_County_Deep_Dives/All_58_Counties_RR_Directory.md`
   - R&R agency name, phone, website for every California county
   - Rural/urban classifications
   - Cross-county suggestions for small counties
   - 36 additional chunks ingested

**Results - Before vs After:**

| Query | Before | After |
|-------|--------|-------|
| Glenn County R&R contact | Generic "contact your local R&R" | "Glenn County Office of Education - (530) 934-6575 - 311 S Villa Ave, Willows" |
| Rural county options | No acknowledgment | "Glenn County is a smaller, more rural area, so childcare options may be more limited" |
| Cross-county suggestions | None | "Neighboring counties: Butte, Colusa, and Tehama counties may have providers" |

**Technical Details:**
- Vector DB: Supabase pgvector (`kiddobot.document_chunks`)
- Total chunks: 1,252
- Embedding model: `text-embedding-3-small` (1536 dimensions)
- Similarity threshold: 0.7
- Ingestion script: `vps:/root/kiddobot-ingest/kiddobot_ingest.py`

**Maintenance:**
- Re-run ingestion when research docs are updated
- Script location: `vps:/root/kiddobot-ingest/`
- Run: `cd /root/kiddobot-ingest && OPENAI_API_KEY=xxx ./venv/bin/python kiddobot_ingest.py`

---

## Future Improvements (Optional)

### Lower-Effort Enhancements

- **Lower similarity threshold** from 0.7 to 0.65 in n8n workflow for more context retrieval
- **Add provider-level data** by scraping MyChildCare.ca.gov (no public API available)
- **System prompt refinement** to explicitly mention rural limitations when detected

### Higher-Effort Enhancements

- **Real-time provider search** integration if state releases an API
- **County-specific cost data** from annual R&R reports
- **Waitlist status tracking** (would require partnerships with APPs)

---

## Useful Commands

```bash
# SSH to VPS
ssh vps

# Edit KiddoBot frontend
ssh vps "vim /root/vanderdev-website/src/pages/KiddoBot.jsx"

# Rebuild frontend after changes
ssh vps "cd /root/vanderdev-website && npm run build"

# View n8n logs
ssh vps "docker logs n8n --tail 100"

# List n8n workflows via MCP
# (use n8n MCP tools in Claude Code)
```

---

## Reference Screenshots

Screenshots showing the generic response issue are at:
- `/Users/slate/Desktop/Screenshots /Screenshot 2026-01-14 at 16.21.38.png`
- `/Users/slate/Desktop/Screenshots /Screenshot 2026-01-14 at 16.29.07.png`

---

## Context for Fresh Session

When starting a new Claude session, provide this context:

> I'm working on KiddoBot (https://vanderdev.net/kiddobot), a California childcare chatbot. The RAG knowledge base has 1,252 chunks covering all 58 counties. Ingestion script is at `vps:/root/kiddobot-ingest/`. To re-ingest after updating research docs, rsync files to VPS and run the ingest script. See KIDDOBOT-IMPROVEMENTS.md in gov-ai-dev/kiddobot/ for full context.
