"""
Declarative skills registry: which agents (graph nodes) have which capabilities,
and which tools implement each skill. Used for documentation and future
delegation or proactive orchestration (e.g. "who has send_email?").
"""

from typing import Callable, Literal

from src.graph.tools.calendar import (
    get_events_today,
    get_events,
    get_events_for_range,
)
from src.gmail.send import send_email as gmail_send_email

SkillKind = Literal[
    "read_calendar",
    "send_email",
    "draft_email",
    "draft_copy",
    "strategy_advice",
]

# Skill -> list of callables that implement it (empty if skill is LLM-only in the node)
SKILL_TOOLS: dict[SkillKind, list[Callable]] = {
    "read_calendar": [get_events_today, get_events, get_events_for_range],
    "send_email": [gmail_send_email],
    "draft_email": [],
    "draft_copy": [],
    "strategy_advice": [],
}

# Graph node name -> list of skills that node uses
NODE_SKILLS: dict[str, list[SkillKind]] = {
    "calendar": ["read_calendar"],
    "email": ["draft_email", "send_email"],
    "copy": ["draft_copy"],
    "strategy": ["strategy_advice"],
}


def get_skills_for_node(node_name: str) -> list[SkillKind]:
    """Return the list of skills for a graph node, or empty if unknown."""
    return list(NODE_SKILLS.get(node_name, []))


def get_nodes_with_skill(skill: SkillKind) -> list[str]:
    """Return graph node names that have the given skill."""
    return [node for node, skills in NODE_SKILLS.items() if skill in skills]
