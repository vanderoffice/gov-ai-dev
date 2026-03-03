#!/usr/bin/env python3
"""
Comprehensive URL fix script for VanderDev bots.
Fixes all broken URLs identified in the validation.
"""

import subprocess
import json
import os
import re
from typing import Dict, List, Tuple

# URL Replacement mappings
# Format: (old_pattern, replacement)
# Patterns are applied in order - more specific patterns first

BIZBOT_REPLACEMENTS = [
    # EDD - site restructured with /en/ prefix
    ("www.edd.ca.gov/payroll_taxes/", "edd.ca.gov/en/payroll_taxes/"),
    ("www.edd.ca.gov/about_edd/", "edd.ca.gov/en/about_edd/"),
    ("www.edd.ca.gov/disability/", "edd.ca.gov/en/disability/"),
    ("edd.ca.gov/employers/", "edd.ca.gov/en/employers/"),

    # FTB - various path changes
    ("www.ftb.ca.gov/file/business/types/index.html", "www.ftb.ca.gov/file/business/"),
    ("www.ftb.ca.gov/file/business/types/limited-liability-company/index.html", "www.ftb.ca.gov/file/business/"),
    ("www.ftb.ca.gov/file/business/types/limited-liability-company/", "www.ftb.ca.gov/file/business/"),
    ("www.ftb.ca.gov/forms/search/index.aspx", "www.ftb.ca.gov/forms/"),
    ("www.ftb.ca.gov/help/business/business-search.html", "www.ftb.ca.gov/"),
    ("www.ftb.ca.gov/help/business/entity-status-letter.html", "www.ftb.ca.gov/"),
    ("www.ftb.ca.gov/help/business/power-of-attorney.html", "www.ftb.ca.gov/"),
    ("www.ftb.ca.gov/help/business/update-business-info.html", "www.ftb.ca.gov/"),
    ("www.ftb.ca.gov/pay/business/web-pay.html", "www.ftb.ca.gov/pay/"),
    ("www.ftb.ca.gov/pay/payment-plans.html", "www.ftb.ca.gov/pay/"),
    ("www.ftb.ca.gov/about-ftb/taxpayer-rights-advocate.html", "www.ftb.ca.gov/about-ftb/"),
    ("www.ftb.ca.gov/tax-pros/law/voluntary-disclosure/index.html", "www.ftb.ca.gov/tax-pros/"),
    ("www.ftb.ca.gov/refund/index.html", "www.ftb.ca.gov/"),

    # CSLB - site restructured
    ("www.cslb.ca.gov/Applicants/Examination_Information/", "www.cslb.ca.gov/contractors/applicants/"),
    ("www.cslb.ca.gov/Applicants", "www.cslb.ca.gov/contractors/applicants/"),
    ("www.cslb.ca.gov/Licensees/Maintain_Bond_And_Insurance/", "www.cslb.ca.gov/contractors/"),
    ("www.cslb.ca.gov/Licensees/Renew_A_License.aspx", "www.cslb.ca.gov/contractors/"),
    ("www.cslb.ca.gov/Forms_Pubs", "www.cslb.ca.gov/resources/"),
    ("www.cslb.ca.gov/about_us/library/legislative_info/", "www.cslb.ca.gov/"),
    ("www.cslb.ca.gov/about_us/library/fees.aspx", "www.cslb.ca.gov/"),
    ("www.cslb.ca.gov/about_us/library/Licensing_Classifications/", "www.cslb.ca.gov/contractors/applicants/"),
    ("www.cslb.ca.gov/About_Us/Library/Licensing_Classifications/", "www.cslb.ca.gov/contractors/applicants/"),
    ("www.cslb.ca.gov/About_Us/Library/Licensing_Timeframes.aspx", "www.cslb.ca.gov/"),
    ("www.cslb.ca.gov/consumers/hire_a_contractor/handyman.aspx", "www.cslb.ca.gov/consumers/"),

    # DCA/CBA - paths changed
    ("www.dca.ca.gov/cba/applicants/education.shtml", "www.dca.ca.gov/cba/applicants/"),
    ("www.dca.ca.gov/cba/licensees/firm_registration.shtml", "www.dca.ca.gov/cba/"),
    ("www.dca.ca.gov/cba/consumers/verify_a_license.shtml", "search.dca.ca.gov"),
    ("www.dca.ca.gov/webapps/breeze/breeze_faqs.shtml", "www.breeze.ca.gov/"),
    ("www.dca.ca.gov/webapps/breeze/", "www.breeze.ca.gov/"),

    # RN Board
    ("www.rn.ca.gov/verification/", "www.rn.ca.gov/"),
    ("www.rn.ca.gov/verification.shtml", "www.rn.ca.gov/"),
    ("www.rn.ca.gov/licensees/renewal.shtml", "www.rn.ca.gov/"),
    ("www.rn.ca.gov/licensees/ce-renewal.shtml", "www.rn.ca.gov/"),
    ("www.rn.ca.gov/applicants/lic-end.shtml", "www.rn.ca.gov/"),
    ("www.rn.ca.gov/applicants/index.shtml", "www.rn.ca.gov/"),

    # BAR
    ("bar.ca.gov/Consumers/License_Status_Lookup", "bar.ca.gov/"),
    ("bar.ca.gov/Industry/Smog_Check_Stations", "bar.ca.gov/"),
    ("bar.ca.gov/Industry/Automotive_Repair_Dealer", "bar.ca.gov/"),

    # BSIS
    ("www.bsis.ca.gov/forms_pubs/guard.shtml", "www.bsis.ca.gov/"),
    ("www.bsis.ca.gov/forms_pubs/pi.shtml", "www.bsis.ca.gov/"),
    ("www.bsis.ca.gov/online_services/license_lookup.shtml", "www.bsis.ca.gov/"),

    # Other agencies
    ("www.pharmacy.ca.gov/licensees/facility/index.shtml", "www.pharmacy.ca.gov/"),
    ("www.barbercosmo.ca.gov/applicants/establishments.shtml", "www.barbercosmo.ca.gov/applicants/"),
    ("www.sfdph.org/dph/EH/", "www.sf.gov/departments/department-public-health"),
    ("cannabis.ca.gov/resources/local-jurisdiction-information/", "cannabis.ca.gov/"),

    # DNS failures - replace with working alternatives or remove
    ("www.calpipetrades.org", "www.ua.org"),  # United Association (parent org)
    ("distributecannabis.org", "cannabis.ca.gov"),
    ("www.guidedogsboard.ca.gov", "www.dca.ca.gov"),  # Defunct board
    ("calcannabis.cdfa.ca.gov", "cannabis.ca.gov"),  # CalCannabis merged
]

KIDDOBOT_REPLACEMENTS = [
    # CDE - various path changes
    ("www.cde.ca.gov/ls/ex/ast/", "www.cde.ca.gov/ls/ex/"),
    ("www.cde.ca.gov/ls/ex/asesinfo.asp", "www.cde.ca.gov/ls/ex/"),
    ("www.cde.ca.gov/ls/ex/21stcclc/", "www.cde.ca.gov/ls/ex/"),
    ("www.cde.ca.gov/sp/cd/re/cdcontractorinfo.asp", "www.cde.ca.gov/sp/cd/"),
    ("www.cde.ca.gov/sp/cd/re/hscollab.asp", "www.cde.ca.gov/sp/cd/"),
    ("www.cde.ca.gov/sp/cd/re/caelresources.asp", "www.cde.ca.gov/sp/cd/"),
    ("www.cde.ca.gov/sp/cd/ci/cspp.asp", "www.cde.ca.gov/sp/cd/"),

    # CDPH
    ("www.cdph.ca.gov/Programs/CCDPHP/DCDIC/CTCA/Pages/Local-Health-Departments.aspx", "www.cdph.ca.gov/"),
    ("www.cdph.ca.gov/Programs/CID/DCDC/Pages/Immunization-Branch.aspx", "www.cdph.ca.gov/Programs/CID/DCDC/"),
    ("www.cdph.ca.gov/Programs/CID/DCDC/Pages/Medical-Exemptions.aspx", "www.cdph.ca.gov/Programs/CID/DCDC/"),

    # CDSS
    ("cdss.ca.gov/inforesources/child-care", "www.cdss.ca.gov/inforesources/child-care-and-development"),
    ("ccld.dss.ca.gov", "www.ccld.dss.ca.gov/carefacilitysearch/"),  # Fix subdomain

    # EDD
    ("edd.ca.gov/disability/paid-family-leave/", "edd.ca.gov/en/disability/paid-family-leave/"),

    # County/local sites - replace with reliable alternatives
    ("dha.saccounty.gov", "www.saccounty.gov/Government/Departments"),
    ("www.kern.org/childcare", "www.kcoe.org"),
    ("www.sandiegocounty.gov/hhsa/programs/ssp/family_resource_centers.html", "www.sandiegocounty.gov/hhsa/"),

    # DNS failures - replace with generic alternatives
    ("cdrc-childcare.org", "rrnetwork.org/family-services/find-child-care"),
    ("www.childrensco", "www.childrenscouncil.org"),  # Truncated URL
    ("www.trintyfamilyresource.org", "rrnetwork.org/about/r-r-directory"),  # Trinity County
    ("www.delnortechildcare.org", "rrnetwork.org/about/r-r-directory"),
    ("cvchn.org", "rrnetwork.org/family-services/find-child-care"),
    ("www.ccld.dcdss.ca.gov/carefacilitysearch/", "www.ccld.dss.ca.gov/carefacilitysearch/"),  # Typo
    ("lassencfr.org", "rrnetwork.org/about/r-r-directory"),
    ("valleyoakcs.org", "www.cde.ca.gov/schooldirectory/"),
    ("sageoakcharter.org", "www.cde.ca.gov/schooldirectory/"),
    ("family-resource.org", "rrnetwork.org/family-services/find-child-care"),
    ("www.sbfamilycare.org", "rrnetwork.org/about/r-r-directory"),  # San Bernardino
    ("iceschildcare.org", "rrnetwork.org/family-services/find-child-care"),
    ("dds.ca.gov", "www.dds.ca.gov"),  # Just missing www

    # Other broken URLs
    ("sfdec.org/pfa", "sfdec.org"),
    ("hslda.org/group-finder", "hslda.org"),
    ("www.k12.com/california-virtual-academies.html", "www.k12.com"),
    ("communityinvestment.lacity.gov/early-intervention-providers-and-e", "communityinvestment.lacity.gov"),
    ("n8n.vanderdev.net/webhook/kiddobot", "vanderdev.net/kiddobot"),  # Internal link
    ("www.publichealthlawcenter.org/sites/default/files/CA%20Child%20Care", "www.publichealthlawcenter.org"),
    ("www.optionsforlearning.org/apps/pages/index.jsp?uREC_ID=4331645&type=d&pREC_ID=2533847", "www.optionsforlearning.org"),
    ("www.fullertonsd.org/departments/educational-services/early-education/preschool/california-state-preschool-program-cspp/cspp-part-day-preschool", "www.fullertonsd.org"),
    ("geocoding.geo.census.gov/geocoder/locations/addressbatch", "geocoding.geo.census.gov/geocoder/"),
]

WATERBOT_REPLACEMENTS = [
    ("www.waterboards.ca.gov/resources/email/watercomplaint.html", "www.waterboards.ca.gov/resources/"),
    ("ciwqs.waterboards.ca.gov/ciwqs/publicReports.jsp", "ciwqs.waterboards.ca.gov/"),
    ("data.ca.gov/api/3/action/datastore_search?resource_id=[RESOURCE_ID", "data.ca.gov"),  # Placeholder in content
    ("www.cdph.ca.gov/Programs/CEH/DFDCS/Pages/FDBPrograms/LocalEnvironmentalHealth.aspx", "www.cdph.ca.gov/"),
    ("www.epa.gov/npdes/npdes-form-2a-new-sources-and-new-discharges", "www.epa.gov/npdes/"),
]


def fix_urls_in_db(bot: str, replacements: List[Tuple[str, str]]) -> int:
    """Apply URL fixes to database using SQL REPLACE."""
    total_updated = 0

    if bot == "bizbot":
        table = "public.bizbot_documents"
        column = "content"
    elif bot == "kiddobot":
        table = "kiddobot.document_chunks"
        column = "chunk_text"
    elif bot == "waterbot":
        table = "public.waterbot_documents"
        column = "content"
    else:
        raise ValueError(f"Unknown bot: {bot}")

    for old_url, new_url in replacements:
        # Escape single quotes for SQL
        old_escaped = old_url.replace("'", "''")
        new_escaped = new_url.replace("'", "''")

        # Build SQL
        sql = f"""
UPDATE {table}
SET {column} = REPLACE({column}::text, '{old_escaped}', '{new_escaped}')::jsonb
WHERE {column}::text LIKE '%{old_escaped}%';
"""
        if bot == "kiddobot":
            # KiddoBot column is text, not jsonb
            sql = f"""
UPDATE {table}
SET {column} = REPLACE({column}, '{old_escaped}', '{new_escaped}')
WHERE {column} LIKE '%{old_escaped}%';
"""

        # Execute
        cmd = f'''ssh vps "docker exec -i supabase-db psql -U postgres -d postgres" <<'SQLEOF'
{sql}
SQLEOF'''

        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        # Count updates
        if "UPDATE" in result.stdout:
            match = re.search(r'UPDATE (\d+)', result.stdout)
            if match and int(match.group(1)) > 0:
                count = int(match.group(1))
                total_updated += count
                print(f"  Fixed {count} rows: {old_url} -> {new_url}")

    return total_updated


def fix_urls_in_json_files(directory: str, replacements: List[Tuple[str, str]]) -> int:
    """Fix URLs in JSON source files."""
    total_fixed = 0

    for filename in os.listdir(directory):
        if not filename.endswith('.json'):
            continue

        filepath = os.path.join(directory, filename)
        try:
            with open(filepath, 'r') as f:
                content = f.read()

            original_content = content
            for old_url, new_url in replacements:
                content = content.replace(old_url, new_url)

            if content != original_content:
                with open(filepath, 'w') as f:
                    f.write(content)
                print(f"  Updated: {filename}")
                total_fixed += 1

        except Exception as e:
            print(f"  Error processing {filename}: {e}")

    return total_fixed


def main():
    base_path = os.path.join(os.path.expanduser("~"), "Documents/GitHub/gov-ai-dev")

    print("="*60)
    print("FIXING BROKEN URLs IN VANDERDEV BOTS")
    print("="*60)

    # BizBot
    print("\n--- BIZBOT ---")
    print("Fixing database...")
    db_fixed = fix_urls_in_db("bizbot", BIZBOT_REPLACEMENTS)
    print(f"Database: {db_fixed} rows updated")

    print("Fixing JSON files...")
    json_dir = os.path.join(base_path, "rag-content/bizbot")
    if os.path.exists(json_dir):
        json_fixed = fix_urls_in_json_files(json_dir, BIZBOT_REPLACEMENTS)
        print(f"JSON files: {json_fixed} files updated")

    # KiddoBot
    print("\n--- KIDDOBOT ---")
    print("Fixing database...")
    db_fixed = fix_urls_in_db("kiddobot", KIDDOBOT_REPLACEMENTS)
    print(f"Database: {db_fixed} rows updated")

    print("Fixing JSON files...")
    json_dir = os.path.join(base_path, "rag-content/kiddobot")
    if os.path.exists(json_dir):
        json_fixed = fix_urls_in_json_files(json_dir, KIDDOBOT_REPLACEMENTS)
        print(f"JSON files: {json_fixed} files updated")

    # WaterBot
    print("\n--- WATERBOT ---")
    print("Fixing database...")
    db_fixed = fix_urls_in_db("waterbot", WATERBOT_REPLACEMENTS)
    print(f"Database: {db_fixed} rows updated")

    print("Fixing JSON files...")
    json_dir = os.path.join(base_path, "rag-content/waterbot")
    if os.path.exists(json_dir):
        json_fixed = fix_urls_in_json_files(json_dir, WATERBOT_REPLACEMENTS)
        print(f"JSON files: {json_fixed} files updated")

    print("\n" + "="*60)
    print("URL FIXES COMPLETE")
    print("="*60)
    print("\nRun test_urls_from_files.py again to verify fixes.")


if __name__ == "__main__":
    main()
