#!/usr/bin/env python3
"""
Batch Ingestion Script for KiddoBot and WaterBot
Reads all batch JSON files and inserts documents into respective databases.
"""

import os
import json
import subprocess
import tempfile
from pathlib import Path
from openai import OpenAI

# Configuration
_REPO_DIR = Path(os.path.expanduser("~")) / "Documents/GitHub/gov-ai-dev"
KIDDOBOT_DIR = _REPO_DIR / "kiddobot/rag-content"
WATERBOT_DIR = _REPO_DIR / "waterbot/rag-content"
EMBEDDING_MODEL = "text-embedding-3-small"

# Initialize OpenAI client
client = OpenAI()

def generate_embedding(text: str) -> list[float]:
    """Generate embedding for text using OpenAI API."""
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    return response.data[0].embedding

def insert_kiddobot(content: str, metadata: dict, embedding: list[float], source_file: str) -> bool:
    """Insert document into KiddoBot PostgreSQL table."""
    tag = "CONTENT_END_12345"
    content_safe = content.replace(tag, "")

    document_id = source_file.replace(".json", "")
    file_name = source_file
    file_path = f"/rag-content/kiddobot/{source_file}"
    category = metadata.get("category", "")
    subcategory = metadata.get("subcategory", "")

    embedding_str = "[" + ",".join(map(str, embedding)) + "]"

    sql = f"""INSERT INTO kiddobot.document_chunks (chunk_text, document_id, file_name, file_path, category, subcategory, embedding)
VALUES (
    ${tag}${content_safe}${tag}$,
    '{document_id}',
    '{file_name}',
    '{file_path}',
    '{category}',
    '{subcategory}',
    '{embedding_str}'::vector
);"""

    return execute_sql(sql)

def insert_waterbot(content: str, metadata: dict, embedding: list[float]) -> bool:
    """Insert document into WaterBot PostgreSQL table."""
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

    return execute_sql(sql)

def execute_sql(sql: str) -> bool:
    """Execute SQL via SSH to VPS."""
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
            print(f"SQL error: {result.stderr[:200]}")
            return False
        if "ERROR" in result.stdout or "ERROR" in result.stderr:
            print(f"SQL error: {result.stdout[:200]} {result.stderr[:200]}")
            return False
        return True
    finally:
        os.unlink(temp_file)

def process_batch_files(directory: Path, bot_type: str) -> tuple[int, int]:
    """Process all batch_*.json files in directory."""
    success = 0
    errors = 0

    batch_files = sorted(directory.glob("batch_*.json"))
    print(f"\nFound {len(batch_files)} batch files for {bot_type}")

    for batch_file in batch_files:
        print(f"\n  Processing {batch_file.name}...")

        with open(batch_file) as f:
            data = json.load(f)

        documents = data.get("documents", [])
        print(f"    {len(documents)} documents in file")

        for i, doc in enumerate(documents, 1):
            content = doc["content"]
            metadata = doc.get("metadata", {})
            topic = metadata.get("topic", "Unknown")

            print(f"      [{i}/{len(documents)}] {topic[:40]}...", end=" ", flush=True)

            try:
                embedding = generate_embedding(content)

                if bot_type == "kiddobot":
                    ok = insert_kiddobot(content, metadata, embedding, batch_file.name)
                else:
                    ok = insert_waterbot(content, metadata, embedding)

                if ok:
                    print("OK")
                    success += 1
                else:
                    print("FAILED (insert)")
                    errors += 1
            except Exception as e:
                print(f"FAILED ({e})")
                errors += 1

    return success, errors

def main():
    print("=" * 60)
    print("BATCH INGESTION: KiddoBot and WaterBot")
    print("=" * 60)

    # Process KiddoBot
    print("\n" + "=" * 40)
    print("KIDDOBOT BATCH INGESTION")
    print("=" * 40)
    kiddo_success, kiddo_errors = process_batch_files(KIDDOBOT_DIR, "kiddobot")

    # Process WaterBot
    print("\n" + "=" * 40)
    print("WATERBOT BATCH INGESTION")
    print("=" * 40)
    water_success, water_errors = process_batch_files(WATERBOT_DIR, "waterbot")

    # Summary
    print("\n" + "=" * 60)
    print("INGESTION COMPLETE")
    print("=" * 60)
    print(f"  KiddoBot: {kiddo_success} success, {kiddo_errors} errors")
    print(f"  WaterBot: {water_success} success, {water_errors} errors")
    print(f"  TOTAL: {kiddo_success + water_success} success, {kiddo_errors + water_errors} errors")

if __name__ == "__main__":
    main()
