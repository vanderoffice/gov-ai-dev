#!/usr/bin/env python3
"""
Comprehensive URL validation script for all VanderDev bots.
Tests every URL in the database and reports broken ones.
"""

import subprocess
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.request
import urllib.error
import ssl
from typing import Tuple, Dict, List
import json

# Timeout for URL checks (seconds)
TIMEOUT = 10

def extract_urls_from_db(bot: str) -> List[str]:
    """Extract all unique URLs from a bot's database."""

    if bot == "bizbot":
        query = "SELECT DISTINCT regexp_matches(content::text, E'https?://[^\\\\s\"'')>\\\\]]+', 'g') FROM public.bizbot_documents;"
    elif bot == "kiddobot":
        query = "SELECT DISTINCT regexp_matches(chunk_text, E'https?://[^\\\\s\"'')>\\\\]]+', 'g') FROM kiddobot.document_chunks;"
    elif bot == "waterbot":
        query = "SELECT DISTINCT regexp_matches(content::text, E'https?://[^\\\\s\"'')>\\\\]]+', 'g') FROM public.waterbot_documents;"
    else:
        raise ValueError(f"Unknown bot: {bot}")

    # Use stdin pipe to avoid nested shell escaping issues
    ssh_cmd = ["ssh", "vps", "docker exec -i supabase-db psql -U postgres -d postgres -t -A"]
    result = subprocess.run(ssh_cmd, input=query, capture_output=True, text=True)

    urls = []
    for line in result.stdout.strip().split('\n'):
        # Extract URL from {url} format
        match = re.match(r'\{(.+)\}', line)
        if match:
            url = match.group(1)
            # Clean up URL - remove trailing punctuation that shouldn't be part of URL
            url = re.sub(r'[`\]\)]+$', '', url)
            urls.append(url)

    return list(set(urls))

def test_url(url: str) -> Tuple[str, int, str]:
    """Test if a URL is reachable. Returns (url, status_code, error_message)."""
    try:
        # Create SSL context that doesn't verify (to avoid cert issues affecting our tests)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
        )

        response = urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx)
        return (url, response.getcode(), "OK")

    except urllib.error.HTTPError as e:
        return (url, e.code, str(e.reason))
    except urllib.error.URLError as e:
        # This includes DNS failures
        return (url, 0, f"URLError: {str(e.reason)}")
    except Exception as e:
        return (url, 0, f"Error: {str(e)}")

def main():
    bots = ["bizbot", "kiddobot", "waterbot"]
    all_results: Dict[str, Dict] = {}

    for bot in bots:
        print(f"\n{'='*60}")
        print(f"Testing {bot.upper()} URLs...")
        print(f"{'='*60}")

        urls = extract_urls_from_db(bot)
        print(f"Found {len(urls)} unique URLs")

        results = {
            "total": len(urls),
            "ok": [],
            "redirect": [],  # 3xx
            "client_error": [],  # 4xx
            "server_error": [],  # 5xx
            "dns_error": [],  # 0 with URLError
            "other_error": []
        }

        # Test URLs in parallel
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = {executor.submit(test_url, url): url for url in urls}

            for i, future in enumerate(as_completed(futures)):
                url, status, msg = future.result()

                if status == 200:
                    results["ok"].append(url)
                elif 300 <= status < 400:
                    results["redirect"].append((url, status, msg))
                elif 400 <= status < 500:
                    results["client_error"].append((url, status, msg))
                elif status >= 500:
                    results["server_error"].append((url, status, msg))
                elif "URLError" in msg or "Name or service not known" in msg or "nodename nor servname" in msg:
                    results["dns_error"].append((url, msg))
                else:
                    results["other_error"].append((url, status, msg))

                # Progress indicator
                if (i + 1) % 50 == 0:
                    print(f"  Tested {i + 1}/{len(urls)} URLs...")

        all_results[bot] = results

        # Print summary for this bot
        print(f"\n{bot.upper()} Summary:")
        print(f"  ✅ OK (200): {len(results['ok'])}")
        print(f"  ↪️  Redirects (3xx): {len(results['redirect'])}")
        print(f"  ❌ Client Errors (4xx): {len(results['client_error'])}")
        print(f"  🔥 Server Errors (5xx): {len(results['server_error'])}")
        print(f"  🚫 DNS Failures: {len(results['dns_error'])}")
        print(f"  ⚠️  Other Errors: {len(results['other_error'])}")

        # Print broken URLs
        broken = results["client_error"] + results["server_error"] + results["dns_error"]
        if broken:
            print(f"\n  BROKEN URLs ({len(broken)}):")
            for item in broken:
                if len(item) == 2:
                    url, msg = item
                    print(f"    - {url}")
                    print(f"      Error: {msg}")
                else:
                    url, status, msg = item
                    print(f"    - {url}")
                    print(f"      Status: {status} - {msg}")

    # Save full results to JSON
    output_file = os.path.join(os.path.expanduser("~"), "Documents/GitHub/gov-ai-dev/url_validation_results.json")
    with open(output_file, 'w') as f:
        # Convert to JSON-serializable format
        json_results = {}
        for bot, data in all_results.items():
            json_results[bot] = {
                "total": data["total"],
                "ok_count": len(data["ok"]),
                "redirect_count": len(data["redirect"]),
                "client_error_count": len(data["client_error"]),
                "server_error_count": len(data["server_error"]),
                "dns_error_count": len(data["dns_error"]),
                "other_error_count": len(data["other_error"]),
                "broken_urls": [
                    {"url": item[0], "status": item[1] if len(item) > 2 else 0, "message": item[-1]}
                    for item in (data["client_error"] + data["server_error"])
                ] + [
                    {"url": item[0], "status": 0, "message": item[1]}
                    for item in data["dns_error"]
                ]
            }
        json.dump(json_results, f, indent=2)

    print(f"\n\nFull results saved to: {output_file}")

    # Final summary
    print("\n" + "="*60)
    print("OVERALL SUMMARY")
    print("="*60)

    total_broken = 0
    for bot, data in all_results.items():
        broken = len(data["client_error"]) + len(data["server_error"]) + len(data["dns_error"])
        total_broken += broken
        pct = (len(data["ok"]) / data["total"] * 100) if data["total"] > 0 else 0
        print(f"{bot.upper()}: {len(data['ok'])}/{data['total']} OK ({pct:.1f}%) - {broken} broken")

    print(f"\nTOTAL BROKEN URLs ACROSS ALL BOTS: {total_broken}")

    return 0 if total_broken == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
