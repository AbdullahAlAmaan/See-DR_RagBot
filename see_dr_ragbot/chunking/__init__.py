"""Chunking utilities"""
from .semantic_chunker import semantic_chunk_with_overlap
# Import from the separate chunking.py file at parent level
import importlib.util
import os

# Load recursive_chunk from parent chunking.py
parent_path = os.path.dirname(os.path.dirname(__file__))
chunking_py_path = os.path.join(parent_path, "chunking.py")
spec = importlib.util.spec_from_file_location("chunking_module", chunking_py_path)
chunking_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(chunking_module)
recursive_chunk = chunking_module.recursive_chunk

__all__ = ["semantic_chunk_with_overlap", "recursive_chunk"]
