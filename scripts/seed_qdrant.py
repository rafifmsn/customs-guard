#!/usr/bin/env python3
"""
CustomsGuard Qdrant Vector Seeding Script
Initializes the 'customs_tariffs' collection in Qdrant,
creates payload indexes (full-text search and keyword filters),
and uploads all 5,612 HS-6 Indonesian tariff records.
"""

import hashlib
import json
import math
import os
import sys
import time
import urllib.error
import urllib.request


def get_qdrant_url():
    """Determine Qdrant base URL based on execution environment."""
    # Check if inside container or host
    for url in ["http://qdrant:6333", "http://localhost:6333"]:
        try:
            req = urllib.request.Request(f"{url}/readyz")
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    return url
        except Exception:
            continue
    return "http://localhost:6333"


def generate_deterministic_vector(text: str, dim: int = 384) -> list:
    """
    Generate normalized semantic hash vector for text.
    Provides fast, deterministic local embeddings without external API costs.
    """
    words = text.lower().split()
    vec = [0.0] * dim

    for i, word in enumerate(words):
        # Character n-grams hash
        h = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        sign = 1.0 if ((h >> 8) & 1) == 0 else -1.0
        weight = 1.0 / (1.0 + math.log(1.0 + i))
        vec[idx] += sign * weight

    # Normalize vector to unit length (L2 norm) for Cosine distance
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [x / norm for x in vec]
    else:
        vec[0] = 1.0

    return [round(x, 6) for x in vec]


def create_collection(qdrant_url: str, collection_name: str, dim: int = 384):
    """Recreate Qdrant collection with cosine distance."""
    # Delete if exists
    del_req = urllib.request.Request(
        f"{qdrant_url}/collections/{collection_name}", method="DELETE"
    )
    try:
        urllib.request.urlopen(del_req, timeout=5)
    except Exception:
        pass

    # Create new collection
    payload = json.dumps({"vectors": {"size": dim, "distance": "Cosine"}}).encode("utf-8")
    create_req = urllib.request.Request(
        f"{qdrant_url}/collections/{collection_name}",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="PUT",
    )
    with urllib.request.urlopen(create_req, timeout=10) as resp:
        print(f"[Qdrant] Created collection '{collection_name}': {resp.status}")


def create_payload_indexes(qdrant_url: str, collection_name: str):
    """Create payload field indexes in Qdrant for full-text and filters."""
    indexes = [
        (
            "search_text",
            {
                "type": "text",
                "tokenizer": "word",
                "min_token_len": 2,
                "max_token_len": 20,
                "lowercase": True,
            },
        ),
        ("chapter", {"type": "keyword"}),
        ("heading", {"type": "keyword"}),
        ("hs_code", {"type": "keyword"}),
        ("risk_level", {"type": "keyword"}),
        ("restricted", {"type": "bool"}),
    ]

    for field_name, schema in indexes:
        payload = json.dumps({"field_name": field_name, "field_schema": schema}).encode("utf-8")
        req = urllib.request.Request(
            f"{qdrant_url}/collections/{collection_name}/index",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="PUT",
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                print(f"[Qdrant] Index created for '{field_name}'")
        except Exception as e:
            print(f"[Qdrant] Warning on index '{field_name}': {e}")


def load_or_generate_embeddings(records: list, json_dir: str) -> dict:
    """
    Load precomputed 384-dimensional dense semantic embeddings from disk if available,
    or generate them via Ollama all-minilm embedding model with graceful deterministic fallback.
    """
    emb_candidates = [
        os.path.join(json_dir, "tariff_embeddings_384.json"),
        os.path.join(os.path.dirname(json_dir), "seed", "tariff_embeddings_384.json"),
        "/app/seed/tariff_embeddings_384.json",
        "/app/data/seed/tariff_embeddings_384.json",
    ]
    for path in emb_candidates:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if len(data) >= len(records) * 0.9:
                    print(f"[Embeddings] Loaded {len(data)} precomputed dense embeddings from {path}")
                    return data
            except Exception as e:
                print(f"[Embeddings] Warning reading {path}: {e}")

    # If file not present, attempt batch generation via Ollama all-minilm
    ollama_urls = [
        os.environ.get("OLLAMA_BASE_URL"),
        "http://localhost:11434",
        "http://172.18.0.1:11434",
        "http://host.docker.internal:11434",
    ]
    valid_ollama = None
    for u in ollama_urls:
        if not u:
            continue
        try:
            req = urllib.request.Request(f"{u}/api/tags")
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    valid_ollama = u
                    break
        except Exception:
            continue

    if valid_ollama:
        print(f"[Embeddings] Generating dense embeddings via Ollama ({valid_ollama}) model 'all-minilm'...")
        embeddings = {}
        batch_size = 250
        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]
            texts = [r["search_text"] for r in batch]
            try:
                payload = json.dumps({"model": "all-minilm", "input": texts}).encode("utf-8")
                req = urllib.request.Request(
                    f"{valid_ollama}/api/embed",
                    data=payload,
                    headers={"Content-Type": "application/json"},
                )
                with urllib.request.urlopen(req, timeout=45) as resp:
                    res = json.loads(resp.read().decode("utf-8"))
                    embs = res.get("embeddings", [])
                    for r, emb in zip(batch, embs):
                        norm = math.sqrt(sum(x * x for x in emb))
                        vec = [x / norm for x in emb] if norm > 0 else emb
                        embeddings[r["hs_code"]] = [round(x, 6) for x in vec]
            except Exception as e:
                print(f"[Embeddings] Batch failed at {i}: {e}")
                break

        if len(embeddings) == len(records):
            out_cache = os.path.join(json_dir, "tariff_embeddings_384.json")
            try:
                with open(out_cache, "w", encoding="utf-8") as f:
                    json.dump(embeddings, f)
                print(f"[Embeddings] Saved {len(embeddings)} dense embeddings to cache: {out_cache}")
            except Exception:
                pass
            return embeddings

    print("[Embeddings] Ollama not reachable; falling back to deterministic token hash projection.")
    return {r["hs_code"]: generate_deterministic_vector(r["search_text"]) for r in records}


def seed_database(qdrant_url: str, json_path: str, collection_name: str = "customs_tariffs"):
    """Load JSON database and upload batch points into Qdrant."""
    if not os.path.exists(json_path):
        print(f"Error: Seed file not found at {json_path}")
        sys.exit(1)

    with open(json_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    print(f"Loaded {len(records)} records from {json_path}")
    json_dir = os.path.dirname(os.path.abspath(json_path))
    embeddings_map = load_or_generate_embeddings(records, json_dir)

    create_collection(qdrant_url, collection_name)
    create_payload_indexes(qdrant_url, collection_name)

    batch_size = 500
    total = len(records)
    print(f"Uploading points in batches of {batch_size}...")

    for i in range(0, total, batch_size):
        batch = records[i : i + batch_size]
        points = []
        for idx, r in enumerate(batch, start=i + 1):
            vector = embeddings_map.get(r["hs_code"])
            if not vector:
                vector = generate_deterministic_vector(r["search_text"])
            points.append({"id": idx, "vector": vector, "payload": r})

        payload = json.dumps({"points": points}).encode("utf-8")
        req = urllib.request.Request(
            f"{qdrant_url}/collections/{collection_name}/points?wait=true",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="PUT",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            pass

        print(f"Uploaded points {i + 1} to {min(i + batch_size, total)} of {total}")

    # Verify collection statistics
    info_req = urllib.request.Request(f"{qdrant_url}/collections/{collection_name}")
    with urllib.request.urlopen(info_req, timeout=10) as resp:
        info = json.loads(resp.read().decode("utf-8"))
        points_count = info.get("result", {}).get("points_count", 0)
        print(f"[Qdrant] Seeding complete! Verified points in collection: {points_count}")


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # Support running either from container or host
    if os.path.exists(os.path.join(base_dir, "data", "seed", "tariff_database.json")):
        seed_file = os.path.join(base_dir, "data", "seed", "tariff_database.json")
    else:
        seed_file = "/app/seed/tariff_database.json"

    url = get_qdrant_url()
    print(f"Connecting to Qdrant at {url}...")
    seed_database(url, seed_file)
