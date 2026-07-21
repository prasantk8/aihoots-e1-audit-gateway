# Your audit log is a security dataset — catch attacks with boring statistics

*Episode 01, part 2. The [audit gateway](https://github.com/prasantk8/aihoots-e1-audit-gateway)
records every LLM interaction. Here's how to make that record *detect* things —
without a single neural network.*

---

In part one I built a tamper-evident audit gateway: every LLM request, response,
and policy decision written to a hash-chained log. That log is passive, though.
It answers "what happened?" after someone asks. The obvious next question is "is
something happening *right now*?" — and the answer is sitting in the log already,
if you're willing to do some statistics.

The reflex in 2026 is to reach for a model. Train an anomaly detector, embed the
prompts, cluster the behaviour. I deliberately didn't. In a regulated setting,
**an alert you can't explain to a human is close to useless** — "the model flagged
it" is not something you say to an auditor. So this module uses nothing but
deterministic statistics: z-scores, medians, and gap analysis. It's boring on
purpose, and boring is the feature.

## Four things worth watching

The audit stream carries four signals that catch a surprising range of real
problems:

**Block-rate spikes.** If the fraction of requests your policy blocks suddenly
triples, either you're under attack or a control broke. Both are worth a page.

**Prompt-length drift.** Injection and jailbreak payloads tend to be long — walls
of text trying to smuggle instructions past the guardrails. A sharp rise in mean
prompt length is a cheap early fingerprint.

**Per-caller volume outliers.** One caller suddenly doing 10x the traffic of every
peer is the oldest abuse signal there is.

**Bimodal latency.** If your response times split into two clusters, something
changed underneath — a model was swapped, a cache broke, something is degrading.

None of these needs training data. All of them can be justified in one sentence to
a non-technical stakeholder. That's the whole pitch.

## Where naive statistics quietly fail

Here's the part I want to keep honest, because I hit both of these while building
it — and my evaluation harness caught both before they'd have shipped.

**Zero-variance baselines break z-scores.** My first prompt-length detector
computed a standard z-score against the baseline window. In testing, the baseline
was perfectly steady — every prompt the same length — so the standard deviation was
zero, and dividing by it meant the detector silently returned "nothing wrong" even
as prompt length exploded. A detector that goes blind exactly when the data is
clean is worse than no detector.

**The outlier-masking problem.** My per-caller detector compared each caller to the
mean and standard deviation of *all* callers. But a single abusive caller with
10x the volume inflates the standard deviation so much that its own z-score drops
below the alarm threshold. The outlier hides inside the noise it creates. This is a
classic, well-documented trap, and I walked right into it.

The fix for both is the same: **robust statistics.** Swap mean and standard
deviation for median and MAD (median absolute deviation), and compare each caller
to its *peers* rather than to a pool that includes itself. Robust measures don't
get dragged around by the very outliers you're trying to find.

## Proving it, with numbers

Claims are cheap. The module ships with an evaluation harness that builds synthetic
audit logs with *known, labelled* anomalies — a block-rate spike here, a
prompt-length explosion there, a clean stream as a control — runs each detector
across dozens of trials, and reports true-positive and false-positive rates. On the
synthetic set, the detectors catch the injected anomalies reliably while staying
quiet on benign traffic. The exact table is in the repo and regenerates when you
run the tests, so you can check my work rather than trust it.

That's the standard for everything here: a security control isn't done when it
works on a demo, it's done when you can state how often it's right *and how often
it's wrong.*

## Run it yourself

```bash
python -m src.stats.cli /data/audit.jsonl
```

Point it at a log from the running gateway and it prints the metrics summary plus
any findings, or exits non-zero if something's anomalous — so you can wire it into
a scheduled job. It also feeds the gateway's `/metrics` endpoint.

Code: **github.com/prasantk8/aihoots-e1-audit-gateway**

Next episode: turning guardrails into an automated evaluation harness that runs as
a CI gate — with, once again, honest numbers on what it catches and what slips
through.

---

*AIHOOTS is a build-in-public lab for enterprise AI governance. Views and projects
here are my own and unrelated to any employer's systems.*
