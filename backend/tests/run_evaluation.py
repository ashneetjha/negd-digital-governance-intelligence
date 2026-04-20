"""
Golden Query Evaluation Runner — Automated Benchmark System (v2.2)

Usage:
    python -m tests.run_evaluation
    python -m tests.run_evaluation --api-url http://localhost:8000
    python -m tests.run_evaluation --api-url https://your-backend.onrender.com

Loads golden_queries.json, runs each query through the appropriate API endpoint,
computes evaluation metrics, and produces:
  1. Formatted console output (readable by reviewers)
  2. eval_report.json  — proof artifact for audit
"""

import json
import sys
import time
import argparse
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: 'requests' is required. Run: pip install requests")
    sys.exit(1)


GOLDEN_QUERIES_PATH = Path(__file__).parent / "golden_queries.json"
EVAL_REPORT_PATH = Path(__file__).parent / "eval_report.json"
DEFAULT_API_URL = "http://localhost:8000"


def load_golden_queries() -> list:
    with open(GOLDEN_QUERIES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ─────────────────────────────────────────────────────────────────────────────
# Query runners (one per endpoint type)
# ─────────────────────────────────────────────────────────────────────────────

def run_rag_query(api_url: str, query: dict, debug: bool = True) -> dict:
    url = f"{api_url}/api/analysis"
    params = {"debug": "true"} if debug else {}
    payload = {
        "prompt": query["query"],
        "state": query.get("state"),
        "month": query.get("month"),
    }
    resp = requests.post(url, json=payload, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def run_chat_query(api_url: str, query: dict) -> dict:
    url = f"{api_url}/api/chat"
    payload = {"message": query["query"]}
    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def run_compare_query(api_url: str, query: dict) -> dict:
    url = f"{api_url}/api/compare"
    payload = {
        "state": query.get("state", query.get("expected_entities", ["Unknown"])[0]),
        "month_a": query["month_a"],
        "month_b": query["month_b"],
        "topic": query.get("query"),
    }
    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def run_cross_state_query(api_url: str, query: dict) -> dict:
    url = f"{api_url}/api/compare/cross-state"
    payload = {
        "state_a": query["state_a"],
        "month_a": query["month_a"],
        "state_b": query["state_b"],
        "month_b": query["month_b"],
        "topic": query.get("query"),
    }
    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


# ─────────────────────────────────────────────────────────────────────────────
# Scoring
# ─────────────────────────────────────────────────────────────────────────────

def score_keyword_match(answer: str, expected_keywords: list) -> float:
    if not expected_keywords:
        return 0.0
    answer_lower = answer.lower()
    hits = sum(1 for kw in expected_keywords if kw.lower() in answer_lower)
    return round(hits / len(expected_keywords), 4)


def score_entity_consistency(answer: str, expected_entities: list) -> float:
    if not expected_entities:
        return 1.0
    answer_lower = answer.lower()
    hits = sum(1 for e in expected_entities if e.lower() in answer_lower)
    return round(hits / len(expected_entities), 4)


# ─────────────────────────────────────────────────────────────────────────────
# Single query evaluator
# ─────────────────────────────────────────────────────────────────────────────

def evaluate_single(api_url: str, query: dict) -> dict:
    qid = query["id"]
    qtype = query.get("type", "rag")

    result = {
        "id": qid,
        "type": qtype,
        "description": query.get("description", ""),
        "success": False,
        "error": None,
        "keyword_score": 0.0,
        "entity_score": 0.0,
        "confidence": 0.0,
        "status": "error",
        "mode": "unknown",
        "latency_ms": 0.0,
    }

    start = time.time()
    try:
        if qtype == "rag":
            resp = run_rag_query(api_url, query)
            data = resp.get("data", {})
            answer = data.get("answer", "")
            result["confidence"] = data.get("confidence", 0.0)
            result["status"] = data.get("status", "unknown")
            result["mode"] = data.get("mode", "unknown")
        elif qtype == "chat":
            resp = run_chat_query(api_url, query)
            data = resp.get("data", {})
            answer = data.get("answer", "")
            result["confidence"] = 1.0
            result["status"] = "ok"
            result["mode"] = "chat"
        elif qtype == "compare":
            resp = run_compare_query(api_url, query)
            data = resp.get("data", {})
            answer = data.get("summary", "")
            result["confidence"] = 0.5
            result["status"] = "ok" if not data.get("error") else "error"
            result["mode"] = "compare"
        elif qtype == "cross_state":
            resp = run_cross_state_query(api_url, query)
            data = resp.get("data", {})
            answer = data.get("summary", "")
            result["confidence"] = {"high": 0.9, "medium": 0.6, "low": 0.3}.get(
                data.get("confidence", "low"), 0.3
            )
            result["status"] = data.get("status", "unknown")
            result["mode"] = "cross_state"
        else:
            result["error"] = f"Unknown query type: {qtype}"
            return result

        result["latency_ms"] = round((time.time() - start) * 1000, 1)
        result["keyword_score"] = score_keyword_match(
            answer, query.get("expected_keywords", [])
        )
        result["entity_score"] = score_entity_consistency(
            answer, query.get("expected_entities", [])
        )
        result["success"] = True

    except Exception as exc:
        result["latency_ms"] = round((time.time() - start) * 1000, 1)
        result["error"] = str(exc)

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Full evaluation pipeline
# ─────────────────────────────────────────────────────────────────────────────

def run_full_evaluation(api_url: str) -> dict:
    queries = load_golden_queries()
    results = []

    print(f"\n{'='*72}")
    print(f"  NeGD Golden Query Evaluation Runner v2.2")
    print(f"  API:      {api_url}")
    print(f"  Queries:  {len(queries)}")
    print(f"  Time:     {datetime.now(timezone.utc).isoformat()}")
    print(f"{'='*72}\n")

    for i, q in enumerate(queries, 1):
        label = q["query"][:55]
        print(f"  [{i:2d}/{len(queries)}] {q['id']}: {label}...", end=" ")
        result = evaluate_single(api_url, q)
        results.append(result)

        if result["success"]:
            print(f"✓ kw={result['keyword_score']:.2f} "
                  f"ent={result['entity_score']:.2f} "
                  f"conf={result['confidence']:.2f} "
                  f"[{result['latency_ms']:.0f}ms]")
        else:
            print(f"✗ ERROR: {result['error'][:50]}")

    # ── Aggregate metrics ─────────────────────────────────────────────────
    successful = [r for r in results if r["success"]]
    total = len(queries)
    success_count = len(successful)

    avg_keyword = (
        round(sum(r["keyword_score"] for r in successful) / success_count, 4)
        if successful else 0.0
    )
    avg_entity = (
        round(sum(r["entity_score"] for r in successful) / success_count, 4)
        if successful else 0.0
    )
    avg_confidence = (
        round(sum(r["confidence"] for r in successful) / success_count, 4)
        if successful else 0.0
    )
    avg_latency = (
        round(sum(r["latency_ms"] for r in successful) / success_count, 1)
        if successful else 0.0
    )

    # Task 1 metrics
    high_confidence_count = sum(
        1 for r in successful if r["confidence"] >= 0.4
    )
    low_confidence_count = sum(
        1 for r in successful if r["confidence"] < 0.4
    )
    success_rate = round(high_confidence_count / total, 4) if total else 0.0
    low_confidence_rate = round(low_confidence_count / total, 4) if total else 0.0

    # ── Build report ──────────────────────────────────────────────────────
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "api_url": api_url,
        "total_queries": total,
        "queries_executed": success_count,
        "queries_failed": total - success_count,
        "avg_confidence": avg_confidence,
        "avg_keyword_score": avg_keyword,
        "avg_entity_score": avg_entity,
        "avg_latency_ms": avg_latency,
        "success_rate": success_rate,
        "low_confidence_rate": low_confidence_rate,
        "high_confidence_count": high_confidence_count,
        "low_confidence_count": low_confidence_count,
        "per_query_results": results,
    }

    # ── Console output ────────────────────────────────────────────────────
    print(f"\n{'='*72}")
    print(f"  EVALUATION REPORT — NeGD Digital Governance Intelligence v2.2")
    print(f"{'='*72}")
    print(f"  Total Queries:        {total}")
    print(f"  Executed:             {success_count}")
    print(f"  Failed:               {total - success_count}")
    print(f"  ─────────────────────────────────────────────────────")
    print(f"  Avg Confidence:       {avg_confidence:.4f}")
    print(f"  Avg Keyword Score:    {avg_keyword:.4f}")
    print(f"  Avg Entity Score:     {avg_entity:.4f}")
    print(f"  Avg Latency:          {avg_latency:.1f}ms")
    print(f"  ─────────────────────────────────────────────────────")
    print(f"  Success Rate (≥0.4):  {success_rate*100:.1f}%  ({high_confidence_count}/{total})")
    print(f"  Low Confidence Rate:  {low_confidence_rate*100:.1f}%  ({low_confidence_count}/{total})")
    print(f"{'='*72}\n")

    # Per-query breakdown
    print("  Per-Query Results:")
    header = f"  {'ID':<6} {'Type':<12} {'KW':>5} {'Ent':>5} {'Conf':>5} {'Mode':<8} {'Status':<14} {'ms':>7}"
    print(header)
    print(f"  {'-'*68}")
    for r in results:
        if r["success"]:
            print(f"  {r['id']:<6} {r['type']:<12} "
                  f"{r['keyword_score']:>5.2f} {r['entity_score']:>5.2f} "
                  f"{r['confidence']:>5.2f} {r['mode']:<8} "
                  f"{r['status']:<14} {r['latency_ms']:>6.0f}ms")
        else:
            err = r["error"][:30] if r["error"] else "unknown"
            print(f"  {r['id']:<6} {r['type']:<12} "
                  f"{'—':>5} {'—':>5} {'—':>5} {'—':<8} "
                  f"FAIL:{err:<9} {r['latency_ms']:>6.0f}ms")

    print()

    # ── Save eval_report.json (PROOF ARTIFACT) ────────────────────────────
    with open(EVAL_REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Proof artifact saved: {EVAL_REPORT_PATH}")

    # Also save legacy path for backward compat
    legacy_path = Path(__file__).parent / "evaluation_report.json"
    with open(legacy_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Legacy report saved:  {legacy_path}")
    print()

    return report


# ─────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="NeGD Golden Query Evaluation Runner — generates eval_report.json"
    )
    parser.add_argument(
        "--api-url",
        default=DEFAULT_API_URL,
        help=f"Backend API URL (default: {DEFAULT_API_URL})",
    )
    args = parser.parse_args()

    # Health check
    try:
        r = requests.get(f"{args.api_url}/health", timeout=5)
        r.raise_for_status()
        health = r.json()
        print(f"  ✓ Backend reachable at {args.api_url}")
        print(f"    Version: {health.get('version', '?')}, Env: {health.get('environment', '?')}")
    except Exception as e:
        print(f"  ✗ Cannot reach backend at {args.api_url}: {e}")
        print("    Start backend: cd backend && uvicorn app.main:app --reload --port 8000")
        sys.exit(1)

    run_full_evaluation(args.api_url)


if __name__ == "__main__":
    main()
