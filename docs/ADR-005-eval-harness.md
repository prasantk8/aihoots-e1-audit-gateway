# ADR-005: A standing adversarial eval harness (Episode 2)

**Status:** Accepted
**Date:** 2026-07-21
**Episode:** E2

## Context

Episode 1 built a gateway whose guardrails block injection and redact PII. But "we
have guardrails" is a claim, not evidence. Guardrails silently weaken all the time:
a model swap, a prompt tweak, a refactor of a regex (E1 already had one such bug).
The question E2 answers: **how good are the guardrails, measured, and does every
change keep them that good?**

## Decision

Build a **standing adversarial evaluation harness**: a versioned corpus of labelled
attack prompts (injection, jailbreak, leakage, role-confusion, encoding tricks) and
a scoring engine that fires them at a target and reports catch-rate, precision, and
recall per category — including the misses.

Crucially, it scores **two targets and publishes the delta**:
- the **raw SLM** directly (no protection), and
- the **same SLM behind the E1 gateway** (guardrails on).

The before/after gap is the headline number: it quantifies exactly what the gateway
buys you. The harness runs locally and as a **CI gate** — a change that weakens
guardrails past a threshold fails the build.

## Alternatives considered (and why they lost)

| Alternative | Why not |
|---|---|
| **Manual red-teaming** | Valuable but not repeatable, not a CI gate, and not a published number. A human red-teams once; a harness red-teams every commit. |
| **One-off eval at release** | Catches nothing between releases — exactly when guardrails silently drift. |
| **Buy a vendor eval tool** | Opaque scoring, no reproducibility for readers, and it wouldn't teach anything. The point here is a transparent, rebuildable method. |
| **Score only the gated path** | Misses the whole story. Without the raw-model baseline there's no delta, and the delta is what proves the gateway's value. |

## Consequences

- **Positive:** a repeatable, published measure of guardrail strength; a CI gate that
  prevents silent regressions; the raw-vs-gated delta as a single persuasive number;
  a corpus that grows as new attack patterns appear.
- **Negative / honest limits:** the corpus only tests attacks we've thought of — a
  passing score means "resists known attacks," not "unbreakable." Scoring whether an
  attack "succeeded" is itself a judgement (see the scoring ADR-006). Both stated openly.

## Guidelines (if you adopt this)

1. Version the corpus. An eval number is meaningless without the corpus version it
   was measured against.
2. Always keep a raw-model baseline in the report — the delta is the point.
3. Publish misses per category, not just an aggregate score. Aggregates hide holes.
4. Gate on a threshold you can defend, and record why that threshold.

## Further reading

- OWASP Top 10 for LLM Applications (LLM01: Prompt Injection)
- NIST AI RMF — MEASURE function (test & evaluation)
- General literature on prompt-injection taxonomies and jailbreak patterns
