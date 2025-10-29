import json
import re
import streamlit as st
import requests
from pathlib import Path

st.set_page_config(page_title="See-DR RAGBot", layout="wide")

API_URL = "http://localhost:8000"

# Conversation storage file (persistent across sessions)
CONVERSATION_FILE = Path("data/conversations.json")

# Load conversation history from file
def load_conversations():
	if CONVERSATION_FILE.exists():
		try:
			with open(CONVERSATION_FILE, "r", encoding="utf-8") as f:
				return json.load(f)
		except Exception:
			return []
	return []

# Save conversation history to file
def save_conversations(conversations):
	CONVERSATION_FILE.parent.mkdir(parents=True, exist_ok=True)
	with open(CONVERSATION_FILE, "w", encoding="utf-8") as f:
		json.dump(conversations, f, ensure_ascii=False, indent=2)

# Initialize session state with persistent storage
if "conversation_history" not in st.session_state:
	st.session_state.conversation_history = load_conversations()
if "expanded_qa" not in st.session_state:
	st.session_state.expanded_qa = None

st.title("See-DR RAGBot")

# JavaScript for smooth scrolling to citations
SCROLL_SCRIPT = """
<script>
function scrollToCitation(id) {
	const element = document.getElementById(id);
	if (element) {
		element.scrollIntoView({ behavior: 'smooth', block: 'center' });
		element.style.backgroundColor = '#ffffcc';
		setTimeout(() => { element.style.backgroundColor = ''; }, 2000);
	}
}
window.scrollToCitation = scrollToCitation;
</script>
"""
st.markdown(SCROLL_SCRIPT, unsafe_allow_html=True)

# Sidebar with conversation history
with st.sidebar:
	st.header("Recent Questions")
	if st.session_state.conversation_history:
		for idx, qa in enumerate(reversed(st.session_state.conversation_history[-3:])):
			qa_id = len(st.session_state.conversation_history) - idx - 1
			question_text = qa["question"][:80] + "..." if len(qa["question"]) > 80 else qa["question"]
			
			if st.button(
				f"Q: {question_text}",
				key=f"history_{qa_id}",
				use_container_width=True,
			):
				st.session_state.expanded_qa = qa_id
				st.rerun()
		
		if st.button("🗑️ Clear History", use_container_width=True):
			st.session_state.conversation_history = []
			save_conversations([])
			st.session_state.expanded_qa = None
			st.rerun()
	else:
		st.caption("No previous questions yet")

# Main content area
if st.session_state.expanded_qa is not None:
	# Show expanded QA from history
	qa = st.session_state.conversation_history[st.session_state.expanded_qa]
	
	st.markdown("---")
	st.markdown("### Previous Question & Answer")
	
	if st.button("← Back to New Query"):
		st.session_state.expanded_qa = None
		st.rerun()
	
	st.markdown(f"**Question:** {qa['question']}")
	st.markdown("**Answer:**")
	
	# Display answer with clickable citations
	answer = qa["answer"]
	sources = qa["sources"]
	
	# Build citation mapping: match titles and pages to source indices
	citation_to_index = {}
	for i, src in enumerate(sources, start=1):
		m = src.get("metadata", {})
		title = m.get("title") or m.get("filename", "")
		page = m.get("page_number")
		# Map various citation formats
		if page:
			citation_to_index[f"[{title}, p. {page}]"] = i
			citation_to_index[f"[{title}, p.{page}]"] = i
		citation_to_index[f"[{title}]"] = i
	
	# Replace citations in answer using regex to find all citation patterns
	def replace_citation_hist(match):
		citation_text = match.group(0)
		# Try to find matching citation in our map
		# Extract title from citation (before comma or "p.")
		title_match = re.search(r'\[([^,\]]+?)(?:\s*,\s*p\.|[\];])', citation_text)
		if title_match:
			citation_title = title_match.group(1).strip()
			# Find matching source by title
			for i, src in enumerate(sources, start=1):
				m = src.get("metadata", {})
				src_title = m.get("title") or m.get("filename", "")
				if citation_title == src_title or citation_title in src_title or src_title in citation_title:
					citation_id = f"cite-hist-{st.session_state.expanded_qa}-{i}"
					return f'<a href="#{citation_id}" onclick="event.preventDefault(); scrollToCitation(\'{citation_id}\'); return false;" style="color: #0066cc; cursor: pointer; text-decoration: underline;">{citation_text}</a>'
		
		# Fallback to simple matching
		for citation_key, num in citation_to_index.items():
			if citation_key in citation_text or citation_text.startswith(citation_key[:-1]):
				citation_id = f"cite-hist-{st.session_state.expanded_qa}-{num}"
				return f'<a href="#{citation_id}" onclick="event.preventDefault(); scrollToCitation(\'{citation_id}\'); return false;" style="color: #0066cc; cursor: pointer; text-decoration: underline;">{citation_text}</a>'
		return citation_text
	
	# Pattern to match citations: [title, p. X] or [title, p. X, Y] or [title, p. X; title2, p. Y]
	citation_pattern = r'\[[^\]]+?\]'
	display_answer = re.sub(citation_pattern, replace_citation_hist, answer)
	
	st.markdown(display_answer, unsafe_allow_html=True)
	
	st.markdown("---")
	st.markdown("#### Citations")
	for i, src in enumerate(sources, start=1):
		m = src.get("metadata", {})
		title = m.get("title") or m.get("filename", "")
		page = m.get("page_number")
		source_text = src.get("text", "")
		citation_id = f"cite-hist-{st.session_state.expanded_qa}-{i}"
		
		# Show only first 2-3 lines (approx 200 chars)
		preview_lines = source_text.split("\n")[:3]
		preview_text = "\n".join(preview_lines)
		if len(preview_text) > 200:
			preview_text = preview_text[:200] + "..."
		
		st.markdown(f'<div id="{citation_id}" style="padding: 10px 0; margin: 5px 0;">', unsafe_allow_html=True)
		st.markdown(
			f'<small><strong>[{i}]</strong> {title}{f", p. {page}" if page else ""}</small>',
			unsafe_allow_html=True
		)
		st.caption(preview_text)
		st.markdown('</div>', unsafe_allow_html=True)
		with st.expander(f"View full source [{i}]", expanded=False):
			st.write(source_text)
	
	st.markdown("---")
else:
	# New query interface
	query = st.text_input("Ask a question about Diabetic Retinopathy research")
	if st.button("Search") and query.strip():
		with st.spinner("Retrieving and generating answer..."):
			resp = requests.post(f"{API_URL}/query", json={"query": query}, timeout=600)
			if not resp.ok:
				st.error(resp.text)
			else:
				data = resp.json()
				
				# Store in history
				qa_entry = {
					"question": query,
					"answer": data.get("answer", ""),
					"sources": data.get("sources", [])
				}
				st.session_state.conversation_history.append(qa_entry)
				save_conversations(st.session_state.conversation_history)  # Persist to file
				
				st.markdown("---")
				st.markdown("### Answer")
				answer = data.get("answer", "")
				sources = data.get("sources", [])
				
				# Build citation mapping: match titles and pages to source indices
				citation_to_index = {}
				for i, src in enumerate(sources, start=1):
					m = src.get("metadata", {})
					title = m.get("title") or m.get("filename", "")
					page = m.get("page_number")
					# Map various citation formats
					if page:
						citation_to_index[f"[{title}, p. {page}]"] = i
						citation_to_index[f"[{title}, p.{page}]"] = i
					citation_to_index[f"[{title}]"] = i
				
				# Replace citations in answer using regex
				def replace_citation_new(match):
					citation_text = match.group(0)
					# Handle complex citations like [title1, p. X; title2, p. Y]
					parts = citation_text.strip('[]').split(';')
					result_parts = []
					
					for part in parts:
						part = part.strip()
						if not part:
							continue
						# Extract title (part before comma or "p.")
						title_match = re.search(r'^([^,]+?)(?:\s*,\s*p\.|$)', part)
						if title_match:
							title = title_match.group(1).strip()
							# Try to find this title in our sources
							matched = False
							for i, src in enumerate(sources, start=1):
								m = src.get("metadata", {})
								src_title = m.get("title") or m.get("filename", "")
								if title == src_title or title in src_title or src_title in title:
									citation_id = f"cite-new-{i}"
									link = f'<a href="#{citation_id}" onclick="scrollToCitation(\'{citation_id}\'); return false;" style="text-decoration: none; color: #0066cc; font-size: 0.75em; cursor: pointer; text-decoration: underline;">[{part}]</a>'
									result_parts.append(link)
									matched = True
									break
							if not matched:
								result_parts.append(f'[{part}]')
						else:
							result_parts.append(f'[{part}]')
					
					# If no matches found, try simpler matching
					if len(parts) == 1:
						# Try to extract title and match
						title_match = re.search(r'\[([^,\]]+?)(?:\s*,\s*p\.|[\];])', citation_text)
						if title_match:
							citation_title = title_match.group(1).strip()
							for i, src in enumerate(sources, start=1):
								m = src.get("metadata", {})
								src_title = m.get("title") or m.get("filename", "")
								if citation_title == src_title or citation_title in src_title or src_title in citation_title:
									citation_id = f"cite-new-{i}"
									return f'<a href="#{citation_id}" onclick="event.preventDefault(); scrollToCitation(\'{citation_id}\'); return false;" style="color: #0066cc; cursor: pointer; text-decoration: underline;">{citation_text}</a>'
						
						for citation_key, num in citation_to_index.items():
							if citation_key in citation_text or citation_text.startswith(citation_key[:-1]):
								citation_id = f"cite-new-{num}"
								return f'<a href="#{citation_id}" onclick="event.preventDefault(); scrollToCitation(\'{citation_id}\'); return false;" style="color: #0066cc; cursor: pointer; text-decoration: underline;">{citation_text}</a>'
						return citation_text
					return '; '.join(result_parts) if result_parts else citation_text
				
				# Pattern to match citations: [title, p. X] or variations
				citation_pattern = r'\[[^\]]+?\]'
				display_answer = re.sub(citation_pattern, replace_citation_new, answer)
				
				st.markdown(display_answer, unsafe_allow_html=True)
				
				st.markdown("---")
				st.markdown("#### Citations")
				for i, src in enumerate(sources, start=1):
					m = src.get("metadata", {})
					title = m.get("title") or m.get("filename", "")
					page = m.get("page_number")
					source_text = src.get("text", "")
					citation_id = f"cite-new-{i}"
					
					# Show only first 2-3 lines (approx 200 chars)
					preview_lines = source_text.split("\n")[:3]
					preview_text = "\n".join(preview_lines)
					if len(preview_text) > 200:
						preview_text = preview_text[:200] + "..."
					
					st.markdown(f'<div id="{citation_id}" style="padding: 10px 0; margin: 5px 0;">', unsafe_allow_html=True)
					st.markdown(
						f'<small><strong>[{i}]</strong> {title}{f", p. {page}" if page else ""}</small>',
						unsafe_allow_html=True
					)
					st.caption(preview_text)
					st.markdown('</div>', unsafe_allow_html=True)
					with st.expander(f"View full source [{i}]", expanded=False):
						st.write(source_text)
