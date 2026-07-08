import time

from pydantic import BaseModel, Field

from config import get_llm
from state import MorningState
from tools.gmail_tools import fetch_recent_emails


# ---- The output schema: this IS the prompt engineering ----
# with_structured_output makes Gemini fill these exact fields.
# The Field descriptions are instructions the model reads.

class EmailInsight(BaseModel):
    sender: str = Field(description="Short sender name, e.g. 'LinkedIn' or 'Jamie Francis'")
    subject: str = Field(description="The email subject, trimmed")
    priority: str = Field(description="One of: URGENT, IMPORTANT, LOW")
    summary: str = Field(description="1-2 sentence summary of what this email actually says")
    recommended_action: str = Field(
        description="Concrete next step, e.g. 'Reply confirming availability', "
                    "'Apply before deadline', 'Archive - promotional'. Imperative mood."
    )
    deadline: str = Field(
        description="Any date/time deadline mentioned or implied, else 'none'"
    )
    action_type: str = Field(
        description="One of: REPLY, APPLY, REVIEW, SCHEDULE, PAY, ARCHIVE, NONE"
    )


class EmailTriage(BaseModel):
    emails: list[EmailInsight] = Field(
        description="One entry per meaningful email. Skip obvious spam/promos "
                    "entirely rather than including them as LOW."
    )
    skipped_count: int = Field(description="How many emails were skipped as noise")
    overall_insight: str = Field(
        description="2-3 sentences: patterns across the inbox and what deserves "
                    "attention first today. Be specific, not generic."
    )


def email_agent(state: MorningState) -> dict:
    start = time.time()
    try:
        emails = fetch_recent_emails()

        if not emails:
            return {
                "email_report": "Inbox quiet — no new emails overnight.",
                "email_items": [],
                "agent_metrics": [{
                    "agent_name": "email_agent", "status": "success",
                    "duration_seconds": round(time.time() - start, 2),
                    "items_processed": 0, "error_message": "",
                }],
            }

        email_text = "\n\n---\n\n".join(
            f"From: {e['sender']}\nSubject: {e['subject']}\nDate: {e['date']}\n"
            f"Body: {e['body'] or e['snippet']}"
            for e in emails
        )

        # .with_structured_output = LangChain guarantees the reply is a
        # valid EmailTriage object, not free text. No parsing, no regex.
        llm = get_llm(temperature=0.2).with_structured_output(EmailTriage)
        triage = llm.invoke(
            "You are an executive email assistant. Triage these emails. "
            "Read the bodies carefully — extract real deadlines, real asks, real "
            "amounts. Prioritize personal/direct emails over automated ones.\n\n"
            + email_text
        )

        # Plain-text version so Discord + compile_briefing still work
        lines = [f"📬 {triage.overall_insight}\n"]
        for e in triage.emails:
            lines.append(
                f"[{e.priority}] {e.sender} — {e.subject}\n"
                f"   → {e.recommended_action}"
                + (f" (deadline: {e.deadline})" if e.deadline != "none" else "")
            )
        lines.append(f"\n(+ {triage.skipped_count} low-value emails skipped)")

        return {
            "email_report": "\n".join(lines),
            "email_items": [e.model_dump() for e in triage.emails],
            "agent_metrics": [{
                "agent_name": "email_agent", "status": "success",
                "duration_seconds": round(time.time() - start, 2),
                "items_processed": len(emails), "error_message": "",
            }],
        }

    except Exception as exc:
        return {
            "email_report": f"⚠️ Email agent failed: {exc}",
            "email_items": [],
            "agent_metrics": [{
                "agent_name": "email_agent", "status": "error",
                "duration_seconds": round(time.time() - start, 2),
                "items_processed": 0, "error_message": str(exc),
            }],
        }