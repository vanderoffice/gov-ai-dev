#!/usr/bin/env python3
"""
URL Validator for CA Business Licensing Database
Validates all URLs and generates health report.

Usage:
    python url_validator.py
    python url_validator.py --output-csv
"""

import requests
import csv
import sys
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

# Import URLs from create_url_database.py by extracting them
# We'll duplicate the URL data here to avoid import issues

URLS_TO_VALIDATE = [
    # Secretary of State
    "https://www.sos.ca.gov/",
    "https://www.sos.ca.gov/business-programs",
    "https://bizfileonline.sos.ca.gov/",
    "https://bizfileonline.sos.ca.gov/search/business",
    "https://www.sos.ca.gov/business-programs/business-entities/starting-business",
    "https://www.sos.ca.gov/business-programs/business-entities/statements",
    "https://www.sos.ca.gov/business-programs/business-entities/name-reservations",
    "https://www.sos.ca.gov/business-programs/business-entities/forms",
    "https://bpd.cdn.sos.ca.gov/pdf/be-fee-schedule-062018.pdf",
    "https://www.sos.ca.gov/business-programs/ucc",
    "https://www.sos.ca.gov/business-programs/ts",
    "https://calicodev.sos.ca.gov/",
    "https://www.sos.ca.gov/business-programs/business-entities/processing-dates",
    "https://www.sos.ca.gov/business-programs/business-entities/faqs",
    "https://www.sos.ca.gov/business-programs/business-entities/contact",

    # Franchise Tax Board
    "https://www.ftb.ca.gov/",
    "https://www.ftb.ca.gov/myftb/index.asp",
    "https://www.ftb.ca.gov/file/business/index.html",
    "https://www.ftb.ca.gov/file/business/types/corporations/index.html",
    "https://www.ftb.ca.gov/file/business/types/limited-liability-company/index.html",
    "https://www.ftb.ca.gov/file/business/types/partnerships/index.html",
    "https://www.ftb.ca.gov/pay/index.html",
    "https://www.ftb.ca.gov/forms/index.html",
    "https://www.ftb.ca.gov/file/business/credits/index.html",
    "https://www.ftb.ca.gov/help/contact/index.html",

    # EDD
    "https://edd.ca.gov/",
    "https://edd.ca.gov/en/Payroll_Taxes/",
    "https://eddservices.edd.ca.gov/",
    "https://edd.ca.gov/en/Payroll_Taxes/Am_I_Required_to_Register_as_an_Employer/",
    "https://edd.ca.gov/en/Payroll_Taxes/Forms_and_Publications/",
    "https://edd.ca.gov/en/Payroll_Taxes/Rates_and_Withholding/",
    "https://edd.ca.gov/en/Payroll_Taxes/File_and_Pay/",
    "https://edd.ca.gov/en/Payroll_Taxes/New_Hire_Reporting/",
    "https://edd.ca.gov/en/Payroll_Taxes/Independent_Contractor_versus_Employee/",
    "https://edd.ca.gov/en/about_edd/contact_edd/",

    # CDTFA
    "https://cdtfa.ca.gov/",
    "https://cdtfa.ca.gov/services/",
    "https://cdtfa.ca.gov/services/registration.htm",
    "https://cdtfa.ca.gov/taxes-and-fees/sutprograms.htm",
    "https://maps.cdtfa.ca.gov/",
    "https://services.cdtfa.ca.gov/webservices/verification.jsp",
    "https://cdtfa.ca.gov/Industry/cannabis/",
    "https://cdtfa.ca.gov/taxes-and-fees/cigarette-and-tobacco-products/",
    "https://cdtfa.ca.gov/formspubs/",
    "https://cdtfa.ca.gov/contact.htm",

    # DCA Main
    "https://www.dca.ca.gov/",
    "https://www.breeze.ca.gov/",
    "https://search.dca.ca.gov/",
    "https://www.dca.ca.gov/about_us/entities.shtml",
    "https://www.dca.ca.gov/consumers/complaints/index.shtml",
    "https://www.dca.ca.gov/consumers/index.shtml",

    # DCA Boards
    "https://www.cslb.ca.gov/",
    "https://www.cslb.ca.gov/onlineservices/",
    "https://www.cslb.ca.gov/about_us/library/licensing_classifications/",
    "https://www.cslb.ca.gov/consumers/license_check.aspx",
    "https://www.rn.ca.gov/",
    "https://www.rn.ca.gov/online/verify.shtml",
    "https://www.rn.ca.gov/applicants/index.shtml",
    "https://www.mbc.ca.gov/",
    "https://www.mbc.ca.gov/License-Verification/",
    "https://www.mbc.ca.gov/Licensing/",
    "https://www.dca.ca.gov/cba/",
    "https://www.dca.ca.gov/cba/applicants/",
    "https://bar.ca.gov/",
    "https://bar.ca.gov/Industry/ard/How_to_Become_Licensed",
    "https://bar.ca.gov/Industry/smog/How_to_Become_Licensed",
    "https://www.pharmacy.ca.gov/",
    "https://www.dbc.ca.gov/",
    "https://www.barbercosmo.ca.gov/",
    "https://www.bsis.ca.gov/",
    "https://www.cab.ca.gov/",
    "https://www.bpelsg.ca.gov/",
    "https://www.vmb.ca.gov/",
    "https://www.brea.ca.gov/",
    "https://www.cfb.ca.gov/",
    "https://www.ptbc.ca.gov/",
    "https://www.psychology.ca.gov/",
    "https://www.bbs.ca.gov/",
    "https://www.rcb.ca.gov/",
    "https://www.acupuncture.ca.gov/",
    "https://www.optometry.ca.gov/",
    "https://www.pab.ca.gov/",
    "https://www.pmbc.ca.gov/",
    "https://www.pestboard.ca.gov/",
    "https://www.courtreportersboard.ca.gov/",
    "https://www.chiro.ca.gov/",
    "https://www.ombc.ca.gov/",
    "https://www.dhbc.ca.gov/",
    "https://www.bvnpt.ca.gov/",
    "https://www.slpab.ca.gov/",
    "https://www.bot.ca.gov/",
    "https://www.fiduciary.ca.gov/",
    "https://bhgs.dca.ca.gov/",
    "https://www.dca.ca.gov/csac/",
    "https://www.bppe.ca.gov/",

    # ABC
    "https://www.abc.ca.gov/",
    "https://services.abc.ca.gov/",
    "https://www.abc.ca.gov/licensing/license-types/",
    "https://www.abc.ca.gov/licensing/license-lookup/",
    "https://www.abc.ca.gov/licensing/apply-for-a-new-license/",
    "https://www.abc.ca.gov/licensing/license-fees/",
    "https://www.abc.ca.gov/licensing/license-forms/",
    "https://www.abc.ca.gov/education/rbs/",
    "https://www.abc.ca.gov/contact/district-offices/",

    # DCC
    "https://cannabis.ca.gov/",
    "https://cannabis.ca.gov/applicants/license-types/",
    "https://cannabis.ca.gov/applicants/how-to-apply/",
    "https://search.cannabis.ca.gov/",
    "https://cannabis.ca.gov/applicants/application-license-fees/",
    "https://cannabis.ca.gov/licensees/track-and-trace/",
    "https://cannabis.ca.gov/applicants/ceqa-review-for-cannabis-businesses/",
    "https://cannabis.ca.gov/cannabis-laws/dcc-regulations/",
    "https://cannabis.ca.gov/about-us/contact-us/",

    # DRE
    "https://www.dre.ca.gov/",
    "https://secure.dre.ca.gov/",
    "https://pplinfo2.dre.ca.gov/",
    "https://www.dre.ca.gov/examinees/requirementssales.html",
    "https://www.dre.ca.gov/examinees/requirementsbroker.html",
    "https://www.dre.ca.gov/licensees/cerequirements.html",
    "https://www.dre.ca.gov/licensees/fees.html",
    "https://www.dre.ca.gov/forms/",
    "https://www.dre.ca.gov/contact.html",

    # CDI
    "https://www.insurance.ca.gov/",
    "https://www.insurance.ca.gov/0200-industry/",
    "https://cdicloud.insurance.ca.gov/cal",
    "https://www.insurance.ca.gov/0200-industry/0010-producer-online-services/",
    "https://www.insurance.ca.gov/0200-industry/0010-producer-online-services/0200-exam-info/",
    "https://www.insurance.ca.gov/0200-industry/0050-renew-license/",
    "https://www.insurance.ca.gov/01-consumers/101-help/",

    # CDFA
    "https://www.cdfa.ca.gov/",
    "https://www.cdfa.ca.gov/ahfss/",
    "https://www.cdfa.ca.gov/is/",
    "https://www.cdfa.ca.gov/plant/",
    "https://www.cdfa.ca.gov/dms/",
    "https://www.cdfa.ca.gov/is/ffldrs/",
    "https://www.cdfa.ca.gov/plant/pe/nursery/",
    "https://www.cdfa.ca.gov/is/organicprogram/",
    "https://www.cdfa.ca.gov/plant/industrialhemp/",
    "https://www.cdfa.ca.gov/exec/county/countymap/",

    # DIR
    "https://www.dir.ca.gov/",
    "https://www.dir.ca.gov/dosh/",
    "https://www.dir.ca.gov/dosh/permits.html",
    "https://www.dir.ca.gov/dosh/esd/elevator-permits.html",
    "https://www.dir.ca.gov/dosh/esd/pressure-vessel-permits.html",
    "https://www.dir.ca.gov/dosh/amusement-rides.html",
    "https://www.dir.ca.gov/dlse/",
    "https://www.dir.ca.gov/dlse/FarmLaborContractor.html",
    "https://www.dir.ca.gov/public-works/public-works.html",
    "https://www.dir.ca.gov/public-works/contractor-registration.html",
    "https://www.dir.ca.gov/das/",
    "https://www.dir.ca.gov/dwc/",

    # CARB
    "https://ww2.arb.ca.gov/",
    "https://arber.arb.ca.gov/",
    "https://ww2.arb.ca.gov/our-work/programs/truck-and-bus-regulation",
    "https://ssl.arb.ca.gov/trucrs_reporting/login.php",
    "https://ww2.arb.ca.gov/our-work/programs/portable-equipment-registration-program-perp",
    "https://cleantruckcheck.arb.ca.gov/",
    "https://ww2.arb.ca.gov/our-work/programs/cap-and-trade-program/about",
    "https://ww2.arb.ca.gov/our-work/programs/low-carbon-fuel-standard",
    "https://ww2.arb.ca.gov/california-air-districts",

    # Water Boards
    "https://www.waterboards.ca.gov/",
    "https://smarts.waterboards.ca.gov/smarts/faces/SwSmartsLogin.xhtml",
    "https://www.waterboards.ca.gov/water_issues/programs/stormwater/",
    "https://www.waterboards.ca.gov/water_issues/programs/stormwater/igp.html",
    "https://www.waterboards.ca.gov/water_issues/programs/stormwater/construction.html",
    "https://www.waterboards.ca.gov/ust/",
    "https://www.waterboards.ca.gov/drinking_water/",
    "https://www.waterboards.ca.gov/northcoast/",
    "https://www.waterboards.ca.gov/sanfranciscobay/",
    "https://www.waterboards.ca.gov/centralcoast/",
    "https://www.waterboards.ca.gov/losangeles/",
    "https://www.waterboards.ca.gov/centralvalley/",
    "https://www.waterboards.ca.gov/lahontan/",
    "https://www.waterboards.ca.gov/coloradoriver/",
    "https://www.waterboards.ca.gov/santaana/",
    "https://www.waterboards.ca.gov/sandiego/",

    # DTSC
    "https://dtsc.ca.gov/",
    "https://dtsc.ca.gov/permits/",
    "https://dtsc.ca.gov/generators/",
    "https://hwts.dtsc.ca.gov/",
    "https://www.envirostor.dtsc.ca.gov/public/",
    "https://evq.dtsc.ca.gov/Register.aspx",
    "https://dtsc.ca.gov/scp/safer-consumer-products-program-overview/",
    "https://dtsc.ca.gov/site-mitigation/",
    "https://dtsc.ca.gov/dtsc-laws-regulations/",
    "https://dtsc.ca.gov/contact-information-3/",

    # Air Districts
    "https://www.aqmd.gov/",
    "https://www.aqmd.gov/home/permits",
    "https://www.baaqmd.gov/",
    "https://www.baaqmd.gov/permits",
    "https://www.valleyair.org/",
    "https://www.valleyair.org/permits/",
    "https://www.airquality.org/",
    "https://www.sdapcd.org/",
    "https://www.vcapcd.org/",
    "https://www.ourair.org/",
    "https://www.mbard.org/",
    "https://www.icapcd.org/",
    "https://www.mdaqmd.ca.gov/",
    "https://www.avaqmd.ca.gov/",
    "https://www.gbuapcd.org/",
    "https://www.placer.ca.gov/2137/Air-Pollution-Control-District",
    "https://www.edcgov.us/Government/aqmd",
    "https://www.ysaqmd.org/",
    "https://bcaqmd.org/",
    "https://www.co.shasta.ca.us/index/aq_index",
    "https://www.tehamacounty.ca.gov/government/departments/environmental-health/air-pollution-control-district",
    "https://www.mendocinoapcd.org/",
    "https://lakeaqmd.org/",
    "https://ncuaqmd.org/",
    "https://www.slocleanair.org/",
    "https://www.kernair.org/",
    "https://www.fraqmd.org/",

    # GO-Biz & CalOSBA
    "https://business.ca.gov/",
    "https://www.calgold.ca.gov/",
    "https://business.ca.gov/advantages/permit-and-regulatory-assistance/",
    "https://business.ca.gov/california-competes-tax-credit/",
    "https://business.ca.gov/advantages/incentives-grants-and-financing/",
    "https://business.ca.gov/resources/international-affairs-and-trade/",
    "https://business.ca.gov/about/contact-us/",
    "https://calosba.ca.gov/",
    "https://calosba.ca.gov/for-small-businesses-and-non-profits/",
    "https://calosba.ca.gov/for-small-businesses-and-non-profits/small-business-centers/",
    "https://calosba.ca.gov/funding-grants-incentives/",
    "https://calosba.ca.gov/for-small-businesses-and-non-profits/permits-licenses-regulation/",
    "https://calosba.ca.gov/for-small-businesses-and-non-profits/set-up-your-business-in-california/",
    "https://outsmartdisaster.calosba.ca.gov/",
    "https://calosba.ca.gov/about/contact-us/",
]

def check_url(url, timeout=15):
    """Check a single URL and return status."""
    result = {
        'url': url,
        'status_code': None,
        'is_healthy': False,
        'redirect': False,
        'final_url': url,
        'error': None,
        'response_time_ms': None,
        'checked_at': datetime.now().isoformat()
    }

    try:
        start = time.time()
        response = requests.head(url, timeout=timeout, allow_redirects=True,
                                headers={'User-Agent': 'Mozilla/5.0 (compatible; URLValidator/1.0)'})
        elapsed = (time.time() - start) * 1000

        result['status_code'] = response.status_code
        result['response_time_ms'] = round(elapsed, 2)
        result['final_url'] = response.url
        result['redirect'] = url != response.url
        result['is_healthy'] = response.status_code < 400

        # If HEAD fails, try GET
        if response.status_code >= 400:
            response = requests.get(url, timeout=timeout, allow_redirects=True,
                                   headers={'User-Agent': 'Mozilla/5.0 (compatible; URLValidator/1.0)'})
            result['status_code'] = response.status_code
            result['is_healthy'] = response.status_code < 400

    except requests.exceptions.Timeout:
        result['error'] = 'Timeout'
    except requests.exceptions.SSLError as e:
        result['error'] = f'SSL Error: {str(e)[:50]}'
    except requests.exceptions.ConnectionError as e:
        result['error'] = f'Connection Error: {str(e)[:50]}'
    except Exception as e:
        result['error'] = f'{type(e).__name__}: {str(e)[:50]}'

    return result

def validate_all_urls(urls, max_workers=10):
    """Validate all URLs in parallel."""
    results = []
    total = len(urls)

    print(f"\nValidating {total} URLs...")
    print("=" * 60)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(check_url, url): url for url in urls}

        for i, future in enumerate(as_completed(future_to_url), 1):
            url = future_to_url[future]
            try:
                result = future.result()
                results.append(result)

                # Print progress
                status = "OK" if result['is_healthy'] else "FAIL"
                status_code = result['status_code'] or "ERR"
                domain = urlparse(url).netloc[:30]
                print(f"[{i:3d}/{total}] {status:4s} {status_code:>3} {domain}")

            except Exception as e:
                print(f"[{i:3d}/{total}] ERROR checking {url}: {e}")
                results.append({
                    'url': url,
                    'status_code': None,
                    'is_healthy': False,
                    'error': str(e),
                    'checked_at': datetime.now().isoformat()
                })

    return results

def generate_report(results):
    """Generate summary report."""
    total = len(results)
    healthy = sum(1 for r in results if r['is_healthy'])
    unhealthy = total - healthy
    redirects = sum(1 for r in results if r.get('redirect'))
    errors = sum(1 for r in results if r.get('error'))

    print("\n" + "=" * 60)
    print("VALIDATION REPORT")
    print("=" * 60)
    print(f"Total URLs checked: {total}")
    print(f"Healthy (2xx/3xx):  {healthy} ({100*healthy/total:.1f}%)")
    print(f"Unhealthy (4xx/5xx/Error): {unhealthy} ({100*unhealthy/total:.1f}%)")
    print(f"Redirects detected: {redirects}")
    print(f"Connection errors:  {errors}")

    if unhealthy > 0:
        print("\n" + "-" * 60)
        print("UNHEALTHY URLs:")
        print("-" * 60)
        for r in results:
            if not r['is_healthy']:
                status = r.get('status_code') or 'ERR'
                error = r.get('error', '')
                print(f"  [{status}] {r['url']}")
                if error:
                    print(f"       Error: {error}")

    if redirects > 0:
        print("\n" + "-" * 60)
        print("REDIRECTED URLs:")
        print("-" * 60)
        for r in results:
            if r.get('redirect'):
                print(f"  {r['url']}")
                print(f"    -> {r['final_url']}")

    return {
        'total': total,
        'healthy': healthy,
        'unhealthy': unhealthy,
        'redirects': redirects,
        'errors': errors,
        'health_percentage': round(100 * healthy / total, 2)
    }

def save_to_csv(results, filename):
    """Save results to CSV file."""
    fieldnames = ['url', 'status_code', 'is_healthy', 'redirect', 'final_url',
                  'response_time_ms', 'error', 'checked_at']

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            row = {k: r.get(k, '') for k in fieldnames}
            writer.writerow(row)

    print(f"\nResults saved to: {filename}")

def main():
    print("=" * 60)
    print("CA Business Licensing URL Validator")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Remove duplicates while preserving order
    urls = list(dict.fromkeys(URLS_TO_VALIDATE))
    print(f"Unique URLs to validate: {len(urls)}")

    # Validate
    results = validate_all_urls(urls)

    # Generate report
    summary = generate_report(results)

    # Save to CSV if requested
    if '--output-csv' in sys.argv:
        csv_path = os.path.join(os.path.expanduser("~"), "Documents/GitHub/gov-ai-dev/bizbot/BizAssessment/url_validation_results.csv")
        save_to_csv(results, csv_path)

    # Return exit code based on health
    if summary['health_percentage'] >= 95:
        print(f"\n[PASS] URL database is healthy ({summary['health_percentage']}%)")
        return 0
    else:
        print(f"\n[WARN] URL database needs attention ({summary['health_percentage']}% healthy)")
        return 1

if __name__ == '__main__':
    sys.exit(main())
