from typing import List, Dict

# Placeholder for evaluation metrics implementation

def evaluate_precision_at_k(ground_truth: List[str], retrieved: List[str], k: int = 5) -> float:
	if not ground_truth:
		return 0.0
	retrieved_at_k = set(retrieved[:k])
	gt = set(ground_truth)
	return len(retrieved_at_k & gt) / min(len(gt), k)
