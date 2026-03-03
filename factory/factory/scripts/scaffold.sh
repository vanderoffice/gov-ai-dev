#!/usr/bin/env bash
set -euo pipefail

# scaffold.sh — Bootstrap a new government automation project
# Usage: scaffold.sh --track <bot|form> --name <slug> --title "Display Name"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FACTORY_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# --- Usage ----------------------------------------------------------------

usage() {
  cat <<'USAGE'
Usage: scaffold.sh --track <bot|form> --name <slug> --title "Display Name" [--output-dir <path>]

Required flags:
  --track     Project track: bot or form
  --name      Project slug (lowercase alphanumeric + hyphens, e.g. waterbot)
  --title     Display name (in quotes, e.g. "Water Rights Assistant")

Optional flags:
  --output-dir  Override default parent directory
                Bot default:  $HOME/Documents/GitHub/gov-ai-dev
                Form default: $HOME/Documents/GitHub/gov-automation

Examples:
  scaffold.sh --track bot --name waterbot --title "Water Rights Assistant"
  scaffold.sh --track form --name calfire --title "CalFire Reporting"
USAGE
}

# --- Parse flags ----------------------------------------------------------

TRACK=""
NAME=""
TITLE=""
OUTPUT_DIR=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --track)
      TRACK="$2"
      shift 2
      ;;
    --name)
      NAME="$2"
      shift 2
      ;;
    --title)
      TITLE="$2"
      shift 2
      ;;
    --output-dir)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Error: Unknown flag '$1'" >&2
      usage >&2
      exit 1
      ;;
  esac
done

# --- Validate flags -------------------------------------------------------

ERRORS=()

if [[ -z "$TRACK" ]]; then
  ERRORS+=("--track is required")
fi

if [[ -z "$NAME" ]]; then
  ERRORS+=("--name is required")
fi

if [[ -z "$TITLE" ]]; then
  ERRORS+=("--title is required")
fi

if [[ ${#ERRORS[@]} -gt 0 ]]; then
  for err in "${ERRORS[@]}"; do
    echo "Error: $err" >&2
  done
  echo "" >&2
  usage >&2
  exit 1
fi

# Validate --track
if [[ "$TRACK" != "bot" && "$TRACK" != "form" ]]; then
  echo "Error: --track must be 'bot' or 'form' (got '$TRACK')" >&2
  exit 1
fi

# Validate --name
if ! [[ "$NAME" =~ ^[a-z][a-z0-9-]*$ ]]; then
  echo "Error: --name must be lowercase alphanumeric + hyphens, starting with a letter (got '$NAME')" >&2
  exit 1
fi

# --- Set output directory -------------------------------------------------

if [[ -z "$OUTPUT_DIR" ]]; then
  if [[ "$TRACK" == "bot" ]]; then
    OUTPUT_DIR="$HOME/Documents/GitHub/gov-ai-dev"
  else
    OUTPUT_DIR="$HOME/Documents/GitHub/gov-automation"
  fi
fi

PROJECT_DIR="$OUTPUT_DIR/$NAME"

# Check target directory doesn't exist
if [[ -d "$PROJECT_DIR" ]]; then
  echo "Error: Directory already exists: $PROJECT_DIR" >&2
  exit 1
fi

# --- Template substitution helper -----------------------------------------

CREATED_DATE="$(date +%Y-%m-%d)"

substitute() {
  # Replace placeholders in a string via sed
  # Usage: substitute "string with {{PLACEHOLDERS}}"
  sed \
    -e "s|{{PROJECT_NAME}}|${NAME}|g" \
    -e "s|{{PROJECT_TITLE}}|${TITLE}|g" \
    -e "s|{{SCHEMA_NAME}}|${NAME}|g" \
    -e "s|{{TRACK}}|${TRACK}|g" \
    -e "s|{{CREATED_DATE}}|${CREATED_DATE}|g"
}

substitute_file() {
  # Substitute placeholders in a file in-place
  local file="$1"
  local tmp="${file}.tmp"
  substitute < "$file" > "$tmp"
  mv "$tmp" "$file"
}

# --- Create directory structure -------------------------------------------

mkdir -p "$PROJECT_DIR"

# Common directories for both tracks
mkdir -p "$PROJECT_DIR/research"
mkdir -p "$PROJECT_DIR/decks"
mkdir -p "$PROJECT_DIR/.planning"

touch "$PROJECT_DIR/research/.gitkeep"
touch "$PROJECT_DIR/decks/.gitkeep"

# Track-specific directories
if [[ "$TRACK" == "bot" ]]; then
  mkdir -p "$PROJECT_DIR/knowledge"
  mkdir -p "$PROJECT_DIR/scripts"

  # knowledge/README.md
  cat > "$PROJECT_DIR/knowledge/README.md" <<'EOF'
# Knowledge

Place domain knowledge `.md` files here.

Each file should follow the factory knowledge template:
- 7-field YAML frontmatter
- H2 headings define chunk boundaries
- See `factory/templates/knowledge/TEMPLATE.md` for the full spec
EOF

  # Create relative symlinks to factory pipeline scripts
  # Default layout: gov-ai-dev/factory/ (repo root) contains factory/scripts/
  # Project lives at gov-ai-dev/${NAME}/
  # From ${NAME}/scripts/ -> ../../factory/factory/scripts/
  FACTORY_SCRIPTS_REL="../../factory/factory/scripts"

  # If --output-dir was overridden, try to compute relative path
  # but fall back to the default assumption
  if [[ "$OUTPUT_DIR" != "$HOME/Documents/GitHub/gov-ai-dev" ]]; then
    # Non-default output dir — symlinks will use absolute path to factory scripts
    FACTORY_SCRIPTS_REL="$FACTORY_ROOT/factory/scripts"
  fi

  ln -s "$FACTORY_SCRIPTS_REL/chunk-knowledge.js" "$PROJECT_DIR/scripts/chunk-knowledge.js"
  ln -s "$FACTORY_SCRIPTS_REL/embed-chunks.py" "$PROJECT_DIR/scripts/embed-chunks.py"
  ln -s "$FACTORY_SCRIPTS_REL/validate-knowledge.py" "$PROJECT_DIR/scripts/validate-knowledge.py"

else
  # Form track
  mkdir -p "$PROJECT_DIR/sql"
  mkdir -p "$PROJECT_DIR/src"
  touch "$PROJECT_DIR/sql/.gitkeep"
  touch "$PROJECT_DIR/src/.gitkeep"
fi

# --- Generate .planning files --------------------------------------------

# PROJECT.md
cat > "$PROJECT_DIR/.planning/PROJECT.md" <<'PROJECTMD'
# {{PROJECT_TITLE}}

## What This Is
[Describe the project]

## Core Value
[What problem this solves]

## Requirements
### Active
- [ ] [First requirement]

### Out of Scope
- [Items explicitly excluded]

## Context
**Track:** {{TRACK}}
**Schema:** {{SCHEMA_NAME}}
**Created:** {{CREATED_DATE}}

## Constraints
- Deploy to vanderdev.net VPS
- Schema: {{SCHEMA_NAME}}.document_chunks for RAG data
- Follow factory standards (see gov-ai-dev/factory/README.md)

## Key Decisions
| Decision | Rationale | Outcome |
|----------|-----------|---------|
PROJECTMD
substitute_file "$PROJECT_DIR/.planning/PROJECT.md"

# ROADMAP.md
if [[ "$TRACK" == "bot" ]]; then
  cat > "$PROJECT_DIR/.planning/ROADMAP.md" <<'EOF'
# Roadmap

Run /gsd:create-roadmap or copy from factory/templates/gsd/bot-ROADMAP.md
EOF
else
  cat > "$PROJECT_DIR/.planning/ROADMAP.md" <<'EOF'
# Roadmap

Run /gsd:create-roadmap or copy from factory/templates/gsd/form-ROADMAP.md
EOF
fi

# STATE.md
cat > "$PROJECT_DIR/.planning/STATE.md" <<'STATEMD'
# Project State

## Current Position
Phase: 0 of 9
Status: Not started
Last activity: {{CREATED_DATE}} — Project scaffolded

## Accumulated Context
### Decisions
None yet.
### Deferred Issues
None.
### Blockers/Concerns
None.
STATEMD
substitute_file "$PROJECT_DIR/.planning/STATE.md"

# config.json
cat > "$PROJECT_DIR/.planning/config.json" <<'EOF'
{
  "mode": "interactive",
  "depth": "standard",
  "gates": {
    "confirm_project": true,
    "confirm_phases": true,
    "confirm_roadmap": true,
    "confirm_breakdown": true,
    "confirm_plan": true,
    "execute_next_plan": true,
    "issues_review": true,
    "confirm_transition": true
  },
  "safety": {
    "always_confirm_destructive": true,
    "always_confirm_external_services": true
  }
}
EOF

# --- Generate CLAUDE.md from template ------------------------------------

TEMPLATE_DIR="$FACTORY_ROOT/factory/templates"
TEMPLATE_FILE="$TEMPLATE_DIR/${TRACK}-CLAUDE.md.template"

if [[ ! -f "$TEMPLATE_FILE" ]]; then
  echo "Error: Template not found: $TEMPLATE_FILE" >&2
  echo "Run this script after creating the CLAUDE.md templates." >&2
  exit 1
fi

cp "$TEMPLATE_FILE" "$PROJECT_DIR/CLAUDE.md"
substitute_file "$PROJECT_DIR/CLAUDE.md"

# --- Generate README.md --------------------------------------------------

cat > "$PROJECT_DIR/README.md" <<READMEEOF
# ${TITLE}

**Track:** ${TRACK}
**Schema:** ${NAME}
**Created:** ${CREATED_DATE}

## Overview

[Project description]

## Quick Start

1. Review \`CLAUDE.md\` for project standards
2. Run \`/gsd:create-roadmap\` to plan the build
3. Follow the factory pipeline for your track

## Factory

This project was scaffolded by [gov-ai-dev/factory](https://github.com/gov-ai-dev/factory).
See \`factory/README.md\` for shared scripts and templates.
READMEEOF

# --- Success summary ------------------------------------------------------

echo ""
echo "✓ Scaffolded ${TRACK} project: ${TITLE}"
echo "  Location: ${PROJECT_DIR}"
echo "  Next: cd ${PROJECT_DIR} && review CLAUDE.md, then /gsd:create-roadmap"
echo ""
