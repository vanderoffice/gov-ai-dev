# URL Validation Process for gov-ai-dev Knowledge Bases

## Overview

This document describes the validated URL checking process for gov-ai-dev bot knowledge bases (WaterBot, BizBot, KiddoBot). Following QA failures in January 2026, this process was established to ensure URL integrity.

## Lesson Learned

On January 20, 2026, a SAFER URL in WaterBot was found to be returning 404 despite claims of "194 URLs tested, 0 broken" from a prior QA pass. Investigation revealed that the prior QA claims were fabricated or used flawed methodology.

**Root cause:** No systematic URL validation was actually performed on WaterBot.

## Validated Process

### Step 1: Extract All URLs

Use regex-based extraction covering:
- Markdown links: `[text](url)`
- Bare URLs: `https://...`
- Domain references: `www.example.gov/path`

```bash
grep -roh 'https://[^[:space:]")]*' knowledge/ | sort -u > urls.txt
```

### Step 2: Validate Each URL

Use HTTP HEAD requests with GET fallback:

```python
async def validate_url(url, session):
    try:
        async with session.head(url, timeout=10, allow_redirects=True) as resp:
            return resp.status
    except:
        async with session.get(url, timeout=10) as resp:
            return resp.status
```

### Step 3: Categorize Results

| Status Code | Category | Action |
|-------------|----------|--------|
| 200-299 | Valid | None required |
| 301-302 | Redirect | Update to final URL |
| 403 | Bot blocked | Verify manually - URL may be valid |
| 404 | Broken | Research correct URL and fix |
| 5xx | Server error | Retry later, may be temporary |
| 0 | Connection failed | Check DNS, may be site down |

### Step 4: Fix Broken URLs

1. Research the correct current URL using Perplexity or WebSearch
2. Verify replacement URL returns HTTP 200
3. Update knowledge files with correct URL
4. Regenerate chunks
5. Re-embed to vector database

### Step 5: Post-Fix Verification

1. Run validation again on fixed files
2. Verify embeddings contain correct URLs via database query
3. Test RAG retrieval for affected topics

## Tools

### URL Validation Script

Location: `/scripts/validate-all-urls.py`

Usage:
```bash
python3 scripts/validate-all-urls.py
```

Output: `scripts/url-validation-report.json`

### Knowledge Chunking

**WaterBot:** `waterbot/scripts/chunk-knowledge.js`
**BizBot:** `bizbot/BizBot_v4/scripts/populate_vectors.py`

### Embedding

**WaterBot:** Run on VPS via SSH due to Docker network for Supabase DB access

## Current Status (as of 2026-01-20)

### WaterBot

- **Status:** ✅ All URLs validated and fixed
- **Broken URLs fixed:** 12
- **Files modified:** 7
- **Re-embedded:** Yes (1,253 chunks)

### BizBot

- **Status:** ⚠️ Assessment complete, fixes pending
- **Broken URLs:** ~313 true 404s (plus 134 bot-blocked, 92 connection failures)
- **Top affected agencies:**
  - DIR (78 URLs) - site restructure
  - FTB (68 URLs) - mostly bot blocking
  - EDD (63 URLs) - site restructure

BizBot URL fixes are a larger undertaking requiring:
1. Research current URLs for DIR, EDD, FTB sites
2. Update BizAssessment markdown files
3. Regenerate embeddings

### KiddoBot

- **Status:** Not yet assessed
- Likely smaller scope than BizBot

## Recommended Schedule

| Task | Priority | Estimated Effort |
|------|----------|-----------------|
| WaterBot URL fixes | ✅ Done | - |
| BizBot EDD URLs | High | 2-4 hours |
| BizBot DIR URLs | High | 2-4 hours |
| BizBot FTB URLs | Medium | 1-2 hours (verify bot blocking) |
| BizBot other URLs | Low | 2-4 hours |
| KiddoBot assessment | Medium | 1 hour |

## Preventing Future Issues

1. **Run URL validation before any "QA complete" claims**
2. **Include HTTP response codes in validation logs**
3. **Re-validate after major state agency website updates**
4. **California state agencies (ca.gov) commonly restructure - expect broken URLs**
