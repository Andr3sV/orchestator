#!/usr/bin/env python3
"""
One-time script to create or update agent system prompts in the Opik prompt library.
Run from repo root with Opik configured (OPIK_API_KEY set).

  python3 scripts/seed_opik_prompts.py

After running, you can edit prompts in the Opik UI; the app will use them (with cache).
"""

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

    import opik
    from src.agents.prompt_loader import OPIK_PROMPT_SPECS

    for opik_name, text in OPIK_PROMPT_SPECS:
        opik.Prompt(name=opik_name, prompt=text)
        print(f"Created/updated prompt: {opik_name}")

    print("Done. Prompts are in the Opik prompt library.")


if __name__ == "__main__":
    main()
