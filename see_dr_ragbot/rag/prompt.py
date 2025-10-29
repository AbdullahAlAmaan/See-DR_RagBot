SYSTEM_PROMPT = (
	"You are See-DR, a RAG assistant specialized in diabetic retinopathy.\n"
	"IMPORTANT: Answer the user's question DIRECTLY using ONLY the provided sources.\n"
	"Do NOT include irrelevant information like article selection criteria, methodology, or background context unless directly asked.\n"
	"For treatment questions: Focus on actual treatment methods, procedures, medications, and therapies mentioned in the sources.\n"
	"Answer BRIEFLY and concisely (2-3 sentences maximum per point).\n"
	"Include citations as [Title, p. X] where X is the page number.\n"
	"Focus on key facts that directly answer the question. Skip redundant or tangential information.\n"
	"If the answer is not in the sources, say you don't know."
)


def build_prompt(query: str, contexts: list[dict]) -> str:
	"""Build a prompt for the LLM with system instructions and retrieved contexts.
	
	Formats the query and retrieved document chunks into a structured prompt that
	instructs the LLM to answer using only the provided sources with citations.
	
	Args:
		query: The user's question or query.
		contexts: List of retrieved document chunks, each containing 'text' and 'metadata'.
		
	Returns:
		Complete prompt string ready for LLM input, including system instructions,
		the question, source contexts with citations, and final instructions.
	"""
	from ..ingestion.text_cleaner import clean_chunk_text
	
	header = SYSTEM_PROMPT
	sources = []
	for c in contexts:
		m = c.get("metadata", {})
		title = m.get("title") or m.get("filename") or "Source"
		page = m.get("page_number")
		prefix = f"[{title}, p. {page}]" if page else f"[{title}]"
		snippet = clean_chunk_text(c.get("text", "").strip())
		# Limit snippet length to avoid overwhelming the LLM
		if len(snippet) > 500:
			snippet = snippet[:500] + "..."
		sources.append(f"{prefix}:\n{snippet}")
	sources_block = "\n\n".join(sources)
	return f"{header}\n\nQuestion: {query}\n\nSources:\n{sources_block}\n\nDirectly answer the question using ONLY the most relevant information from the sources above. Skip any information about article selection, methodology, or background unless it directly answers the question:\n"
