import os
import json
from typing import List, Dict, Tuple

import numpy as np
import faiss

from ..embeddings.embedding import EmbeddingModel
from ..config import AppConfig
from ..logging_utils import get_logger


logger = get_logger(__name__)


INDEX_FILE = "index.faiss"
META_FILE = "metadata.jsonl"


def _load_chunks(processed_dir: str) -> List[Dict]:
	chunks: List[Dict] = []
	for name in os.listdir(processed_dir):
		if not name.endswith(".jsonl"):
			continue
		with open(os.path.join(processed_dir, name), "r", encoding="utf-8") as f:
			for line in f:
				line = line.strip()
				if not line:
					continue
				try:
					chunks.append(json.loads(line))
				except Exception:
					continue
	return chunks


def _build_embeddings(embedding_model: EmbeddingModel, chunks: List[Dict]) -> np.ndarray:
	texts = [c.get("text", "") for c in chunks]
	embs = embedding_model.embed_texts(texts)
	# ensure normalized for cosine similarity via inner product
	faiss.normalize_L2(embs)
	return embs


def build_faiss_index(cfg: AppConfig) -> Tuple[str, str, int]:
	chunks = _load_chunks(cfg.paths.processed_dir)
	if not chunks:
		raise RuntimeError("No chunks found. Run ingestion first.")
	embedding_model = EmbeddingModel(cfg.models.embedding_model)
	embs = _build_embeddings(embedding_model, chunks)
	dim = embs.shape[1]
	index = faiss.IndexFlatIP(dim)
	index.add(embs)

	# persist
	os.makedirs(cfg.paths.vector_store_dir, exist_ok=True)
	index_path = os.path.join(cfg.paths.vector_store_dir, INDEX_FILE)
	faiss.write_index(index, index_path)

	meta_path = os.path.join(cfg.paths.vector_store_dir, META_FILE)
	with open(meta_path, "w", encoding="utf-8") as f:
		for i, ch in enumerate(chunks):
			record = {"id": i, "text": ch.get("text", ""), "metadata": ch.get("metadata", {})}
			f.write(json.dumps(record, ensure_ascii=False) + "\n")

	logger.info(f"Built FAISS index with {len(chunks)} vectors @ {index_path}")
	return index_path, meta_path, len(chunks)


def load_faiss_index(cfg: AppConfig) -> Tuple[faiss.Index, List[Dict]]:
	index_path = os.path.join(cfg.paths.vector_store_dir, INDEX_FILE)
	meta_path = os.path.join(cfg.paths.vector_store_dir, META_FILE)
	if not os.path.exists(index_path) or not os.path.exists(meta_path):
		raise RuntimeError("Vector store not found. Build the index first.")
	index = faiss.read_index(index_path)
	metadata: List[Dict] = []
	with open(meta_path, "r", encoding="utf-8") as f:
		for line in f:
			line = line.strip()
			if not line:
				continue
			try:
				metadata.append(json.loads(line))
			except Exception:
				continue
	return index, metadata
