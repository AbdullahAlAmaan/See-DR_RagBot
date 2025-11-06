from __future__ import annotations
from typing import List, Dict
import asyncio
import os
import sys

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..config import load_config, ensure_directories, AppConfig
from ..ingestion.ingest import ingest_directory
from ..vector_store.faiss_store import load_faiss_index
from ..retrieval.retriever import Retriever
from ..rag.prompt import build_prompt
from ..llm.gemini_client import GeminiClient


class QueryRequest(BaseModel):
	"""Request model for querying the RAG system.
	
	Attributes:
		query: The user's question or query string.
		k: Optional number of top results to retrieve. If None, uses default from config.
	"""
	query: str
	k: int | None = None


class QueryResponse(BaseModel):
	"""Response model containing the generated answer and source citations.
	
	Attributes:
		answer: The generated answer from the LLM.
		sources: List of retrieved source documents with metadata and text chunks.
	"""
	answer: str
	sources: List[Dict]


app = FastAPI(title="See-DR RAGBot API")

# Add CORS middleware for frontend access
# Allow CORS from environment variable or default to all origins
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
if cors_origins == ["*"]:
    allow_origins = ["*"]
else:
    allow_origins = [origin.strip() for origin in cors_origins]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
	"""Global exception handler to catch all unhandled errors."""
	import traceback
	error_msg = str(exc)
	traceback_str = traceback.format_exc()
	print(f"Unhandled exception: {error_msg}", file=sys.stderr)
	print(traceback_str, file=sys.stderr)
	return JSONResponse(
		status_code=500,
		content={"error": error_msg, "path": str(request.url)}
	)


@app.on_event("startup")
async def on_startup() -> None:
	"""Initialize FastAPI application on startup.
	
	Loads configuration, ensures required directories exist, and preloads models
	to reduce cold start time on Render free tier.
	"""
	try:
		# Preload config and ensure dirs
		print("Loading configuration...", file=sys.stderr)
		app.state.cfg = load_config()
		print(f"Config loaded. Vector store dir: {app.state.cfg.paths.vector_store_dir}", file=sys.stderr)
		ensure_directories(app.state.cfg)
		
		# Check if vector store exists
		import os
		index_path = os.path.join(app.state.cfg.paths.vector_store_dir, "index.faiss")
		meta_path = os.path.join(app.state.cfg.paths.vector_store_dir, "metadata.jsonl")
		if not os.path.exists(index_path) or not os.path.exists(meta_path):
			print(f"WARNING: Vector store not found at {app.state.cfg.paths.vector_store_dir}", file=sys.stderr)
			print(f"  Looking for: {index_path} and {meta_path}", file=sys.stderr)
		else:
			print(f"Vector store found at {app.state.cfg.paths.vector_store_dir}", file=sys.stderr)
		
		# Check for API key
		api_key = os.getenv("GEMINI_API_KEY")
		if not api_key:
			print("WARNING: GEMINI_API_KEY not set in environment", file=sys.stderr)
		else:
			print("GEMINI_API_KEY found in environment", file=sys.stderr)
		
		# Preload only lightweight Gemini client (not embedding model to save memory)
		# Embedding model will be lazy-loaded on first request to avoid memory issues on free tier
		async def preload_gemini():
			try:
				from ..llm.gemini_client import GeminiClient
				print("Preloading Gemini client...", file=sys.stderr)
				app.state.gemini_client = GeminiClient(app.state.cfg)
				print("Gemini client loaded", file=sys.stderr)
			except Exception as e:
				import traceback
				print(f"Gemini client preload warning (will load on first request): {e}", file=sys.stderr)
				print(traceback.format_exc(), file=sys.stderr)
		
		# Start preloading Gemini client in background (don't await - let it run async)
		asyncio.create_task(preload_gemini())
		
		# Note: Embedding model is NOT preloaded to save memory on Render free tier
		# It will be loaded on first query request (lazy loading)
		app.state.embedding_model = None
		
	except Exception as e:
		# Log error but don't crash - allow health check to work
		import traceback
		print(f"CRITICAL: Startup error: {e}", file=sys.stderr)
		print(traceback.format_exc(), file=sys.stderr)
		# Set a default config so the app can still respond
		app.state.cfg = None


@app.get("/")
async def root() -> Dict:
	"""Root endpoint providing API information."""
	return {
		"service": "See-DR RAGBot API",
		"version": "1.0.0",
		"endpoints": {
			"health": "/health",
			"query": "/query (POST)",
			"ingest": "/ingest (POST)",
			"docs": "/docs",
			"openapi": "/openapi.json"
		}
	}


@app.get("/health")
async def health() -> Dict:
	"""Health check endpoint for monitoring.
	
	Returns:
		Dict with status and timestamp.
	"""
	try:
		status = "ok"
		if not hasattr(app.state, 'cfg') or app.state.cfg is None:
			status = "degraded"
		models_loaded = {
			"embedding": hasattr(app.state, 'embedding_model') and app.state.embedding_model is not None,
			"gemini": hasattr(app.state, 'gemini_client') and app.state.gemini_client is not None
		}
		return {
			"status": status,
			"service": "See-DR RAGBot API",
			"models_loaded": models_loaded
		}
	except Exception as e:
		import traceback
		return {"status": "error", "service": "See-DR RAGBot API", "error": str(e)}


@app.post("/ingest")
async def ingest() -> Dict:
	"""Ingest PDF documents from the configured directory.
	
	Processes all PDFs in the configured directory, extracts text, chunks them,
	and saves to the processed directory.
	
	Returns:
		Dict containing:
			- processed_files: Number of files processed
			- outputs: List of output file paths
	"""
	cfg: AppConfig = app.state.cfg
	written = ingest_directory(cfg)
	return {"processed_files": len(written), "outputs": written}


@app.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest) -> QueryResponse:
	"""Process a user query and return an answer with source citations.
	
	Retrieves relevant documents from the vector store, builds a prompt with context,
	generates an answer using the LLM, and returns the answer with cleaned source citations.
	
	For treatment-related queries, automatically expands the query with relevant terms
	to improve retrieval quality.
	
	Args:
		req: QueryRequest containing the user's query and optional k parameter.
		
	Returns:
		QueryResponse with the generated answer and list of source citations.
	"""
	from ..ingestion.text_cleaner import clean_chunk_text
	from fastapi import HTTPException
	import os
	
	if app.state.cfg is None:
		raise HTTPException(status_code=503, detail="Service not fully initialized. Check logs for startup errors.")
	
	cfg: AppConfig = app.state.cfg
	
	# Check if vector store exists before trying to load
	index_path = os.path.join(cfg.paths.vector_store_dir, "index.faiss")
	meta_path = os.path.join(cfg.paths.vector_store_dir, "metadata.jsonl")
	if not os.path.exists(index_path) or not os.path.exists(meta_path):
		raise HTTPException(
			status_code=503,
			detail=f"Vector store not found. Expected files at {index_path} and {meta_path}. Please ensure the vector store is built and deployed."
		)
	
	try:
		index, metadata = load_faiss_index(cfg)
	except Exception as e:
		raise HTTPException(
			status_code=500,
			detail=f"Failed to load vector store: {str(e)}"
		)
	
	# Use preloaded embedding model if available, otherwise Retriever will lazy-load it
	# (Lazy loading saves memory on Render free tier)
	preloaded_embedder = None
	if hasattr(app.state, 'embedding_model') and app.state.embedding_model is not None:
		preloaded_embedder = app.state.embedding_model
	
	retriever = Retriever(cfg, index, metadata, embedder=preloaded_embedder)
	
	# Expand query for treatment-related questions to improve retrieval
	expanded_query = req.query
	query_lower = req.query.lower()
	if any(word in query_lower for word in ['treat', 'treatment', 'therapy', 'cure', 'medication', 'drug', 'procedure']):
		expanded_query = f"{req.query} treatment methods procedures medications therapies"
	
	top = retriever.retrieve(expanded_query, top_k=req.k)
	prompt = build_prompt(req.query, top)
	
	# Use preloaded Gemini client if available
	if hasattr(app.state, 'gemini_client') and app.state.gemini_client is not None:
		client = app.state.gemini_client
	else:
		client = GeminiClient(cfg)
	
	answer = await client.generate(prompt, max_tokens=500)  # Limit answer length
	
	# Clean sources for display
	cleaned_sources = []
	for source in top:
		cleaned = dict(source)
		cleaned["text"] = clean_chunk_text(source.get("text", ""))
		cleaned_sources.append(cleaned)
	
	return QueryResponse(answer=answer, sources=cleaned_sources)


@app.post("/evaluate")
async def evaluate(payload: Dict) -> Dict:
	"""Evaluate retrieval performance (placeholder endpoint).
	
	Args:
		payload: Evaluation payload containing queries and expected results.
		
	Returns:
		Dict with evaluation status. Currently returns placeholder response.
	"""
	# Placeholder: later add retrieval precision, etc.
	return {"status": "ok"}
