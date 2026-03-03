#!/usr/bin/env python3
"""
Comprehensive URL Validator for All Bot Knowledge Bases
Extracts URLs from markdown files and validates them with HTTP requests.

Usage: python3 scripts/validate-all-urls.py [--fix]
"""

import re
import os
import sys
import json
import asyncio
import aiohttp
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Configuration
KNOWLEDGE_DIRS = {
    'waterbot': Path(__file__).parent.parent / 'waterbot' / 'knowledge',
    'bizbot': Path(__file__).parent.parent / 'bizbot' / 'BizAssessment',
    'kiddobot': Path(__file__).parent.parent / 'kiddobot' / 'ChildCareAssessment',
}

# URL patterns to extract
URL_PATTERNS = [
    # Markdown links [text](url)
    r'\[([^\]]+)\]\(([^)]+)\)',
    # Bare URLs with https/http
    r'(?<![\(\[])(https?://[^\s\)\]<>"]+)',
    # URLs without protocol (domain.gov patterns)
    r'(?<![/\w])((?:www\.)?[a-zA-Z0-9-]+\.(?:ca\.gov|gov|org|com|net|edu)[^\s\)\]<>"]*)',
]

# Skip patterns (not real URLs)
SKIP_PATTERNS = [
    r'example\.com',
    r'placeholder',
    r'your-.*\.com',
    r'\.(png|jpg|jpeg|gif|svg|ico|pdf|doc|docx|xlsx)$',
    r'^mailto:',
    r'^tel:',
    r'^#',  # Anchor links
    r'\.md$',  # Markdown file references (e.g., County_Name.md)
    r'^https?://\d+_',  # URLs starting with numbered directories (01_Entity_Formation)
    r'^https?://[^/]+\.md',  # Domain is a .md file
    r'^https?://[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+$',  # Simple path without TLD (research-protocol/summaries)
]

# Known redirects that are fine
KNOWN_REDIRECTS = {
    'waterboards.ca.gov/safer': 'waterboards.ca.gov/drinking_water/programs/SAFER_Drinking_Water',
}


def extract_urls_from_file(filepath: Path) -> dict[str, list[str]]:
    """Extract all URLs from a markdown file with context."""
    urls = defaultdict(list)  # url -> list of contexts

    try:
        content = filepath.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return urls

    lines = content.split('\n')

    for line_num, line in enumerate(lines, 1):
        # Extract markdown links
        for match in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', line):
            link_text, url = match.groups()
            url = url.strip().strip('`')  # Strip whitespace and backticks
            # Skip relative file paths, anchors, and non-URLs
            if url and not url.startswith('#') and not url.startswith('./') and not url.startswith('../'):
                # Skip if it's clearly a relative file path (no protocol, ends in .md, or is a simple path)
                if not url.startswith(('http://', 'https://')):
                    # Skip if ends with .md or .html (relative links)
                    if url.endswith('.md') or url.endswith('.html'):
                        continue
                    # Skip if it looks like a directory path (contains / but no dots before first /)
                    if '/' in url and '.' not in url.split('/')[0]:
                        continue
                urls[url].append(f"{filepath}:{line_num}")

        # Extract bare URLs
        for match in re.finditer(r'(?<!["\(\[])(https?://[^\s\)\]<>"\']+)', line):
            url = match.group(1).rstrip('.,;:`')  # Strip trailing punctuation including backticks
            urls[url].append(f"{filepath}:{line_num}")

        # Extract domain-style references (waterboards.ca.gov/...)
        # Note: (?<![/\w@.]) includes . to prevent matching "ca.gov" inside "business.ca.gov"
        for match in re.finditer(r'(?<![/\w@.])((?:www\.)?[a-zA-Z0-9-]+\.(?:ca\.gov|gov)[^\s\)\]<>"\'`]*)', line):
            domain = match.group(1).rstrip('.,;:`')  # Strip trailing punctuation including backticks
            if not domain.startswith('http'):
                domain = f"https://{domain}"
            # Clean up common trailing issues
            domain = re.sub(r'[.,;:`]+$', '', domain)
            urls[domain].append(f"{filepath}:{line_num}")

    return urls


def should_skip_url(url: str) -> bool:
    """Check if URL should be skipped."""
    for pattern in SKIP_PATTERNS:
        if re.search(pattern, url, re.IGNORECASE):
            return True
    return False


def normalize_url(url: str) -> str:
    """Normalize URL for comparison."""
    url = url.strip().rstrip('/')
    # Add https if no protocol
    if not url.startswith(('http://', 'https://')):
        url = f"https://{url}"
    return url


async def check_url(session: aiohttp.ClientSession, url: str, semaphore: asyncio.Semaphore) -> tuple[str, int, str]:
    """Check a single URL and return (url, status_code, error_msg)."""
    async with semaphore:
        try:
            # Use HEAD first, fall back to GET
            async with session.head(url, allow_redirects=True, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                return (url, resp.status, '')
        except aiohttp.ClientResponseError as e:
            # Try GET if HEAD fails
            try:
                async with session.get(url, allow_redirects=True, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    return (url, resp.status, '')
            except Exception as e2:
                return (url, 0, str(e2))
        except asyncio.TimeoutError:
            return (url, 0, 'Timeout')
        except aiohttp.ClientConnectorError as e:
            return (url, 0, f'Connection error: {str(e)[:50]}')
        except Exception as e:
            return (url, 0, str(e)[:100])


async def validate_urls(urls: dict[str, list[str]]) -> dict:
    """Validate all URLs concurrently."""
    results = {
        'valid': [],
        'broken': [],
        'redirected': [],
        'skipped': [],
    }

    # Filter and normalize URLs
    urls_to_check = {}
    for url, sources in urls.items():
        if should_skip_url(url):
            results['skipped'].append({'url': url, 'sources': sources})
            continue
        normalized = normalize_url(url)
        if normalized not in urls_to_check:
            urls_to_check[normalized] = {'original': url, 'sources': sources}
        else:
            urls_to_check[normalized]['sources'].extend(sources)

    print(f"\nValidating {len(urls_to_check)} unique URLs...")

    # Concurrent validation with rate limiting
    semaphore = asyncio.Semaphore(20)  # Max 20 concurrent requests

    connector = aiohttp.TCPConnector(limit=20, limit_per_host=5)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 WaterBot-URLValidator/1.0'
    }

    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        tasks = [check_url(session, url, semaphore) for url in urls_to_check.keys()]

        checked = 0
        for coro in asyncio.as_completed(tasks):
            url, status, error = await coro
            checked += 1

            info = urls_to_check[url]
            result_entry = {
                'url': url,
                'original': info['original'],
                'sources': info['sources'],
                'status': status,
                'error': error
            }

            if status == 200:
                results['valid'].append(result_entry)
                print(f"[{checked}/{len(urls_to_check)}] ✓ {url[:60]}")
            elif status in (301, 302, 303, 307, 308):
                results['redirected'].append(result_entry)
                print(f"[{checked}/{len(urls_to_check)}] → {url[:60]} (redirect)")
            elif status == 0:
                results['broken'].append(result_entry)
                print(f"[{checked}/{len(urls_to_check)}] ✗ {url[:60]} - {error}")
            elif status >= 400:
                results['broken'].append(result_entry)
                print(f"[{checked}/{len(urls_to_check)}] ✗ {url[:60]} - HTTP {status}")
            else:
                results['valid'].append(result_entry)
                print(f"[{checked}/{len(urls_to_check)}] ? {url[:60]} - HTTP {status}")

    return results


def main():
    print("=" * 70)
    print("gov-ai-dev Bot Knowledge Base URL Validator")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Collect all URLs from all bots
    all_urls = defaultdict(list)
    bot_stats = {}

    for bot_name, knowledge_dir in KNOWLEDGE_DIRS.items():
        if not knowledge_dir.exists():
            print(f"\n⚠ {bot_name}: Knowledge directory not found at {knowledge_dir}")
            continue

        print(f"\n📁 Scanning {bot_name}: {knowledge_dir}")

        md_files = list(knowledge_dir.rglob('*.md'))
        print(f"   Found {len(md_files)} markdown files")

        bot_urls = defaultdict(list)
        for md_file in md_files:
            file_urls = extract_urls_from_file(md_file)
            for url, sources in file_urls.items():
                bot_urls[url].extend(sources)
                all_urls[url].extend([f"[{bot_name}] {s}" for s in sources])

        bot_stats[bot_name] = {
            'files': len(md_files),
            'unique_urls': len(bot_urls),
        }
        print(f"   Extracted {len(bot_urls)} unique URLs")

    # Summary before validation
    print(f"\n{'=' * 70}")
    print("URL EXTRACTION SUMMARY")
    print(f"{'=' * 70}")
    for bot, stats in bot_stats.items():
        print(f"  {bot}: {stats['files']} files, {stats['unique_urls']} URLs")
    print(f"\n  TOTAL UNIQUE URLs: {len(all_urls)}")

    # Validate URLs
    print(f"\n{'=' * 70}")
    print("VALIDATING URLs")
    print(f"{'=' * 70}")

    results = asyncio.run(validate_urls(all_urls))

    # Report
    print(f"\n{'=' * 70}")
    print("VALIDATION RESULTS")
    print(f"{'=' * 70}")
    print(f"  ✓ Valid:      {len(results['valid'])}")
    print(f"  → Redirected: {len(results['redirected'])}")
    print(f"  ✗ Broken:     {len(results['broken'])}")
    print(f"  ⊘ Skipped:    {len(results['skipped'])}")

    if results['broken']:
        print(f"\n{'=' * 70}")
        print("BROKEN URLs - REQUIRE FIXING")
        print(f"{'=' * 70}")
        for entry in sorted(results['broken'], key=lambda x: x['url']):
            print(f"\n✗ {entry['url']}")
            print(f"  Status: {entry['status']} | Error: {entry['error']}")
            print(f"  Found in:")
            for source in entry['sources'][:5]:  # Limit sources shown
                print(f"    - {source}")
            if len(entry['sources']) > 5:
                print(f"    ... and {len(entry['sources']) - 5} more locations")

    # Save detailed report
    report_path = Path(__file__).parent / 'url-validation-report.json'
    with open(report_path, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'valid': len(results['valid']),
                'redirected': len(results['redirected']),
                'broken': len(results['broken']),
                'skipped': len(results['skipped']),
            },
            'broken_urls': results['broken'],
            'redirected_urls': results['redirected'],
        }, f, indent=2)
    print(f"\n📄 Detailed report saved to: {report_path}")

    # Exit with error if broken URLs found
    if results['broken']:
        print(f"\n❌ VALIDATION FAILED: {len(results['broken'])} broken URLs found")
        return 1
    else:
        print(f"\n✅ VALIDATION PASSED: All URLs are valid")
        return 0


if __name__ == '__main__':
    sys.exit(main())
