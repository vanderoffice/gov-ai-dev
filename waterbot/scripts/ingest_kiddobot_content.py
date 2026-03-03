#!/usr/bin/env python3
"""
KiddoBot RAG Content Ingestion Script
Reads JSON content files, generates embeddings, and inserts into PostgreSQL.
Uses stdin pipe approach for safe SQL execution through Docker.
"""

import os
import json
import subprocess
import tempfile
from pathlib import Path
from openai import OpenAI

# Configuration
CONTENT_DIR = Path(os.path.expanduser("~")) / "Documents/GitHub/gov-ai-dev/kiddobot/rag-content"
TABLE_NAME = "kiddobot.document_chunks"
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536

# Initialize OpenAI client
client = OpenAI()

def generate_embedding(text: str) -> list[float]:
    """Generate embedding for text using OpenAI API."""
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    return response.data[0].embedding

def load_documents() -> list[dict]:
    """Load all documents from JSON files."""
    documents = []
    for json_file in CONTENT_DIR.glob("*.json"):
        print(f"Loading {json_file.name}...")
        with open(json_file) as f:
            data = json.load(f)
            for doc in data.get("documents", []):
                doc["source_file"] = json_file.name
                documents.append(doc)
    return documents

def insert_to_database(content: str, metadata: dict, embedding: list[float], source_file: str) -> bool:
    """Insert document into PostgreSQL via SSH to VPS using stdin pipe.

    KiddoBot uses normalized schema with individual columns instead of JSONB metadata.
    """
    # Use dollar-quoted strings to avoid escaping issues
    tag = "CONTENT_END_12345"
    content_safe = content.replace(tag, "")

    # Extract metadata fields for KiddoBot's normalized schema
    document_id = source_file.replace(".json", "")
    file_name = source_file
    file_path = f"/rag-content/kiddobot/{source_file}"
    category = metadata.get("category", "")
    subcategory = metadata.get("subcategory", "")

    embedding_str = "[" + ",".join(map(str, embedding)) + "]"

    # KiddoBot schema: chunk_text, document_id, file_name, file_path, category, subcategory, embedding
    sql = f"""INSERT INTO {TABLE_NAME} (chunk_text, document_id, file_name, file_path, category, subcategory, embedding)
VALUES (
    ${tag}${content_safe}${tag}$,
    '{document_id}',
    '{file_name}',
    '{file_path}',
    '{category}',
    '{subcategory}',
    '{embedding_str}'::vector
);"""

    # Write SQL to local temp file
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

def main():
    print("=" * 60)
    print("KiddoBot RAG Content Ingestion")
    print("=" * 60)

    # Load documents
    documents = load_documents()
    print(f"\nLoaded {len(documents)} documents from {CONTENT_DIR}")

    # Process each document
    success_count = 0
    error_count = 0

    for i, doc in enumerate(documents, 1):
        content = doc["content"]
        metadata = doc.get("metadata", {})

        print(f"\n[{i}/{len(documents)}] Processing: {metadata.get('topic', 'Unknown')}")
        print(f"  Category: {metadata.get('category', 'N/A')}")
        print(f"  Subcategory: {metadata.get('subcategory', 'N/A')}")

        # Generate embedding
        print("  Generating embedding...", end=" ", flush=True)
        try:
            embedding = generate_embedding(content)
            print(f"OK ({len(embedding)} dims)")
        except Exception as e:
            print(f"FAILED: {e}")
            error_count += 1
            continue

        # Insert to database
        print("  Inserting to database...", end=" ", flush=True)
        source_file = doc.get("source_file", "unknown.json")
        if insert_to_database(content, metadata, embedding, source_file):
            print("OK")
            success_count += 1
        else:
            print("FAILED")
            error_count += 1

    # Summary
    print("\n" + "=" * 60)
    print("INGESTION COMPLETE")
    print("=" * 60)
    print(f"  Success: {success_count}")
    print(f"  Errors:  {error_count}")
    print(f"  Total:   {len(documents)}")

if __name__ == "__main__":
    main()
