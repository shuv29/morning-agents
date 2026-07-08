"""
api.py — Web API wrapping the LangGraph pipeline.
Run with:  uvicorn api:app --reload --port 8000

The interesting endpoint is /api/run/stream: it uses Server-Sent Events
(SSE) to push each agent's result to the browser THE MOMENT it finishes.
This is the same .stream() vs .invoke() idea from Streamlit, now over HTTP.
"""

import json
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from graph import build_graph

app = FastAPI(title="Morning Agents API")

# CORS: the browser blocks requests between different "origins"
# (localhost:5173 → localhost:8000 counts as different). This
# middleware tells the browser our React dev server is allowed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    """Quick check that the server is alive."""
    return {"status": "ok"}


@app.get("/api/history")
def history():
    """Return past run metrics for the dashboard's history view."""
    if not os.path.exists("metrics_history.jsonl"):
        return []
    with open("metrics_history.jsonl") as f:
        return [json.loads(line) for line in f.readlines()[-14:]]


@app.get("/api/run/stream")
def run_stream():
    """
    SSE endpoint. Each time a LangGraph node finishes, we yield one
    event. The browser's EventSource API receives them live.
    SSE format is just text: lines starting with "data: ", blank line ends an event.
    """
    def event_generator():
        graph = build_graph()
        for chunk in graph.stream({"agent_metrics": []}):
            for node_name, update in chunk.items():
                payload = {"node": node_name, "update": update}
                yield f"data: {json.dumps(payload)}\n\n"
        yield 'data: {"node": "__done__", "update": {}}\n\n'

    return StreamingResponse(event_generator(), media_type="text/event-stream")