# AIHOOTS E1 — LLM Audit Gateway

An OpenAI-compatible proxy that produces a **tamper-evident, independently
verifiable audit trail** of every LLM request, response, and policy decision —
the control every AI regulation implies and almost nobody ships as working code.

Part of [AIHOOTS](https://aihoots.com): AI governance, built end-to-end, in the open.

## Quickstart
```bash
docker compose up            # gateway + containerized SLM
# point any OpenAI client at http://localhost:8000/v1
python -m src.verifier.cli /data/audit.jsonl   # prove the chain is intact
```

## What's inside
- **Gateway** (`src/gateway`) — OpenAI-compatible proxy, policy layer, audit engine
- **Verifier** (`src/verifier`) — independent tamper detector (`audit-verify`)
- **Stats** (`src/stats`) — deterministic behavioural security analysis (ADR-003)
- **Docs** (`docs/`) — architecture decision records with the *why*, alternatives, and trade-offs

## Design decisions
See `docs/ADR-001`..`ADR-003`. Every choice records the alternatives considered and why they lost.

## Tests
```bash
pip install -r requirements-dev.txt
pytest --cov=src        # 18 tests, ~90% coverage
```
Includes tamper-detection across every record position, plus gateway allow/redact/block
integration tests against a stubbed upstream (see `docs/ADR-004`).

## Reproduce it yourself
See `REBUILD.md` — verified on a clean machine.

*Views and projects here are my own and unrelated to any employer's systems.*
