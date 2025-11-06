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
	"""Retrieves relevant documents from a FAISS vector index using semantic search.
	
	Supports optional reranking with cross-encoder models and similarity threshold filtering
	to improve retrieval quality.
	"""
	
	def __init__(self, cfg: AppConfig, index: faiss.Index, metadata: List[Dict], embedder: EmbeddingModel | None = None) -> None:
		"""Initialize the Retriever with configuration, index, and metadata.
		
		Args:
			cfg: Application configuration.
			index: Pre-built FAISS index containing document embeddings.
			metadata: List of metadata dictionaries corresponding to index vectors.
			embedder: Optional preloaded EmbeddingModel. If None, creates a new one.
		"""
		self.cfg = cfg
		self.index = index
		self.metadata = metadata
		self.embedder = embedder or EmbeddingModel(cfg.models.embedding_model)
		# Lazy-load reranker only when needed to save memory
		self._reranker = None
		self._reranker_model_name = cfg.models.reranker_model if _RERANK_AVAILABLE else None

	def retrieve(self, query: str, top_k: int | None = None) -> List[Dict]:
		"""Retrieve top-k relevant documents for a given query.
		
		Performs semantic search using the FAISS index, optionally filters by similarity
		threshold, and applies cross-encoder reranking if available for improved relevance.
		
		Args:
			query: The search query string.
			top_k: Number of documents to retrieve. If None, uses config default.
			
		Returns:
			List of dictionaries containing retrieved document chunks with metadata.
			Each dictionary contains 'text' and 'metadata' keys.
		"""
		k = top_k or self.cfg.retrieval.top_k
		q = self.embedder.embed_texts([query])
		faiss.normalize_L2(q)
		
		# Retrieve enough candidates to ensure we have k results after filtering by similarity
		rerank_n = self.cfg.retrieval.rerank_top_n
		min_sim = getattr(self.cfg.retrieval, 'min_similarity_score', 0.0)
		
		# Retrieve more candidates to account for similarity filtering
		# Use max(k, rerank_n) as minimum, but scale up if filtering is enabled
		# to increase chances of getting k results after filtering
		search_k = max(k, rerank_n)
		if min_sim > 0.0:
			# If filtering is enabled, retrieve more candidates to compensate
			# Multiply by a factor to account for potential filtering
			search_k = max(k * 3, rerank_n * 2, search_k)
		
		# Cap at index size to avoid errors
		max_search = min(search_k, self.index.ntotal) if hasattr(self.index, 'ntotal') else search_k
		dists, idxs = self.index.search(q, max_search)
		
		# Filter by similarity threshold if configured
		cand_ids = []
		for dist, idx in zip(dists[0], idxs[0]):
			if idx >= 0 and (1.0 - dist) >= min_sim:  # Convert distance to similarity
				cand_ids.append(idx)
		
		cands = [self.metadata[i] for i in cand_ids]

		# Optional reranking for better relevance (lazy-loaded to save memory)
		if self._reranker_model_name is not None and len(cands) > k:
			if self._reranker is None:
				self._reranker = CrossEncoder(self._reranker_model_name)
			pairs = [(query, c.get("text", "")) for c in cands]
			scores = self._reranker.predict(pairs).tolist()
			scored = sorted(zip(cands, scores), key=lambda x: x[1], reverse=True)
			# Return top k after reranking
			return [c for c, _ in scored[:k]]
		
		# Return top k without reranking
		return cands[:k]
