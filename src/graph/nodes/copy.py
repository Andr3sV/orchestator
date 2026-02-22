"""Copy agent node: suggests email copy and marketing text."""

from langchain_core.messages import SystemMessage, AIMessage

from src.agents.llm import get_llm
from src.agents.prompt_loader import get_system_prompt
from src.graph.state import GraphState


def copy_node(state: GraphState) -> dict:
    """Generate copy/email suggestion from user message."""
    llm = get_llm()
    messages = [SystemMessage(content=get_system_prompt("copy"))] + list(state["messages"])
    response = llm.invoke(messages)
    return {"messages": [AIMessage(content=response.content or "")]}

