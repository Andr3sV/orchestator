"""Tests for the declarative skills registry."""

import pytest

from src.graph.skills import NODE_SKILLS, get_skills_for_node, get_nodes_with_skill


def test_node_skills_has_all_agent_nodes():
    """NODE_SKILLS must include calendar, copy, strategy, email."""
    expected = {"calendar", "copy", "strategy", "email"}
    assert expected <= set(NODE_SKILLS.keys())


def test_each_node_has_at_least_one_skill():
    """Every registered node must have at least one skill."""
    for node, skills in NODE_SKILLS.items():
        assert len(skills) >= 1, f"Node {node} has no skills"


def test_get_nodes_with_skill_read_calendar():
    """get_nodes_with_skill('read_calendar') returns ['calendar']."""
    assert get_nodes_with_skill("read_calendar") == ["calendar"]


def test_get_skills_for_node():
    """get_skills_for_node returns the node's skills; unknown node returns empty."""
    assert get_skills_for_node("calendar") == ["read_calendar"]
    assert get_skills_for_node("email") == ["draft_email", "send_email"]
    assert get_skills_for_node("unknown_node") == []
