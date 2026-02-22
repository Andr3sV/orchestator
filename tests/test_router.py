"""Tests for planner node (plan = list of agents)."""

import os

import pytest
from langchain_core.messages import HumanMessage

from src.graph.state import GraphState, create_initial_state
from src.graph.nodes.router import planner_node, ROUTE_VALUES

pytestmark = pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set",
)


def test_planner_returns_valid_plan(sample_state):
    """Planner should return a list of valid agent names."""
    out = planner_node(sample_state)
    assert "plan" in out
    assert isinstance(out["plan"], list)
    assert len(out["plan"]) >= 1
    for r in out["plan"]:
        assert r in ROUTE_VALUES


def test_planner_calendar_like_message():
    """Messages about agenda should plan calendar."""
    state = create_initial_state("What's on my calendar today?")
    out = planner_node(state)
    assert "calendar" in out["plan"]


def test_planner_copy_like_message():
    """Messages about writing copy should plan copy."""
    state = create_initial_state("Write a short email for a product launch")
    out = planner_node(state)
    assert "copy" in out["plan"]


def test_planner_strategy_like_message():
    """Messages about strategy should plan strategy."""
    state = create_initial_state("How should I market on LinkedIn?")
    out = planner_node(state)
    assert "strategy" in out["plan"]
