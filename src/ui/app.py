"""
Streamlit Web Application (Owner: Member P4)
Interactive document assistant for the Ashen Era Archive with inline figure & table rendering.
"""

import streamlit as st
from src.retrieval.retriever import retrieve
from src.generation.generator import generate_answer

st.set_page_config(
    page_title="DeepThink — Ashen Era Archive Assistant",
    page_icon="📖",
    layout="wide"
)

st.title("📖 DeepThink — Intelligent Document Assistant")
st.caption("SLIIT Codefest 2026 AI Competition | Sub-track 1A: Rich Answers, Not Just Text")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Input
if prompt := st.chat_input("Ask a question about the Ashen Era Archive..."):
    # Append user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Retrieval & Generation
    with st.chat_message("assistant"):
        with st.spinner("Searching archive and retrieving relevant diagrams/tables..."):
            chunks = retrieve(prompt)
            response = generate_answer(prompt, chunks)
            st.markdown(response)
            
            # Show source inspector in expander
            if chunks:
                with st.expander("🔍 View Retrieved Source Chunks & Figures"):
                    for c in chunks:
                        st.write(f"**Source:** {c.get('document_name')} (Page {c.get('page_number')}) | **Modality:** `{c.get('modality')}`")
                        if c.get("media_path"):
                            st.image(c.get("media_path"), caption=c.get("caption"))
                        st.text(c.get("content"))
                        st.divider()

    st.session_state.messages.append({"role": "assistant", "content": response})
