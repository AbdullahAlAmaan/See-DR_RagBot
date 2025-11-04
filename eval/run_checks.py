import math
import os
import re
import sys
from typing import Dict, List, Optional, Tuple

import requests


def resolve_api_url(cli_url: Optional[str]) -> str:
    # Priority: CLI arg -> ENV var -> probe common candidates
    if cli_url:
        return cli_url.rstrip("/") + "/query"
    env_url = os.getenv("API_URL")
    if env_url:
        return env_url.rstrip("/") + "/query"
    candidates = [
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://0.0.0.0:8000",
    ]
    for base in candidates:
        try:
            # Probe FastAPI docs or health via GET /docs (best effort)
            requests.get(base + "/docs", timeout=2)
            return base + "/query"
        except Exception:
            continue
    # Fallback to default
    return "http://127.0.0.1:8000/query"


def ndcg_at_k(relevances: List[int]) -> float:
    dcg = sum((2 ** r - 1) / math.log2(i + 2) for i, r in enumerate(relevances))
    idcg = sum((2 ** 1 - 1) / math.log2(i + 2) for i in range(sum(relevances)))
    return dcg / idcg if idcg else 0.0


def jaccard_overlap(a: str, b: str) -> float:
    tokens_a = set(re.findall(r"\w+", a.lower()))
    tokens_b = set(re.findall(r"\w+", b.lower()))
    union = tokens_a | tokens_b
    return len(tokens_a & tokens_b) / len(union) if union else 0.0


def faithfulness_ratio(answer: str, sources: List[Dict], threshold: float = 0.35) -> float:
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", answer.strip()) if s.strip()]
    if not sentences:
        return 0.0
    supported = 0
    for sent in sentences:
        best = 0.0
        for src in sources:
            src_text = src.get("text", "")
            best = max(best, jaccard_overlap(sent, src_text))
        if best >= threshold:
            supported += 1
    return supported / len(sentences)


def evaluate_query(api_query_url: str, query: str, expected_titles: List[str], k: int = 5) -> Dict:
    resp = requests.post(api_query_url, json={"query": query, "k": k}, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    titles = [s.get("metadata", {}).get("title", "") for s in data.get("sources", [])]
    relevances = [1 if t in expected_titles else 0 for t in titles[:k]]
    p_at_k = sum(relevances) / min(len(expected_titles), k) if expected_titles else 0.0
    ndcg = ndcg_at_k(relevances)
    faithful = faithfulness_ratio(data.get("answer", ""), data.get("sources", []))
    return {
        "query": query,
        "P@%d" % k: round(p_at_k, 3),
        "nDCG@%d" % k: round(ndcg, 3),
        "faithfulness": round(faithful, 3),
        "retrieved_titles": titles,
    }


def main() -> None:
    # Seed test set (edit as needed)
    tests: List[Tuple[str, List[str]]] = [
        ("What are the main screening methods for diabetic retinopathy?", ["503.full", "s41598-021-93632-8"]),
        ("What treatments are recommended for proliferative diabetic retinopathy?", ["95881", "503.full"]),
        ("How does OCT help in diagnosing diabetic macular edema?", ["95881", "s41591-023-02702-z"]),
    ]

    # CLI: python eval/run_checks.py [k] [api_base_url]
    k = 5
    api_cli = None
    if len(sys.argv) > 1:
        try:
            k = int(sys.argv[1])
        except Exception:
            api_cli = sys.argv[1]
    if len(sys.argv) > 2:
        api_cli = sys.argv[2]

    api_query_url = resolve_api_url(api_cli)

    for q, expect in tests:
        try:
            res = evaluate_query(api_query_url, q, expect, k)
            print({"api": api_query_url, **res})
        except Exception as e:
            print({"api": api_query_url, "query": q, "error": str(e)})


if __name__ == "__main__":
    main()


