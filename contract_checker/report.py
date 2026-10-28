"""Human-readable and JSON output for the CLI."""

from __future__ import annotations

from .heuristics import Finding

FILTER = "\u2500" * 56

DISCLAIMER = (
    "NOT LEGAL ADVICE. This scan only points at language that stands out "
    "(a trap-claim-free way of saying: double-check this). Nothing here "
    "tells you a clause is valid, invalid, or enforceable."
)


def render_report(
    findings: list[Finding],
    questions: list[str],
    review_text: str | None,
    source_label: str,
) -> str:
    lines: list[str] = []
    lines.append(FILTER)
    lines.append(f"Plain-English contract read: {source_label}")
    lines.append(FILTER)
    if not findings:
        lines.append(
            "No one-sided pattern matched. That is not a clean bill of "
            "health: heuristics miss plenty. Still read it, and ask the "
            "questions below."
        )
    else:
        ranked = {"high": "HIGH", "medium": "medium", "low": "low"}
        for index, finding in enumerate(findings, start=1):
            lines.append("")
            lines.append(
                f"{index}. [{ranked[finding.severity]}] {finding.title}"
            )
            lines.append(f"   Why it stands out: {finding.why}")
            lines.append("")
            lines.append(f"   Matched text: \"{finding.excerpt}\"")
            for question in finding.questions:
                lines.append(f"   Q: {question}")
    if review_text:
        lines.append("")
        lines.append(FILTER)
        lines.append("AI review pass (optional, via your own local endpoint)")
        lines.append(FILTER)
        lines.append(review_text)
    lines.append("")
    lines.append(FILTER)
    lines.append(f"Questions to ask ({len(questions)})")
    lines.append(FILTER)
    for index, question in enumerate(questions, start=1):
        lines.append(f"{index:>2}. {question}")
    lines.append("")
    lines.append(FILTER)
    lines.append(DISCLAIMER)
    lines.append(FILTER)
    return "\n".join(lines)


def render_json(findings: list[Finding], questions: list[str]) -> str:
    import json

    return json.dumps(
        {
            "disclaimer": DISCLAIMER,
            "not_legal_advice": True,
            "findings": [finding.as_dict() for finding in findings],
            "questions": questions,
        },
        indent=2,
        ensure_ascii=False,
    )
