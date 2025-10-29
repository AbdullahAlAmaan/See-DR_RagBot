#!/usr/bin/env python3
"""Pre-download all models used by See-DR RAGBot"""
import sys
import os

REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from see_dr_ragbot.config import load_config

print("Loading configuration...")
cfg = load_config()

print(f"Downloading embedding model: {cfg.models.embedding_model}")
from sentence_transformers import SentenceTransformer
SentenceTransformer(cfg.models.embedding_model)
print("✓ Embedding model downloaded")

try:
    print(f"Downloading reranker model: {cfg.models.reranker_model}")
    from sentence_transformers import CrossEncoder
    CrossEncoder(cfg.models.reranker_model)
    print("✓ Reranker model downloaded")
except Exception as e:
    print(f"⚠ Reranker model not available (optional): {e}")

try:
    print(f"\nDownloading LayoutLMv3 model: microsoft/layoutlmv3-base")
    from transformers import AutoProcessor, AutoModelForTokenClassification
    AutoProcessor.from_pretrained("microsoft/layoutlmv3-base")
    AutoModelForTokenClassification.from_pretrained("microsoft/layoutlmv3-base")
    print("✓ LayoutLMv3 model downloaded")
except Exception as e:
    print(f"⚠ LayoutLMv3 not available (optional, will use fallback): {e}")

print("\n✓ All models downloaded successfully!")
print(f"\nNote: LLM model '{cfg.models.llm_model}' must be pulled via Ollama:")
print(f"  ollama pull {cfg.models.llm_model}")

