"""The claim under test: tampering with ANY historical record is detected.

We don't test that the chain "works" — we test that manipulation is CAUGHT,
at every position, for every field mutated. This is the clinical standard for
the whole project: write the test that could falsify the claim.
"""
import json

import pytest

from src.gateway.audit.chain import AuditChain, new_event
from src.verifier.cli import verify


def _build_log(path, n=5):
    chain = AuditChain(str(path))
    for i in range(n):
        chain.append(new_event(
            request_id=f"req-{i}", caller="test", model="m",
            event_type="decision", decision="allow",
            prompt_digest=f"digest-{i}", prompt_len=10 + i,
        ))
    return path


def test_intact_chain_verifies(tmp_path):
    log = _build_log(tmp_path / "audit.jsonl")
    assert verify(str(log)) == []


@pytest.mark.parametrize("target_seq", [0, 1, 2, 3, 4])
def test_altering_any_record_is_detected(tmp_path, target_seq):
    log = _build_log(tmp_path / "audit.jsonl")
    lines = log.read_text().splitlines()

    # Mutate a semantic field of the target record WITHOUT recomputing its hash,
    # exactly as an attacker editing the file would.
    rec = json.loads(lines[target_seq])
    rec["prompt_len"] = rec["prompt_len"] + 999
    lines[target_seq] = json.dumps(rec, sort_keys=True, separators=(",", ":"))
    log.write_text("\n".join(lines) + "\n")

    errors = verify(str(log))
    assert errors, f"tampering at seq={target_seq} went undetected"
    # The altered record itself must be flagged (content hash mismatch).
    assert any(e.seq == target_seq for e in errors)


def test_deleting_a_record_breaks_sequence(tmp_path):
    log = _build_log(tmp_path / "audit.jsonl")
    lines = log.read_text().splitlines()
    del lines[2]
    log.write_text("\n".join(lines) + "\n")
    assert verify(str(log)), "record deletion went undetected"


def test_reordering_records_is_detected(tmp_path):
    log = _build_log(tmp_path / "audit.jsonl")
    lines = log.read_text().splitlines()
    lines[1], lines[2] = lines[2], lines[1]
    log.write_text("\n".join(lines) + "\n")
    assert verify(str(log)), "reordering went undetected"


def test_resume_extends_existing_chain(tmp_path):
    log = _build_log(tmp_path / "audit.jsonl", n=3)
    # New writer instance resumes from the file and must keep the chain valid.
    chain2 = AuditChain(str(log))
    chain2.append(new_event(request_id="req-3", caller="test", model="m",
                            event_type="decision", decision="allow"))
    assert verify(str(log)) == []


# --- verifier CLI coverage ---------------------------------------------------

def test_verifier_cli_intact(tmp_path, capsys):
    from src.verifier.cli import main
    log = _build_log(tmp_path / "audit.jsonl", n=4)
    code = main([str(log)])
    assert code == 0
    assert "intact" in capsys.readouterr().out


def test_verifier_cli_tampered(tmp_path, capsys):
    import json as _json
    from src.verifier.cli import main
    log = _build_log(tmp_path / "audit.jsonl", n=4)
    lines = log.read_text().splitlines()
    rec = _json.loads(lines[1])
    rec["prompt_len"] = 9999
    lines[1] = _json.dumps(rec, sort_keys=True, separators=(",", ":"))
    log.write_text("\n".join(lines) + "\n")
    code = main([str(log)])
    assert code == 1
    assert "TAMPERING" in capsys.readouterr().err
