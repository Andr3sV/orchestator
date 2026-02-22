"""Load agent system prompts from Opik when configured, with fallback to local defaults."""

import logging
import os

from src.agents.prompts import (
    CALENDAR_SYSTEM,
    COPY_SYSTEM,
    EMAIL_SYSTEM,
    EMAIL_SYSTEM_FROM_DRAFT_BODY,
    PLANNER_SYSTEM,
    STRATEGY_SYSTEM,
    SYNTHESIZER_SYSTEM,
)

logger = logging.getLogger(__name__)

# Logical name (used by nodes) -> (Opik prompt name, default text)
_PROMPT_MAP: dict[str, tuple[str, str]] = {
    "planner": ("orchestrator-planner", PLANNER_SYSTEM),
    "copy": ("orchestrator-copy", COPY_SYSTEM),
    "strategy": ("orchestrator-strategy", STRATEGY_SYSTEM),
    "calendar": ("orchestrator-calendar", CALENDAR_SYSTEM),
    "email": ("orchestrator-email", EMAIL_SYSTEM),
    "email_from_draft": ("orchestrator-email-from-draft", EMAIL_SYSTEM_FROM_DRAFT_BODY),
    "synthesizer": ("orchestrator-synthesizer", SYNTHESIZER_SYSTEM),
}

_cache: dict[str, str] = {}

# For seed script: list of (Opik prompt name, default text)
OPIK_PROMPT_SPECS: list[tuple[str, str]] = list(_PROMPT_MAP.values())


def get_system_prompt(name: str) -> str:
    """Return the system prompt for the given logical name (e.g. planner, copy, email).

    When OPIK_API_KEY is set, fetches from Opik (cached). Otherwise or on failure,
    returns the default from src.agents.prompts. Unknown names fall back to COPY_SYSTEM.
    """
    if name not in _PROMPT_MAP:
        logger.warning("Unknown prompt name %r, using copy default", name)
        return COPY_SYSTEM

    opik_name, default_text = _PROMPT_MAP[name]

    if name in _cache:
        return _cache[name]

    api_key = os.environ.get("OPIK_API_KEY")
    if not api_key or not api_key.strip():
        return default_text

    try:
        import opik

        client = opik.Opik()
        prompt_obj = client.get_prompt(name=opik_name)
        if prompt_obj and getattr(prompt_obj, "prompt", None):
            text = prompt_obj.prompt.strip() or default_text
            _cache[name] = text
            return text
    except Exception as e:  # noqa: BLE001
        logger.warning("Opik get_prompt(%s) failed: %s. Using default.", opik_name, e)

    return default_text
