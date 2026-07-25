# ADR-007: Governing an autonomous agent (Episode 3)

**Status:** Accepted
**Date:** 2026-07-22
**Episode:** E3

## Context

Episodes 1 and 2 governed *model inference*: an LLM answering questions through
a proxy. Episode 3 is a harder, more realistic problem: governing an *autonomous
agent* — a system that calls tools, reads files, executes shell commands, and
browses the web on behalf of a user.

OpenClaw is the right subject. It is the most widely deployed autonomous agent
framework as of 2026, open-source, locally installable, and extensively studied:
<cite index="6-1">its rapid adoption — exceeding 200,000 GitHub stars within weeks of its January
2026 relaunch — made it an unusually high-visibility target for security
researchers</cite>. <cite index="6-1">470 published security advisories exist</cite> across its four
principal subsystems. Known CVEs include <cite index="9-1">command injection (CVE-2026-24763),
SSRF (CVE-2026-26322), path traversal enabling local file reads (CVE-2026-26329),
and prompt-injection-driven code execution (CVE-2026-30741)</cite>.

The core vulnerability is architectural: <cite index="11-1">give a language model the ability to
read your inbox, run shell commands, and pull third-party skills from a public
registry, and you have handed an attacker a remote-code-execution primitive the
moment one untrusted token enters the context window. You cannot patch your way
out of that with a system prompt.</cite>

## The clean-provenance rule (non-negotiable)

This episode is designed entirely from public security literature and a freshly
installed home instance of OpenClaw. It is not a re-creation of, and draws no
content from, any employer system, architecture, or deployment. This rule is
written into the ADR, not just the README.

## Decision

Install OpenClaw locally (home hardware, fresh install). Wire its LLM calls
through the E1 Audit Gateway. Run an adversarial battery of agent-specific attacks
— indirect injection via tool output, malicious file reads, cross-agent
manipulation — against two configurations:

1. **Bare OpenClaw** talking directly to the local SLM
2. **Gated OpenClaw** with all LLM calls routed through the E1 gateway

Measure and publish the **before/after defense rate**, using the same honest
methodology as E2 (ADR-006): layered deterministic scoring, explicit ambiguous
bucket, real numbers unretouched.

The headline E3 produces: *"putting your agent's LLM calls behind a governance
layer catches X% more attacks than the bare agent — here's the methodology and
the delta."*

## Why agent-level governance is different from inference governance

<cite index="3-1">Prompt injection in external content can lead AI agents to perform
unintended actions such as executing code, accessing sensitive resources, or
exfiltrating data.</cite> The key difference: a governed *inference call* limits
what the model *says*. Governing an *agent's* inference calls limits what it
*does* — which is categorically more dangerous.

<cite index="3-1">The most effective way to secure AI agents is not through prompt guardrails
alone, but by enforcing deterministic controls over what actions agents are
allowed to perform.</cite> This is what routing through the gateway provides:
every agent LLM call is audited, policy-checked, and logged before it produces
a tool-use decision.

## Alternatives considered (and why they lost)

| Alternative | Why not |
|---|---|
| **A different agent framework** | OpenClaw is the most studied, most deployed, and has the richest public adversarial literature to draw from. It makes E3 immediately relevant to the most readers. |
| **Build our own agent** | Misses the point — E3's value is governing a *real, widely deployed* system, not a toy. |
| **Governing at the tool layer only** | Tool-layer controls (what the agent *can* do) are complementary, not substitutes. Governing the LLM call is what stops the model from *deciding* to do something harmful. Both layers matter; E3 focuses on the LLM governance layer since that's what we've built. |
| **Full MCP integration testing** | MCP supply-chain attacks are a real vector but a separate episode — adding them here would explode scope. Logged in LATER.md. |

## Attack categories for E3 corpus (extends E2)

1. **Indirect prompt injection** — malicious content planted in tool output (web
   pages, file contents, calendar events) that the agent reads and executes as
   instructions. The canonical E3 attack class.
2. **Tool-output poisoning** — a bash command returns an output crafted to redirect
   the agent's next action.
3. **Memory injection** — a persistent note or memory record contains embedded
   instructions that activate on the next agent session.
4. **Cross-agent manipulation** — one agent instance sends a crafted message to
   another, attempting to hijack its task.
5. **Exfiltration via tool use** — injection that convinces the agent to write
   sensitive data to an externally accessible file or URL.

## Honest limits (stated upfront)

Routing agent LLM calls through the gateway audits and can block the model's
*instructions* — it cannot stop a tool action the model has already decided
upon and dispatched before the next gateway call. Complete agent governance
requires both LLM-call governance AND tool-invocation allow-lists; E3
demonstrates and measures the LLM-governance layer only. The limit is stated in
the article and the README.

## Further reading

- MITRE ATLAS — agent-specific attack techniques
- CVE-2026-25253 (canonical OpenClaw CSRF → RCE chain)
- "Don't let the claw grip your hand" — arXiv 2603.10387 (security analysis)
- "A systematic taxonomy of security vulnerabilities in OpenClaw" — arXiv 2603.27517
- OWASP Top 10 for LLM — LLM02: Insecure Agents, LLM07: Indirect Prompt Injection
