# Chunking and Extraction Guide

## LayoutLMv3 Integration

LayoutLMv3 is now available for layout-aware PDF extraction. It's optional - the system falls back to `unstructured` (hi_res) then `pdfplumber` if LayoutLM isn't available.

### To use LayoutLMv3:

1. Install dependencies:
```bash
source .venv/bin/activate
pip install pdf2image pillow transformers
```

2. Download the model (first use will auto-download):
```bash
python -c "from transformers import AutoProcessor, AutoModelForTokenClassification; \
AutoProcessor.from_pretrained('microsoft/layoutlmv3-base'); \
AutoModelForTokenClassification.from_pretrained('microsoft/layoutlmv3-base')"
```

3. Enable in code by updating `see_dr_ragbot/ingestion/ingest.py` to use `extract_with_layoutlm()` as the first option.

## Semantic Chunking with Overlap

The system now supports:
- **Overlap**: 20% by default (15-25% recommended)
- **Similarity threshold**: 0.65 (0.6-0.7 for semantic breaks)
- **Token ranges**: 200-800 tokens, target 600

### Configuration (`config.yaml`):
```yaml
chunking:
  target_tokens: 600
  max_tokens: 800
  min_tokens: 200
  overlap_percent: 20
  similarity_threshold: 0.65
```

## Viewing Extracted Chunks

To inspect what was extracted:

```bash
source .venv/bin/activate
python scripts/inspect_chunks.py --limit 5
```

This shows:
- Chunk previews
- Token counts
- Page numbers
- Full text examples

## Citation Granularity

Each chunk now includes:
- `start_sentence` / `end_sentence`: Sentence indices
- `num_sentences`: Count
- `page_number`: Source page
- `title`: Paper title

Citations will show: `[Paper Title, p. X, Lines Y-Z]`

## Next Steps

1. **Rebuild index with semantic chunking**:
```bash
python scripts/build_index.py
```

2. **Inspect results**:
```bash
python scripts/inspect_chunks.py
```

3. **Query and verify citations** in the Streamlit UI.

