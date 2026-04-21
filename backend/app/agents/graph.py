"""
OutreachX — LangGraph StateGraph (complete pipeline)

Three entry paths:
  A) Discovery  : query → planner → discovery → researcher → contact_finder → email_gen → validator
  B) Uploaded DB: file  → planner → discovery → researcher → contact_finder → email_gen → validator
  C) Direct     : "email Razorpay, Groww" → planner → direct_input → researcher → contact_finder → email_gen → validator
"""

from langgraph.graph import StateGraph, START, END
from typing import Literal

from app.agents.state import AgentState
from app.agents.nodes.planner         import planner_node
from app.agents.nodes.discovery       import discovery_node
from app.agents.nodes.direct_input    import direct_input_node
from app.agents.nodes.researcher      import researcher_node
from app.agents.nodes.contact_finder  import contact_finder_node
from app.agents.nodes.email_generator import email_generator_node
from app.agents.nodes.validator       import validator_node


def route_after_planner(state: AgentState) -> Literal["discovery", "direct_input", "__end__"]:
    if state.get("errors") and not state.get("query") and not state.get("uploaded_file_path"):
        return "__end__"
    if state.get("entry_mode") == "direct":
        return "direct_input"
    return "discovery"


def build_graph() -> StateGraph:
    builder = StateGraph(AgentState)

    builder.add_node("planner",         planner_node)
    builder.add_node("discovery",       discovery_node)
    builder.add_node("direct_input",    direct_input_node)
    builder.add_node("researcher",      researcher_node)
    builder.add_node("contact_finder",  contact_finder_node)
    builder.add_node("email_generator", email_generator_node)
    builder.add_node("validator",       validator_node)

    builder.add_edge(START, "planner")
    builder.add_conditional_edges(
        "planner", route_after_planner,
        {"discovery": "discovery", "direct_input": "direct_input", "__end__": END},
    )

    # Both discovery and direct_input feed into researcher
    builder.add_edge("discovery",    "researcher")
    builder.add_edge("direct_input", "researcher")

    builder.add_edge("researcher",      "contact_finder")
    builder.add_edge("contact_finder",  "email_generator")
    builder.add_edge("email_generator", "validator")
    builder.add_edge("validator",       END)

    return builder.compile()


graph = build_graph()