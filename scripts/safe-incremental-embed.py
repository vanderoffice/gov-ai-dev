#!/usr/bin/env python3
"""
Safe Incremental Embedding Update Script
gov-ai-dev Phase 1.4 - URL Remediation Re-embedding

Features:
- Surgical updates (only affected chunks)
- Built-in verification at each step
- Automatic abort on failure
- Rollback instructions provided

Usage:
    export OPENAI_API_KEY='your-key'
    python scripts/safe-incremental-embed.py --dry-run     # Preview only
    python scripts/safe-incremental-embed.py --bizbot      # Update BizBot only
    python scripts/safe-incremental-embed.py --kiddobot    # Update KiddoBot only
    python scripts/safe-incremental-embed.py --all         # Update both

Backups at: .backups/2026-01-20/
"""

import os
import sys
import json
import hashlib
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Check dependencies
try:
    import openai
    import psycopg2
    from psycopg2.extras import execute_values
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install openai psycopg2-binary")
    sys.exit(1)

# Configuration
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
BACKUP_DIR = PROJECT_ROOT / ".backups" / "2026-01-20"

# VPS Database (all bots are here) - via SSH tunnel
# Tunnel: ssh -fN -L 5433:172.18.0.3:5432 root@100.111.63.3
DB_CONFIG = {
    "host": "localhost",  # Via SSH tunnel to Docker network
    "port": 5433,
    "database": "postgres",
    "user": "postgres",
    "password": "2LofmsGNMYUfgF6bGPoFmdcU6M4"
}

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMS = 1536

# URLs that were fixed (old -> new)
URL_FIXES = {
    "eddservices.edd.ca.gov": "edd.ca.gov/en/employers",
    "forms/search/index.aspx": "forms/search/",
    "pay/business/web-pay.html": "pay/bank-account/index.asp",
    "pay/payment-plans.html": "pay/payment-plans/index.asp",
    "refund/index.html": "refund/index.asp",
    "help/business/entity-status-letter.html": "help/business/entity-status-letter.asp",
    "help/business/power-of-attorney.html": "tax-pros/power-of-attorney/index.html",
    "about-ftb/taxpayer-rights-advocate.html": "help/disagree-or-resolve-an-issue/taxpayer-advocate-services.html",
    "tax-pros/law/voluntary-disclosure/index.html": "tax-pros/law/index.html",
    "help/business/update-business-info.html": "help/contact/index.html",
    "help/business/business-search.html": "help/business/entity-status-letter.asp",
}

# KiddoBot files that were modified
KIDDOBOT_MODIFIED_FILES = [
    "CCDF_Overview.md",
    "CalWORKs_Application_Flowchart.md",
    "SF_Bay_Area.md",
    "Sacramento.md",
    "San_Diego.md",
    "Employer_Benefits.md",
    "All_58_Counties_RR_Directory.md",
]


class VerificationError(Exception):
    """Raised when a verification check fails."""
    pass


def get_db_connection():
    """Get PostgreSQL connection to VPS."""
    return psycopg2.connect(**DB_CONFIG)


def get_openai_client():
    """Get OpenAI client."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable required")
    return openai.OpenAI(api_key=api_key)


def verify_no_broken_urls(conn, table: str, schema: str = "public", content_col: str = "content") -> bool:
    """Verify no broken URLs remain in the table."""
    cur = conn.cursor()

    broken_patterns = list(URL_FIXES.keys())
    conditions = " OR ".join([f"{content_col} LIKE '%{pat}%'" for pat in broken_patterns])

    query = f"""
        SELECT COUNT(*) FROM {schema}.{table}
        WHERE {conditions}
    """
    cur.execute(query)
    count = cur.fetchone()[0]
    cur.close()

    if count > 0:
        raise VerificationError(f"Found {count} chunks with broken URLs in {schema}.{table}")

    print(f"  ✓ No broken URLs in {schema}.{table}")
    return True


def verify_no_nulls(conn, table: str, schema: str = "public", content_col: str = "content") -> bool:
    """Verify no NULL content or embeddings."""
    cur = conn.cursor()

    query = f"""
        SELECT
            SUM(CASE WHEN {content_col} IS NULL THEN 1 ELSE 0 END) as null_content,
            SUM(CASE WHEN embedding IS NULL THEN 1 ELSE 0 END) as null_embedding
        FROM {schema}.{table}
    """
    cur.execute(query)
    null_content, null_embedding = cur.fetchone()
    cur.close()

    if null_content > 0:
        raise VerificationError(f"Found {null_content} NULL content rows in {schema}.{table}")
    if null_embedding > 0:
        raise VerificationError(f"Found {null_embedding} NULL embedding rows in {schema}.{table}")

    print(f"  ✓ No NULL values in {schema}.{table}")
    return True


def verify_no_duplicates(conn, table: str, schema: str = "public", content_col: str = "content") -> bool:
    """Verify no duplicate content."""
    cur = conn.cursor()

    query = f"""
        SELECT COUNT(*) - COUNT(DISTINCT md5({content_col}::text)) as duplicates
        FROM {schema}.{table}
    """
    cur.execute(query)
    duplicates = cur.fetchone()[0]
    cur.close()

    if duplicates > 0:
        raise VerificationError(f"Found {duplicates} duplicate chunks in {schema}.{table}")

    print(f"  ✓ No duplicates in {schema}.{table}")
    return True


def verify_embedding_dims(conn, table: str, schema: str = "public") -> bool:
    """Verify all embeddings have correct dimensions."""
    cur = conn.cursor()

    query = f"""
        SELECT vector_dims(embedding) as dims, COUNT(*) as count
        FROM {schema}.{table}
        WHERE embedding IS NOT NULL
        GROUP BY vector_dims(embedding)
    """
    cur.execute(query)
    results = cur.fetchall()
    cur.close()

    for dims, count in results:
        if dims != EMBEDDING_DIMS:
            raise VerificationError(
                f"Found {count} embeddings with wrong dimensions ({dims}) in {schema}.{table}"
            )

    print(f"  ✓ All embeddings are {EMBEDDING_DIMS} dimensions in {schema}.{table}")
    return True


def verify_row_count(conn, table: str, schema: str = "public",
                     expected_min: int = 0, expected_max: int = 999999) -> int:
    """Verify row count is within expected range."""
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM {schema}.{table}")
    count = cur.fetchone()[0]
    cur.close()

    if count < expected_min or count > expected_max:
        raise VerificationError(
            f"Row count {count} outside expected range [{expected_min}, {expected_max}] in {schema}.{table}"
        )

    print(f"  ✓ Row count {count} in {schema}.{table}")
    return count


def run_all_verifications(conn, table: str, schema: str = "public",
                          content_col: str = "content",
                          expected_min: int = 0, expected_max: int = 999999) -> bool:
    """Run all verification checks."""
    print(f"\nRunning verifications for {schema}.{table}...")

    verify_no_broken_urls(conn, table, schema, content_col)
    verify_no_nulls(conn, table, schema, content_col)
    verify_no_duplicates(conn, table, schema, content_col)
    verify_embedding_dims(conn, table, schema)
    verify_row_count(conn, table, schema, expected_min, expected_max)

    print(f"✓ All verifications passed for {schema}.{table}\n")
    return True


def embed_texts(client: openai.OpenAI, texts: List[str]) -> List[List[float]]:
    """Generate embeddings for texts."""
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
        dimensions=EMBEDDING_DIMS
    )
    return [item.embedding for item in response.data]


def update_bizbot_surgical(conn, client: openai.OpenAI, dry_run: bool = False) -> int:
    """
    Surgical update of BizBot chunks with broken URLs.
    Only updates the specific chunks that contain broken URLs.
    """
    print("\n" + "="*60)
    print("BizBot Surgical Update")
    print("="*60)

    cur = conn.cursor()

    # Find chunks with broken URLs
    broken_patterns = list(URL_FIXES.keys())
    conditions = " OR ".join([f"content LIKE '%{pat}%'" for pat in broken_patterns])

    cur.execute(f"""
        SELECT id, content FROM public.bizbot_documents
        WHERE {conditions}
    """)
    affected_chunks = cur.fetchall()

    print(f"Found {len(affected_chunks)} chunks with broken URLs")

    if len(affected_chunks) == 0:
        print("No chunks need updating!")
        cur.close()
        return 0

    if dry_run:
        print("\n[DRY RUN] Would update these chunks:")
        for chunk_id, content in affected_chunks:
            preview = content[:100].replace('\n', ' ')
            print(f"  ID {chunk_id}: {preview}...")
        cur.close()
        return len(affected_chunks)

    # Update content with fixed URLs
    updated_chunks = []
    for chunk_id, content in affected_chunks:
        new_content = content
        for old_url, new_url in URL_FIXES.items():
            new_content = new_content.replace(old_url, new_url)
        updated_chunks.append((chunk_id, new_content))

    # Generate new embeddings
    print(f"Generating embeddings for {len(updated_chunks)} chunks...")
    texts = [content for _, content in updated_chunks]
    embeddings = embed_texts(client, texts)

    # Update database
    print("Updating database...")
    for (chunk_id, new_content), embedding in zip(updated_chunks, embeddings):
        cur.execute("""
            UPDATE public.bizbot_documents
            SET content = %s, embedding = %s::vector
            WHERE id = %s
        """, (new_content, str(embedding), chunk_id))

    conn.commit()
    cur.close()

    print(f"✓ Updated {len(updated_chunks)} chunks")

    # Run verifications
    run_all_verifications(conn, "bizbot_documents", "public", "content", 400, 450)

    return len(updated_chunks)


def chunk_markdown(text: str, max_chunk_size: int = 800) -> List[str]:
    """
    Split markdown text into chunks, respecting section boundaries.
    Chunks on ## headers, with fallback splitting for large sections.
    """
    import re

    # Split on ## headers (keep the header with its content)
    sections = re.split(r'(?=^## )', text, flags=re.MULTILINE)

    chunks = []
    for section in sections:
        section = section.strip()
        if not section:
            continue

        # If section is small enough, keep it whole
        if len(section) <= max_chunk_size:
            chunks.append(section)
        else:
            # Split large sections on ### subheaders or paragraphs
            subsections = re.split(r'(?=^### )', section, flags=re.MULTILINE)

            current_chunk = ""
            for subsec in subsections:
                subsec = subsec.strip()
                if not subsec:
                    continue

                if len(current_chunk) + len(subsec) + 2 <= max_chunk_size:
                    current_chunk = (current_chunk + "\n\n" + subsec).strip()
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    # If subsection itself is too large, split on paragraphs
                    if len(subsec) > max_chunk_size:
                        paragraphs = subsec.split('\n\n')
                        para_chunk = ""
                        for para in paragraphs:
                            if len(para_chunk) + len(para) + 2 <= max_chunk_size:
                                para_chunk = (para_chunk + "\n\n" + para).strip()
                            else:
                                if para_chunk:
                                    chunks.append(para_chunk)
                                para_chunk = para
                        if para_chunk:
                            chunks.append(para_chunk)
                        current_chunk = ""
                    else:
                        current_chunk = subsec

            if current_chunk:
                chunks.append(current_chunk)

    return chunks


def find_source_file(filename: str) -> Optional[Path]:
    """Find the source file path for a given filename."""
    kiddobot_dir = PROJECT_ROOT / "kiddobot"
    matches = list(kiddobot_dir.rglob(filename))

    # Prefer specific paths if multiple matches
    if len(matches) > 1:
        # Prioritize ChildCareAssessment over county_variations
        for match in matches:
            if "county_variations" not in str(match):
                return match

    return matches[0] if matches else None


def update_kiddobot_incremental(conn, client: openai.OpenAI, dry_run: bool = False) -> int:
    """
    Incremental update of KiddoBot chunks from modified files.
    Deletes chunks from modified files and re-inserts with new embeddings.
    """
    print("\n" + "="*60)
    print("KiddoBot Incremental Update")
    print("="*60)

    cur = conn.cursor()

    # Get current chunk counts for modified files
    placeholders = ",".join(["%s"] * len(KIDDOBOT_MODIFIED_FILES))
    cur.execute(f"""
        SELECT file_name, COUNT(*) as chunks
        FROM kiddobot.document_chunks
        WHERE file_name IN ({placeholders})
        GROUP BY file_name
    """, KIDDOBOT_MODIFIED_FILES)

    current_counts = dict(cur.fetchall())
    total_current = sum(current_counts.values())

    print(f"Found {total_current} existing chunks from {len(current_counts)} modified files:")
    for fname, count in sorted(current_counts.items()):
        print(f"  {fname}: {count} chunks")

    # Find and chunk source files
    file_chunks = {}
    for fname in KIDDOBOT_MODIFIED_FILES:
        source_path = find_source_file(fname)
        if source_path:
            content = source_path.read_text()
            chunks = chunk_markdown(content)
            file_chunks[fname] = {
                'path': source_path,
                'chunks': chunks,
                'relative_path': str(source_path.relative_to(PROJECT_ROOT))
            }
            print(f"  {fname}: {len(chunks)} new chunks from {source_path.name}")
        else:
            print(f"  ⚠️ {fname}: source file not found!")

    total_new = sum(len(fc['chunks']) for fc in file_chunks.values())
    print(f"\nTotal: {total_current} existing → {total_new} new chunks")

    if dry_run:
        print("\n[DRY RUN] Would:")
        print(f"  1. Delete {total_current} existing chunks")
        print(f"  2. Generate embeddings for {total_new} new chunks")
        print(f"  3. Insert {total_new} new chunks")
        cur.close()
        return total_new

    # Get existing metadata for category/subcategory inference
    cur.execute(f"""
        SELECT DISTINCT file_name, category, subcategory
        FROM kiddobot.document_chunks
        WHERE file_name IN ({placeholders})
    """, KIDDOBOT_MODIFIED_FILES)
    file_metadata = {row[0]: {'category': row[1], 'subcategory': row[2]} for row in cur.fetchall()}

    # Delete existing chunks for modified files
    print(f"\nDeleting {total_current} existing chunks...")
    cur.execute(f"""
        DELETE FROM kiddobot.document_chunks
        WHERE file_name IN ({placeholders})
    """, KIDDOBOT_MODIFIED_FILES)
    deleted = cur.rowcount
    print(f"  Deleted {deleted} chunks")

    # Prepare new chunks for embedding
    all_chunks = []
    chunk_metadata = []
    for fname, fc in file_chunks.items():
        meta = file_metadata.get(fname, {'category': 'unknown', 'subcategory': 'unknown'})
        for idx, chunk_text in enumerate(fc['chunks']):
            all_chunks.append(chunk_text)
            chunk_metadata.append({
                'file_name': fname,
                'file_path': fc['relative_path'],
                'chunk_index': idx,
                'document_id': f"{fname}_{idx}",
                'category': meta['category'],
                'subcategory': meta['subcategory']
            })

    # Generate embeddings in batches
    print(f"\nGenerating embeddings for {len(all_chunks)} chunks...")
    BATCH_SIZE = 50
    all_embeddings = []
    for i in range(0, len(all_chunks), BATCH_SIZE):
        batch = all_chunks[i:i+BATCH_SIZE]
        embeddings = embed_texts(client, batch)
        all_embeddings.extend(embeddings)
        print(f"  Embedded {min(i+BATCH_SIZE, len(all_chunks))}/{len(all_chunks)}")

    # Insert new chunks
    print(f"\nInserting {len(all_chunks)} new chunks...")
    for chunk_text, embedding, meta in zip(all_chunks, all_embeddings, chunk_metadata):
        cur.execute("""
            INSERT INTO kiddobot.document_chunks
            (document_id, chunk_text, chunk_index, file_name, file_path, category, subcategory, embedding)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s::vector)
        """, (
            meta['document_id'],
            chunk_text,
            meta['chunk_index'],
            meta['file_name'],
            meta['file_path'],
            meta['category'],
            meta['subcategory'],
            str(embedding)
        ))

    conn.commit()
    print(f"✓ Inserted {len(all_chunks)} new chunks")

    # Run verifications
    run_all_verifications(conn, "document_chunks", "kiddobot", "chunk_text", 1350, 1500)

    cur.close()
    return len(all_chunks)


def print_rollback_instructions():
    """Print instructions for rolling back if something goes wrong."""
    print("\n" + "="*60)
    print("ROLLBACK INSTRUCTIONS (if needed)")
    print("="*60)
    print(f"""
If something went wrong, restore from backups:

1. BizBot:
   psql -h 100.111.63.3 -U postgres -d postgres -c "TRUNCATE public.bizbot_documents"
   # Then re-import from: {BACKUP_DIR}/bizbot_documents_backup.csv

2. KiddoBot:
   psql -h 100.111.63.3 -U postgres -d postgres -c "TRUNCATE kiddobot.document_chunks"
   # Then re-import from: {BACKUP_DIR}/kiddobot_chunks_backup.csv

3. WaterBot (if touched):
   psql -h 100.111.63.3 -U postgres -d postgres -c "TRUNCATE public.waterbot_documents"
   # Then re-import from: {BACKUP_DIR}/waterbot_documents_backup.csv
""")


def main():
    parser = argparse.ArgumentParser(description="Safe incremental embedding updates")
    parser.add_argument("--dry-run", action="store_true", help="Preview without making changes")
    parser.add_argument("--bizbot", action="store_true", help="Update BizBot only")
    parser.add_argument("--kiddobot", action="store_true", help="Update KiddoBot only")
    parser.add_argument("--all", action="store_true", help="Update all bots")
    args = parser.parse_args()

    if not (args.bizbot or args.kiddobot or args.all):
        parser.print_help()
        print("\nError: Specify --bizbot, --kiddobot, or --all")
        sys.exit(1)

    print("="*60)
    print("gov-ai-dev Safe Incremental Embedding Update")
    print("="*60)
    print(f"Dry run: {args.dry_run}")
    print(f"Backup location: {BACKUP_DIR}")

    # Verify backups exist
    if not BACKUP_DIR.exists():
        print(f"\n❌ ERROR: Backup directory not found: {BACKUP_DIR}")
        print("Run backup first before updating!")
        sys.exit(1)

    # Verify OpenAI key
    if not args.dry_run:
        if not os.environ.get("OPENAI_API_KEY"):
            print("\n❌ ERROR: OPENAI_API_KEY not set")
            print("Run: export OPENAI_API_KEY='your-key'")
            sys.exit(1)

    try:
        conn = get_db_connection()
        client = get_openai_client() if not args.dry_run else None

        if args.bizbot or args.all:
            update_bizbot_surgical(conn, client, args.dry_run)

        if args.kiddobot or args.all:
            update_kiddobot_incremental(conn, client, args.dry_run)

        conn.close()

        print("\n" + "="*60)
        print("✓ UPDATE COMPLETE")
        print("="*60)

    except VerificationError as e:
        print(f"\n❌ VERIFICATION FAILED: {e}")
        print_rollback_instructions()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print_rollback_instructions()
        sys.exit(1)


if __name__ == "__main__":
    main()
