"""Tests for router node (classification)."""

import os

import pytest
from langchain_core.messages import HumanMessage

from src.graph.state import GraphState, create_initial_state
from src.graph.nodes.router import router_node, ROUTE_VALUES

pytestmark = pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set",
)


def test_router_returns_valid_route(sample_state):
    """Router should return one of copy, strategy, calendar."""
    out = router_node(sample_state)
    assert "route" in out
    assert out["route"] in ROUTE_VALUES


def test_router_calendar_like_message():
    """Messages about agenda should route to calendar."""
    state = create_initial_state("What's on my calendar today?")
    out = router_node(state)
    assert out["route"] == "calendar"


def test_router_copy_like_message():
    """Messages about writing copy should route to copy."""
    state = create_initial_state("Write a short email for a product launch")
    out = router_node(state)
    assert out["route"] == "copy"


def test_router_strategy_like_message():
    """Messages about strategy should route to strategy."""
    state = create_initial_state("How should I market on LinkedIn?")
    out = router_node(state)
    assert out["route"] == "strategy"
