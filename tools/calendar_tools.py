from datetime import datetime, timedelta, timezone

from googleapiclient.discovery import build

from config import CALENDAR_LOOKAHEAD_HOURS
from tools.gmail_tools import get_google_credentials


def fetch_upcoming_events() -> list[dict]:
    service = build("calendar", "v3", credentials=get_google_credentials())
    now = datetime.now(timezone.utc)
    time_max = now + timedelta(hours=CALENDAR_LOOKAHEAD_HOURS)

    result = service.events().list(
        calendarId="primary",
        timeMin=now.isoformat(),
        timeMax=time_max.isoformat(),
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    events = []
    for ev in result.get("items", []):
        events.append({
            "title": ev.get("summary", "(untitled)"),
            "start": ev["start"].get("dateTime", ev["start"].get("date")),
            "end": ev["end"].get("dateTime", ev["end"].get("date")),
            "location": ev.get("location", ""),
            "description": ev.get("description", "")[:300],
            "attendees": [a.get("email", "") for a in ev.get("attendees", [])][:10],
        })
    return events


if __name__ == "__main__":
    for ev in fetch_upcoming_events():
        print(f"{ev['start']} — {ev['title']}")