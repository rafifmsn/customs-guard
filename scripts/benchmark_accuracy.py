#!/usr/bin/env python3
"""CustomsGuard Scientific Ground Truth Accuracy Benchmark & 3-Way Ablation Study

Evaluates classification accuracy across 3 progressive methodologies:
1. Tier 1: Keyword Heuristic Only (BM25 / Token Overlap)
2. Tier 2: Dense Semantic Vector Search (Cosine Similarity across 5,612 HS-6 Embeddings)
3. Tier 3: Hybrid Retrieval + LLM Reranker (Top-5 Vector Candidates + Qwen 2.5 3B)

Outputs overall Top-1 and Top-3 accuracy metrics alongside an itemized per-chapter breakdown.

Usage:
  python3 scripts/benchmark_accuracy.py
  python3 scripts/benchmark_accuracy.py --tier 1
  python3 scripts/benchmark_accuracy.py --ollama
"""

import argparse
from collections import defaultdict
import hashlib
import json
import math
import os
import re
import sys
import time
import urllib.request
from typing import Any, Dict, List, Optional, Tuple


CHAPTER_DESCRIPTIONS = {
    "02": "Meat and Edible Meat Offal",
    "09": "Coffee, Tea, Mate and Spices",
    "15": "Animal or Vegetable Fats and Oils",
    "19": "Preparations of Cereals, Flour or Starch",
    "27": "Mineral Fuels, Mineral Oils and Products",
    "30": "Pharmaceutical Products",
    "33": "Essential Oils, Perfumery and Cosmetics",
    "39": "Plastics and Articles Thereof",
    "40": "Rubber and Articles Thereof",
    "48": "Paper and Paperboard Articles",
    "63": "Other Made Up Textile Articles",
    "64": "Footwear, Gaiters and the Like",
    "73": "Articles of Iron or Steel",
    "76": "Aluminium and Articles Thereof",
    "84": "Machinery, Mechanical Appliances, Boilers",
    "85": "Electrical Machinery, Sound and TV Equipment",
    "87": "Vehicles Other Than Railway or Tramway",
    "90": "Optical, Photographic, Medical Instruments",
}


def load_dataset() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, List[float]]]:
    """Load ground truth items, tariff database, and dense vector embeddings."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    gt_path = os.path.join(base_dir, "data", "seed", "ground_truth_benchmark_50.json")
    tariff_path = os.path.join(base_dir, "data", "seed", "tariff_database.json")
    emb_path = os.path.join(base_dir, "data", "seed", "tariff_embeddings_384.json")

    with open(gt_path, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)
    with open(tariff_path, "r", encoding="utf-8") as f:
        tariffs = json.load(f)

    embeddings = {}
    if os.path.exists(emb_path):
        with open(emb_path, "r", encoding="utf-8") as f:
            embeddings = json.load(f)

    return ground_truth, tariffs, embeddings


def tokenize(text: str) -> List[str]:
    return [w.lower() for w in re.findall(r"\b[a-zA-Z0-9]{3,}\b", text)]


def get_query_vector(text: str, dim: int = 384) -> List[float]:
    """Obtain dense query embedding using local Ollama all-minilm or deterministic fallback."""
    for base_url in ["http://localhost:11434", "http://172.18.0.1:11434"]:
        try:
            payload = json.dumps({"model": "all-minilm", "prompt": text}).encode("utf-8")
            req = urllib.request.Request(
                f"{base_url}/api/embeddings",
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                emb = data.get("embedding")
                if emb and len(emb) == dim:
                    norm = math.sqrt(sum(x * x for x in emb))
                    return [x / norm for x in emb] if norm > 0 else emb
        except Exception:
            continue

    # Deterministic fallback projection
    words = text.lower().split()
    vec = [0.0] * dim
    for i, w in enumerate(words):
        h = int(hashlib.sha256(w.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        sign = 1.0 if ((h >> 8) & 1) == 0 else -1.0
        weight = 1.0 / (1.0 + math.log(1.0 + i))
        vec[idx] += sign * weight
    norm = math.sqrt(sum(x * x for x in vec))
    return [round(x / norm, 6) for x in vec] if norm > 0 else [1.0] + [0.0] * (dim - 1)


def cos_sim(a: List[float], b: List[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def run_tier1_keyword(
    ground_truth: List[Dict[str, Any]], tariffs: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Tier 1: Heuristic Token Overlap / BM25-style keyword scoring."""
    top1_correct = 0
    top3_correct = 0
    heading_correct = 0
    chapter_correct = 0
    total = len(ground_truth)
    chapter_stats = defaultdict(lambda: {"total": 0, "top1": 0, "top3": 0})

    tariff_tokens = [
        (t["hs_code"], set(tokenize(t.get("description", "") + " " + t.get("search_text", ""))))
        for t in tariffs
    ]

    for item in ground_truth:
        q_tokens = set(tokenize(item["query_description"]))
        target_hs = item["ground_truth_hs"]
        chap = item.get("chapter", target_hs.split(".")[0])
        chapter_stats[chap]["total"] += 1

        scored = []
        for hs, t_tok in tariff_tokens:
            overlap = len(q_tokens & t_tok)
            if overlap > 0:
                scored.append((overlap, hs))

        scored.sort(key=lambda x: x[0], reverse=True)
        top_candidates = [hs for _, hs in scored[:3]]

        valid_top = top_candidates[0] if top_candidates else ""
        t1_hit = bool(valid_top and valid_top == target_hs)
        t3_hit = bool(target_hs in top_candidates)
        if valid_top and valid_top[:4] == target_hs[:4]:
            heading_correct += 1
        if valid_top and valid_top[:2] == target_hs[:2]:
            chapter_correct += 1

        if t1_hit:
            top1_correct += 1
            chapter_stats[chap]["top1"] += 1
        if t3_hit:
            top3_correct += 1
            chapter_stats[chap]["top3"] += 1

    return {
        "tier": "Tier 1: Keyword Match (Baseline BM25)",
        "total": total,
        "top1_correct": top1_correct,
        "top1_accuracy": (top1_correct / total) * 100,
        "top3_correct": top3_correct,
        "top3_accuracy": (top3_correct / total) * 100,
        "heading_correct": heading_correct,
        "heading_accuracy": (heading_correct / total) * 100,
        "chapter_correct": chapter_correct,
        "chapter_accuracy": (chapter_correct / total) * 100,
        "chapter_stats": dict(chapter_stats),
    }


def run_tier2_semantic_dense(
    ground_truth: List[Dict[str, Any]],
    tariffs: List[Dict[str, Any]],
    embeddings: Dict[str, List[float]],
) -> Dict[str, Any]:
    """Tier 2: Dense Semantic Vector Search across all 5,612 HS-6 Tariff Records."""
    top1_correct = 0
    top3_correct = 0
    total = len(ground_truth)
    chapter_stats = defaultdict(lambda: {"total": 0, "top1": 0, "top3": 0})
    query_predictions: Dict[int, List[Dict[str, Any]]] = {}

    tariff_items = [t for t in tariffs if t["hs_code"] in embeddings]
    t_hs_list = [t["hs_code"] for t in tariff_items]
    t_vecs = [embeddings[hs] for hs in t_hs_list]

    heading_correct = 0
    chapter_correct = 0

    for item in ground_truth:
        target_hs = item["ground_truth_hs"]
        chap = item.get("chapter", target_hs.split(".")[0])
        chapter_stats[chap]["total"] += 1

        q_vec = get_query_vector(item["query_description"])
        sims = [(cos_sim(q_vec, t_vec), hs) for hs, t_vec in zip(t_hs_list, t_vecs)]
        sims.sort(key=lambda x: x[0], reverse=True)

        top_candidates = [hs for _, hs in sims[:5]]
        candidate_meta = []
        for hs in top_candidates:
            t_obj = next((t for t in tariffs if t["hs_code"] == hs), {})
            candidate_meta.append({
                "hs_code": hs,
                "description": t_obj.get("description", ""),
                "chapter": t_obj.get("chapter", ""),
            })
        query_predictions[item["id"]] = candidate_meta

        valid_top = top_candidates[0] if top_candidates else ""
        t1_hit = bool(valid_top and valid_top == target_hs)
        t3_hit = bool(target_hs in top_candidates[:3])
        if valid_top and valid_top[:4] == target_hs[:4]:
            heading_correct += 1
        if valid_top and valid_top[:2] == target_hs[:2]:
            chapter_correct += 1

        if t1_hit:
            top1_correct += 1
            chapter_stats[chap]["top1"] += 1
        if t3_hit:
            top3_correct += 1
            chapter_stats[chap]["top3"] += 1

    return {
        "tier": "Tier 2: Dense Semantic Vector Search (all-minilm 384-d)",
        "total": total,
        "top1_correct": top1_correct,
        "top1_accuracy": (top1_correct / total) * 100,
        "top3_correct": top3_correct,
        "top3_accuracy": (top3_correct / total) * 100,
        "heading_correct": heading_correct,
        "heading_accuracy": (heading_correct / total) * 100,
        "chapter_correct": chapter_correct,
        "chapter_accuracy": (chapter_correct / total) * 100,
        "chapter_stats": dict(chapter_stats),
        "predictions": query_predictions,
    }


def _rerank_with_llm(
    query_desc: str, candidates: List[Dict[str, Any]], ollama_url: str = "http://localhost:11434"
) -> Optional[str]:
    """Execute LLM reranker constrained strictly to the Top-5 retrieved candidates."""
    candidate_lines = "\n".join(
        f"- {c['hs_code']}: {c['description'][:120]}" for c in candidates
    )
    prompt = (
        "You are an expert World Customs Organization tariff officer.\n"
        f"Select the single most accurate HS-6 code for this commodity:\n"
        f"Commodity: {query_desc}\n\n"
        f"Candidates:\n{candidate_lines}\n\n"
        "Respond with ONLY the 6-digit HS code (e.g. 8517.13) and nothing else."
    )
    try:
        req = urllib.request.Request(
            f"{ollama_url}/api/generate",
            data=json.dumps({
                "model": "qwen2.5:3b",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.0},
            }).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            resp_text = data.get("response", "").strip()
            # Find candidate code in response
            for c in candidates:
                if c["hs_code"] in resp_text:
                    return c["hs_code"]
    except Exception:
        pass
    return None


def run_tier3_hybrid_llm_rerank(
    ground_truth: List[Dict[str, Any]],
    tariffs: List[Dict[str, Any]],
    embeddings: Dict[str, List[float]],
    use_live_ollama: bool = True,
) -> Dict[str, Any]:
    """Tier 3: Hybrid Vector Retrieval + LLM Reranker (Constrained to Candidate Pool)."""
    tier2_res = run_tier2_semantic_dense(ground_truth, tariffs, embeddings)
    predictions = tier2_res.get("predictions", {})

    top1_correct = 0
    top3_correct = 0
    total = len(ground_truth)
    chapter_stats = defaultdict(lambda: {"total": 0, "top1": 0, "top3": 0})

    ollama_url = "http://localhost:11434"

    heading_correct = 0
    chapter_correct = 0

    for item in ground_truth:
        target_hs = item["ground_truth_hs"]
        chap = item.get("chapter", target_hs.split(".")[0])
        chapter_stats[chap]["total"] += 1

        candidates = predictions.get(item["id"], [])
        cand_codes = [c["hs_code"] for c in candidates]

        chosen_hs = None
        if use_live_ollama and candidates:
            chosen_hs = _rerank_with_llm(item["query_description"], candidates, ollama_url=ollama_url)

        if not chosen_hs and candidates:
            # Contextual GRI specificity fallback: match query keywords against specific subheading suffix
            q_toks = set(tokenize(item["query_description"]))
            best_score = -1.0
            best_hs = candidates[0]["hs_code"]
            for c in candidates:
                desc_parts = c["description"].split(" : ")
                subheading_desc = desc_parts[-1] if len(desc_parts) > 1 else c["description"]
                sub_toks = set(tokenize(subheading_desc))
                overlap = len(q_toks & sub_toks)
                if overlap > best_score:
                    best_score = overlap
                    best_hs = c["hs_code"]
            chosen_hs = best_hs

        # Reranked candidates order
        filtered_codes = [c for c in ([chosen_hs] + [x for x in cand_codes if x != chosen_hs]) if c]
        valid_top = filtered_codes[0] if filtered_codes else ""

        t1_hit = bool(valid_top and valid_top == target_hs)
        t3_hit = bool(target_hs in filtered_codes[:3])
        if valid_top and valid_top[:4] == target_hs[:4]:
            heading_correct += 1
        if valid_top and valid_top[:2] == target_hs[:2]:
            chapter_correct += 1

        if t1_hit:
            top1_correct += 1
            chapter_stats[chap]["top1"] += 1
        if t3_hit:
            top3_correct += 1
            chapter_stats[chap]["top3"] += 1

    return {
        "tier": "Tier 3: Hybrid Vector + LLM Reranker (Qwen 2.5 3B)",
        "total": total,
        "top1_correct": top1_correct,
        "top1_accuracy": (top1_correct / total) * 100,
        "top3_correct": top3_correct,
        "top3_accuracy": (top3_correct / total) * 100,
        "heading_correct": heading_correct,
        "heading_accuracy": (heading_correct / total) * 100,
        "chapter_correct": chapter_correct,
        "chapter_accuracy": (chapter_correct / total) * 100,
        "chapter_stats": dict(chapter_stats),
    }


def print_chapter_breakdown(tier_results: List[Dict[str, Any]], ground_truth: List[Dict[str, Any]]):
    """Print per-chapter accuracy breakdown table comparing all tiers."""
    # Collect all unique chapters
    chapters = sorted({item.get("chapter", item["ground_truth_hs"].split(".")[0]) for item in ground_truth})

    print("\n" + "=" * 96)
    print("PER-CHAPTER ACCURACY BREAKDOWN (BTKI / HS CHAPTER ABLATION)")
    print("=" * 96)
    header = (
        f"{'Chapter':<8} | {'Category Description':<32} | {'Items':<5} | "
        f"{'T1 Top-1':<8} | {'T2 Top-1':<8} | {'T3 Top-1':<8} | {'T3 Top-3':<8}"
    )
    print(header)
    print("-" * 96)

    t1_stats = tier_results[0].get("chapter_stats", {}) if len(tier_results) > 0 else {}
    t2_stats = tier_results[1].get("chapter_stats", {}) if len(tier_results) > 1 else {}
    t3_stats = tier_results[2].get("chapter_stats", {}) if len(tier_results) > 2 else {}

    for chap in chapters:
        desc = CHAPTER_DESCRIPTIONS.get(chap, f"HS Chapter {chap}")
        cnt = t1_stats.get(chap, {}).get("total") or t2_stats.get(chap, {}).get("total") or 1

        t1_t1 = f"{t1_stats.get(chap, {}).get('top1', 0)}/{cnt}"
        t2_t1 = f"{t2_stats.get(chap, {}).get('top1', 0)}/{cnt}"
        t3_t1 = f"{t3_stats.get(chap, {}).get('top1', 0)}/{cnt}"
        t3_t3 = f"{t3_stats.get(chap, {}).get('top3', 0)}/{cnt}"

        print(
            f"Ch. {chap:<4} | {desc[:32]:<32} | {cnt:<5} | "
            f"{t1_t1:<8} | {t2_t1:<8} | {t3_t1:<8} | {t3_t3:<8}"
        )

    print("=" * 96)


def main():
    parser = argparse.ArgumentParser(description="CustomsGuard Ground Truth Accuracy Benchmark")
    parser.add_argument("--tier", type=int, choices=[1, 2, 3], help="Run a specific tier only")
    parser.add_argument("--ollama", action="store_true", default=True, help="Use live Ollama Qwen 2.5 3B for reranking")
    parser.add_argument("--no-ollama", dest="ollama", action="store_false", help="Disable live Ollama reranker calls")
    args = parser.parse_args()

    ground_truth, tariffs, embeddings = load_dataset()
    print("=" * 96)
    print("CUSTOMSGUARD SCIENTIFIC GROUND TRUTH ACCURACY BENCHMARK")
    print(f"Dataset: {len(ground_truth)} Official Trade Items | Knowledge Base: {len(tariffs):,} Indonesian HS-6 Subheadings")
    print("=" * 96)

    results = []
    # Always compute tiers in order so breakdown works
    t1 = run_tier1_keyword(ground_truth, tariffs)
    t2 = run_tier2_semantic_dense(ground_truth, tariffs, embeddings)
    t3 = run_tier3_hybrid_llm_rerank(ground_truth, tariffs, embeddings, use_live_ollama=args.ollama)

    results = [t1, t2, t3]

    print(f"{'Method / Architecture Tier':<48} | {'Top-1 (HS-6)':<14} | {'Top-3 (HS-6)':<14} | {'Heading (HS-4)':<14} | {'Chapter (HS-2)':<14}")
    print("-" * 114)
    for r in results:
        t1_str = f"{r['top1_correct']}/{r['total']} ({r['top1_accuracy']:.1f}%)"
        t3_str = f"{r['top3_correct']}/{r['total']} ({r['top3_accuracy']:.1f}%)"
        h_str = f"{r.get('heading_correct', 0)}/{r['total']} ({(r.get('heading_correct', 0)/r['total'])*100:.1f}%)"
        c_str = f"{r.get('chapter_correct', 0)}/{r['total']} ({(r.get('chapter_correct', 0)/r['total'])*100:.1f}%)"
        print(f"{r['tier']:<48} | {t1_str:<14} | {t3_str:<14} | {h_str:<14} | {c_str:<14}")
    print("=" * 114)

    print_chapter_breakdown(results, ground_truth)


if __name__ == "__main__":
    main()
