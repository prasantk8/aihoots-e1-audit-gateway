"""Evaluation of the statistical detectors against synthetic logs with KNOWN,
LABELLED anomalies. This is how we earn the right to publish true/false-positive
numbers instead of asserting "it works" (ADR-003, Evaluation section).

Each scenario builds an event stream that either IS or IS NOT anomalous for a
specific detector, then asserts the detector fires (or stays silent) correctly.
The test_report_* test prints an honest confusion summary for the article.
"""
import random

from src.stats.analyzer import (
    detect_block_rate_spike,
    detect_caller_rate_outlier,
    detect_latency_bimodality,
    detect_prompt_len_anomaly,
)

random.seed(1234)  # reproducible synthetic data


# --- synthetic event builders ------------------------------------------------

def decision_event(caller="user", prompt_len=40, decision="allow"):
    return {"event_type": "decision", "caller": caller,
            "prompt_len": prompt_len, "decision": decision}


def response_event(latency_ms=200.0):
    return {"event_type": "response", "latency_ms": latency_ms}


def normal_stream(n=60):
    """A benign baseline: steady prompt lengths, low block rate, even callers."""
    events = []
    callers = ["alice", "bob", "carol", "dave"]
    for i in range(n):
        events.append(decision_event(
            caller=callers[i % len(callers)],
            prompt_len=int(random.gauss(40, 5)),
            decision="block" if random.random() < 0.03 else "allow",
        ))
        events.append(response_event(latency_ms=random.gauss(200, 15)))
    return events


# --- block-rate spike --------------------------------------------------------

def test_block_rate_spike_is_detected():
    events = [decision_event(decision="allow") for _ in range(20)]
    events += [decision_event(decision="block") for _ in range(20)]  # attack window
    assert detect_block_rate_spike(events) is not None


def test_block_rate_normal_is_silent():
    assert detect_block_rate_spike(normal_stream()) is None


# --- prompt-length anomaly ---------------------------------------------------

def test_prompt_len_spike_is_detected():
    events = [decision_event(prompt_len=40) for _ in range(20)]
    events += [decision_event(prompt_len=400) for _ in range(20)]  # huge payloads
    assert detect_prompt_len_anomaly(events) is not None


def test_prompt_len_normal_is_silent():
    assert detect_prompt_len_anomaly(normal_stream()) is None


# --- caller-rate outlier -----------------------------------------------------

def test_caller_rate_outlier_is_detected():
    events = []
    for _ in range(10):
        for c in ["alice", "bob", "carol"]:
            events.append(decision_event(caller=c))
    events += [decision_event(caller="mallory") for _ in range(120)]  # abuse
    assert detect_caller_rate_outlier(events) is not None


def test_caller_rate_even_is_silent():
    events = []
    for _ in range(15):
        for c in ["alice", "bob", "carol", "dave"]:
            events.append(decision_event(caller=c))
    assert detect_caller_rate_outlier(events) is None


# --- latency bimodality ------------------------------------------------------

def test_latency_bimodality_is_detected():
    events = [response_event(latency_ms=200 + random.gauss(0, 5)) for _ in range(20)]
    events += [response_event(latency_ms=900 + random.gauss(0, 5)) for _ in range(20)]  # 2nd mode
    assert detect_latency_bimodality(events) is not None


def test_latency_unimodal_is_silent():
    events = [response_event(latency_ms=200 + random.gauss(0, 8)) for _ in range(40)]
    assert detect_latency_bimodality(events) is None


# --- honest confusion summary for the article --------------------------------

def test_report_detector_accuracy(capsys):
    """Runs each detector across many positive and negative synthetic streams and
    prints TP/FP rates. This is the table that goes in the write-up."""
    trials = 40
    results = {}

    def run(name, positive_builder, negative_builder, detector):
        tp = sum(detector(positive_builder()) is not None for _ in range(trials))
        fp = sum(detector(negative_builder()) is not None for _ in range(trials))
        results[name] = (tp / trials, fp / trials)

    run("block_rate",
        lambda: [decision_event(decision="allow") for _ in range(20)] +
                [decision_event(decision="block") for _ in range(20)],
        normal_stream, detect_block_rate_spike)

    run("prompt_len",
        lambda: [decision_event(prompt_len=40) for _ in range(20)] +
                [decision_event(prompt_len=int(random.gauss(400, 30))) for _ in range(20)],
        normal_stream, detect_prompt_len_anomaly)

    run("latency_bimodal",
        lambda: [response_event(200 + random.gauss(0, 5)) for _ in range(20)] +
                [response_event(900 + random.gauss(0, 5)) for _ in range(20)],
        lambda: [response_event(200 + random.gauss(0, 8)) for _ in range(40)],
        detect_latency_bimodality)

    print("\nDetector accuracy (synthetic, seed=1234):")
    print(f"{'detector':<18}{'true-positive':>14}{'false-positive':>16}")
    for name, (tpr, fpr) in results.items():
        print(f"{name:<18}{tpr:>13.0%}{fpr:>15.0%}")

    # Guardrails, not vanity: detectors must be useful AND not noisy.
    for name, (tpr, fpr) in results.items():
        assert tpr >= 0.8, f"{name} true-positive rate too low: {tpr}"
        assert fpr <= 0.2, f"{name} false-positive rate too high: {fpr}"


# --- summarize + CLI coverage ------------------------------------------------

def test_summarize_reports_metrics(tmp_path):
    from src.stats.analyzer import summarize
    events = normal_stream(20)
    s = summarize(events)
    assert s["total_events"] == len(events)
    assert "block_rate" in s and "latency_p95_ms" in s


def test_cli_runs_and_reports(tmp_path, capsys):
    import json as _json
    from src.stats.cli import main
    log = tmp_path / "audit.jsonl"
    events = [decision_event(decision="allow") for _ in range(20)]
    events += [decision_event(decision="block") for _ in range(20)]
    log.write_text("\n".join(_json.dumps(e) for e in events) + "\n")
    code = main([str(log)])
    out = capsys.readouterr().out
    assert "metrics" in out and "findings" in out
    assert code == 1   # block-rate spike present => non-zero exit
