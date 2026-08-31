"""
Streamlit Web Application (Owner: Member P4 - Generation, Evaluation & Delivery Lead)
Interactive document assistant for the Ashen Era Archive with inline figure & table rendering.
"""

import os
import re
import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to sys.path for Streamlit execution
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st

from src.config import (
    PROJECT_ROOT, 
    DATA_DIR, 
    EXTRACTED_MEDIA_DIR,
    CHUNKS_JSON_PATH, 
    CHROMA_PERSIST_DIR,
    DEFAULT_TOP_K,
    MODALITY_BOOST_FACTOR,
    LLM_MODEL_NAME,
    OPENROUTER_API_KEY
)
from src.retrieval.retriever import retrieve
from src.retrieval.router import analyze_query_intent
from src.generation.generator import generate_answer, resolve_media_path


def load_sample_questions() -> List[Dict[str, Any]]:
    """Loads the 20 benchmark questions for fast demo selection."""
    sample_file = DATA_DIR / "sample_questions.json"
    if sample_file.exists():
        try:
            with open(sample_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def get_corpus_stats() -> Dict[str, Any]:
    """Computes basic statistics about the ingested corpus and assets."""
    stats = {
        "total_chunks": 0,
        "figures_count": 0,
        "tables_count": 0,
        "is_indexed": False
    }
    
    if CHUNKS_JSON_PATH.exists():
        try:
            with open(CHUNKS_JSON_PATH, "r", encoding="utf-8") as f:
                chunks = json.load(f)
                stats["total_chunks"] = len(chunks)
        except Exception:
            pass

    fig_dir = EXTRACTED_MEDIA_DIR / "figures"
    tab_dir = EXTRACTED_MEDIA_DIR / "tables"
    if fig_dir.exists():
        stats["figures_count"] = len(list(fig_dir.glob("*.*")))
    if tab_dir.exists():
        stats["tables_count"] = len(list(tab_dir.glob("*.*")))

    if CHROMA_PERSIST_DIR.exists() and any(CHROMA_PERSIST_DIR.iterdir()):
        stats["is_indexed"] = True

    return stats


def render_message_content(content: str):
    """
    Renders message text and converts markdown image tags ![alt](path)
    into native st.image() elements so local image assets display properly in the browser.
    """
    if not content:
        return

    # Split by markdown image tags: ![alt](path)
    image_pattern = r"(!\[.*?\]\(.*?\))"
    parts = re.split(image_pattern, content)

    for part in parts:
        part_clean = part.strip()
        if not part_clean:
            continue

        img_match = re.match(r"^!\[(.*?)\]\((.*?)\)$", part_clean)
        if img_match:
            alt_text = img_match.group(1)
            img_path = img_match.group(2)
            resolved = resolve_media_path(img_path)
            
            displayed = False
            if resolved:
                abs_path = PROJECT_ROOT / resolved
                if abs_path.exists() and abs_path.is_file():
                    st.image(str(abs_path), caption=alt_text or "Archival Figure Plate", use_container_width=True)
                    displayed = True
            
            if not displayed:
                # Direct lookup across known directories
                img_name = Path(img_path).name
                candidates = [
                    EXTRACTED_MEDIA_DIR / "figures" / img_name,
                    EXTRACTED_MEDIA_DIR / "tables" / img_name,
                    DATA_DIR / "Ashen_Era_Archive" / "wiki" / "images" / img_name,
                    DATA_DIR / "Ashen_Era_Archive" / "codex" / "images" / img_name,
                    PROJECT_ROOT / img_path
                ]
                for cand in candidates:
                    if cand.exists() and cand.is_file():
                        st.image(str(cand), caption=alt_text or "Archival Figure Plate", use_container_width=True)
                        displayed = True
                        break

            if not displayed:
                if img_path.startswith("http://") or img_path.startswith("https://") or img_path.startswith("data:image"):
                    st.image(img_path, caption=alt_text or "Figure", use_container_width=True)
                else:
                    st.caption(f"🖼️ *{alt_text}*")
        else:
            st.markdown(part)


def main():
    """Main Streamlit application interface."""
    st.set_page_config(
        page_title="DeepThink — Ashen Era Archive Assistant",
        page_icon="📖",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS for polished, competition-ready visual design
    st.markdown("""
    <style>
        .main-header {
            font-size: 2.2rem;
            font-weight: 700;
            color: #1E293B;
            margin-bottom: 0.2rem;
        }
        .sub-header {
            font-size: 1.05rem;
            color: #64748B;
            margin-bottom: 1.5rem;
        }
        .badge-1a {
            background-color: #FEF3C7;
            color: #92400E;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.85rem;
            font-weight: 600;
            display: inline-block;
        }
        .modality-badge-image {
            background-color: #DBEAFE;
            color: #1E40AF;
            padding: 3px 8px;
            border-radius: 8px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        .modality-badge-table {
            background-color: #D1FAE5;
            color: #065F46;
            padding: 3px 8px;
            border-radius: 8px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        .modality-badge-text {
            background-color: #F3F4F6;
            color: #374151;
            padding: 3px 8px;
            border-radius: 8px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        .chunk-card {
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 10px;
            background-color: #F8FAFC;
        }
    </style>
    """, unsafe_allow_html=True)

    # --- SIDEBAR CONTROLS ---
    with st.sidebar:
        st.markdown("### 📖 **DeepThink Controls**")
        st.markdown("<span class='badge-1a'>Sub-track 1A: Rich Answers</span>", unsafe_allow_html=True)
        st.markdown("---")

        # Benchmark Preset Selector
        sample_questions = load_sample_questions()
        selected_sample = None
        if sample_questions:
            st.markdown("#### 🎯 Benchmark Questions Preset")
            q_options = [f"[{q.get('qid', 'Q')}] {q.get('question', '')[:60]}..." for q in sample_questions]
            selected_idx = st.selectbox(
                "Select Sample Question (20 Benchmark Suite):", 
                range(len(q_options)), 
                format_func=lambda i: q_options[i]
            )
            if st.button("Load Question into Chat", use_container_width=True):
                selected_sample = sample_questions[selected_idx]["question"]

        st.markdown("---")
        st.markdown("#### ⚙️ Retrieval & LLM Settings")
        top_k = st.slider("Top-K Chunks to Retrieve", min_value=1, max_value=10, value=DEFAULT_TOP_K)
        boost_factor = st.slider("Modality Boost Factor (W_modality)", min_value=1.0, max_value=3.0, value=MODALITY_BOOST_FACTOR, step=0.1)
        
        model_choice = st.selectbox(
            "LLM Model (OpenRouter Free Tier):",
            [LLM_MODEL_NAME, "deepseek/deepseek-chat", "meta-llama/llama-3-8b-instruct:free", "google/gemini-2.0-flash-lite-preview-02-05:free"],
            index=0
        )

        api_key_input = st.text_input("OpenRouter API Key (Optional override):", value="", type="password", help="Leave blank to use .env key or local grounded synthesizer.")

        st.markdown("---")
        st.markdown("#### 📊 Corpus Telemetry")
        corpus_stats = get_corpus_stats()
        col1, col2 = st.columns(2)
        col1.metric("Indexed Chunks", f"{corpus_stats['total_chunks']:,}")
        col2.metric("Visual Assets", f"{corpus_stats['figures_count']}")
        
        status_color = "🟢 Ready" if corpus_stats["is_indexed"] else "🟡 Standalone Index"
        st.caption(f"Vector Store Status: **{status_color}**")

        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    # --- MAIN CHAT INTERFACE ---
    st.markdown("<div class='main-header'>📖 DeepThink — Multimodal Document Assistant</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>SLIIT Codefest 2026 AI Competition &bull; <i>The Ashen Era Archive</i> (415 documents, ~1,277 pages)</div>", unsafe_allow_html=True)

    # Session State for Messages
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Greetings! I am **DeepThink**, your multimodal archival assistant for *The Ashen Era*. Ask me any question about history, battle accords, relics, or request visual figure plates, diagrams, and structured data tables.",
                "chunks": []
            }
        ]

    # Display Existing Chat History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            render_message_content(msg["content"])
            
            # Render media files if embedded paths exist in assistant message
            if msg["role"] == "assistant" and msg.get("chunks"):
                chunks = msg.get("chunks", [])
                with st.expander(f"🔍 View {len(chunks)} Retrieved Context Chunks & Modality Breakdown"):
                    for idx, c in enumerate(chunks, 1):
                        modality = c.get("modality", "text")
                        badge_class = "modality-badge-image" if modality == "image-caption" else ("modality-badge-table" if modality == "table" else "modality-badge-text")
                        
                        st.markdown(f"**Chunk #{idx}** &bull; Source: `{c.get('document_name')}` (Page {c.get('page_number')}) &bull; <span class='{badge_class}'>{modality.upper()}</span> &bull; Relevance: `{c.get('relevance_score', 0.0)}`", unsafe_allow_html=True)
                        
                        media_p = c.get("media_path")
                        if media_p:
                            resolved = resolve_media_path(media_p)
                            if resolved and (PROJECT_ROOT / resolved).exists():
                                st.image(str(PROJECT_ROOT / resolved), caption=c.get("caption") or "Archival Figure Plate", width=420)
                        
                        st.text(c.get("content", "")[:300] + ("..." if len(c.get("content", "")) > 300 else ""))
                        st.markdown("---")

    # Handle User Query Input (From Chat Input or Preset Loader)
    user_prompt = None
    if selected_sample:
        user_prompt = selected_sample
    elif chat_in := st.chat_input("Ask a question about the Ashen Era Archive (e.g. 'Show me the diagram of the Sky-Fortress...')..."):
        user_prompt = chat_in

    if user_prompt:
        # 1. Append User Message
        st.session_state.messages.append({"role": "user", "content": user_prompt, "chunks": []})
        with st.chat_message("user"):
            st.markdown(user_prompt)

        # 2. Process Intent, Retrieval, and Generation
        with st.chat_message("assistant"):
            start_time = time.time()
            
            # Analyze Intent
            intent_info = analyze_query_intent(user_prompt)
            intent_label = intent_info.get("intent", "narrative_text")
            target_mod = intent_info.get("target_modality", "text")
            
            with st.spinner(f"Classifying intent [{intent_label.upper()}] & searching multimodal vector store..."):
                retrieved_chunks = retrieve(
                    query=user_prompt, 
                    top_k=top_k
                )

            with st.spinner("Synthesizing grounded response with citations and inline media..."):
                active_key = api_key_input.strip() if api_key_input.strip() else None
                response_text = generate_answer(
                    query=user_prompt, 
                    context_chunks=retrieved_chunks,
                    model=model_choice,
                    api_key=active_key
                )

            elapsed_time = round(time.time() - start_time, 2)

            # 3. Render Assistant Response with Native Streamlit Image Handling
            render_message_content(response_text)

            st.caption(f"⏱️ Retrieval & Synthesis Latency: **{elapsed_time}s** &bull; Intent Detected: `{intent_label}` &bull; Target Modality: `{target_mod}`")

            # 4. Render Expandable Context Inspector
            if retrieved_chunks:
                with st.expander(f"🔍 Inspect {len(retrieved_chunks)} Retrieved Context Chunks & Modality Breakdown"):
                    for idx, c in enumerate(retrieved_chunks, 1):
                        modality = c.get("modality", "text")
                        badge_class = "modality-badge-image" if modality == "image-caption" else ("modality-badge-table" if modality == "table" else "modality-badge-text")
                        
                        st.markdown(f"**Chunk #{idx}** &bull; Source: `{c.get('document_name')}` (Page {c.get('page_number')}) &bull; <span class='{badge_class}'>{modality.upper()}</span> &bull; Boosted Score: `{c.get('relevance_score', 0.0)}` &bull; Raw Sim: `{c.get('raw_similarity', 0.0)}`", unsafe_allow_html=True)
                        
                        media_p = c.get("media_path")
                        if media_p:
                            resolved = resolve_media_path(media_p)
                            if resolved and (PROJECT_ROOT / resolved).exists():
                                st.image(str(PROJECT_ROOT / resolved), caption=c.get("caption") or "Archival Figure Plate", width=400)
                        
                        st.text(c.get("content", "")[:350] + ("..." if len(c.get("content", "")) > 350 else ""))
                        st.markdown("---")

        # 5. Save to Session History
        st.session_state.messages.append({
            "role": "assistant",
            "content": response_text,
            "chunks": retrieved_chunks
        })


if __name__ == "__main__":
    main()
