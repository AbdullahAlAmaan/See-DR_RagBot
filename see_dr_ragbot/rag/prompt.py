SYSTEM_PROMPT = (
	"You are See-DR, a RAG assistant specialized in diabetic retinopathy.\n"
	"Use ONLY the provided sources.\n"
	"Answer concisely and include bracketed citations like [Title, p. X].\n"
	"If the answer is not in the sources, say you don't know."
)


def build_prompt(query: str, contexts: list[dict]) -> str:
	header = SYSTEM_PROMPT
	sources = []
	for c in contexts:
		m = c.get("metadata", {})
		title = m.get("title") or m.get("filename") or "Source"
		page = m.get("page_number")
		prefix = f"[{title}, p. {page}]" if page else f"[{title}]"
		snippet = c.get("text", "").strip()
		sources.append(f"{prefix}:\n{snippet}")
	sources_block = "\n\n".join(sources)
	return f"{header}\n\nQuestion: {query}\n\nSources:\n{sources_block}\n\nAnswer:"
