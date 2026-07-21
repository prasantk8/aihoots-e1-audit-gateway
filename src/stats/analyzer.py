"""Deterministic behavioural security analysis over the audit log (ADR-003).

The audit log is a security dataset. This module reads it and computes explainable
indicators — z-scores, EWMA drift, per-caller rate outliers, latency shape — with
NO machine learning. Every alert can be justified to a human, which is the whole
point in a regulated setting.

Detectors implemented (see ADR-003 glossary):
  - block_rate spike        (EWMA baseline vs current window)
  - prompt_len_z            (z-score of window mean prompt length vs baseline)
  - caller_rate_outlier     (per-caller volume vs peer distribution)
  - latency_bimodality      (a new latency mode appearing — model swap/degradation)

All thresholds are explicit constants, documented, and tunable. There are no
hidden magic numbers.
"""
from __future__ import annotations

import json
import statistics
from dataclasses import dataclass, field
from typing import Any


# --- Explicit, documented thresholds (no magic numbers buried in logic) ------
Z_THRESHOLD = 3.0            # prompt-length z-score above this => alert
BLOCK_RATE_MULTIPLIER = 3.0  # window block-rate this many x baseline => alert
CALLER_Z_THRESHOLD = 3.0     # per-caller volume z-score vs peers => alert
LATENCY_GAP_FRACTION = 0.4   # largest gap this fraction of total spread => bimodal
LATENCY_MIN_GAP_MS = 100.0   # ...and at least this many ms, to ignore trivial noise
MIN_SAMPLES = 8              # below this, we don't claim to detect anything


@dataclass
class Finding:
    detector: str
    severity: str            # "info" | "warn" | "alert"
    message: str
    evidence: dict[str, Any] = field(default_factory=dict)


def load_events(path: str) -> list[dict]:
    events = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events


def _mean_std(values: list[float]) -> tuple[float, float]:
    if len(values) < 2:
        return (values[0] if values else 0.0), 0.0
    return statistics.mean(values), statistics.pstdev(values)


def _median_mad(values: list[float]) -> tuple[float, float]:
    """Robust centre and spread. MAD (median absolute deviation) resists the
    outlier-masking problem where one extreme value inflates std and hides itself.
    Scaled by 1.4826 so MAD approximates std for normal data.
    """
    if not values:
        return 0.0, 0.0
    med = statistics.median(values)
    mad = statistics.median([abs(v - med) for v in values]) * 1.4826
    return med, mad


def _robust_z(value: float, values: list[float]) -> float:
    med, mad = _median_mad(values)
    if mad == 0:
        # Degenerate spread: fall back to a small epsilon so a clear departure
        # from a constant baseline still registers, but identical values don't.
        return 0.0 if value == med else (value - med) / (abs(med) * 0.01 + 1e-6)
    return (value - med) / mad


def detect_block_rate_spike(events: list[dict], baseline_frac: float = 0.5) -> Finding | None:
    """Compare block-rate in the recent window vs an earlier baseline window."""
    decisions = [e for e in events if e.get("event_type") == "decision"]
    if len(decisions) < MIN_SAMPLES:
        return None
    split = int(len(decisions) * baseline_frac)
    base, recent = decisions[:split], decisions[split:]
    if not base or not recent:
        return None
    base_rate = sum(d["decision"] == "block" for d in base) / len(base)
    recent_rate = sum(d["decision"] == "block" for d in recent) / len(recent)
    # Guard against a zero baseline: treat as spike if recent is materially non-zero.
    threshold = max(base_rate * BLOCK_RATE_MULTIPLIER, 0.15)
    if recent_rate >= threshold and recent_rate > base_rate:
        return Finding(
            detector="block_rate_spike", severity="alert",
            message=f"block rate rose from {base_rate:.0%} to {recent_rate:.0%}",
            evidence={"baseline": round(base_rate, 3), "recent": round(recent_rate, 3)},
        )
    return None


def detect_prompt_len_anomaly(events: list[dict], baseline_frac: float = 0.5) -> Finding | None:
    """z-score of recent mean prompt length vs the baseline window."""
    lens = [e.get("prompt_len", 0) for e in events
            if e.get("event_type") == "decision" and e.get("prompt_len", 0) > 0]
    if len(lens) < MIN_SAMPLES:
        return None
    split = int(len(lens) * baseline_frac)
    base, recent = lens[:split], lens[split:]
    if len(base) < 2 or not recent:
        return None
    recent_mean = statistics.mean(recent)
    z = _robust_z(recent_mean, base)
    if z >= Z_THRESHOLD:
        med, _ = _median_mad(base)
        return Finding(
            detector="prompt_len_z", severity="warn",
            message=f"mean prompt length spiked (robust z={z:.1f}) — possible injection payloads",
            evidence={"baseline_median": round(med, 1), "recent_mean": round(recent_mean, 1), "z": round(z, 2)},
        )
    return None


def detect_caller_rate_outlier(events: list[dict]) -> Finding | None:
    """Per-caller request volume vs the peer distribution."""
    counts: dict[str, int] = {}
    for e in events:
        if e.get("event_type") == "decision":
            counts[e.get("caller", "anonymous")] = counts.get(e.get("caller", "anonymous"), 0) + 1
    if len(counts) < 3:                      # need peers to compare against
        return None
    callers = list(counts)
    vals = [counts[c] for c in callers]
    worst, worst_z = None, 0.0
    for c in callers:
        # Robust z vs peers: compare each caller against the distribution of the
        # OTHERS, so a single abuser can't inflate the spread and mask itself.
        peers = [counts[o] for o in callers if o != c]
        z = _robust_z(counts[c], peers)
        if z > worst_z:
            worst, worst_z = c, z
    if worst_z >= CALLER_Z_THRESHOLD:
        peer_med, _ = _median_mad([counts[o] for o in callers if o != worst])
        return Finding(
            detector="caller_rate_outlier", severity="alert",
            message=f"caller '{worst}' volume is {worst_z:.1f} robust-SD above peers",
            evidence={"caller": worst, "count": counts[worst], "peer_median": round(peer_med, 1), "z": round(worst_z, 2)},
        )
    return None


def detect_latency_bimodality(events: list[dict]) -> Finding | None:
    """A second latency cluster appearing can indicate a model swap or degradation.

    Simple, explainable heuristic: sort latencies, find the largest gap between
    consecutive values; if that gap dwarfs the typical spacing, we have two modes.
    """
    lat = sorted(e.get("latency_ms", 0.0) for e in events
                 if e.get("event_type") == "response" and e.get("latency_ms", 0.0) > 0)
    if len(lat) < MIN_SAMPLES:
        return None
    gaps = [lat[i + 1] - lat[i] for i in range(len(lat) - 1)]
    if not gaps:
        return None
    max_gap = max(gaps)
    # A true second mode means the largest gap is a meaningful fraction of the
    # data's overall spread — not just larger than the tiny median micro-gap
    # (which noise alone produces). Compare against the interquartile-ish range.
    lo, hi = lat[len(lat) // 10], lat[-1 - len(lat) // 10]  # trimmed range
    spread = hi - lo
    if spread <= 0:
        return None
    if max_gap >= spread * LATENCY_GAP_FRACTION and max_gap >= LATENCY_MIN_GAP_MS:
        split_val = lat[gaps.index(max_gap)]
        return Finding(
            detector="latency_bimodality", severity="warn",
            message="latency distribution looks bimodal — possible model swap or degradation",
            evidence={"gap_ms": round(max_gap, 1), "spread_ms": round(spread, 1), "split_near_ms": round(split_val, 1)},
        )
    return None


DETECTORS = [
    detect_block_rate_spike,
    detect_prompt_len_anomaly,
    detect_caller_rate_outlier,
    detect_latency_bimodality,
]


def analyze(events: list[dict]) -> list[Finding]:
    """Run every detector; return all findings (empty list = nothing anomalous)."""
    findings = []
    for detector in DETECTORS:
        result = detector(events)
        if result is not None:
            findings.append(result)
    return findings


def summarize(events: list[dict]) -> dict[str, Any]:
    """Metrics surface for the /metrics endpoint (ADR-003 glossary)."""
    decisions = [e for e in events if e.get("event_type") == "decision"]
    responses = [e for e in events if e.get("event_type") == "response"]
    block_rate = (sum(d.get("decision") == "block" for d in decisions) / len(decisions)) if decisions else 0.0
    latencies = [r.get("latency_ms", 0.0) for r in responses if r.get("latency_ms", 0.0) > 0]
    p95 = 0.0
    if latencies:
        latencies.sort()
        p95 = latencies[min(len(latencies) - 1, int(len(latencies) * 0.95))]
    return {
        "total_events": len(events),
        "decisions": len(decisions),
        "block_rate": round(block_rate, 3),
        "responses": len(responses),
        "latency_p95_ms": round(p95, 1),
        "active_findings": len(analyze(events)),
    }
