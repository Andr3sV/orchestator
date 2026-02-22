"""Tests for planner node (plan = list of agents) and email node context."""

import os

import pytest
from langchain_core.messages import HumanMessage, AIMessage

from src.graph.state import GraphState, create_initial_state
from src.graph.nodes.router import planner_node, ROUTE_VALUES
from src.graph.nodes.email import email_node

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
    """Messages about marketing copy (not sending email) should plan copy."""
    state = create_initial_state("Write a headline for a Facebook ad for our product launch")
    out = planner_node(state)
    assert "copy" in out["plan"]


def test_planner_strategy_like_message():
    """Messages about strategy should plan strategy."""
    state = create_initial_state("How should I market on LinkedIn?")
    out = planner_node(state)
    assert "strategy" in out["plan"]


def test_planner_draft_and_send_email_uses_email_only():
    """Draft and send email should plan email only (not copy,email); email agent drafts and sends."""
    state = create_initial_state(
        "Recomiéndame un mensaje para enviar a juan@gmail.com diciendo que llegaremos mañana"
    )
    out = planner_node(state)
    assert "email" in out["plan"]
    assert "copy" not in out["plan"]


def test_planner_use_calendar_to_write_email_plans_calendar_and_email():
    """When user asks to use calendar to write/send an email, plan must include calendar and email."""
    state = create_initial_state(
        "usa mi calendario para escribir un email a josep diciendole que haré mañana"
    )
    out = planner_node(state)
    assert "calendar" in out["plan"]
    assert "email" in out["plan"]


def test_planner_follow_up_envialo_a_plans_email():
    """When user says 'envialo a X' after a draft, planner should include email (conversation context)."""
    draft_summary = (
        "**Para:** old@example.com\n**Asunto:** Agenda\n**Cuerpo:**\nHola.\n\nResponde 'sí' para enviar."
    )
    state = GraphState(
        messages=[
            HumanMessage(content="envía un email a old@example.com con asunto Agenda diciendo Hola"),
            AIMessage(content=draft_summary),
            HumanMessage(content="envialo a other@example.com"),
        ],
        route=None,
        plan=None,
        plan_index=None,
        calendar_events=None,
        email_draft=None,
    )
    out = planner_node(state)
    assert "email" in out["plan"]


def test_email_follow_up_envialo_a_reuses_draft():
    """When user says 'envialo a X' after a draft, email node should return draft with new to, same subject/body."""
    draft_summary = (
        "Voy a enviar este email:\n\n**Para:** old@example.com\n**Asunto:** Agenda de mañana\n"
        "**Cuerpo:**\nMañana tengo reunión.\n\nResponde 'sí' o 'confirmo' para enviar."
    )
    state = GraphState(
        messages=[
            HumanMessage(content="usa mi calendario para escribir un email a old@example.com"),
            AIMessage(content="(calendar output)"),
            AIMessage(content=draft_summary),
            HumanMessage(content="envialo a other@example.com"),
        ],
        route=None,
        plan=None,
        plan_index=None,
        calendar_events=None,
        email_draft=None,
    )
    out = email_node(state)
    assert "email_draft" in out and out["email_draft"] is not None
    assert out["email_draft"]["to"] == "other@example.com"
    assert out["email_draft"]["subject"] == "Agenda de mañana"
    assert "reunión" in out["email_draft"]["body"] or "Mañana" in out["email_draft"]["body"]
