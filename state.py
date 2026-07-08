import operator
from typing import Annotated, TypedDict


class AgentMetric(TypedDict):
    agent_name: str
    status: str
    duration_seconds: float
    items_processed: int
    error_message: str


class MorningState(TypedDict):
    email_report: str
    email_items: list
    calendar_report: str
    news_report: str
    news_items: list

    # operator.add = when parallel agents write here at once, APPEND
    # their lists instead of overwriting each other.
    agent_metrics: Annotated[list[AgentMetric], operator.add]

    monitor_report: str
    final_briefing: str