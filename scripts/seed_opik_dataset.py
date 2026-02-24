#!/usr/bin/env python3
"""
One-time script to create the evaluation dataset in Opik and upload items from data/eval_dataset.json.
Run from repo root with Opik configured (OPIK_API_KEY set).

  python3 scripts/seed_opik_dataset.py

After running, the dataset "orchestrator-eval" appears in the Opik UI with all items for evaluation.
"""

import json
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


def main() -> None:
    if not os.environ.get("OPIK_API_KEY", "").strip():
        print("OPIK_API_KEY is not set. Run 'opik configure' or set it in .env.", file=sys.stderr)
        sys.exit(1)

    data_path = _project_root / "data" / "eval_dataset.json"
    if not data_path.exists():
        print(f"Dataset file not found: {data_path}", file=sys.stderr)
        sys.exit(1)

    with open(data_path, encoding="utf-8") as f:
        payload = json.load(f)

    name = payload.get("name", "orchestrator-eval")
    description = payload.get("description", "")
    items_spec = payload.get("items", [])

    if not items_spec:
        print("No items in dataset file.", file=sys.stderr)
        sys.exit(1)

    import opik

    client = opik.Opik()
    dataset = client.get_or_create_dataset(name, description=description or None)

    # Opik items: source + data (data holds input, expected_output, metadata for evaluation)
    items = []
    for spec in items_spec:
        data = {
            "item_id": spec.get("id"),
            "input": spec.get("input", {}),
            "expected_output": spec.get("expected_output", ""),
            **spec.get("metadata", {}),
        }
        items.append({"source": "sdk", "data": data})

    dataset.insert(items)
    print(f"Dataset {name!r}: inserted {len(items)} items.")

    print("Done. Open the Opik UI → Datasets to see the dataset and run experiments.")


if __name__ == "__main__":
    main()
