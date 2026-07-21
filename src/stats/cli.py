"""audit-stats: run the deterministic security analysis over an audit log.

Usage:
    python -m src.stats.cli /data/audit.jsonl

Prints a metrics summary and any findings. Exit code 0 = no findings,
1 = at least one finding (so it can gate a scheduled job).
"""
from __future__ import annotations

import argparse
import json
import sys

try:
    from src.stats.analyzer import analyze, load_events, summarize
except ImportError:  # pragma: no cover - path shim for direct execution
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    from src.stats.analyzer import analyze, load_events, summarize


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze an AIHOOTS audit log.")
    parser.add_argument("path", help="Path to the JSONL audit log")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args(argv)

    events = load_events(args.path)
    metrics = summarize(events)
    findings = analyze(events)

    if args.json:
        print(json.dumps({
            "metrics": metrics,
            "findings": [f.__dict__ for f in findings],
        }, indent=2))
    else:
        print("== metrics ==")
        for k, v in metrics.items():
            print(f"  {k}: {v}")
        print("== findings ==")
        if not findings:
            print("  none — nothing anomalous")
        for f in findings:
            print(f"  [{f.severity.upper()}] {f.detector}: {f.message}")

    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
