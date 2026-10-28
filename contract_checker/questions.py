"""Build the questions-to-ask list from findings plus baseline questions."""

from __future__ import annotations

from .heuristics import GENERIC_QUESTIONS


def build_questions(findings) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()

    def add(question: str) -> None:
        key = question.strip().lower()
        if key in seen:
            return
        seen.add(key)
        ordered.append(question.strip())

    for finding in findings:
        for question in finding.questions:
            add(question)
    for question in GENERIC_QUESTIONS:
        add(question)
    return ordered
