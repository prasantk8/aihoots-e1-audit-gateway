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

## Day 6 — 2026-07-21 (E2 begins)
- Started Episode 2: Guardrail & Injection Eval Harness. Decision (Prashant): score BOTH
  raw model and gated gateway, publish the before/after delta. Same repo, new src/eval/ module.
- ADR-005 (standing eval harness, why-not-alternatives) + ADR-006 (layered deterministic
  scoring: gate-block -> refusal -> success-marker; explicit "ambiguous" bucket, no LLM-judge).
- Versioned attack corpus v1 (src/eval/corpus/attacks-v1.json): 9 attacks across
  injection/jailbreak/leakage/role-confusion/encoding + 2 benign controls, each with a concrete
  success_marker.
- Scorer (src/eval/scorer.py): run_eval + score_case + delta_report (raw vs gated headline).
- audit-eval CLI (src/eval/cli.py): runs corpus vs --raw and/or --gated live endpoints, prints
  per-category catch-rates + delta, exits 1 below threshold (CI gate).
- Tests: 12 eval tests incl. full raw-vs-gated end-to-end with fake targets + CLI gate logic.
- Full suite now 41 tests, 87% coverage, gate green.
- NEXT: run audit-eval against the LIVE stack (real qwen raw vs gated) to capture the REAL
  delta numbers for the article; add eval as a CI job; write + publish the E2 article.

## Day 7 — 2026-07-22 (E3 begins)
- Started Episode 3: Governing an autonomous agent (OpenClaw). Clean-provenance rule confirmed
  in ADR-007: public security literature + fresh home install only.
- Research: OpenClaw has 470 published security advisories, 200k+ GitHub stars, live CVEs
  (CVE-2026-24763 command injection, CVE-2026-25253 CSRF→RCE, CVE-2026-26329 path traversal,
  CVE-2026-30741 prompt-injection→code execution). MITRE ATLAS-documented attack patterns.
- ADR-007 (E3 scope: why agent governance is different, attack categories, honest limits).
- ADR-008 (routing OpenClaw calls through E1 gateway via config-only change — zero code mods).
- E3 agent attack corpus v1 (src/e3_agent/corpus/agent-attacks-v1.json): 8 attacks across
  indirect_injection, tool_output_poison, memory_injection, exfiltration + 2 controls.
- Agent harness (src/e3_agent/harness.py): run_agent_eval, make_agent_caller, extended
  exfil file detection, CLI with --raw/--gated/--threshold.
- 12 E3 tests including full fake-target end-to-end + exfil file detection.
- BUG: E3 corpus used "task" key; scorer expected "prompt" -> KeyError. Fixed by
  renaming corpus key to "prompt" for interface consistency. Worth a sentence in the article.
- Full suite: 53 tests, 80.27% coverage, gate green.
- NEXT: install OpenClaw locally, configure it to point at the E1 gateway (ADR-008),
  run the harness against the REAL stack, capture before/after numbers, write the E3 article.
