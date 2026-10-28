"""Tests for the questions-to-ask list builder."""

from contract_checker.heuristics import scan
from contract_checker.questions import GENERIC_QUESTIONS, build_questions

from .samples import UNILATERAL_CHANGE, BENIGN


def test_questions_generated_for_findings():
    findings = scan(UNILATERAL_CHANGE)
    questions = build_questions(findings)
    assert questions
    assert len(questions) > len(GENERIC_QUESTIONS)
    joined = "\n".join(questions)
    assert "consent" in joined.lower() or "agree" in joined.lower()


def test_generic_questions_always_included():
    findings = build_questions([])
    for question in GENERIC_QUESTIONS:
        assert question in findings


def test_no_duplicate_questions():
    questions = build_questions(scan(UNILATERAL_CHANGE))
    lowered = [question.lower() for question in questions]
    assert len(lowered) == len(set(lowered))


def test_benign_still_gets_baseline_questions():
    questions = build_questions(scan(BENIGN))
    assert questions == GENERIC_QUESTIONS


def test_case_insensitive_dedup():
    stub = type("F", (), {"questions": ["Same Question?", "same question?"]})()
    result = build_questions([stub])
    assert result.count("Same Question?") == 1
