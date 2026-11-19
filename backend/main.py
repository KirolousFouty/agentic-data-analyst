from __future__ import annotations

import csv
import io
import time
import uuid
from collections import defaultdict
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from pydantic import BaseModel, Field

from agents.context import BUSINESS_CONTEXT
from agents.workflow import build_graph

app = FastAPI(title="Enterprise AI Data Analyst Agent", version="0.1.0")
REQUESTS = Counter("analyst_requests_total", "Analyst requests", ["outcome"])
LATENCY = Histogram("analyst_response_seconds", "Analyst response latency")
history: dict[str, list[dict[str, Any]]] = defaultdict(list)
graph = build_graph()

class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    conversation_id: str | None = None

class AskResponse(BaseModel):
    conversation_id: str
    answer: str
    sql: str | None = None
    columns: list[str] = []
    rows: list[dict[str, Any]] = []
    chart: dict[str, Any] | None = None
    error: str | None = None

def jsonable(value: Any) -> Any:
    if isinstance(value, (datetime,)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value

@app.get("/health")
def health() -> dict[str, str]: return {"status": "ok"}

@app.get("/metrics")
def metrics() -> PlainTextResponse: return PlainTextResponse(generate_latest().decode(), media_type=CONTENT_TYPE_LATEST)

@app.get("/metrics/definitions")
def definitions() -> dict[str, str]: return {"definitions": BUSINESS_CONTEXT}

@app.get("/conversations/{conversation_id}")
def conversation_history(conversation_id: str) -> list[dict[str, Any]]: return history[conversation_id]

@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    cid = request.conversation_id or str(uuid.uuid4())
    began = time.perf_counter()
    try:
        state = graph.invoke({"question": request.question, "conversation": history[cid]})
        result = state.get("result")
        response = AskResponse(conversation_id=cid, answer=state.get("answer", state.get("error", "No response.")), sql=state.get("sql"), columns=result.columns if result else [], rows=[{k: jsonable(v) for k,v in r.items()} for r in (result.rows if result else [])], chart=state.get("chart"), error=state.get("error"))
        history[cid].append({"at": datetime.now(UTC).isoformat(), "question": request.question, "answer": response.answer, "sql": response.sql})
        REQUESTS.labels("error" if response.error else "success").inc()
        return response
    except httpx.HTTPError:
        REQUESTS.labels("model_unavailable").inc()
        return AskResponse(
            conversation_id=cid,
            answer=("The local Ollama model is not available yet. It may still be downloading; "
                    "please retry in a moment."),
            error="local_model_unavailable",
        )
    finally:
        LATENCY.observe(time.perf_counter() - began)

@app.get("/conversations/{conversation_id}/latest.csv")
def latest_csv(conversation_id: str) -> PlainTextResponse:
    entries = history.get(conversation_id, [])
    if not entries or not entries[-1].get("sql"):
        raise HTTPException(404, "No executed result available.")
    from backend.sql_security import SecureQueryExecutor
    result = SecureQueryExecutor().execute(entries[-1]["sql"])
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=result.columns)
    writer.writeheader()
    writer.writerows([{k: jsonable(v) for k, v in row.items()} for row in result.rows])
    return PlainTextResponse(stream.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=analysis.csv"})
