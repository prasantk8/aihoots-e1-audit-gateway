# Security

This is a reference project meant to be read and rebuilt. It is not hardened for
production as-is. The security *posture* below is part of the lesson.

## Threat model (what the audit log defends against)

| Threat | Defended? | How |
|---|---|---|
| Operator silently edits a past record | **Yes** | Hash chain — any edit breaks verification and names the record |
| Records reordered | **Yes** | Sequence + prev-hash checks |
| A record deleted | **Yes** | Sequence gap detected |
| Whole log deleted | **No (by design for E1)** | Needs append-only/WORM storage + off-box replication (documented upgrade) |
| Forged authorship of a record | **No (by design for E1)** | Needs per-record signing (documented upgrade) |
| Prompt injection / jailbreak | **Partially** | Pattern blocklist; measured, not assumed — see policy tests |
| PII leakage to the model | **Partially** | Pattern redaction; precision/recall published, misses included |

Honesty about the "No"s is the point: a governance tool that overstates its coverage
is worse than one that states its limits.

## Engineering hygiene in this repo

- **No secrets in code.** All config via environment variables (`pydantic-settings`).
  `gitleaks` runs in CI on every push.
- **SAST** (`bandit`) and **dependency audit** (`pip-audit`) run in CI.
- **SBOM** (SPDX) generated for the built image on every pipeline run.
- **Least privilege container.** The gateway runs as a non-root user; the model is
  reachable only on an internal network, never exposed to the host.
- **Deterministic, tested controls.** Every security claim has a test that could
  falsify it (e.g. tamper detection at every record position).

## Reporting a vulnerability

Found a real gap — especially a way to tamper with the log undetected, or a policy
bypass? Please open an issue describing the reproduction. That's the most valuable
contribution this project can receive.

*Views and projects here are the author's own and unrelated to any employer's systems.*
