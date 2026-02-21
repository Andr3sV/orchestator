"""Strategy agent node: helps with marketing strategy and planning."""

from langchain_core.messages import SystemMessage, AIMessage

from src.agents.llm import get_llm
from src.agents.prompts import STRATEGY_SYSTEM
from src.graph.state import GraphState


def strategy_node(state: GraphState) -> dict:
    """Generate strategy advice from user message."""
    llm = get_llm()
    messages = [SystemMessage(content=STRATEGY_SYSTEM)] + list(state["messages"])
    response = llm.invoke(messages)
    return {"messages": [AIMessage(content=response.content or "")]}

