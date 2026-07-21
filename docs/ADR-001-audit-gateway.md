# ADR-001: An LLM Audit Gateway with a tamper-evident event log

**Status:** Accepted
**Date:** 2026-07-20
**Episode:** E1

## Context

Regulated organisations adopting LLMs face a recurring, unglamorous requirement that
appears in nearly every AI governance regime (EU AI Act record-keeping obligations,
NIST AI RMF `MANAGE`/`MEASURE` functions, most central-bank AI guidance): **you must be
able to show, after the fact, what an AI system was asked, what it answered, and what
controls acted on that interaction.**

In practice this is usually met with ordinary application logging. Ordinary logs have a
fatal weakness for audit purposes: whoever controls the system can rewrite them. An audit
trail that the operator can silently alter is not evidence — it is a diary.

We need a control that (a) sits transparently in front of any LLM, (b) records every
interaction, and (c) makes undetected tampering with historical records infeasible.

## Decision

Build a **gateway** — a reverse proxy that speaks the OpenAI-compatible
`/v1/chat/completions` API — through which all model traffic flows. The gateway writes an
**append-only, hash-chained event log**: each record stores the SHA-256 digest of the
previous record, so altering any historical record breaks the chain from that point on and
is detectable by an independent verifier.

## Alternatives considered (and why they lost)

| Alternative | Why not (for E1) |
|---|---|
| **Library/SDK the app calls** | Requires modifying every caller; a bypassed library logs nothing. A gateway governs traffic regardless of caller cooperation. |
| **Sidecar that tails app logs** | Still trusts logs the app already controls; adds a moving part without closing the tampering gap. |
| **Full blockchain / distributed ledger** | Enormous operational weight for a single-writer audit need. A hash chain gives tamper-*evidence* (detect changes) without consensus machinery. We are not trying to prevent writes across mutually distrusting parties — we are proving a single operator's log wasn't edited. |
| **Write-once cloud storage (object lock)** | A strong complement, not a substitute — it protects the file, not the *internal consistency* of records. Hash-chaining is portable and verifiable offline; object-lock is vendor-specific. We note this as a production hardening step, not the core mechanism. |
| **Signed logs (per-record digital signatures)** | Excellent and compatible — but key management is a whole subject. Hash-chaining gives tamper-evidence with zero key infrastructure, which keeps E1 reproducible by any reader. Signing is a documented upgrade path. |

## Consequences

- **Positive:** caller-agnostic; reproducible with no external services; tamper-evidence is
  demonstrable on camera (mutate a byte, run the verifier, watch it catch the exact record);
  the log doubles as a dataset for later statistical security analysis (see ADR-003).
- **Negative / honest limits:** a hash chain proves *internal consistency*, not *authenticity*
  of authorship (that needs signing) and not *availability* (an operator could delete the
  whole file — mitigated in production by append-only storage + off-box replication). We
  state these limits plainly rather than overselling. This honesty is itself a deliverable.

## Guidelines (if you adopt this pattern)

1. The gateway must be the **only** path to the model in your environment, or the audit is
   theatre. Enforce at the network layer.
2. Log **decisions**, not just traffic: every allow/redact/block is an event.
3. Store **digests** of prompts/responses in the chain, with full payloads in a separate,
   access-controlled store if you need them — keeps the chain small and reduces sensitive-data
   sprawl in the audit record.
4. Verify the chain on a schedule, not just on demand. An unchecked verifier proves nothing.

## Further reading

- NIST AI Risk Management Framework (AI RMF 1.0) — `MEASURE` and `MANAGE` functions
- EU AI Act — record-keeping and logging obligations for high-risk systems
- RFC 6962 (Certificate Transparency) — hash-chained/Merkle audit logs in the wild
- "Tamper-evident logging" — Schneier & Kelsey, secure audit log foundations
