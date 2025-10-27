from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer


class EmbeddingModel:
	def __init__(self, model_name: str) -> None:
		self.model = SentenceTransformer(model_name)

	def embed_texts(self, texts: List[str]) -> np.ndarray:
		if not texts:
			return np.zeros((0, self.model.get_sentence_embedding_dimension()), dtype=np.float32)
		embeddings = self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
		return embeddings.astype(np.float32)
