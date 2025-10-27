import json
import streamlit as st
import requests

st.set_page_config(page_title="See-DR RAGBot", layout="wide")

API_URL = "http://localhost:8000"

st.title("See-DR RAGBot")

with st.sidebar:
	st.header("Actions")
	if st.button("Ingest PDFs"):
		resp = requests.post(f"{API_URL}/ingest", timeout=600)
		if resp.ok:
			st.success(f"Ingested: {resp.json().get('processed_files')} files")
		else:
			st.error(resp.text)

query = st.text_input("Ask a question about Diabetic Retinopathy research")
if st.button("Search") and query.strip():
	with st.spinner("Retrieving and generating answer..."):
		resp = requests.post(f"{API_URL}/query", json={"query": query}, timeout=600)
		if not resp.ok:
			st.error(resp.text)
		else:
			data = resp.json()
			st.subheader("Answer")
			st.write(data.get("answer", ""))
			st.subheader("Citations")
			for i, src in enumerate(data.get("sources", []), start=1):
				m = src.get("metadata", {})
				title = m.get("title") or m.get("filename")
				page = m.get("page_number")
				st.markdown(f"**[{i}]** {title}{f', p. {page}' if page else ''}")
				with st.expander("View source text"):
					st.write(src.get("text", ""))
