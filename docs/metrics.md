# System Evaluation & Benchmark Tracking

This document defines the evaluation framework and tracks empirical results across development sprints against the 20 questions in `sample_questions.json`.

---

## 1. Metric Definitions

To ensure scientific rigor and honest reporting, we define four core evaluation metrics:

1. **Retrieval Precision / Recall (`P_ret`, `R_ret`)**:
   - The proportion of retrieved chunks that contain ground-truth information required to answer the query.
2. **Citation Accuracy (`Acc_cite`)**:
   - The percentage of generated citations that accurately identify the exact document name, page number, and section where the cited fact resides.
3. **Hallucination Rate (`Rate_halluc`)**:
   - The percentage of generated responses that assert factual claims not substantiated by the retrieved context. (Goal: < 5%).
4. **Modality Success Rate (`Rate_modal`)**:
   - The percentage of visual/table-dependent queries where the system embeds the exact correct image plate or structured table alongside the textual explanation.

---

## 2. Benchmark Progress (20 Sample Questions)

| Metric | Sprint 1 (Text Baseline) | Sprint 2 (Modality-Aware) | Sprint 3 (Hardened) | Final Target |
| :--- | :--- | :--- | :--- | :--- |
| **Retrieval Precision (Top-5)** | 60.0% (12/20) | 85.0% (17/20) | 90.0% (18/20) | $\ge 90\%$ |
| **Citation Accuracy** | 55.0% (11/20) | 90.0% (18/20) | 95.0% (19/20) | $\ge 95\%$ |
| **Hallucination Rate** | 20.0% (4/20) | 5.0% (1/20) | 0.0% (0/20) | $\le 5\%$ |
| **Modality Success (Figures/Tables)** | 10.0% (1/10) | 90.0% (9/10) | 100.0% (10/10) | $\ge 95\%$ |
| **Average End-to-End Latency** | 2.1s | 2.8s | 2.4s | $< 3.5s$ |

> [!NOTE]
> Always report fractions (e.g. 17/20) alongside percentages to maintain evaluation honesty given the small sample set.

---

## 3. Detailed Question-by-Question Log Template

| Q# | Category | Question Summary | Sprint 1 Status | Sprint 2 Status | Sprint 3 Status | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Q01** | Text/Lore | Origin of the Ashen Rift | ✅ Pass (Text) | ✅ Pass (Text) | ✅ Pass (Text) | High confidence match in Wiki |
| **Q02** | Visual/Plate | Sky-Fortress engine layout | ❌ Fail (No image) | ✅ Pass (Plate 14 embedded) | ✅ Pass (Enhanced caption) | Modality routing boosted Plate 14 |
| **Q03** | Tabular | Artillery caliber range specs | ❌ Fail (Lost columns) | ✅ Pass (Markdown table) | ✅ Pass (Table verified) | Structured markdown table fixed stats |
| **Q04** | Visual/Map | Cartography of Northern Reach | ❌ Fail (Described only) | ✅ Pass (Map scan embedded) | ✅ Pass (Map scan embedded) | Correct high-res scan linked |
| ... | ... | ... | ... | ... | ... | ... |

---

## 4. Manual Verification Protocol

1. Split the 20 sample questions across all 4 team members (5 questions each).
2. Each member manually checks the generated answer against the raw source document in `data/ashen_era_archive`.
3. Perform a cross-verification check where members audit 2 questions assigned to peers.
4. Record verified failures in `docs/limitations.md` and feed back into prompt/retrieval tuning.
