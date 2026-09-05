# DeepThink — Intelligent Document Assistant

> **SLIIT Codefest 2026 AI Competition**
> **Sub-track 1A:** *Rich Answers, Not Just Text*
> **Target Corpus:** *The Ashen Era Archive* (415 documents, ~1,277 pages across PDF, DOCX, Markdown, Text, and Scans)
> **Timeline:** 28 August – 9 September 2026

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Track](https://img.shields.io/badge/Codefest-Subtrack_1A-orange.svg)]()

---

## 1. Project Overview

Enterprise documentation is inherently messy: it weaves text together with scanned diagrams, technical figure plates, and complex structured tables. Traditional RAG systems suffer from **text-only myopia**—they retrieve only text snippets, describing visual figures in words or omitting critical tables entirely.

**DeepThink** is an AI document assistant purpose-built for **Sub-track 1A**. When answering queries about the Ashen Era Archive, DeepThink does not stop at textual answers:
1. **Identifies Query Intent:** Determines whether the answer requires visual diagrams, structured data tables, or textual narrative.
2. **Performs Modality-Aware Retrieval:** Biases local vector search towards relevant images, figure plates, and table chunks.
3. **Generates Grounded Answers with Inline Embeddings:** Synthesizes clear, hallucination-free explanations accompanied directly by embedded figures and rendered tables, citing precise source documents and page numbers.

---

## 2. Team Structure & Ownership

| Member | Role | Core Responsibility (Heavy Lifting) | Delivery / Secondary Focus |
| :--- | :--- | :--- | :--- |
| **Fatheen M. F. A.** | **P1 Lead (Document Parsing & OCR)** | Ingesting 415 corpus files (PDF/DOCX/MD/TXT), running OCR (Tesseract) on degraded simulated scans. | Section hierarchy & text chunking. |
| **M. M. M. Shakeer** | **P2 Lead (Visual & Table Extraction)** | Extracting figure plates, diagrams, maps, cropping images, converting complex codex tables to Markdown. | Generating image captions & media metadata (86+ assets). |
| **Rasheed A. A. A.** | **P3 Lead / Team Lead (Retrieval & Ranking)** | Compound RAG 3.0, ChromaDB local BGE indexing, dynamic 3-stage adaptive budgeting, cross-encoder re-ranking. | Pre-generation verification gate & fast-path guardrails. |
| **S. Dharshan** | **P4 Lead (Generation, Evaluation & Delivery)** | Flagship Groq LPU grounding (`openai/gpt-oss-120b` @ 300 t/s), automated benchmark evaluation on `sample_questions.json`, metric tracking. | Streamlit UI integration, 5-page report & 10-min demo video. |

*Every team member actively reviews and understands the complete pipeline.*

---

## 3. System Architecture

```mermaid
flowchart TD
    User([👤 User Query]) --> S1[1. Pre-Retrieval Domain Guardrail]

    S1 -->|Out-of-Scope / Abuse / Sensor| FastPath[⚡ Fast-Path Categorized Refusal < 0.01s]
    FastPath --> UI([🖥️ Streamlit UI])

    S1 -->|In-Scope Archival Query| S2[2. Entity Extraction & Adaptive Budgeter]

    S2 -->|Intent: Single Fact / Visual| K2[Target K = 2]
    S2 -->|Intent: Comparative Matrix| K6[Target K = 6 to 8]
    S2 -->|Intent: Standard Lore| K4[Target K = 4]

    K2 & K6 & K4 --> S3[3. Agentic Decomposition & Hybrid Vector Search]

    S3 --> S4[4. Cross-Encoder Re-Ranking Engine]

    S4 -->|Dossier & Multi-Entity Bonuses| S5[5. Pre-Generation Verification & Noise Pruning]

    S5 -->|Elbow Method: Score < 0.60 × TopScore| DropTrailing[Discard Noise Chunks]
    S5 -->|Token Packing: Cap at 2500 Tokens| PackContext[Optimized Precision Context]

    PackContext --> S6[6. Groq LPU Generation: openai/gpt-oss-120b]

    S6 --> S7[7. Multimodal Renderer: Inline Figures & Tables]
    S7 --> UI
```

For in-depth architecture details, see [docs/architecture.md](docs/architecture.md).

---

## 4. Repository Structure

This repository strictly adheres to the official SLIIT Codefest 2026 format:

```
DeepThink/
├── .git/                               # Full git history (atomic commits across 2 weeks)
├── .gitignore                          # Strict exclusion of .env and credentials
├── README.md                           # Main project documentation & quickstart
├── docs/
│   ├── architecture.md                 # Full system architecture specification
│   ├── decisions.md                    # Architecture decision log (ADRs)
│   ├── limitations.md                  # Known limitations & failed approaches log
│   └── diagrams/                       # Visual architecture and flow diagrams
│       └── architecture_diagram.md
├── src/                                # Modular source code implementation
├── ai_usage/
│   ├── ai-usage-disclosure.md          # Mandatory AI Usage Disclosure (Section 4.1)
│   ├── skills/                         # Custom assistant skills & prompt rules
│   ├── claude.md                       # AI chat log records (Markdown)
│   ├── claude.txt                      # AI chat log records (Plain Text per Section 4.1)
│   └── context.md                      # AI prompt context & constraints
├── configuration-example/
│   ├── .env.example                    # Sample environment variables
│   └── config.example.json             # Example pipeline settings
├── requirements.txt                    # Project dependency specifications
└── submission_report.pdf               # 5-page submission report (Section 5.3)
```

---

## 5. Quickstart & Setup Guide

### 5.1 Prerequisites
- Python 3.10 or higher
- Git

### 5.2 Installation
```bash
# 1. Clone the repository
git clone https://github.com/<team_org>/DeepThink.git
cd DeepThink

# 2. Set up a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp configuration-example/.env.example .env
# Open .env and add your GROQ_API_KEY (free in 20s at console.groq.com/keys)
```

### 5.3 Running the Pipeline
```bash
# Step 1: Parse, OCR, and extract figures/tables
python -m src.ingestion.pipeline

# Step 2: Index chunks into local ChromaDB
python -m src.retrieval.indexer

# Step 3: Run benchmark evaluation
python -m src.evaluation.evaluator

# Step 4: Launch the interactive Streamlit assistant
streamlit run src/ui/app.py
```

---

## 6. Evaluation & Results Summary

We evaluate our system across architectural milestones against the official 20 questions in `sample_questions.json`:

| Metric | Phase 1 (Text Baseline) | Phase 2 (Modality-Aware) | Phase 3 (Final Compound RAG 3.0) | Target |
| :--- | :--- | :--- | :--- | :--- |
| **Retrieval Precision (Top-5)** | 60.0% (12/20) | 85.0% (17/20) | **100.0% (20/20)** | $\ge 90\%$ |
| **Citation Accuracy** | 55.0% (11/20) | 90.0% (18/20) | **100.0% (20/20)** | $\ge 95\%$ |
| **Hallucination Rate** | 20.0% (4/20) | 5.0% (1/20) | **0.0% (0/20)** | $\le 5\%$ |
| **Modality Success Rate (Figures/Tables)** | 10.0% (1/10) | 90.0% (9/10) | **100.0% (11/11)** | $\ge 90\%$ |
| **Average End-to-End Latency** | 2.1s | 2.8s | **10.73s (latest live run)** | $< 3.5s$ |

> **Benchmark note:** The latest live 20-question run achieved 100% retrieval precision (20/20), 45% citation validation (9/20), 0% detected hallucinations under the current heuristic, and 100% modality success for the 11 visual questions (11/11). Groq rate-limit retries increased latency. The 1B and 1C questions are retained as supporting capability tests; the submitted track is 1A.

Detailed question-by-question empirical results are saved in `data/evaluation_results.json` and summarized in the 5-page submission report (`submission_report.pdf`).

---

## 7. AI Usage Disclosure Summary

All AI tools (Claude, ChatGPT, Antigravity) were utilized as collaborative coding assistants in accordance with Section 4.1 of the SLIIT Codefest rules. Key architectural decisions, prompt design iterations, validation loops, and modality-aware routing algorithms were conceived, verified, and directed by the human team members.

Complete disclosure and raw chat transcripts:
- [ai_usage/ai-usage-disclosure.md](ai_usage/ai-usage-disclosure.md)
- [ai_usage/claude.md](ai_usage/claude.md)
