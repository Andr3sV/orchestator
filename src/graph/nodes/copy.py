"""Copy agent node: suggests email copy and marketing text."""

from langchain_core.messages import SystemMessage, AIMessage

from src.agents.llm import get_llm
from src.agents.prompts import COPY_SYSTEM
from src.graph.state import GraphState


def copy_node(state: GraphState) -> dict:
    """Generate copy/email suggestion from user message."""
    llm = get_llm()
    messages = [SystemMessage(content=COPY_SYSTEM)] + list(state["messages"])
    response = llm.invoke(messages)
    return {"messages": [AIMessage(content=response.content or "")]}

