import os
import json
import hashlib
from typing import Dict, List, Iterable, Tuple

import pdfplumber

try:
	from unstructured.partition.pdf import partition_pdf  # type: ignore
	_UNSTRUCTURED_AVAILABLE = True
except Exception:
	_UNSTRUCTURED_AVAILABLE = False

from ..chunking import recursive_chunk, semantic_chunk_with_overlap
from ..config import AppConfig
from ..logging_utils import get_logger
from .text_cleaner import clean_text, clean_chunk_text

try:
    from .layoutlm_extractor import extract_with_layoutlm
    _LAYOUTLM_AVAILABLE = True
except Exception:
    _LAYOUTLM_AVAILABLE = False


logger = get_logger(__name__)


def _sha1(s: str) -> str:
	"""Generate SHA1 hash of a string.
	
	Args:
		s: Input string to hash.
		
	Returns:
		Hexadecimal representation of the SHA1 hash.
	"""
	return hashlib.sha1(s.encode("utf-8")).hexdigest()


def list_pdf_files(pdf_dir: str) -> List[str]:
	"""List all PDF files in a directory.
	
	Args:
		pdf_dir: Directory path to search for PDF files.
		
	Returns:
		Sorted list of full paths to PDF files found in the directory.
	"""
	paths: List[str] = []
	for name in os.listdir(pdf_dir):
		if name.lower().endswith(".pdf"):
			paths.append(os.path.join(pdf_dir, name))
	return sorted(paths)


def extract_with_unstructured(path: str) -> Tuple[str, List[Dict]]:
	"""Extract text from PDF using the unstructured library.
	
	Uses high-resolution extraction strategy with table structure inference
	for better layout-aware text extraction.
	
	Args:
		path: Path to the PDF file.
		
	Returns:
		Tuple of:
			- full_text: Complete extracted text as a single string.
			- page_level: List of page-level text chunks with metadata.
			
	Raises:
		RuntimeError: If unstructured library is not available.
	"""
	if not _UNSTRUCTURED_AVAILABLE:
		raise RuntimeError("unstructured not available")
	elements = partition_pdf(filename=path, strategy="hi_res", infer_table_structure=True)
	texts: List[str] = []
	page_level: List[Dict] = []
	for el in elements:
		text = str(getattr(el, "text", "") or "").strip()
		if not text:
			continue
		meta = {
			"type": el.category if hasattr(el, "category") else None,
			"page_number": getattr(el.metadata, "page_number", None) if hasattr(el, "metadata") else None,
		}
		page_level.append({"text": text, "metadata": meta})
		texts.append(text)
	full_text = "\n".join(texts)
	return full_text, page_level


def extract_with_pdfplumber(path: str) -> Tuple[str, List[Dict]]:
	"""Extract text from PDF using pdfplumber library (fallback method).
	
	Extracts text page by page with tolerance settings for better text recovery.
	
	Args:
		path: Path to the PDF file.
		
	Returns:
		Tuple of:
			- full_text: Complete extracted text as a single string.
			- page_level: List of page-level text chunks with metadata including page numbers.
	"""
	texts: List[str] = []
	page_level: List[Dict] = []
	with pdfplumber.open(path) as pdf:
		for i, page in enumerate(pdf.pages, start=1):
			try:
				text = page.extract_text(x_tolerance=2, y_tolerance=2) or ""
			except Exception:
				text = ""
			text = text.strip()
			if not text:
				continue
			page_level.append({"text": text, "metadata": {"page_number": i}})
			texts.append(text)
	full_text = "\n".join(texts)
	return full_text, page_level


def extract_pdf(path: str) -> Tuple[str, List[Dict]]:
	"""Extract text from PDF using the best available method.
	
	Tries extraction methods in order of preference:
	1. LayoutLMv3 (layout-aware extraction, if available)
	2. unstructured library (high-resolution with table structure)
	3. pdfplumber (fallback method)
	
	Args:
		path: Path to the PDF file.
		
	Returns:
		Tuple of:
			- full_text: Complete extracted text as a single string.
			- page_level: List of page-level text chunks with metadata.
	"""
	# Try LayoutLMv3 first (layout-aware), then unstructured, then pdfplumber
	if _LAYOUTLM_AVAILABLE:
		try:
			logger.info(f"Using LayoutLMv3 for {os.path.basename(path)}")
			return extract_with_layoutlm(path)
		except Exception as e:
			logger.debug(f"LayoutLMv3 failed: {e}, falling back...")
	
	try:
		return extract_with_unstructured(path)
	except Exception:
		logger.info(f"Falling back to pdfplumber for {os.path.basename(path)}")
		return extract_with_pdfplumber(path)


def build_doc_record(path: str) -> Dict:
	"""Build a document record from a PDF file path.
	
	Extracts text and metadata from a PDF file and creates a structured document record
	with ID, filename, title, and page-level elements. Text is cleaned during extraction.
	
	Args:
		path: Path to the PDF file.
		
	Returns:
		Dictionary containing:
			- id: SHA1 hash of the file path
			- filename: Base filename
			- title: Filename without extension
			- authors: None (placeholder)
			- doi: None (placeholder)
			- text: Full extracted and cleaned text
			- pages: List of page-level text chunks with metadata
	"""
	filename = os.path.basename(path)
	doc_id = _sha1(path)
	full_text, page_elements = extract_pdf(path)
	# Clean the full text
	full_text = clean_text(full_text)
	# Clean page-level elements too
	for page_elem in page_elements:
		if "text" in page_elem:
			page_elem["text"] = clean_text(page_elem["text"])
	return {
		"id": doc_id,
		"filename": filename,
		"title": os.path.splitext(filename)[0],
		"authors": None,
		"doi": None,
		"text": full_text,
		"pages": page_elements,
	}


def chunk_document(doc: Dict, cfg: AppConfig, use_semantic: bool = True) -> List[Dict]:
	"""Chunk a document into smaller text segments for retrieval.
	
	Uses semantic chunking by default, falling back to recursive chunking if semantic
	chunking fails. Enriches chunks with metadata and page numbers based on text overlap.
	All chunk text is cleaned during processing.
	
	Args:
		doc: Document dictionary containing 'id', 'title', 'filename', 'text', and 'pages'.
		cfg: Application configuration for chunking parameters.
		use_semantic: Whether to attempt semantic chunking first (default: True).
		
	Returns:
		List of chunk dictionaries, each containing:
			- text: Cleaned chunk text
			- metadata: Dictionary with doc_id, title, filename, and page_number
	"""
	base = {
		"doc_id": doc["id"],
		"title": doc["title"],
		"filename": doc["filename"],
	}
	
	if use_semantic:
		# Use semantic chunking with overlap
		try:
			chunks = semantic_chunk_with_overlap(
				text=doc.get("text", ""),
				cfg=cfg,
				similarity_threshold=cfg.chunking.similarity_threshold,
			)
			# Merge base metadata into each chunk and clean chunk text
			for ch in chunks:
				ch["text"] = clean_chunk_text(ch.get("text", ""))
				ch["metadata"] = {**ch.get("metadata", {}), **base}
		except Exception as e:
			logger.warning(f"Semantic chunking failed: {e}, falling back to basic chunker")
			use_semantic = False
	
	if not use_semantic:
		# Fallback to basic chunker
		chunks = recursive_chunk(
			text=doc.get("text", ""),
			target_tokens=cfg.chunking.target_tokens,
			max_tokens=cfg.chunking.max_tokens,
			min_tokens=cfg.chunking.min_tokens,
			metadata=base,
		)
		# Clean chunk texts
		for ch in chunks:
			ch["text"] = clean_chunk_text(ch.get("text", ""))
	
	# Enrich with page hints via simple overlap heuristic
	for ch in chunks:
		ch_text = ch["text"]
		best_page = None
		best_overlap = 0
		for page in doc.get("pages", []):
			page_text = page.get("text", "")
			if not page_text:
				continue
			overlap = sum(1 for w in ch_text.split() if w in page_text)
			if overlap > best_overlap:
				best_overlap = overlap
				best_page = page.get("metadata", {}).get("page_number")
		if best_page:
			ch["metadata"]["page_number"] = best_page
	
	return chunks


def save_chunks(doc: Dict, chunks: List[Dict], out_dir: str) -> str:
	"""Save document chunks to a JSONL file.
	
	Each chunk is written as a single JSON object on one line, with the filename
	based on the document ID.
	
	Args:
		doc: Document dictionary containing 'id' for filename generation.
		chunks: List of chunk dictionaries to save.
		out_dir: Output directory path (created if it doesn't exist).
		
	Returns:
		Path to the saved JSONL file.
	"""
	os.makedirs(out_dir, exist_ok=True)
	out_path = os.path.join(out_dir, f"{doc['id']}.jsonl")
	with open(out_path, "w", encoding="utf-8") as f:
		for ch in chunks:
			f.write(json.dumps(ch, ensure_ascii=False) + "\n")
	return out_path


def ingest_directory(cfg: AppConfig) -> List[str]:
	"""Ingest all PDF files from the configured directory.
	
	Processes all PDF files in the configured directory: extracts text, chunks documents,
	cleans text, and saves chunks to JSONL files in the processed directory.
	
	Args:
		cfg: Application configuration containing paths and chunking settings.
		
	Returns:
		List of output file paths for the processed chunks.
	"""
	paths = list_pdf_files(cfg.paths.pdf_dir)
	logger.info(f"Found {len(paths)} PDFs in {cfg.paths.pdf_dir}")
	written: List[str] = []
	for p in paths:
		doc = build_doc_record(p)
		chunks = chunk_document(doc, cfg)
		out = save_chunks(doc, chunks, cfg.paths.processed_dir)
		written.append(out)
		logger.info(f"Processed {doc['filename']} -> {out}")
	return written
