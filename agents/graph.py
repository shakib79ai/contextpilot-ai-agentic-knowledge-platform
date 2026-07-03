"""LangGraph orchestration for the query-time agent pipeline:

    Retriever Agent -> Answer Agent -> Evaluator Agent -> Human Escalation Agent

The Knowledge Update Agent is intentionally NOT part of this graph — it only
runs later, out-of-band, when a human reviewer resolves an escalated answer
with a correction (see agents/knowledge_update_agent.py).
"""
from langgraph.graph import END, StateGraph

from agents import answer_agent, escalation_agent, evaluator_agent, retriever_agent
from agents.state import AgentState


def build_graph(db=None):
    workflow = StateGraph(AgentState)

    workflow.add_node("retrieve", retriever_agent.run)
    workflow.add_node("answer", answer_agent.run)
    workflow.add_node("evaluate", lambda state: evaluator_agent.run(state, db=db))
    workflow.add_node("escalate", escalation_agent.run)

    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "answer")
    workflow.add_edge("answer", "evaluate")
    workflow.add_edge("evaluate", "escalate")
    workflow.add_edge("escalate", END)

    return workflow.compile()


def run_query_graph(question: str, top_k: int = 5, db=None) -> AgentState:
    graph = build_graph(db=db)
    initial_state: AgentState = {"question": question, "top_k": top_k}
    return graph.invoke(initial_state)
