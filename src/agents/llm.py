"""Shared LLM instance for all agents (OpenAI)."""

from langchain_openai import ChatOpenAI

from src.config import get_settings


def get_llm() -> ChatOpenAI:
    """Return configured ChatOpenAI. Uses settings from env."""
    s = get_settings()
    return ChatOpenAI(
        model=s.openai_model,
        temperature=s.openai_temperature,
        api_key=s.openai_api_key,
    )
