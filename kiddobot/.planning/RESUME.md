# KiddoBot Overhaul — Session Resume

## Current Phase
Phase 0: Audit & Baseline

## Current Status
Scaffolded. Bot-audit complete (84/100). Bot-eval baseline not yet run.

## Last Completed
- `/bot-audit kiddobot` — 2026-02-16 (report: `BOT-AUDIT-kiddobot-2026-02-16.md`)
- `/bot-scaffold kiddobot` — 2026-02-16 (generated `.planning/` structure)

## Next Action
Run `/gsd:plan-phase 00-audit-baseline` to create the Phase 0 plan, then execute it (run bot-eval baseline).

## Key Files
- Audit report: `BOT-AUDIT-kiddobot-2026-02-16.md`
- PROJECT: `.planning/PROJECT.md`
- ROADMAP: `.planning/ROADMAP.md`
- Production file: `/root/vanderdev-website/src/pages/KiddoBot.jsx` (VPS)

## DO NOT
- Edit code in `gov-ai-dev/kiddobot/` — dev repo is READ-ONLY
- Change shared components without testing all 3 bots
- Hardcode SMI/FPL thresholds — use JSON config

## DO
- All code changes via SSH to VPS (`/root/vanderdev-website/`)
- Verify builds with `ssh vps "cd /root/vanderdev-website && npm run build"`
- Run `/bot-eval` after every significant change
