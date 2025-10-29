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
		dists, idxs = self.index.search(q, max(k, self.cfg.retrieval.rerank_top_n))
		cand_ids = idxs[0].tolist()
		cands = [self.metadata[i] for i in cand_ids if i >= 0]

		# optional reranking
		if self.reranker is not None and len(cands) > k:
			pairs = [(query, c.get("text", "")) for c in cands]
			scores = self.reranker.predict(pairs).tolist()
			scored = sorted(zip(cands, scores), key=lambda x: x[1], reverse=True)
			return [c for c, _ in scored[:k]]
		return cands[:k]
