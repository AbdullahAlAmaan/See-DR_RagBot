from __future__ import annotations
from typing import List, Dict
import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup() -> None:
	"""Initialize FastAPI application on startup.
	
	Loads configuration and ensures required directories exist.
	"""
	# Preload config and ensure dirs
	app.state.cfg = load_config()
	ensure_directories(app.state.cfg)


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
	
	cfg: AppConfig = app.state.cfg
	index, metadata = load_faiss_index(cfg)
	retriever = Retriever(cfg, index, metadata)
	
	# Expand query for treatment-related questions to improve retrieval
	expanded_query = req.query
	query_lower = req.query.lower()
	if any(word in query_lower for word in ['treat', 'treatment', 'therapy', 'cure', 'medication', 'drug', 'procedure']):
		expanded_query = f"{req.query} treatment methods procedures medications therapies"
	
	top = retriever.retrieve(expanded_query, top_k=req.k)
	prompt = build_prompt(req.query, top)
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
