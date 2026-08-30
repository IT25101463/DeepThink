"""
Benchmark Evaluation Runner (Owner: Member P4)
Evaluates DeepThink against the 20 sample_questions.json and logs results in docs/metrics.md.
"""

import json
from pathlib import Path
from src.config import DATA_DIR
from src.retrieval.retriever import retrieve
from src.generation.generator import generate_answer


def run_benchmark(questions_file: Path = DATA_DIR / "sample_questions.json"):
    """
    Runs the 20 sample questions end-to-end, evaluating retrieval precision,
    citation accuracy, hallucination, and figure embedding success.
    """
    if not questions_file.exists():
        print(f"Questions file not found: {questions_file}")
        return

    with open(questions_file, "r", encoding="utf-8") as f:
        questions = json.load(f)

    print(f"Evaluating {len(questions)} benchmark questions...")
    # TODO (P4): Implement automated evaluation loop and metrics computation


if __name__ == "__main__":
    run_benchmark()
