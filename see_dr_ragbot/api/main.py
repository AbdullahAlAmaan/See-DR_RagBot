from __future__ import annotations
from typing import List, Dict
import asyncio

from fastapi import FastAPI
from pydantic import BaseModel

from ..config import load_config, ensure_directories, AppConfig
from ..ingestion.ingest import ingest_directory
from ..vector_store.faiss_store import load_faiss_index
from ..retrieval.retriever import Retriever
from ..rag.prompt import build_prompt
from ..llm.ollama_client import OllamaClient


class QueryRequest(BaseModel):
	query: str
	k: int | None = None


class QueryResponse(BaseModel):
	answer: str
	sources: List[Dict]


app = FastAPI(title="See-DR RAGBot API")


@app.on_event("startup")
async def on_startup() -> None:
	# Preload config and ensure dirs
	app.state.cfg = load_config()
	ensure_directories(app.state.cfg)


@app.post("/ingest")
async def ingest() -> Dict:
	cfg: AppConfig = app.state.cfg
	written = ingest_directory(cfg)
	return {"processed_files": len(written), "outputs": written}


@app.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest) -> QueryResponse:
	cfg: AppConfig = app.state.cfg
	index, metadata = load_faiss_index(cfg)
	retriever = Retriever(cfg, index, metadata)
	top = retriever.retrieve(req.query, top_k=req.k)
	prompt = build_prompt(req.query, top)
	client = OllamaClient(cfg)
	answer = await client.generate(prompt)
	return QueryResponse(answer=answer, sources=top)


@app.post("/evaluate")
async def evaluate(payload: Dict) -> Dict:
	# Placeholder: later add retrieval precision, etc.
	return {"status": "ok"}
