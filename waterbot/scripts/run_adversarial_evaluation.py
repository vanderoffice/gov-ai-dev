#!/usr/bin/env python3
"""
Adversarial Test Set Evaluation Script
Runs the non-circular test queries against all three bots and scores coverage.
"""

import json
import subprocess
import tempfile
import os
from pathlib import Path
from openai import OpenAI
from datetime import datetime

# Configuration
_REPO_DIR = Path(os.path.expanduser("~")) / "Documents/GitHub/gov-ai-dev"
TEST_SET_PATH = _REPO_DIR / "waterbot/.planning/adversarial_test_set.json"
OUTPUT_DIR = _REPO_DIR / "waterbot/.planning"
EMBEDDING_MODEL = "text-embedding-3-small"
TOP_K = 3  # Number of results to retrieve per query
SIMILARITY_THRESHOLD_STRONG = 0.40  # Threshold for "strong" match
SIMILARITY_THRESHOLD_ACCEPTABLE = 0.30  # Threshold for "acceptable" match

# Bot configurations
BOTS = {
    "bizbot": {
        "table": "public.bizbot_documents",
        "content_col": "content",
        "embedding_col": "embedding"
    },
    "kiddobot": {
        "table": "kiddobot.document_chunks",
        "content_col": "chunk_text",
        "embedding_col": "embedding"
    },
    "waterbot": {
        "table": "public.waterbot_documents",
        "content_col": "content",
        "embedding_col": "embedding"
    }
}

# Initialize OpenAI client
client = OpenAI()


def generate_embedding(text: str) -> list[float]:
    """Generate embedding for text using OpenAI API."""
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    return response.data[0].embedding


def run_similarity_query(bot_name: str, query_embedding: list[float], top_k: int = TOP_K) -> list[dict]:
    """Run similarity search against a bot's database."""
    config = BOTS[bot_name]
    embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

    sql = f"""
    SELECT
        {config['content_col']} as content,
        1 - ({config['embedding_col']} <=> '{embedding_str}'::vector) as similarity
    FROM {config['table']}
    ORDER BY {config['embedding_col']} <=> '{embedding_str}'::vector
    LIMIT {top_k};
    """

    with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
        f.write(sql)
        temp_file = f.name

    try:
        with open(temp_file, 'r') as f:
            result = subprocess.run(
                ["ssh", "vps", "docker exec -i supabase-db psql -U postgres -d postgres -t -A -F '|||'"],
                stdin=f,
                capture_output=True,
                text=True
            )

        if result.returncode != 0:
            print(f"SQL error for {bot_name}: {result.stderr}")
            return []

        results = []
        for line in result.stdout.strip().split('\n'):
            if '|||' in line:
                parts = line.rsplit('|||', 1)
                if len(parts) == 2:
                    content, similarity = parts
                    try:
                        results.append({
                            "content": content[:500] + "..." if len(content) > 500 else content,
                            "similarity": float(similarity)
                        })
                    except ValueError:
                        continue
        return results
    finally:
        os.unlink(temp_file)


def evaluate_query(query: dict, bot_name: str) -> dict:
    """Evaluate a single query against a bot."""
    # Generate embedding for query
    query_embedding = generate_embedding(query["query"])

    # Run similarity search
    results = run_similarity_query(bot_name, query_embedding)

    # Score the results
    if not results:
        score = "NO_RESULTS"
        top_similarity = 0.0
    else:
        top_similarity = results[0]["similarity"]
        if top_similarity >= SIMILARITY_THRESHOLD_STRONG:
            score = "STRONG"
        elif top_similarity >= SIMILARITY_THRESHOLD_ACCEPTABLE:
            score = "ACCEPTABLE"
        else:
            score = "WEAK"

    return {
        "query_id": query["id"],
        "query": query["query"],
        "type": query["type"],
        "expected_coverage": query.get("expected_coverage", ""),
        "score": score,
        "top_similarity": round(top_similarity, 4),
        "top_results": results[:TOP_K]
    }


def run_full_evaluation():
    """Run evaluation for all bots."""
    # Load test set
    with open(TEST_SET_PATH) as f:
        test_set = json.load(f)

    results = {
        "metadata": {
            "run_date": datetime.now().isoformat(),
            "thresholds": {
                "strong": SIMILARITY_THRESHOLD_STRONG,
                "acceptable": SIMILARITY_THRESHOLD_ACCEPTABLE
            },
            "top_k": TOP_K
        },
        "summary": {},
        "details": {}
    }

    for bot_name in ["bizbot", "kiddobot", "waterbot"]:
        print(f"\n{'='*60}")
        print(f"Evaluating {bot_name.upper()}")
        print(f"{'='*60}")

        queries = test_set[bot_name]["queries"]
        bot_results = []

        for i, query in enumerate(queries, 1):
            print(f"  [{i}/{len(queries)}] {query['id']}: {query['query'][:50]}...")
            result = evaluate_query(query, bot_name)
            bot_results.append(result)
            print(f"    → {result['score']} (similarity: {result['top_similarity']})")

        # Calculate summary
        scores = [r["score"] for r in bot_results]
        summary = {
            "total": len(queries),
            "strong": scores.count("STRONG"),
            "acceptable": scores.count("ACCEPTABLE"),
            "weak": scores.count("WEAK"),
            "no_results": scores.count("NO_RESULTS"),
            "coverage_rate": round((scores.count("STRONG") + scores.count("ACCEPTABLE")) / len(queries) * 100, 1)
        }

        results["summary"][bot_name] = summary
        results["details"][bot_name] = bot_results

        print(f"\n  Summary for {bot_name}:")
        print(f"    Strong: {summary['strong']}/{summary['total']}")
        print(f"    Acceptable: {summary['acceptable']}/{summary['total']}")
        print(f"    Weak: {summary['weak']}/{summary['total']}")
        print(f"    Coverage Rate: {summary['coverage_rate']}%")

    # Save results
    output_file = OUTPUT_DIR / f"adversarial_evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*60}")
    print("OVERALL RESULTS")
    print(f"{'='*60}")
    for bot_name, summary in results["summary"].items():
        print(f"  {bot_name}: {summary['coverage_rate']}% coverage ({summary['strong']} strong, {summary['acceptable']} acceptable)")

    print(f"\nResults saved to: {output_file}")

    # Also save a gap analysis for queries that failed
    gaps = []
    for bot_name in ["bizbot", "kiddobot", "waterbot"]:
        for result in results["details"][bot_name]:
            if result["score"] in ["WEAK", "NO_RESULTS"]:
                gaps.append({
                    "bot": bot_name,
                    "query_id": result["query_id"],
                    "query": result["query"],
                    "type": result["type"],
                    "expected_coverage": result["expected_coverage"],
                    "top_similarity": result["top_similarity"],
                    "top_result_preview": result["top_results"][0]["content"][:200] if result["top_results"] else "No results"
                })

    gap_file = OUTPUT_DIR / f"coverage_gaps_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(gap_file, 'w') as f:
        json.dump(gaps, f, indent=2)

    print(f"Gap analysis saved to: {gap_file}")
    print(f"\nTotal gaps identified: {len(gaps)}")

    return results


if __name__ == "__main__":
    run_full_evaluation()
