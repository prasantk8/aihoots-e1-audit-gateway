"""AIHOOTS Audit Gateway — an OpenAI-compatible reverse proxy that audits every
interaction and enforces pre-flight policy. See docs/ADR-001, ADR-002, ADR-003.

Flow per request:
  1. Policy evaluation  -> audited "decision" event (allow/redact/block)
  2. If not blocked, forward (possibly redacted) prompt to the SLM backend
  3. Audit request + response with digests, token counts, latency
"""
from __future__ import annotations

import time
import uuid

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.gateway.audit.chain import AuditChain, digest, new_event
from src.gateway.policy.checks import Decision, evaluate
from src.gateway.config import settings

app = FastAPI(title="AIHOOTS Audit Gateway", version="0.1.0")
_chain = AuditChain(settings.audit_log_path)


def _extract_prompt(body: dict) -> str:
    """Concatenate message contents for policy + digest purposes."""
    messages = body.get("messages", [])
    return "\n".join(str(m.get("content", "")) for m in messages)


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}


@app.get("/metrics")
async def metrics() -> dict:
    """Minimal metrics surface; the stats module (ADR-003) enriches this."""
    return {"audit_log": settings.audit_log_path}


@app.post("/v1/chat/completions")
async def chat_completions(request: Request) -> JSONResponse:
    request_id = str(uuid.uuid4())
    caller = request.headers.get("x-caller-id", "anonymous")
    body = await request.json()
    model = body.get("model", settings.default_model)
    prompt = _extract_prompt(body)

    # 1. Policy decision (audited regardless of outcome).
    result = evaluate(prompt)
    _chain.append(new_event(
        request_id=request_id, caller=caller, model=model,
        event_type="decision", decision=result.decision.value,
        prompt_digest=digest(prompt), prompt_len=len(prompt),
        detail={"reasons": result.reasons},
    ))

    if result.decision == Decision.BLOCK:
        return JSONResponse(
            status_code=403,
            content={"error": "blocked by policy", "request_id": request_id,
                     "reasons": result.reasons},
        )

    # 2. Forward to the SLM backend (redacted prompt if applicable).
    forward_body = dict(body)
    if result.decision == Decision.REDACT:
        forward_body["messages"] = [{"role": "user", "content": result.text}]

    started = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=settings.upstream_timeout_s) as client:
            upstream = await client.post(
                f"{settings.upstream_base_url}/v1/chat/completions",
                json=forward_body,
            )
        latency_ms = (time.perf_counter() - started) * 1000
        data = upstream.json()
    except Exception as exc:  # upstream failure is itself an audited event
        _chain.append(new_event(
            request_id=request_id, caller=caller, model=model,
            event_type="response", decision="n/a",
            detail={"upstream_error": str(exc)},
        ))
        return JSONResponse(status_code=502,
                            content={"error": "upstream failure", "request_id": request_id})

    # 3. Audit the response.
    response_text = ""
    usage = data.get("usage", {})
    try:
        response_text = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        pass

    _chain.append(new_event(
        request_id=request_id, caller=caller, model=model,
        event_type="response", decision="n/a",
        response_digest=digest(response_text), response_len=len(response_text),
        prompt_tokens=usage.get("prompt_tokens", 0),
        completion_tokens=usage.get("completion_tokens", 0),
        latency_ms=latency_ms,
    ))

    # Surface the request id so callers can correlate with the audit log.
    if isinstance(data, dict):
        data["aihoots_request_id"] = request_id
    return JSONResponse(content=data)
