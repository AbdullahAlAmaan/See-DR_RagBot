from __future__ import annotations
from typing import List, Dict, Tuple
import numpy as np
import faiss

try:
	from sentence_transformers import CrossEncoder  # type: ignore
	_RERANK_AVAILABLE = True
except Exception:
	_RERANK_AVAILABLE = False

from ..embeddings.embedding import EmbeddingModel
from ..config import AppConfig


class Retriever:
	def __init__(self, cfg: AppConfig, index: faiss.Index, metadata: List[Dict]) -> None:
		self.cfg = cfg
		self.index = index
		self.metadata = metadata
		self.embedder = EmbeddingModel(cfg.models.embedding_model)
		self.reranker = CrossEncoder(cfg.models.reranker_model) if _RERANK_AVAILABLE else None

	def retrieve(self, query: str, top_k: int | None = None) -> List[Dict]:
		k = top_k or self.cfg.retrieval.top_k
		q = self.embedder.embed_texts([query])
		faiss.normalize_L2(q)
		
		# Retrieve more candidates for reranking
		rerank_n = self.cfg.retrieval.rerank_top_n
		dists, idxs = self.index.search(q, rerank_n)
		
		# Filter by similarity threshold if configured
		min_sim = getattr(self.cfg.retrieval, 'min_similarity_score', 0.0)
		cand_ids = []
		for dist, idx in zip(dists[0], idxs[0]):
			if idx >= 0 and (1.0 - dist) >= min_sim:  # Convert distance to similarity
				cand_ids.append(idx)
		
		cands = [self.metadata[i] for i in cand_ids]

		# Optional reranking for better relevance
		if self.reranker is not None and len(cands) > k:
			pairs = [(query, c.get("text", "")) for c in cands]
			scores = self.reranker.predict(pairs).tolist()
			scored = sorted(zip(cands, scores), key=lambda x: x[1], reverse=True)
			# Return top k after reranking
			return [c for c, _ in scored[:k]]
		
		# Return top k without reranking
		return cands[:k]
