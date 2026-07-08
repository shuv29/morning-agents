import json
import os
from datetime import datetime

from langchain_core.messages import HumanMessage, SystemMessage

from config import get_llm
from state import MorningState

HISTORY_FILE = "metrics_history.jsonl"

SYSTEM_PROMPT = """You are a systems monitoring assistant for a multi-agent pipeline.
You receive today's per-agent metrics plus recent historical runs. Produce a SHORT
health report: one line per agent (✅/❌, duration, items), call out failures,
flag agents slower than usual or repeatedly failing. If all healthy, one line."""


def _load_history(max_runs: int = 7) -> list[dict]:
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE) as f:
        lines = f.readlines()
    return [json.loads(line) for line in lines[-max_runs:]]


def _append_history(metrics: list[dict]) -> None:
    record = {"run_at": datetime.now().isoformat(), "metrics": metrics}
    with open(HISTORY_FILE, "a") as f:
        f.write(json.dumps(record) + "\n")


def monitor_agent(state: MorningState) -> dict:
    todays_metrics = state["agent_metrics"]
    history = _load_history()
    _append_history(todays_metrics)

    llm = get_llm(temperature=0.1)
    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=(
            f"TODAY'S METRICS:\n{json.dumps(todays_metrics, indent=2)}\n\n"
            f"LAST {len(history)} RUNS:\n{json.dumps(history, indent=2)}"
        )),
    ])
    return {"monitor_report": response.content}


def compile_briefing(state: MorningState) -> dict:
    briefing = f"""
{'=' * 60}
☀️  MORNING BRIEFING — {datetime.now().strftime('%A, %B %d, %Y %H:%M')}
{'=' * 60}

📧 EMAIL
{state['email_report']}

📅 CALENDAR
{state['calendar_report']}

📈 MARKETS
{state['news_report']}

🩺 SYSTEM HEALTH
{state['monitor_report']}
{'=' * 60}
"""
    return {"final_briefing": briefing}