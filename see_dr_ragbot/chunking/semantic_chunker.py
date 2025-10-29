"""Semantic chunking with overlap and similarity-based breaks"""
from __future__ import annotations
from typing import List, Dict, Optional
import numpy as np

from ..embeddings.embedding import EmbeddingModel
from ..config import AppConfig
from ..logging_utils import get_logger

logger = get_logger(__name__)


def semantic_chunk_with_overlap(
    text: str,
    cfg: AppConfig,
    embedding_model: Optional[EmbeddingModel] = None,
    similarity_threshold: float = 0.65,
) -> List[Dict]:
    """
    Chunk text semantically with overlap, using sentence similarity for breaks.
    
    Args:
        text: Input text
        cfg: Configuration
        embedding_model: Pre-initialized embedding model (optional)
        similarity_threshold: Minimum similarity to keep in same chunk (0.6-0.7 recommended)
    
    Returns:
        List of chunks with metadata including overlap info
    """
    # Simple sentence splitting
    sentences = []
    current = []
    bland_seps = [". ", "? ", "! "]
    for ch in text:
        current.append(ch)
        if ch in ".?!" and len(current) > 1 and current[-2] != ".":
            sent = "".join(current).strip()
            if sent:
                sentences.append(sent)
            current = []
    if current:
        sent = "".join(current).strip()
        if sent:
            sentences.append(sent)
    
    if not sentences:
        return []
    
    # Initialize embedding model if not provided
    if embedding_model is None:
        embedding_model = EmbeddingModel(cfg.models.embedding_model)
    
    # Compute sentence embeddings
    sentence_embeddings = embedding_model.embed_texts(sentences)
    
    # Compute overlaps
    overlap_tokens = int(cfg.chunking.target_tokens * 0.2)  # 20% overlap
    
    chunks: List[Dict] = []
    buf_indices: List[int] = []
    buf_tokens = 0
    chunk_id = 0
    
    def _tokens(sent_idx: int) -> int:
        return max(1, len(sentences[sent_idx].split()))
    
    def _flush() -> None:
        nonlocal chunk_id
        if not buf_indices:
            return
        
        chunk_text = " ".join(sentences[i] for i in buf_indices).strip()
        start_sent = buf_indices[0]
        end_sent = buf_indices[-1]
        
        chunks.append({
            "text": chunk_text,
            "tokens": buf_tokens,
            "metadata": {
                "chunk_id": chunk_id,
                "start_sentence": start_sent,
                "end_sentence": end_sent,
                "num_sentences": len(buf_indices),
            }
        })
        chunk_id += 1
    
    for i, sent in enumerate(sentences):
        sent_tokens = _tokens(i)
        
        # Check if adding this sentence would exceed max
        if buf_tokens + sent_tokens > cfg.chunking.max_tokens:
            _flush()
            buf_indices = []
            buf_tokens = 0
        
        # If buffer empty, start new chunk
        if not buf_indices:
            buf_indices.append(i)
            buf_tokens = sent_tokens
            continue
        
        # Check semantic similarity with last sentence in buffer
        if len(buf_indices) > 0:
            last_idx = buf_indices[-1]
            similarity = np.dot(
                sentence_embeddings[last_idx],
                sentence_embeddings[i]
            )
            
            # If similarity drops and we have enough tokens, break here
            if similarity < similarity_threshold and buf_tokens >= cfg.chunking.min_tokens:
                _flush()
                # Start new chunk with overlap
                overlap_start = max(0, len(buf_indices) - overlap_tokens // 10)
                buf_indices = buf_indices[overlap_start:] + [i]
                buf_tokens = sum(_tokens(j) for j in buf_indices)
            elif buf_tokens + sent_tokens <= cfg.chunking.target_tokens:
                buf_indices.append(i)
                buf_tokens += sent_tokens
            else:
                # Hit target size, flush and start with overlap
                _flush()
                overlap_start = max(0, len(buf_indices) - overlap_tokens // 10)
                buf_indices = buf_indices[overlap_start:] + [i]
                buf_tokens = sum(_tokens(j) for j in buf_indices)
        else:
            buf_indices.append(i)
            buf_tokens += sent_tokens
    
    _flush()
    
    return chunks

