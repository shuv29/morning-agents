import time

from langchain_core.messages import HumanMessage, SystemMessage

from config import get_llm
from state import MorningState
from tools.calendar_tools import fetch_upcoming_events

SYSTEM_PROMPT = """You are a scheduling assistant preparing a morning day-preview.
For each event: time/title, what to expect and how to prepare, and flag anything
unusual (back-to-back meetings, very early events, large attendee lists).
End with one sentence on the day's shape. Be concise and practical."""


def calendar_agent(state: MorningState) -> dict:
    start = time.time()
    try:
        events = fetch_upcoming_events()
        if not events:
            report = "No events in the next 24 hours. Open day."
        else:
            events_text = "\n".join(
                f"- {ev['start']} to {ev['end']}: {ev['title']}"
                f" | Location: {ev['location'] or 'n/a'}"
                f" | Attendees: {', '.join(ev['attendees']) or 'none'}"
                f" | Notes: {ev['description'] or 'none'}"
                for ev in events
            )
            llm = get_llm(temperature=0.3)
            response = llm.invoke([
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=f"Today's {len(events)} events:\n\n{events_text}"),
            ])
            report = response.content

        return {
            "calendar_report": report,
            "agent_metrics": [{
                "agent_name": "calendar_agent", "status": "success",
                "duration_seconds": round(time.time() - start, 2),
                "items_processed": len(events), "error_message": "",
            }],
        }
    except Exception as exc:
        return {
            "calendar_report": f"⚠️ Calendar agent failed: {exc}",
            "agent_metrics": [{
                "agent_name": "calendar_agent", "status": "error",
                "duration_seconds": round(time.time() - start, 2),
                "items_processed": 0, "error_message": str(exc),
            }],
        }