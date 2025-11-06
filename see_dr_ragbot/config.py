from __future__ import annotations
import os
import yaml
from dataclasses import dataclass
from typing import Any, Dict
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv(override=True)


@dataclass
class PathsConfig:
	pdf_dir: str
	processed_dir: str
	vector_store_dir: str


@dataclass
class ModelsConfig:
	embedding_model: str
	reranker_model: str
	llm_model: str


@dataclass
class RetrievalConfig:
	top_k: int
	rerank_top_n: int
	min_similarity_score: float = 0.0


@dataclass
class ChunkingConfig:
	target_tokens: int
	max_tokens: int
	min_tokens: int
	overlap_percent: int = 20
	similarity_threshold: float = 0.65


@dataclass
class EnvConfig:
	offline: bool
	ollama_base_url: str


@dataclass
class AppConfig:
	paths: PathsConfig
	models: ModelsConfig
	retrieval: RetrievalConfig
	chunking: ChunkingConfig
	environment: EnvConfig


DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")


def _read_yaml(path: str) -> Dict[str, Any]:
	with open(path, "r", encoding="utf-8") as f:
		return yaml.safe_load(f) or {}


def _env_override(cfg: Dict[str, Any]) -> Dict[str, Any]:
	# Simple env overrides
	env_map = {
		"models.embedding_model": os.getenv("EMBEDDING_MODEL"),
		"models.reranker_model": os.getenv("RERANKER_MODEL"),
		"models.llm_model": os.getenv("LLM_MODEL"),
		"environment.ollama_base_url": os.getenv("OLLAMA_BASE_URL"),
		"paths.pdf_dir": os.getenv("PDF_DIR"),
		"paths.processed_dir": os.getenv("PROCESSED_DIR"),
		"paths.vector_store_dir": os.getenv("VECTOR_STORE_DIR"),
	}
	for dotted, value in env_map.items():
		if value is None:
			continue
		parts = dotted.split(".")
		node = cfg
		for key in parts[:-1]:
			node = node.setdefault(key, {})
		node[parts[-1]] = value
	return cfg


def load_config(path: str | None = None) -> AppConfig:
	cfg_path = path or DEFAULT_CONFIG_PATH
	data = _read_yaml(cfg_path)
	data = _env_override(data)

	# Resolve paths relative to config file location (project root)
	config_dir = os.path.dirname(os.path.abspath(cfg_path))
	paths_data = data["paths"].copy()
	
	# Only resolve relative paths (not absolute paths)
	if not os.path.isabs(paths_data.get("pdf_dir", "")):
		paths_data["pdf_dir"] = os.path.join(config_dir, paths_data.get("pdf_dir", ""))
	if not os.path.isabs(paths_data.get("processed_dir", "")):
		paths_data["processed_dir"] = os.path.join(config_dir, paths_data.get("processed_dir", ""))
	if not os.path.isabs(paths_data.get("vector_store_dir", "")):
		paths_data["vector_store_dir"] = os.path.join(config_dir, paths_data.get("vector_store_dir", ""))

	paths = PathsConfig(**paths_data)  # type: ignore[arg-type]
	models = ModelsConfig(**data["models"])  # type: ignore[arg-type]
	retrieval = RetrievalConfig(**data["retrieval"])  # type: ignore[arg-type]
	chunking = ChunkingConfig(**data["chunking"])  # type: ignore[arg-type]
	environment = EnvConfig(**data["environment"])  # type: ignore[arg-type]
	return AppConfig(paths=paths, models=models, retrieval=retrieval, chunking=chunking, environment=environment)


def ensure_directories(cfg: AppConfig) -> None:
	os.makedirs(cfg.paths.processed_dir, exist_ok=True)
	os.makedirs(cfg.paths.vector_store_dir, exist_ok=True)
