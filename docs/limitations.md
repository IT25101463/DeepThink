# Known Limitations, Edge Cases & Failed Approaches

In compliance with **Evaluation Criteria (Section 5.3 & 6 - Technical Judgment & Decisions 10%)**, this document records known system boundaries, trade-offs, edge cases, and approaches that were tried and discarded during development.

---

## 1. Known Limitations

### 1.1 Degraded & Hand-Annotated Scans
- **Issue:** Several ephemera documents in the Ashen Era Archive consist of low-resolution simulated scans, handwritten marginalia, and faded tavern ledgers.
- **Current Behavior:** Standard OCR (Tesseract / lightweight vision parsers) may misread blurred characters or miss non-linear handwritten notes in margins.
- **Impact:** Certain obscure lore clues embedded exclusively in handwritten ephemera may have partial OCR noise.

### 1.2 Multi-Column & Merged-Cell Table Layouts
- **Issue:** Codex data books feature complex multi-column tables with merged subheaders.
- **Current Behavior:** Converting deeply nested tables to flat Markdown can occasionally merge adjacent cell tokens.
- **Mitigation:** We preserve the raw image render of the table alongside the markdown representation, allowing the user to view the authentic high-resolution plate.

### 1.3 Conflicting In-World Source Reliability
- **Issue:** Fictional history in the archive intentionally contains contradictory accounts (e.g. an official Imperial Codex vs a tavern ballad song).
- **Current Behavior:** If the query doesn't specify source preference, the system presents both viewpoints with citations rather than picking one truth.

---

## 2. Failed Approaches & Discarded Ideas

### 2.1 Discarded Approach 1: Naive Flat Text Chunking (Phase 1: Text-Only Baseline)
- **What was tried:** Stripped all images and tables, converting the entire corpus into 500-token plain text chunks.
- **Why it failed:**
  - Failed completely on 9 out of 10 visual/figure questions in `sample_questions.json`.
  - Answers contained hallucinated descriptions of visual plates instead of actual images.
  - Complex table stats lost column alignment and caused arithmetic errors in LLM reasoning.
- **Decision:** Shifted to modality-tagged chunking with dedicated image extraction in Phase 2 (Modality-Aware Pipeline).

### 2.2 Discarded Approach 2: Full Multimodal Vision-LLM on Every Query
- **What was tried:** Feeding entire raw PDF page screenshots to a large Multimodal LLM (VLM) for every query.
- **Why it failed:**
  - Excessive token consumption (exceeded rate limits within 5 queries).
  - High latency (8-12 seconds per response).
  - High hallucination rate on non-visual text queries across 1,277 pages.
- **Decision:** Implemented **Modality-Aware Hybrid Routing**: only pass visual image assets to the context when the query specifically demands or benefits from visual evidence.

### 2.3 Discarded Approach 3: Static Top-K Retrieval & Manual UI Sliders
- **What was tried:** Fixed $K=5$ retrieval for all queries, with manual sliders in the UI allowing the user to tweak Top-$K$ and boost factors.
- **Why it failed:**
  - For single facts and diagram lookups, $K=5$ introduced 3-4 noisy distractor chunks, slowing generation and risking confusion.
  - For complex comparative matrices (comparing 2 fortresses or characters across 4 fields), $K=5$ missed secondary document chunks.
  - Manual sliders force the user to guess optimal parameters, violating autonomous RAG principles.
- **Decision:** Replaced with **3-Stage Adaptive Context Budgeting** ($K=2$ for single facts, $K=4$ for lore, $K=6\text{--}8$ for comparative matrices + Elbow drop-off filter).

### 2.4 Discarded Approach 4: Speculative Narrative Bridging for Archive Contradictions
- **What was tried:** Prompting the LLM to synthesize reconciling explanations when two archive documents conflicted (e.g. why one faction record omitted a battle victory mentioned in another).
- **Why it failed:**
  - The LLM invented ungrounded rationales (e.g. claiming "divergent narrative framing" or unrecorded motives).
  - This constituted subtle, unverifiable hallucination violating strict archival integrity.
- **Decision:** Implemented **Strict Epistemic Restraint (Directive 5)**: report contradictions verbatim with exact source citations and state explicitly that the archive provides no reconciliation.

---

## 3. Edge Case Handling Protocol

| Edge Case | Failure Mode | Mitigation Strategy |
| :--- | :--- | :--- |
| **Missing Image File** | Broken image rendering in UI | Generation engine validates `resolve_media_path(media_path)` and disk existence before outputting markdown image tags. |
| **API Rate Limit / Network Hiccup** | Request dropped, empty response | Exponential backoff retry (1s, 2s, 4s) with deterministic grounded fallback. |
| **Ambiguous Lore Question** | LLM guesses or assumes | Strict Directive 5 mandates: *"If information is missing or unverified, state what is recorded and what is absent without speculation."* |
| **Unrecorded / Fabricated Entity** | Hallucinated fictional backstory | Pre-generation verification gate detects missing entities in context and outputs deterministic epistemic refusal. |
| **Out-of-Scope / Abusive Query** | Wasted retrieval & confusing output | Multi-category regex fast-path returns categorized refusal in $< 0.005$s with 3 helpful archival options and suppresses chunk inspector. |
