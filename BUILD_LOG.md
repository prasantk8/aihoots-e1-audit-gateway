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

## Day 3 — 2026-07-20 (prepared)
- Pushed to private GitHub: git@github.com:prasantk8/aihoots-e1-audit-gateway.git
- Wrote REBUILD.md: the reproducibility contract. Two paths — full Docker stack (real SLM) and
  tests-only. Includes the self-serve tamper demo so a stranger PROVES governance themselves.
- Added scripts/smoke_test.sh: local integration tier (ADR-004) — hits the live stack with a
  REAL model and asserts allow/block/redact end to end. This is what earns the "works with a
  real SLM" claim vs the stubbed CI.
- Verified compose wiring matches REBUILD (model:11434 internal-only, gateway:8000 sole surface).
- TODO before publish: actually EXECUTE REBUILD.md on a clean machine/container as a stranger,
  run smoke_test.sh against the live stack, fix anything that breaks, and paste the CI-green
  screenshot + tamper-demo screenshot for the article.

## Day 4 — 2026-07-21
- Wrote ARCHITECTURE.md (system-design narrative + mermaid diagram + honest limits).
- Wrote SECURITY.md (threat model table with explicit "not defended, by design for E1" rows).
- Built the Cloudflare Pages docs site (aihoots-site/): single static page, no build step.
  Design theme = "verification instrument": cool near-black, signal-green for INTACT, mono type,
  and the SIGNATURE element is an interactive hash-chain — click a record to "tamper", the
  verifier line flips to TAMPERING DETECTED at that seq. Added _headers for CSP + hardening.
- Deferred: deploy to Cloudflare Pages (Prashant, local) + article draft next.

## Day 5 — 2026-07-21
- Built src/stats/analyzer.py: 4 deterministic detectors (block-rate spike, prompt-len z,
  caller-rate outlier, latency bimodality) + summarize() for /metrics. No ML, all thresholds explicit.
- Built tests/test_stats.py: synthetic labelled anomalies + honest TP/FP report table.
- TWO REAL BUGS caught by the eval harness (both now Field Notes in article-2):
  1) Zero-variance baseline broke the z-score (std=0 -> detector went blind on clean data).
  2) Outlier masking — one heavy caller inflated std and hid its own z below threshold.
  Fix for both: robust statistics (median + MAD; compare caller vs PEERS not the whole pool).
  Also fixed a latency FALSE POSITIVE: gap-vs-median-microgap flagged unimodal noise;
  changed to gap-vs-total-spread + min absolute ms.
- Added src/stats/cli.py (audit-stats, exit 1 on findings); wired summarize() into /metrics.
- Full suite: 29 tests pass, coverage 89%.
- Wrote docs/article-2-stats.md (the 2nd post: "your audit log is a security dataset").
- NEXT (Prashant, local): commit+push stats module & 2nd article, watch CI green, then publish
  article-2 on aihoots.com + LinkedIn. E1 then fully complete per vision-doc Definition of Done.
