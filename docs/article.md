# Building a tamper-evident LLM audit gateway — end to end, in the open

*Episode 01 of AIHOOTS: AI governance built as working systems, not slideware.*

---

Every AI regulation worth reading asks for the same unglamorous thing. The EU AI
Act wants record-keeping. NIST's AI Risk Management Framework wants you to
*measure* and *manage*. Central-bank AI guidance wants an audit trail. Strip away
the legal language and the requirement is: **prove, after the fact, what your AI
system was asked, what it answered, and what controls acted on that interaction.**

Most teams meet this with ordinary application logging. And ordinary logging has a
quiet, fatal weakness for audit purposes: whoever runs the system can edit the
logs. An audit trail the operator can silently rewrite isn't evidence — it's a
diary.

So for the first episode of this build-in-public series, I built the control that
actually closes that gap: an **LLM audit gateway** that records every interaction
in a *tamper-evident* log, plus an independent verifier that proves the record
hasn't been altered. It runs end to end against a local model, ships with a full
security pipeline, and anyone can rebuild it from the repo.

Here's how it works, why I made the choices I made, and the bug my own tests caught
along the way.

## The shape of the system

The gateway is a reverse proxy that speaks the OpenAI-compatible
`/v1/chat/completions` API. Any client that already talks to an LLM points at the
gateway instead — no code changes — and the gateway becomes the single path to the
model. That "single path" property is the whole game: governance you can bypass is
theatre.

Every request flows through three steps. First, a **policy decision** — oversized
or injection-shaped prompts are blocked, PII is redacted, everything else is
allowed — and the decision itself is written to the audit log. Second, allowed
traffic is **forwarded** to a small language model running in a container on an
internal-only network. Third, the **response is audited** with digests, token
counts, and latency, and the caller gets back a request ID that links to the
audit records.

## The core: a hash-chained log

The audit log is append-only JSON lines. The trick that makes it tamper-evident is
simple and old: each record stores the SHA-256 hash of the record before it — a
hash chain. Change any historical record and its hash changes, which breaks every
link after it. An independent verifier walks the file and names the first broken
record.

Two design decisions here were deliberate, and I wrote both up as architecture
decision records in the repo:

**Store digests, not payloads, in the chain.** The chain holds a fingerprint of
each prompt and response, not the text itself. It keeps the audit record small and
avoids copying sensitive content into a second place. If you need the full text,
it lives in a separate, access-controlled store.

**A hash chain, not a blockchain or digital signatures — for now.** I'm proving a
single operator didn't edit their own log. That needs tamper-*evidence*, not
distributed consensus. A hash chain gives that with zero key management, which
keeps the whole thing reproducible by any reader. Per-record signing (for
authorship) and write-once storage (for availability) are real upgrades — and
they're documented as such, not pretended to be already present.

## What it honestly does not do

A governance tool that oversells its coverage is worse than one that states its
limits, so the repo is explicit. The hash chain proves *internal consistency*. It
does not prove *who* wrote a record (that needs signing), and it does not stop an
operator from deleting the entire file (that needs append-only storage plus
off-box replication). The policy rules are deliberately simple — the point is the
audited-decision *pattern*, not a state-of-the-art classifier.

## The bug my tests caught

This is the part I want to keep in, because build-in-public that only shows the
wins isn't worth much.

The gateway blocks obvious prompt-injection patterns. My first blocklist rule
matched "ignore all instructions" and "ignore previous instructions" — but the
regex only allowed *one* of those words. So the single most common real-world
jailbreak phrasing, **"ignore all previous instructions,"** sailed straight
through as *allowed*.

I didn't catch this by reading the code. I caught it because I'd written an
integration test that sends that exact phrase and asserts a 403 — and the test
failed. A guardrail that misses the textbook attack is the kind of thing that
looks fine in a demo and fails in production. The fix was a better regex; the
lesson was the test. Your guardrail is only ever as good as the adversarial cases
you actually test it against.

## Governed AI, built with governed engineering

The second story running through this episode is the pipeline. Every push runs
linting, the test suite with a coverage floor, static analysis, a dependency
audit, and a secret scan; every build produces a software bill of materials. The
model runs as a non-root container reachable only by the gateway. None of that is
incidental — if you're going to publish a governance tool, the engineering around
it should meet the same bar the tool demands.

## Rebuild it yourself

The repo includes a step-by-step rebuild guide verified on a clean machine: bring
up the stack, pull a small model, send a request through the gateway, watch it get
audited, then tamper with one record by hand and watch the verifier catch exactly
that record. If you can't reproduce it, that's a bug worth an issue — reproducibility
is a feature here, not an afterthought.

Code and full write-up: **github.com/prasantk8/aihoots-e1-audit-gateway**

Next episode: turning an LLM endpoint's guardrails into an automated evaluation
harness that runs as a CI gate — with honest numbers on what it catches and what
it misses.

---

*AIHOOTS is a build-in-public lab for enterprise AI governance. Views and projects
here are my own and unrelated to any employer's systems.*
