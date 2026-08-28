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

### 2.1 Discarded Approach 1: Naive Flat Text Chunking (Sprint 1 Baseline)
- **What was tried:** Stripped all images and tables, converting the entire corpus into 500-token plain text chunks.
- **Why it failed:** 
  - Failed completely on 9 out of 10 visual/figure questions in `sample_questions.json`.
  - Answers contained hallucinated descriptions of visual plates instead of actual images.
  - Complex table stats lost column alignment and caused arithmetic errors in LLM reasoning.
- **Decision:** Shifted to modality-tagged chunking with dedicated image extraction in Sprint 2.

### 2.2 Discarded Approach 2: Full Multimodal Vision-LLM on Every Query
- **What was tried:** Feeding entire raw PDF page screenshots to a large Multimodal LLM (VLM) for every query.
- **Why it failed:** 
  - Excessive token consumption (exceeded rate limits within 5 queries).
  - High latency (8-12 seconds per response).
  - High hallucination rate on non-visual text queries across 1,277 pages.
- **Decision:** Implemented **Modality-Aware Hybrid Routing**: only pass visual image assets to the context when the query specifically demands or benefits from visual evidence.

---

## 3. Edge Case Handling Protocol

| Edge Case | Failure Mode | Mitigation Strategy |
| :--- | :--- | :--- |
| **Missing Image File** | Broken image rendering in UI | Generation engine validates `os.path.exists(media_path)` before outputting markdown image tags. |
| **OpenRouter 429 Rate Limit** | Request dropped, empty response | Exponential backoff (1s, 2s, 4s, 8s, 16s) with automatic fallback model failover. |
| **Ambiguous Lore Question** | LLM guesses or assumes | Prompt instructions strictly enforce: *"If information is missing or unverified in retrieved chunks, state what is known and what cannot be confirmed."* |
