#!/usr/bin/env python3
"""
RAGAS evaluation runner for archi_RAG.

Usage:
    python eval/run_ragas.py                        # run all ready entries
    python eval/run_ragas.py --id eval_001          # run a single entry
    python eval/run_ragas.py --out eval/results.csv # custom output path

An entry is considered "ready" when its ground_truth_context field does not
start with "TODO". Refusal entries (question_type == "refusal") are always
ready and are evaluated separately.
"""

import argparse
import csv
import json
import sys
from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from loguru import logger
from ragas import evaluate, EvaluationDataset
from ragas.dataset_schema import SingleTurnSample
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import AnswerCorrectness, Faithfulness, LLMContextRecall

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.agent.graph import build_agent
from src.config import LLAMACPP_HOST, LLM_MODEL_NAME
from src.retrieval.retriever import Retriever

GOLDEN_SET = ROOT / "eval" / "golden_set.jsonl"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_golden_set(filter_id: str | None = None) -> list[dict]:
    entries = []
    with open(GOLDEN_SET) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            if filter_id and entry["id"] != filter_id:
                continue
            entries.append(entry)
    return entries


def is_ready(entry: dict) -> bool:
    """Entry is ready when the domain expert has filled in the TODO fields."""
    if entry["question_type"] == "refusal":
        return True
    return not entry.get("ground_truth_context", "").startswith("TODO")


def run_pipeline(question: str, agent, retriever: Retriever) -> tuple[str, list[str]]:
    """
    Run the full agent for a question.

    Returns:
        answer:   Final model response string.
        contexts: All parent_text passages retrieved across all tool calls.
    """
    result = agent.invoke({"messages": [HumanMessage(content=question)]})
    messages = result["messages"]

    answer = ""
    contexts: list[str] = []

    for msg in messages:
        if isinstance(msg, ToolMessage):
            contexts.append(msg.content)
        elif isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
            answer = msg.content

    return answer, contexts


def make_ragas_llm() -> LangchainLLMWrapper:
    llm = ChatOpenAI(
        model=LLM_MODEL_NAME,
        base_url=f"{LLAMACPP_HOST}/v1",
        api_key="local",
        temperature=0.0,
    )
    return LangchainLLMWrapper(llm)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", help="Run a single golden set entry by ID")
    parser.add_argument("--out", default="eval/results.csv", help="Output CSV path")
    args = parser.parse_args()

    logger.remove()
    logger.add(sys.stderr, level="INFO", colorize=True)

    entries = load_golden_set(filter_id=args.id)
    ready = [e for e in entries if is_ready(e)]
    skipped = [e for e in entries if not is_ready(e)]

    if skipped:
        logger.warning(
            f"Skipping {len(skipped)} entries still marked TODO: "
            + ", ".join(e["id"] for e in skipped)
        )

    if not ready:
        logger.error("No ready entries found. Fill in ground_truth_context fields first.")
        sys.exit(1)

    logger.info(f"Running evaluation on {len(ready)} entries…")
    logger.info("Loading agent and retriever (this may take a minute)…")

    retriever = Retriever()
    agent = build_agent(retriever)
    ragas_llm = make_ragas_llm()

    # Metrics — all LLM-based, no embedding model required
    standard_metrics = [
        LLMContextRecall(llm=ragas_llm),   # Did retrieval surface the right passage?
        Faithfulness(llm=ragas_llm),        # Is the answer grounded in retrieved contexts?
        AnswerCorrectness(llm=ragas_llm),   # Is the answer factually correct vs ground truth?
    ]
    refusal_metrics = [
        Faithfulness(llm=ragas_llm),        # Refusal answers have no context; just check grounding
    ]

    samples: list[SingleTurnSample] = []
    raw_rows: list[dict] = []

    for entry in ready:
        logger.info(f"  [{entry['id']}] {entry['question'][:70]}…")

        answer, contexts = run_pipeline(entry["question"], agent, retriever)

        is_refusal = entry["question_type"] == "refusal"

        sample = SingleTurnSample(
            user_input=entry["question"],
            response=answer,
            retrieved_contexts=contexts if not is_refusal else [],
            reference=entry["ground_truth_answer"],
            reference_contexts=(
                [entry["ground_truth_context"]] if not is_refusal else []
            ),
        )
        samples.append(sample)

        raw_rows.append({
            "id": entry["id"],
            "question_type": entry["question_type"],
            "authority": entry["authority"],
            "question": entry["question"],
            "answer": answer,
            "n_contexts_retrieved": len(contexts),
            "expected_citation": entry["expected_citation"],
        })

    # Run RAGAS evaluate
    dataset = EvaluationDataset(samples=samples)
    logger.info("Running RAGAS metrics…")
    results = evaluate(dataset=dataset, metrics=standard_metrics)

    # Merge RAGAS scores into raw_rows
    scores_df = results.to_pandas()
    out_rows = []
    for i, row in enumerate(raw_rows):
        ragas_scores = scores_df.iloc[i].to_dict() if i < len(scores_df) else {}
        out_rows.append({**row, **ragas_scores})

    # Print summary
    print("\n" + "=" * 70)
    print("RAGAS EVALUATION RESULTS")
    print("=" * 70)
    for row in out_rows:
        print(f"\n[{row['id']}] ({row['question_type']}) {row['question'][:60]}…")
        for metric in ["llm_context_recall", "faithfulness", "answer_correctness"]:
            val = row.get(metric)
            if val is not None:
                print(f"  {metric}: {val:.3f}")

    print("\n--- Aggregate ---")
    for metric in ["llm_context_recall", "faithfulness", "answer_correctness"]:
        vals = [r[metric] for r in out_rows if r.get(metric) is not None]
        if vals:
            print(f"  {metric}: {sum(vals)/len(vals):.3f} (n={len(vals)})")

    # Save CSV
    out_path = ROOT / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_rows:
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=out_rows[0].keys())
            writer.writeheader()
            writer.writerows(out_rows)
        logger.info(f"Results saved to {out_path}")


if __name__ == "__main__":
    main()
