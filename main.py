import os

import requests
from dotenv import load_dotenv

from graph import build_graph

load_dotenv()


def send_to_discord(text: str) -> None:
    url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not url:
        return
    for i in range(0, len(text), 1900):
        requests.post(url, json={"content": text[i:i + 1900]}, timeout=15)


def main() -> None:
    app = build_graph()
    final_state = app.invoke({"agent_metrics": []})
    print(final_state["final_briefing"])
    send_to_discord(final_state["final_briefing"])


if __name__ == "__main__":
    main()