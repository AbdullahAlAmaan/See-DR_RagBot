import argparse
from see_dr_ragbot.config import load_config, ensure_directories
from see_dr_ragbot.ingestion.ingest import ingest_directory
from see_dr_ragbot.vector_store.faiss_store import build_faiss_index


def main() -> None:
	parser = argparse.ArgumentParser(description="Build See-DR RAGBot FAISS Index")
	parser.add_argument("--config", type=str, default=None, help="Path to config.yaml (optional)")
	args = parser.parse_args()

	cfg = load_config(args.config)
	ensure_directories(cfg)
	print(f"Ingesting PDFs from {cfg.paths.pdf_dir} ...")
	ingest_directory(cfg)
	print("Building FAISS index ...")
	index_path, meta_path, n = build_faiss_index(cfg)
	print(f"Index built with {n} vectors.\nIndex: {index_path}\nMeta:  {meta_path}")


if __name__ == "__main__":
	main()
