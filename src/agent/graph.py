from typing import Annotated

from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

from src.agent.llm import get_llm
from src.agent.prompts import SYSTEM_PROMPT
from src.agent.tools import make_tools
from src.retrieval.retriever import Retriever


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def build_agent(retriever: Retriever | None = None):
    """
    Build and return the LangGraph agent using the low-level StateGraph API.

    This approach is version-agnostic and doesn't rely on prebuilt agents
    that have changed signatures between LangGraph releases.

    Args:
        retriever: An initialized Retriever. Creates a new one if None.

    Returns:
        A compiled LangGraph graph. Call .invoke() or .stream() on it.
    """
    if retriever is None:
        retriever = Retriever()

    llm = get_llm()
    tools = make_tools(retriever)
    llm_with_tools = llm.bind_tools(tools)

    def agent_node(state: AgentState):
        """LLM agent node: prepend system message and invoke."""
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def should_continue(state: AgentState) -> str:
        """Route: tools if agent called a tool, else END."""
        return "tools" if state["messages"][-1].tool_calls else END

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(tools))

    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", should_continue)
    graph.add_edge("tools", "agent")

    return graph.compile()
