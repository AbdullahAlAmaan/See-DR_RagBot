import os
import sys

# Ensure repository root is on sys.path
REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
if REPO_ROOT not in sys.path:
	sys.path.insert(0, REPO_ROOT)

from see_dr_ragbot.config import load_config


def main() -> None:
	cfg = load_config()
	# Trigger downloads by instantiating models
	from sentence_transformers import SentenceTransformer
	SentenceTransformer(cfg.models.embedding_model)
	try:
		from sentence_transformers import CrossEncoder
		CrossEncoder(cfg.models.reranker_model)
	except Exception:
		pass
	print("Models downloaded.")

if __name__ == "__main__":
	main()
