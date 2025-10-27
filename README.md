# See-DR RAGBot

Closed-domain retrieval-augmented generation assistant for diabetic retinopathy research. Runs locally with offline embeddings and a local Ollama LLM.

## Quickstart

1) Create and activate venv
```bash
python3 -m venv .venv && source .venv/bin/activate
```

2) Install dependencies
```bash
pip install -r requirements.txt
```

3) Configure environment
```bash
cp env.example .env  # edit values if needed
```

4) Prepare data and build the index
```bash
python scripts/build_index.py
```

5) Run the API
```bash
uvicorn see_dr_ragbot.api.main:app --reload --port 8000
```

6) Run the UI (in another terminal)
```bash
streamlit run see_dr_ragbot/ui/app.py
```

## Configuration
Edit `config.yaml` to set paths and models. Environment variables in `.env` override YAML for secure local changes.

## Notes
- LLM is expected to be available locally via Ollama (e.g., `wizardlm2`, `mistral`, `phi3`).
- All retrieval and generation stays within the local machine; there are no external API calls.
