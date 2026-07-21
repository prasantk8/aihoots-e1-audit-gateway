# ADR-002: A containerized small language model as the E1 backend

**Status:** Accepted
**Date:** 2026-07-20
**Episode:** E1

## Context

The gateway needs a model behind it. The choice of *how* the model runs is not incidental —
it directly determines whether a stranger can reproduce this system, which is a stated
first principle of the project ("if it can't be retried by a reader, it isn't done").

## Decision

Run a **small language model (SLM)** — a quantized open-weights model in the ~3B parameter
class — served over an OpenAI-compatible HTTP API **inside a Docker container**, orchestrated
with the gateway via a single `docker compose up`.

Reference model: a quantized instruct model (e.g. Qwen2.5-3B-Instruct or Phi-4-mini) served
by llama.cpp's OpenAI-compatible server or Ollama. The gateway is model-agnostic; the compose
file pins one so results are reproducible.

## Alternatives considered (and why they lost)

| Alternative | Why not (for E1) |
|---|---|
| **Desktop GUI runner (LM Studio, etc.)** | Superb for personal experimentation, but it's a GUI app: a reader can't script it, and CI cannot drive it headlessly. Kills reproducibility and automated testing — the two things E1 exists to demonstrate. |
| **Hosted API (OpenAI/Anthropic/etc.)** | Introduces cost, API keys, network dependency, and non-determinism into every reader's rebuild. Also couples a *governance demo* to a specific vendor — the wrong signal. |
| **Large local model (30B+)** | Needs hardware most readers lack. E1's subject is the *gateway and its controls*, not model quality — a 3B model is more than enough to exercise every code path and keeps the barrier to reproduction low. |
| **No model / stub responder** | Tempting for speed, but integration tests that never touch a real model produce false confidence. A containerized SLM lets CI run true end-to-end tests cheaply. |

## Why an SLM specifically (the teaching)

For a *governance* demonstration, model intelligence is almost irrelevant — what matters is
that requests and responses flow through real inference so the controls are exercised
authentically. An SLM is the right tool because it is: cheap enough to run in CI, small enough
for any reader's laptop, open enough to inspect, and fast enough for a tight build loop. This
reflects a broader field truth worth stating: **a large fraction of enterprise LLM value comes
from constrained, well-governed small models on narrow tasks, not from the biggest model
available.** The gateway is where the value and the risk actually live.

## Consequences

- **Positive:** one-command reproducible stack; CI runs real integration tests; zero API cost;
  no vendor coupling; portable across any reader's machine.
- **Negative / honest limits:** container inference on CPU is slower than GPU/hosted; we set
  modest timeouts and small max-token limits in tests. Model quality is deliberately not a
  concern here and should not be judged from this episode.

## Guidelines (if you adopt this pattern)

1. Pin the model **and** the runtime version in your compose file — "latest" destroys
   reproducibility.
2. Expose the model **only** to the gateway on an internal network, never to the host, so the
   gateway genuinely is the sole path.
3. Keep a stub/mock backend available for unit tests; use the real container only for the
   integration tier — fast inner loop, honest outer loop.

## Further reading

- llama.cpp server — OpenAI-compatible endpoint documentation
- Ollama — model library and Docker usage
- The general literature on quantization (GGUF, 4-bit) and small-model capability trends
