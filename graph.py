from langgraph.graph import END, START, StateGraph

from agents.calendar_agent import calendar_agent
from agents.email_agent import email_agent
from agents.monitor_agent import compile_briefing, monitor_agent
from agents.news_agent import news_agent
from state import MorningState


def build_graph():
    graph = StateGraph(MorningState)

    graph.add_node("email", email_agent)
    graph.add_node("calendar", calendar_agent)
    graph.add_node("news", news_agent)
    graph.add_node("monitor", monitor_agent)
    graph.add_node("briefing", compile_briefing)

    # Fan-out: three edges from START = these run IN PARALLEL
    graph.add_edge(START, "email")
    graph.add_edge(START, "calendar")
    graph.add_edge(START, "news")

    # Fan-in: monitor WAITS for all three to finish
    graph.add_edge("email", "monitor")
    graph.add_edge("calendar", "monitor")
    graph.add_edge("news", "monitor")

    graph.add_edge("monitor", "briefing")
    graph.add_edge("briefing", END)

    return graph.compile()