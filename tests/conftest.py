"""Pytest configuration and fixtures."""

import os

import pytest


@pytest.fixture(scope="session")
def needs_openai():
    """Skip if OPENAI_API_KEY is not set (for integration tests)."""
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")


@pytest.fixture
def sample_state():
    """Initial graph state with one user message."""
    from src.graph.state import create_initial_state
    return create_initial_state("What do I have today?")
