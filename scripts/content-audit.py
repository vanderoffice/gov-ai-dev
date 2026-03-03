#!/usr/bin/env python3
"""
Content Quality Audit Script for gov-ai-dev Bots
Phase 2 of Bot Quality Audit project

Scans knowledge base files for potentially outdated content:
- Year references (2020-2025)
- Dollar amounts
- Percentages
- Date patterns
- Contact information
- Legislative references

Usage:
    python content-audit.py --bizbot     # Scan BizBot only
    python content-audit.py --kiddobot   # Scan KiddoBot only
    python content-audit.py --waterbot   # Scan WaterBot only
    python content-audit.py --all        # Scan all bots
    python content-audit.py --bot bizbot --summary  # Summary only

Output: scripts/content-audit-report.json
"""

import argparse
import json
import os
import re
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from typing import Optional

# Base paths
PROJECT_ROOT = Path(__file__).parent.parent
BIZBOT_PATH = PROJECT_ROOT / "bizbot" / "BizAssessment"
KIDDOBOT_PATH = PROJECT_ROOT / "kiddobot" / "ChildCareAssessment"
WATERBOT_PATH = PROJECT_ROOT / "waterbot" / "knowledge"
OUTPUT_FILE = PROJECT_ROOT / "scripts" / "content-audit-report.json"

# Current year for severity calculation
CURRENT_YEAR = datetime.now().year

# Patterns to scan for
PATTERNS = {
    "year": {
        "regex": r'\b(20[0-2][0-9])\b',
        "description": "Year reference (may be outdated)",
        "severity_func": lambda match: severity_by_year(int(match.group(1)))
    },
    "dollar_amount": {
        "regex": r'\$[\d,]+(?:\.\d{2})?(?:\s*(?:million|billion|thousand))?',
        "description": "Dollar amount (fees/costs may have changed)",
        "severity_func": lambda match: "moderate"
    },
    "percentage": {
        "regex": r'\b\d{1,3}(?:\.\d+)?%',
        "description": "Percentage statistic (may be outdated)",
        "severity_func": lambda match: "moderate"
    },
    "date_month_year": {
        "regex": r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+20[0-2][0-9]\b',
        "description": "Month/year date reference",
        "severity_func": lambda match: severity_by_date_string(match.group(0))
    },
    "effective_date": {
        "regex": r'[Ee]ffective\s+(?:(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+)?20[0-2][0-9]',
        "description": "Effective date (regulation/law timing)",
        "severity_func": lambda match: severity_by_effective_date(match.group(0))
    },
    "phone_number": {
        "regex": r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
        "description": "Phone number (contact info may have changed)",
        "severity_func": lambda match: "low"
    },
    "email_ca_gov": {
        "regex": r'[\w.+-]+@[\w-]+\.ca\.gov',
        "description": "CA.gov email address",
        "severity_func": lambda match: "low"
    },
    "assembly_bill": {
        "regex": r'\bAB\s*\d{1,4}\b',
        "description": "Assembly Bill reference",
        "severity_func": lambda match: "moderate"
    },
    "senate_bill": {
        "regex": r'\bSB\s*\d{1,4}\b',
        "description": "Senate Bill reference",
        "severity_func": lambda match: "moderate"
    },
    "chapter_ref": {
        "regex": r'\b[Cc]hapter\s+\d+(?:\.\d+)?(?:\s+of\s+the\s+[\w\s]+)?',
        "description": "Chapter reference (statute/regulation)",
        "severity_func": lambda match: "low"
    },
    "ccr_section": {
        "regex": r'\b(?:CCR|California Code of Regulations?)\s*(?:Section|§)?\s*\d+(?:\.\d+)?',
        "description": "California Code of Regulations citation",
        "severity_func": lambda match: "low"
    },
    "fiscal_year": {
        "regex": r'\bFY\s*20[0-2][0-9][-–]?(?:20)?[0-2]?[0-9]?\b',
        "description": "Fiscal year reference",
        "severity_func": lambda match: severity_by_fiscal_year(match.group(0))
    }
}

# Files/patterns to skip (test files, archives, etc.)
SKIP_PATTERNS = [
    r'/tests/',
    r'test-results',
    r'PROJECT_SUMMARY',
    r'ARCHITECTURE',
    r'README-DEPLOYMENT',
    r'MANIFEST',
    r'IMPLEMENTATION-GUIDE',
    r'/\.', # Hidden files
]

def severity_by_year(year: int) -> str:
    """Determine severity based on how old a year reference is."""
    if year < 2024:
        return "critical"
    elif year == 2024:
        return "moderate"
    elif year == 2025:
        return "low"
    else:
        return "current"

def severity_by_date_string(date_str: str) -> str:
    """Extract year from date string and determine severity."""
    year_match = re.search(r'20[0-2][0-9]', date_str)
    if year_match:
        return severity_by_year(int(year_match.group(0)))
    return "moderate"

def severity_by_effective_date(date_str: str) -> str:
    """Effective dates are often intentionally historical, mark as low unless very old."""
    year_match = re.search(r'20[0-2][0-9]', date_str)
    if year_match:
        year = int(year_match.group(0))
        if year < 2022:
            return "critical"
        elif year < 2024:
            return "moderate"
        else:
            return "low"
    return "low"

def severity_by_fiscal_year(fy_str: str) -> str:
    """Fiscal year references - extract first year and check."""
    year_match = re.search(r'20([0-2][0-9])', fy_str)
    if year_match:
        year = int("20" + year_match.group(1))
        if year < 2024:
            return "critical"
        elif year == 2024:
            return "moderate"
    return "low"

def should_skip_file(filepath: str) -> bool:
    """Check if file should be skipped based on patterns."""
    for pattern in SKIP_PATTERNS:
        if re.search(pattern, filepath):
            return True
    return False

def get_context(lines: list, line_num: int, context_lines: int = 1) -> str:
    """Get surrounding context for a match."""
    start = max(0, line_num - context_lines)
    end = min(len(lines), line_num + context_lines + 1)
    context = []
    for i in range(start, end):
        prefix = ">>>" if i == line_num else "   "
        context.append(f"{prefix} {lines[i].strip()}")
    return "\n".join(context)

def is_url_or_citation(line: str, context: str) -> bool:
    """Check if the finding is within a URL or citation reference."""
    # Check for URL patterns
    url_indicators = [
        r'https?://',           # URLs
        r'\[\^[\d_]+\]:',       # Markdown footnote definitions
        r'\[[\d_]+\]',          # Citation brackets
        r'\.pdf',               # PDF links
        r'\.html',              # HTML links
        r'\.asp',               # ASP links
        r'github\.com',         # GitHub URLs
        r'\.gov/',              # Gov site paths
    ]

    for pattern in url_indicators:
        if re.search(pattern, line, re.IGNORECASE):
            return True

    return False

def is_historical_date(line: str, pattern_type: str) -> bool:
    """Check if this is an intentionally historical date (formation, effective dates)."""
    historical_indicators = [
        r'[Ff]ormed',
        r'[Ee]stablished',
        r'[Cc]reated',
        r'[Ee]ffective\s+\d',
        r'[Ss]ince\s+\d',
        r'[Aa]s\s+of',
        r'[Ee]nacted',
        r'[Ss]igned\s+into\s+law',
    ]

    for pattern in historical_indicators:
        if re.search(pattern, line):
            return True

    return False

def scan_file(filepath: Path, bot_name: str) -> list:
    """Scan a single file for all patterns."""
    findings = []

    if should_skip_file(str(filepath)):
        return findings

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            lines = content.split('\n')
    except Exception as e:
        print(f"  Error reading {filepath}: {e}")
        return findings

    relative_path = str(filepath.relative_to(PROJECT_ROOT))

    for pattern_name, pattern_config in PATTERNS.items():
        regex = pattern_config["regex"]
        description = pattern_config["description"]
        severity_func = pattern_config["severity_func"]

        for line_num, line in enumerate(lines, start=1):
            for match in re.finditer(regex, line, re.IGNORECASE):
                matched_text = match.group(0)
                severity = severity_func(match)

                # Skip "current" severity (2026+)
                if severity == "current":
                    continue

                context = get_context(lines, line_num - 1)  # 0-indexed

                # Classify context type
                if is_url_or_citation(line, context):
                    context_type = "url_citation"
                elif is_historical_date(line, pattern_name):
                    context_type = "historical"
                else:
                    context_type = "content"

                finding = {
                    "bot": bot_name,
                    "file": relative_path,
                    "line": line_num,
                    "column": match.start() + 1,
                    "pattern_type": pattern_name,
                    "matched_text": matched_text,
                    "description": description,
                    "severity": severity,
                    "context_type": context_type,
                    "context": context
                }
                findings.append(finding)

    return findings

def scan_bot(bot_name: str, bot_path: Path) -> list:
    """Scan all markdown files in a bot's knowledge base."""
    findings = []

    if not bot_path.exists():
        print(f"  Warning: {bot_path} does not exist")
        return findings

    md_files = list(bot_path.rglob("*.md"))
    print(f"  Found {len(md_files)} markdown files")

    for filepath in md_files:
        file_findings = scan_file(filepath, bot_name)
        findings.extend(file_findings)

    return findings

def generate_summary(findings: list) -> dict:
    """Generate summary statistics from findings."""
    summary = {
        "total_findings": len(findings),
        "by_bot": defaultdict(int),
        "by_severity": defaultdict(int),
        "by_pattern": defaultdict(int),
        "by_context_type": defaultdict(int),
        "critical_files": defaultdict(int),
        "actionable_count": 0,
        "scan_timestamp": datetime.now().isoformat()
    }

    for f in findings:
        summary["by_bot"][f["bot"]] += 1
        summary["by_severity"][f["severity"]] += 1
        summary["by_pattern"][f["pattern_type"]] += 1
        summary["by_context_type"][f.get("context_type", "unknown")] += 1
        if f["severity"] == "critical":
            summary["critical_files"][f["file"]] += 1
        # Count actionable items (critical/moderate content, not citations)
        if f.get("context_type") == "content" and f["severity"] in ["critical", "moderate"]:
            summary["actionable_count"] += 1

    # Convert defaultdicts to regular dicts for JSON
    summary["by_bot"] = dict(summary["by_bot"])
    summary["by_severity"] = dict(summary["by_severity"])
    summary["by_pattern"] = dict(summary["by_pattern"])
    summary["by_context_type"] = dict(summary["by_context_type"])
    summary["critical_files"] = dict(sorted(
        summary["critical_files"].items(),
        key=lambda x: x[1],
        reverse=True
    )[:20])  # Top 20 critical files

    return summary

def print_summary(summary: dict, findings: list):
    """Print a human-readable summary."""
    print("\n" + "="*60)
    print("CONTENT AUDIT SUMMARY")
    print("="*60)

    print(f"\nTotal findings: {summary['total_findings']}")
    print(f"Actionable items: {summary.get('actionable_count', 'N/A')}")

    print("\nBy Bot:")
    for bot, count in summary["by_bot"].items():
        print(f"  {bot}: {count}")

    print("\nBy Context Type:")
    for ctx in ["content", "historical", "url_citation"]:
        count = summary["by_context_type"].get(ctx, 0)
        print(f"  {ctx}: {count}")

    print("\nBy Severity:")
    for sev in ["critical", "moderate", "low"]:
        count = summary["by_severity"].get(sev, 0)
        print(f"  {sev}: {count}")

    print("\nBy Pattern Type:")
    for pattern, count in sorted(summary["by_pattern"].items(), key=lambda x: x[1], reverse=True):
        print(f"  {pattern}: {count}")

    if summary["critical_files"]:
        print("\nTop Files with Critical Issues:")
        for filepath, count in list(summary["critical_files"].items())[:10]:
            print(f"  {filepath}: {count}")

    # Print actionable critical findings (content type only)
    actionable_critical = [f for f in findings
                          if f["severity"] == "critical"
                          and f.get("context_type") == "content"]
    if actionable_critical:
        print("\n" + "-"*60)
        print(f"ACTIONABLE CRITICAL FINDINGS ({len(actionable_critical)} items):")
        print("-"*60)
        for f in actionable_critical[:10]:
            print(f"\nFile: {f['file']}:{f['line']}")
            print(f"Type: {f['pattern_type']} - {f['matched_text']}")
            print(f"Context:\n{f['context']}")
    else:
        # If no actionable critical, show some moderate content findings
        actionable_moderate = [f for f in findings
                              if f["severity"] == "moderate"
                              and f.get("context_type") == "content"
                              and f["pattern_type"] in ["year", "dollar_amount", "percentage"]][:5]
        if actionable_moderate:
            print("\n" + "-"*60)
            print(f"SAMPLE MODERATE CONTENT FINDINGS (first 5):")
            print("-"*60)
            for f in actionable_moderate:
                print(f"\nFile: {f['file']}:{f['line']}")
                print(f"Type: {f['pattern_type']} - {f['matched_text']}")
                print(f"Context:\n{f['context']}")

def main():
    parser = argparse.ArgumentParser(description="Content Quality Audit for gov-ai-dev Bots")
    parser.add_argument("--bizbot", action="store_true", help="Scan BizBot only")
    parser.add_argument("--kiddobot", action="store_true", help="Scan KiddoBot only")
    parser.add_argument("--waterbot", action="store_true", help="Scan WaterBot only")
    parser.add_argument("--all", action="store_true", help="Scan all bots")
    parser.add_argument("--summary", action="store_true", help="Print summary only (no JSON update)")
    parser.add_argument("--output", type=str, help="Custom output file path")

    args = parser.parse_args()

    # Default to --all if no bot specified
    if not any([args.bizbot, args.kiddobot, args.waterbot, args.all]):
        args.all = True

    output_file = Path(args.output) if args.output else OUTPUT_FILE

    all_findings = []

    # Scan requested bots
    if args.bizbot or args.all:
        print("\nScanning BizBot...")
        findings = scan_bot("BizBot", BIZBOT_PATH)
        all_findings.extend(findings)
        print(f"  Found {len(findings)} potential issues")

    if args.kiddobot or args.all:
        print("\nScanning KiddoBot...")
        findings = scan_bot("KiddoBot", KIDDOBOT_PATH)
        all_findings.extend(findings)
        print(f"  Found {len(findings)} potential issues")

    if args.waterbot or args.all:
        print("\nScanning WaterBot...")
        findings = scan_bot("WaterBot", WATERBOT_PATH)
        all_findings.extend(findings)
        print(f"  Found {len(findings)} potential issues")

    # Generate summary
    summary = generate_summary(all_findings)

    # Print summary
    print_summary(summary, all_findings)

    # Save report (unless summary-only mode)
    if not args.summary:
        report = {
            "summary": summary,
            "findings": all_findings
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\nReport saved to: {output_file}")

    return all_findings

if __name__ == "__main__":
    main()
