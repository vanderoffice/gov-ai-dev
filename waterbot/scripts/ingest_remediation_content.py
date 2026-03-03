#!/usr/bin/env python3
"""
Targeted ingestion script for WaterBot and KiddoBot remediation content.
Only ingests NEW files created during the 2026-01-18 remediation.
"""

import os
import json
import subprocess
import tempfile
from pathlib import Path
from openai import OpenAI

# Configuration
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536

# New files to ingest
_REPO_DIR = os.path.join(os.path.expanduser("~"), "Documents/GitHub/gov-ai-dev")

WATERBOT_NEW_FILES = [
    os.path.join(_REPO_DIR, "waterbot/rag-content/batch_consumer_faq.json"),
    os.path.join(_REPO_DIR, "waterbot/rag-content/batch_advocate_toolkit.json"),
    os.path.join(_REPO_DIR, "waterbot/rag-content/batch_operator_guides.json"),
]

KIDDOBOT_NEW_FILES = [
    os.path.join(_REPO_DIR, "kiddobot/rag-content/family_fees_vs_copayments.json"),
]

# Initialize OpenAI client
client = OpenAI()


def execute_sql(sql: str) -> tuple[bool, str]:
    """Execute arbitrary SQL via SSH to VPS."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
        f.write(sql)
        temp_file = f.name

    try:
        with open(temp_file, 'r') as f:
            result = subprocess.run(
                ["ssh", "vps", "docker exec -i supabase-db psql -U postgres -d postgres"],
                stdin=f,
                capture_output=True,
                text=True
            )

        if result.returncode != 0:
            return False, result.stderr
        if "ERROR" in result.stdout or "ERROR" in result.stderr:
            return False, f"{result.stdout} {result.stderr}"
        return True, result.stdout
    finally:
        os.unlink(temp_file)


def rebuild_indexes():
    """
    Rebuild IVFFlat indexes after bulk insert.

    IVFFlat indexes pre-compute cluster centroids. New vectors inserted after
    index creation may not be properly indexed until rebuild.
    See: ISSUES.md - Lesson 2026-01-18
    """
    print("\n" + "-" * 40)
    print("REBUILDING IVFFLAT INDEXES")
    print("-" * 40)

    indexes = [
        ("WaterBot", "REINDEX INDEX public.waterbot_documents_embedding_idx;"),
        ("KiddoBot", "REINDEX INDEX kiddobot.document_chunks_embedding_idx;"),
    ]

    for name, sql in indexes:
        print(f"  {name}...", end=" ", flush=True)
        success, output = execute_sql(sql)
        if success:
            print("OK")
        else:
            print(f"FAILED: {output}")


def generate_embedding(text: str) -> list[float]:
    """Generate embedding for text using OpenAI API."""
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    return response.data[0].embedding

def insert_waterbot_doc(content: str, metadata: dict, embedding: list[float]) -> bool:
    """Insert document into WaterBot table (public.waterbot_documents)."""
    tag = "CONTENT_END_12345"
    content_safe = content.replace(tag, "")

    metadata_json = json.dumps(metadata)
    embedding_str = "[" + ",".join(map(str, embedding)) + "]"

    sql = f"""INSERT INTO public.waterbot_documents (content, metadata, embedding)
VALUES (
    ${tag}${content_safe}${tag}$,
    ${tag}${metadata_json}${tag}$::jsonb,
    '{embedding_str}'::vector
);"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
        f.write(sql)
        temp_file = f.name

    try:
        with open(temp_file, 'r') as f:
            result = subprocess.run(
                ["ssh", "vps", "docker exec -i supabase-db psql -U postgres -d postgres"],
                stdin=f,
                capture_output=True,
                text=True
            )

        if result.returncode != 0:
            print(f"SQL error: {result.stderr}")
            return False
        if "ERROR" in result.stdout or "ERROR" in result.stderr:
            print(f"SQL error: {result.stdout} {result.stderr}")
            return False
        return True
    finally:
        os.unlink(temp_file)

def insert_kiddobot_doc(content: str, metadata: dict, embedding: list[float], source_file: str) -> bool:
    """Insert document into KiddoBot table (kiddobot.document_chunks)."""
    tag = "CONTENT_END_12345"
    content_safe = content.replace(tag, "")

    # KiddoBot schema is different - uses chunk_text, file_name, category, subcategory
    category = metadata.get("category", "Uncategorized")
    subcategory = metadata.get("subcategory", "General")
    topic = metadata.get("topic", "Unknown")

    embedding_str = "[" + ",".join(map(str, embedding)) + "]"

    sql = f"""INSERT INTO kiddobot.document_chunks (chunk_text, file_name, file_path, category, subcategory, embedding)
VALUES (
    ${tag}${content_safe}${tag}$,
    ${tag}${topic}${tag}$,
    ${tag}${source_file}${tag}$,
    ${tag}${category}${tag}$,
    ${tag}${subcategory}${tag}$,
    '{embedding_str}'::vector
);"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
        f.write(sql)
        temp_file = f.name

    try:
        with open(temp_file, 'r') as f:
            result = subprocess.run(
                ["ssh", "vps", "docker exec -i supabase-db psql -U postgres -d postgres"],
                stdin=f,
                capture_output=True,
                text=True
            )

        if result.returncode != 0:
            print(f"SQL error: {result.stderr}")
            return False
        if "ERROR" in result.stdout or "ERROR" in result.stderr:
            print(f"SQL error: {result.stdout} {result.stderr}")
            return False
        return True
    finally:
        os.unlink(temp_file)

def process_files(files: list[str], bot: str) -> tuple[int, int]:
    """Process a list of JSON files for a specific bot."""
    success = 0
    errors = 0

    for json_file in files:
        path = Path(json_file)
        if not path.exists():
            print(f"  WARNING: File not found: {json_file}")
            continue

        print(f"\nProcessing {path.name}...")

        with open(path) as f:
            data = json.load(f)

        docs = data.get("documents", [])
        print(f"  Found {len(docs)} documents")

        for i, doc in enumerate(docs, 1):
            content = doc["content"]
            metadata = doc.get("metadata", {})
            topic = metadata.get("topic", "Unknown")

            print(f"  [{i}/{len(docs)}] {topic[:50]}...", end=" ", flush=True)

            # Generate embedding
            try:
                embedding = generate_embedding(content)
            except Exception as e:
                print(f"EMBEDDING FAILED: {e}")
                errors += 1
                continue

            # Insert to appropriate table
            if bot == "waterbot":
                result = insert_waterbot_doc(content, metadata, embedding)
            else:
                result = insert_kiddobot_doc(content, metadata, embedding, path.name)

            if result:
                print("OK")
                success += 1
            else:
                print("INSERT FAILED")
                errors += 1

    return success, errors

def main():
    print("=" * 60)
    print("Remediation Content Ingestion")
    print("=" * 60)
    print("\nThis script ingests ONLY the new remediation content:")
    print(f"  WaterBot: {len(WATERBOT_NEW_FILES)} files")
    print(f"  KiddoBot: {len(KIDDOBOT_NEW_FILES)} files")

    total_success = 0
    total_errors = 0

    # Process WaterBot files
    print("\n" + "-" * 40)
    print("WATERBOT INGESTION")
    print("-" * 40)
    s, e = process_files(WATERBOT_NEW_FILES, "waterbot")
    total_success += s
    total_errors += e
    print(f"\nWaterBot: {s} success, {e} errors")

    # Process KiddoBot files
    print("\n" + "-" * 40)
    print("KIDDOBOT INGESTION")
    print("-" * 40)
    s, e = process_files(KIDDOBOT_NEW_FILES, "kiddobot")
    total_success += s
    total_errors += e
    print(f"\nKiddoBot: {s} success, {e} errors")

    # Rebuild indexes for similarity search to work
    if total_success > 0:
        rebuild_indexes()

    # Summary
    print("\n" + "=" * 60)
    print("INGESTION COMPLETE")
    print("=" * 60)
    print(f"  Total Success: {total_success}")
    print(f"  Total Errors:  {total_errors}")
    print("\n  ⚠️  IVFFlat indexes rebuilt - new content is now searchable")

if __name__ == "__main__":
    main()
