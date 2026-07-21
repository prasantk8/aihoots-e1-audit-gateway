# ADR-003: Deterministic statistical analysis for behavioural security monitoring

**Status:** Accepted
**Date:** 2026-07-20
**Episode:** E1

## Context

An audit log is a passive record. Governance also wants *detection*: is something anomalous
happening right now? The audit event stream (request rate, prompt length, block rate, latency,
token counts per caller) is a rich behavioural dataset. The question is what method to analyse
it with.

## Decision

Add a **batch statistical analysis module** that reads the audit log and computes deterministic,
explainable indicators: z-scores against a rolling baseline, EWMA drift on block-rate and
prompt-length distributions, per-caller rate outliers, and latency distribution shape checks.
No machine learning. Results feed the `/metrics` endpoint and a short analysis report.

## Alternatives considered (and why they lost)

| Alternative | Why not (for E1) |
|---|---|
| **ML anomaly detection (autoencoder, isolation forest)** | Opaque to an auditor ("the model flagged it" is not an explanation a regulator accepts), needs training data and tuning, and adds a second AI system to govern *inside* a governance tool. Deterministic stats are explainable, reproducible, and honest about their thresholds. |
| **Real-time streaming detection** | Operational complexity (stream processor, state store) far beyond E1's need. Batch analysis over the append-only log is simpler and sufficient to demonstrate the pattern. |
| **No analysis (log only)** | Leaves the "so what do I *do* with the log" question unanswered — the analysis is what turns a record into a control. |

## Why deterministic statistics (the teaching)

A large share of practical AI-security monitoring is **distribution-watching**, not neural
networks: sudden shifts in prompt length can fingerprint injection attempts; block-rate spikes
signal an attack or a broken upstream; per-caller rate outliers catch abuse; bimodal latency
can indicate a silent model swap or degradation. Boring, explainable statistics are a *feature*
in a regulated setting because every alert can be justified to a human. State this plainly: the
reader should leave understanding that they can get 80% of the value with z-scores and EWMA
before they ever need ML.

## Consequences

- **Positive:** explainable alerts, no training data, trivially reproducible, testable against
  synthetic logs with known injected anomalies (so we can publish true/false-positive rates).
- **Negative / honest limits:** deterministic thresholds miss novel attack shapes that don't
  move the tracked statistics; batch (not real-time) means detection latency equals the batch
  interval. Both are stated, not hidden.

## Metrics this module defines (glossary)

- **block_rate** — fraction of requests the policy layer blocked in a window. *Bad:* sudden
  spike (attack or upstream break) or drop to zero (control silently disabled).
- **prompt_len_z** — z-score of mean prompt length vs baseline. *Bad:* large positive excursion
  (possible injection payloads).
- **caller_rate_outlier** — per-caller request rate vs peer distribution. *Bad:* single caller
  many SDs above peers.
- **latency_p95 / bimodality** — response latency shape. *Bad:* new mode appearing (model swap,
  degradation).

## Evaluation (how we prove it works)

Generate synthetic audit logs with **injected, labelled anomalies**; run the module; report
true-positive and false-positive rates in the article. We publish the misses. Honest numbers
are the differentiator.

## Further reading

- EWMA control charts — statistical process control foundations
- NIST AI RMF `MEASURE` function — continuous monitoring guidance
- General reading on prompt-injection detection heuristics
