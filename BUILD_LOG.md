# BUILD LOG (private until publish)

Rough notes as they happen — decisions, dead-ends, surprises. This is what makes
the eventual article a real engineering story instead of a sanitized tutorial.

## Day 1 — 2026-07-20
- Scaffolded repo: gateway (proxy + policy + audit), verifier, stats stub, tests, CI, compose.
- ADR-001/002/003 written first, before code — decisions drove the structure, not the reverse.
- Hash-chain design choice: store DIGESTS not payloads in the chain (keeps it small, less
  sensitive-data sprawl). Full payloads would go to a separate access-controlled store in prod.
- Gotcha to remember for the article: `record_hash` must be excluded from its own hash input,
  and serialization must be deterministic (sort_keys) or verification fails across machines.
- Tamper suite (14 tests) green: catches field-mutation at every position + delete + reorder.
- Live demo confirmed: mutate 1 record -> verifier names exactly that record, exits 1. Screenshot this.
- OPEN: decide Ollama vs llama.cpp server for the pinned model image (compose currently Ollama).
- OPEN: stats module (Day 6) — z-score + EWMA over the log; test against synthetic labelled anomalies.

## Day 2 — 2026-07-20
- Added stubbed-upstream integration tests for the gateway (test_gateway_integration.py):
  allow / block / redact paths + audit records. Decision: CI uses a FAKE upstream (fast,
  deterministic); the real containerized SLM is exercised locally in REBUILD, not in CI.
  -> becomes ADR-004.
- REAL BUG caught by the new block test: the injection blocklist regex
  `ignore (all|previous) instructions` only allowed ONE of all/previous, so the most common
  real payload "ignore ALL PREVIOUS instructions" slipped through as ALLOW. This is exactly
  the miss the clinical standard exists to catch. Fixed regex to handle all/previous/prior/
  above variants + a `disregard ...` pattern. Verified: blocks variants, benign text still allows.
  -> This is a Field Note for the article: your guardrail is only as good as your adversarial tests.
- Coverage now 90% (was failing 80% before integration tests). main.py 89%, checks.py 100%.
- Known warning: Starlette TestClient + httpx deprecation notice. Non-blocking; note for later.
- NEXT (Day 2 finish): git init, signed commit, push to PRIVATE GitHub repo, watch CI go green,
  then Cloudflare Pages for docs.
