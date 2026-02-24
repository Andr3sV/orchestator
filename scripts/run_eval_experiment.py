#!/usr/bin/env python3
"""
Run an Opik evaluation experiment on the orchestrator-eval dataset.
Invokes the graph for each dataset item and scores with the Hallucination metric.

  python3 scripts/run_eval_experiment.py
  python3 scripts/run_eval_experiment.py --samples 5

Requires: OPIK_API_KEY, OPENAI_API_KEY. Optional: Google env for calendar/email items.
"""

import argparse
import os
import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root))

try:
    from dotenv import load_dotenv

    load_dotenv(_project_root / ".env")
except ImportError:
    pass


def _evaluation_task(app, item: dict) -> dict:
    """Run the graph for one dataset item; return output and input for scoring."""
    from langchain_core.messages import AIMessage, HumanMessage

    data = item.get("data", item)
    user_message = (data.get("input") or {}).get("user_message", "")
    item_id = data.get("item_id") or hash(user_message)

    result = app.invoke(
        {"messages": [HumanMessage(content=user_message)]},
        config={"configurable": {"thread_id": f"eval-{item_id}"}},
    )
    messages = result.get("messages") or []
    content = ""
    for m in reversed(messages):
        if isinstance(m, AIMessage) and getattr(m, "content", None):
            content = (m.content or "").strip() if isinstance(m.content, str) else str(m.content or "").strip()
            break
    return {"output": content, "input": user_message}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Opik evaluation experiment on orchestrator-eval dataset.")
    parser.add_argument("--samples", type=int, default=None, help="Limit to N dataset items (default: all)")
    args = parser.parse_args()

    if not os.environ.get("OPIK_API_KEY", "").strip():
        print("OPIK_API_KEY is not set. Run 'opik configure' or set it in .env.", file=sys.stderr)
        sys.exit(1)

    from src.graph.graph import get_app

    app = get_app()

    def evaluation_task(item: dict) -> dict:
        return _evaluation_task(app, item)

    import opik
    from opik.evaluation import evaluate
    from opik.evaluation.metrics import Hallucination

    try:
        from src.config import Settings
        settings = Settings()
        model = getattr(settings, "openai_model", "gpt-4o-mini")
    except Exception:
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    client = opik.Opik()
    dataset = client.get_or_create_dataset("orchestrator-eval")

    evaluation = evaluate(
        dataset=dataset,
        task=evaluation_task,
        scoring_metrics=[Hallucination()],
        experiment_name="Orchestrator eval",
        experiment_config={"model": model},
        nb_samples=args.samples,
        task_threads=1,
    )

    print("Experiment finished.")
    if getattr(evaluation, "experiment_id", None):
        print(f"Experiment ID: {evaluation.experiment_id}")
    if getattr(evaluation, "aggregate_evaluation_scores", None):
        try:
            scores = evaluation.aggregate_evaluation_scores()
            if scores and getattr(scores, "aggregated_scores", None):
                for metric_name, stats in scores.aggregated_scores.items():
                    print(f"  {metric_name}: {stats}")
        except Exception:
            pass
    print("Open the Opik UI → Experiments to view results and traces.")


if __name__ == "__main__":
    main()
