import time

from pydantic import BaseModel, Field

from config import get_llm
from state import MorningState
from tools.news_tools import fetch_market_news


# ---- Structured output schema ----
# CRITICAL DESIGN CHOICE: the model returns article_index, NOT a link.
# LLMs hallucinate URLs. The real link lives in our fetched data,
# and we attach it back by index in plain Python below.

class NewsPick(BaseModel):
    article_index: int = Field(
        description="The index number of the chosen article from the provided list"
    )
    headline: str = Field(
        description="The story's headline, cleaned up — no source prefixes, no ALL CAPS"
    )
    summary: str = Field(
        description="2-3 sentence summary of the story's actual content and its "
                    "market relevance. Concrete: name companies, numbers, directions."
    )
    heat: str = Field(
        description="One of: HOT (major market-moving story), NOTABLE (worth knowing), "
                    "BACKGROUND (context/slower burn)"
    )


class NewsDigest(BaseModel):
    picks: list[NewsPick] = Field(
        description="The 10 best stock-market stories, ordered most important first. "
                    "Deduplicate: if multiple outlets cover the same story, pick the "
                    "best single version. Skip clickbait and pure opinion pieces."
    )
    market_pulse: str = Field(
        description="One sentence capturing today's overall market mood/theme"
    )


def news_agent(state: MorningState) -> dict:
    start = time.time()
    try:
        articles = fetch_market_news()

        if not articles:
            return {
                "news_report": "No market news retrieved — feeds may be down.",
                "news_items": [],
                "agent_metrics": [{
                    "agent_name": "news_agent", "status": "success",
                    "duration_seconds": round(time.time() - start, 2),
                    "items_processed": 0, "error_message": "",
                }],
            }

        # Number every article so the model can reference them by index
        numbered = "\n\n".join(
            f"[{i}] ({a['source']}) {a['title']}\n{a['summary']}"
            for i, a in enumerate(articles)
        )

        llm = get_llm(temperature=0.3).with_structured_output(NewsDigest)
        digest = llm.invoke(
            "You are a sharp financial news curator building a morning stock-market "
            "digest. From the numbered articles below, select the 10 most "
            "market-relevant stories. This is informational only — do not give "
            "investment advice or recommend trades.\n\n" + numbered
        )

        # ---- Attach REAL links back by index (code, not LLM) ----
        news_items = []
        for pick in digest.picks:
            if 0 <= pick.article_index < len(articles):
                src = articles[pick.article_index]
                news_items.append({
                    "headline": pick.headline,
                    "summary": pick.summary,
                    "heat": pick.heat,
                    "link": src["link"],          # real URL from RSS
                    "source": src["source"],
                    "published": src["published"],
                })

        # Plain-text fallback for Discord / compiled briefing
        lines = [f"📊 Market pulse: {digest.market_pulse}\n"]
        for n in news_items:
            lines.append(f"[{n['heat']}] {n['headline']}\n   {n['summary']}\n   {n['link']}")

        return {
            "news_report": "\n".join(lines),
            "news_items": news_items,
            "agent_metrics": [{
                "agent_name": "news_agent", "status": "success",
                "duration_seconds": round(time.time() - start, 2),
                "items_processed": len(articles), "error_message": "",
            }],
        }

    except Exception as exc:
        return {
            "news_report": f"⚠️ News agent failed: {exc}",
            "news_items": [],
            "agent_metrics": [{
                "agent_name": "news_agent", "status": "error",
                "duration_seconds": round(time.time() - start, 2),
                "items_processed": 0, "error_message": str(exc),
            }],
        }