"""Strategy agent node: helps with marketing strategy and planning."""

from langchain_core.messages import SystemMessage, AIMessage

from src.agents.llm import get_llm
from src.agents.prompt_loader import get_system_prompt
from src.graph.state import GraphState


def strategy_node(state: GraphState) -> dict:
    """Generate strategy advice from user message."""
    llm = get_llm()
    messages = [SystemMessage(content=get_system_prompt("strategy"))] + list(state["messages"])
    response = llm.invoke(messages)
    return {"messages": [AIMessage(content=response.content or "")]}

