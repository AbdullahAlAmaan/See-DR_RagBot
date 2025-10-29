from __future__ import annotations
from typing import List, Dict


def _simple_sentence_split(text: str) -> List[str]:
	# Lightweight sentence splitter to avoid external data downloads
	separators = [". ", "? ", "! "]
	sentences: List[str] = []
	current = text.strip()
	if not current:
		return []
	buf = ""
	for ch in current:
		buf += ch
		if ch in ".?!":
			# lookahead for space/newline or end
			sentences.append(buf.strip())
			buf = ""
	if buf.strip():
		sentences.append(buf.strip())
	return [s for s in sentences if s]


def _approx_token_count(s: str) -> int:
	# Rough token estimate ~ words
	return max(1, len(s.split()))


def recursive_chunk(
	text: str,
	target_tokens: int = 600,
	max_tokens: int = 800,
	min_tokens: int = 200,
	metadata: Dict | None = None,
) -> List[Dict]:
	"""
	Split text into semantically coherent chunks using a simple sentence splitter and token budget.
	Returns list of {text, tokens, metadata} dicts.
	"""
	sentences = _simple_sentence_split(text)
	chunks: List[Dict] = []
	buf: List[str] = []
	buf_tokens = 0

	for sent in sentences:
		s_tokens = _approx_token_count(sent)
		if buf_tokens + s_tokens <= target_tokens:
			buf.append(sent)
			buf_tokens += s_tokens
			continue

		# flush the buffer if it has at least min_tokens or adding would exceed max
		if buf and (buf_tokens >= min_tokens or buf_tokens + s_tokens > max_tokens):
			chunk_text = " ".join(buf).strip()
			chunks.append({
				"text": chunk_text,
				"tokens": buf_tokens,
				"metadata": dict(metadata or {}),
			})
			buf, buf_tokens = [], 0

		# start new buffer with the current sentence (may be long)
		buf.append(sent)
		buf_tokens = _approx_token_count(sent)

	# final flush
	if buf:
		chunk_text = " ".join(buf).strip()
		chunks.append({
			"text": chunk_text,
			"tokens": buf_tokens,
			"metadata": dict(metadata or {}),
		})

	return chunks
