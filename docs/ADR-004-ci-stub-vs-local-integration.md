# ADR-004: Stubbed upstream in CI, real SLM locally

**Status:** Accepted
**Date:** 2026-07-20
**Episode:** E1

## Context

The gateway's request flow must be tested end to end. But running the real
containerized SLM (ADR-002) inside CI means every pipeline run pulls a multi-GB
model and does CPU inference — slow, flaky, and expensive on shared runners.

## Decision

Two testing tiers:
- **CI tier (fast, deterministic):** the upstream model is *stubbed* — a fake
  OpenAI-compatible response is injected by monkeypatching the gateway's HTTP client.
  This exercises all gateway logic (policy decisions, audit writes, request/response
  handling, error paths) without any real inference.
- **Local integration tier (real):** during REBUILD verification the full
  `docker compose up` stack runs with the actual SLM, and a smoke test sends real
  traffic. This proves the compose wiring and real model path work.

## Alternatives considered (and why they lost)

| Alternative | Why not |
|---|---|
| **Real SLM in CI** | Slow (model pull + CPU inference), flaky, costly. Turns a 30-second pipeline into many minutes and introduces non-determinism into gateway logic tests. |
| **No integration test at all** | Leaves `main.py` untested; coverage and confidence both suffer. |
| **Mock at the policy/audit layer only** | Doesn't exercise the actual HTTP proxy path in `main.py`. |

## Consequences

- **Positive:** fast, deterministic CI that still covers the gateway end to end;
  honest real-model verification kept where it belongs (local, pre-publish).
- **Negative / honest limit:** CI does not catch issues that only appear with a real
  model (e.g. response-shape surprises). Mitigated by the local integration tier and
  by the gateway treating upstream output defensively.

## Guidelines

1. Keep the stub's response shape faithful to the real API contract, or the test lies.
2. Never let the stub tier be the *only* tier — a real run must happen before publish.
