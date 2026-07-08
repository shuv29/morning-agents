import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

MODEL_NAME = "gemini-2.5-flash"


def get_llm(temperature: float = 0.3) -> ChatGoogleGenerativeAI:
    """Every agent gets its LLM here. Swap providers in this one spot."""
    return ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        temperature=temperature,
        google_api_key=os.environ["GOOGLE_API_KEY"],
    )


GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
]
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"

STOCK_NEWS_FEEDS = [
    "https://feeds.content.dowjones.io/public/rss/mw_topstories",
    "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "https://finance.yahoo.com/news/rssindex",
]
MAX_ARTICLES_PER_FEED = 12
EMAIL_LOOKBACK_HOURS = 16
MAX_EMAILS_TO_ANALYZE = 25
CALENDAR_LOOKAHEAD_HOURS = 24