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

| Metric | Sprint 1 (Text Baseline) | Sprint 2 (Modality-Aware) | Sprint 3 (Hardened Final System) | Target |
| :--- | :--- | :--- | :--- | :--- |
| **Retrieval Precision (Top-5)** | 60.0% (12/20) | 85.0% (17/20) | **100.0% (20/20)** | $\ge 90\%$ |
| **Citation Accuracy** | 55.0% (11/20) | 90.0% (18/20) | **100.0% (20/20)** | $\ge 95\%$ |
| **Hallucination Rate** | 20.0% (4/20) | 5.0% (1/20) | **0.0% (0/20)** | $\le 5\%$ |
| **Modality Success (Figures/Tables)** | 10.0% (1/10) | 90.0% (9/10) | **100.0% (11/11)** | $\ge 95\%$ |
| **Average End-to-End Latency** | 2.1s | 2.8s | **0.89s** | $< 3.5s$ |

> [!NOTE]
> All metrics report exact fractions alongside percentages for scientific transparency.

---

## 3. Detailed Question-by-Question Evaluation Log (20 Benchmark Questions)

| QID | Track | Question Summary | Retrieval | Citation | Modality | Latency |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1a_v12** | 1A | What is the central emblem on the banner of H... | ✅ Pass | ✅ Pass | ✅ Pass | 13.731s |
| **1a_v06** | 1A | In the portrait of Ignatz Ashgrove the Oathle... | ✅ Pass | ✅ Pass | ✅ Pass | 0.251s |
| **1a_008** | 1A | According to the official threat-classificati... | ✅ Pass | ✅ Pass | ✅ Pass | 0.216s |
| **1a_004** | 1A | According to the figure plate detailing weapo... | ✅ Pass | ✅ Pass | ✅ Pass | 0.253s |
| **1a_013** | 1A | On the figure plate depicting 'The Cinder-Wro... | ✅ Pass | ✅ Pass | ✅ Pass | 0.215s |
| **1a_v11** | 1A | What is the central emblem on the banner of T... | ✅ Pass | ✅ Pass | ✅ Pass | 0.206s |
| **1a_v07** | 1A | In the portrait of Aldous Wrenfield the Last ... | ✅ Pass | ✅ Pass | ✅ Pass | 0.211s |
| **1a_009** | 1A | According to the figure plate, what is the re... | ✅ Pass | ✅ Pass | ✅ Pass | 0.208s |
| **1a_007** | 1A | According to the figure plate, what is the at... | ✅ Pass | ✅ Pass | ✅ Pass | 0.219s |
| **1a_v21** | 1A | What motif is engraved on Gauntlet of Sorrowf... | ✅ Pass | ✅ Pass | ✅ Pass | 0.189s |
| **1a_001** | 1A | According to the figure plate illustrating Em... | ✅ Pass | ✅ Pass | ✅ Pass | 0.2s |
| **1b_007** | 1B | Which accord was ultimately won by the factio... | ✅ Pass | ✅ Pass | ✅ Pass | 0.197s |
| **1b_006** | 1B | Which individual was a member of the faction ... | ✅ Pass | ✅ Pass | ✅ Pass | 0.218s |
| **1b_022** | 1B | Which war did Ravena Stormwell's own faction ... | ✅ Pass | ✅ Pass | ✅ Pass | 0.252s |
| **1b_013** | 1B | Whose dominion encompasses the lair of the Gr... | ✅ Pass | ✅ Pass | ✅ Pass | 0.177s |
| **1b_005** | 1B | Which war was won by the organization that in... | ✅ Pass | ✅ Pass | ✅ Pass | 0.269s |
| **1b_009** | 1B | In what way is Halvard Crowhurst connected to... | ✅ Pass | ✅ Pass | ✅ Pass | 0.214s |
| **1b_003** | 1B | To which shadowed redoubt must one journey to... | ✅ Pass | ✅ Pass | ✅ Pass | 0.239s |
| **1c_000** | 1C | State the precise year in the Age of Shadows ... | ✅ Pass | ✅ Pass | ✅ Pass | 0.196s |
| **1c_003** | 1C | In which year was the 'Gauntlet of Sorrowfell... | ✅ Pass | ✅ Pass | ✅ Pass | 0.191s |

---

## 4. Evaluation Methodology

1. **End-to-End Pipeline Verification**: Every query passes through Intent Classification $\rightarrow$ Modality-Aware Retrieval $\rightarrow$ Grounded Generation.
2. **Strict Grounding & Citation Validation**: Answers are verified to contain explicit `[Document Name, Page Number]` references matching the corpus.
3. **Visual Embedding Confirmation**: Image and table queries are evaluated to confirm direct markdown figure embeds referencing verified assets on disk.
