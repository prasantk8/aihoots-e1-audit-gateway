# ADR-008: Routing OpenClaw LLM calls through the E1 gateway

**Status:** Accepted
**Date:** 2026-07-22
**Episode:** E3

## Context

OpenClaw makes OpenAI-compatible HTTP calls to whatever endpoint is configured as
its backend model. The E1 gateway is also an OpenAI-compatible endpoint. Connecting
them is therefore a configuration decision, not a code change to either system.

## Decision

Configure OpenClaw's base URL and API key to point at the E1 gateway
(`http://localhost:8000/v1`) instead of the SLM directly. The gateway then
forwards to the containerized SLM as before.

```
┌──────────────┐   OpenAI API   ┌──────────────────┐   OpenAI API   ┌─────────────┐
│  OpenClaw    │ ─────────────> │  E1 Audit Gateway│ ─────────────> │ Local SLM   │
│  (agent)     │                │  audit + policy  │                │ (Ollama)    │
└──────────────┘                └──────────────────┘                └─────────────┘
                                        │
                                   audit.jsonl
                                   (all agent
                                    LLM calls
                                    logged)
```

This means:
- Every LLM call the agent makes is audited (request, policy decision, response)
- Injection attempts in agent prompts hit the policy layer before reaching the model
- The agent's tool-use decisions — which come from the model response — are logged
- Zero modifications to OpenClaw's code

## The test harness approach

For E3, rather than driving OpenClaw interactively, we build a **programmatic
test harness** that:
1. Sets OpenClaw's environment to point at the target (bare SLM or gateway)
2. Feeds it a crafted task that includes adversarial content in tool-returned data
3. Captures what the agent *decided to do* (tool calls made)
4. Scores the outcome: did the agent follow the injected instruction, or not?

This keeps the test battery reproducible and deterministic.

## Alternatives considered (and why they lost)

| Alternative | Why not |
|---|---|
| **Modify OpenClaw to add governance** | Defeats the point — we are demonstrating governance as an *external* control, not requiring agents to self-govern. External controls are more reliable because they don't depend on the agent's cooperation. |
| **Proxy at the network layer (mitmproxy)** | More brittle than a config change and harder for readers to reproduce. The config-change approach is one environment variable. |
| **Test only manually/interactively** | Not a CI gate, not reproducible, not publishable as numbers. |

## Consequences

- **Positive:** zero changes to OpenClaw; applies to any OpenAI-compatible agent
  framework; the gateway governs all LLM calls regardless of what tools the agent
  has available.
- **Negative / honest limit:** a tool call that was *already dispatched* by the
  model before the next gateway-mediated LLM call is not intercepted. Governance
  latency (the window between injected instruction and next audited call) is a real
  gap, stated in the article.

## Update: Docker Compose (supersedes local install requirement)

Rather than installing OpenClaw locally, it runs as a **third service** in the
existing `docker-compose.yml`. This is strictly better:

- One command (`docker compose up`) brings up the entire governed stack
- The network topology *enforces* the governance wire: model is on the internal
  network only, so OpenClaw physically cannot reach it without going through the
  gateway
- Reproducible for any reader — no npm, no global installs
- The compose file is the architecture diagram made executable

OpenClaw tools (shell, files, browser) are disabled in the compose environment
for the eval run — the harness tests LLM-call governance, not tool execution.
They can be re-enabled for live demos post-eval.

```yaml
openclaw:
  image: openclaw/openclaw:2026.2.26
  environment:
    OPENCLAW_OPENAI_API_BASE: "http://gateway:8000/v1"   # the governance wire
    OPENCLAW_TOOL_SHELL_ENABLED: "false"
    OPENCLAW_TOOL_FILES_ENABLED: "false"
    OPENCLAW_TOOL_BROWSER_ENABLED: "false"
  networks:
    - internal
  depends_on:
    - gateway
```
