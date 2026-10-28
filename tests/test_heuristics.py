"""Tests for the offline heuristics."""

from contract_checker.heuristics import scan

from .samples import (
    AUTO_RENEW,
    BENIGN,
    BROAD_IP,
    HUGE_LIABILITY,
    NON_COMPETE,
    PAYMENT_TRAP,
    PERSONNEL_CONTROL,
    TERMINATION,
    UNILATERAL_CHANGE,
    VAGUE_SCOPE,
)

BY_ID = {
    "auto_renew": AUTO_RENEW,
    "unilateral_change": UNILATERAL_CHANGE,
    "huge_liability": HUGE_LIABILITY,
    "vague_scope": VAGUE_SCOPE,
    "one_sided_termination": TERMINATION,
    "personnel_control": PERSONNEL_CONTROL,
    "payment_trap": PAYMENT_TRAP,
    "non_compete": NON_COMPETE,
    "broad_ip_grab": BROAD_IP,
}


def test_each_flagged_sample_fires_its_own_check():
    for check_id, text in BY_ID.items():
        found = scan(text)
        ids = [finding.check_id for finding in found]
        assert check_id in ids, (
            f"{check_id} failed to fire; found {ids} for: {text!r}"
        )


def test_high_severity_checks_flagged_high():
    for check_id in ("unilateral_change", "huge_liability"):
        finding = next(
            f for f in scan(BY_ID[check_id]) if f.check_id == check_id
        )
        assert finding.severity == "high"


def test_finding_captures_excerpt_and_questions():
    findings = scan(AUTO_RENEW)
    finding = findings[0]
    assert finding.excerpt
    assert "renew" in finding.excerpt.lower()
    assert finding.questions


def test_benign_clause_stays_quiet():
    findings = scan(BENIGN)
    ids = {finding.check_id for finding in findings}
    assert not ids, f"benign clause flagged as {ids}"


def test_scan_full_fictional_contract_finds_many():
    contract = "\n\n".join(
        sample for sample in BY_ID.values() if sample != AUTO_RENEW
    ) + "\n\n" + AUTO_RENEW
    findings = scan(contract)
    assert {f.check_id for f in findings} == set(BY_ID)


def test_severity_sort_high_first():
    findings = scan("\n".join(BY_ID.values()))
    severities = [f.severity for f in findings]
    rank = {"high": 0, "medium": 1, "low": 2}
    assert severities == sorted(severities, key=lambda s: rank[s])


def test_line_breaks_in_source_text_do_not_break_matching():
    wrapped = UNILATERAL_CHANGE.replace("at any time", "at any\n        time")
    assert any(f.check_id == "unilateral_change" for f in scan(wrapped))


def test_empty_input_returns_no_findings():
    assert scan("") == []
    assert scan("   \n  ") == []
