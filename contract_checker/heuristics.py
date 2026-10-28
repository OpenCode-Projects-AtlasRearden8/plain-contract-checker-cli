"""Offline heuristic checks for one-sided contract language.

Each check is a plain regex pass over the pasted text. None of this is
legal advice — a finding only means "this stands out, take a closer look",
never "this is a trap" or "this clause is invalid".
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Pattern

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}
_EXCERPT_MAX = 240


@dataclass
class Finding:
    check_id: str
    title: str
    severity: str
    why: str
    excerpt: str
    questions: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "check_id": self.check_id,
            "title": self.title,
            "severity": self.severity,
            "why": self.why,
            "excerpt": self.excerpt,
            "questions": list(self.questions),
        }


@dataclass
class Heuristic:
    check_id: str
    title: str
    severity: str
    why: str
    patterns: list[str]
    questions: list[str]

    def compile(self) -> list[Pattern[str]]:
        return [
            re.compile(p, re.IGNORECASE | re.DOTALL)
            for p in self.patterns
        ]


def _sentence_around(text: str, start: int, end: int) -> str:
    excerpt = text[max(0, start) : min(len(text), end)]
    if len(excerpt) >= _EXCERPT_MAX:
        half = _EXCERPT_MAX // 2
        lead = "..." if start > 0 else ""
        tail = "..." if end < len(text) else ""
        excerpt = lead + text[start : start + half] + " [...] " + text[end - half : end] + tail
    return " ".join(excerpt.split())


def _normalize(text: str) -> str:
    squashed = " ".join(text.split())
    return squashed if squashed else ""


HEURISTICS: list[Heuristic] = [
    Heuristic(
        check_id="auto_renew",
        title="Auto-renewal / evergreen term",
        severity="medium",
        why=(
            "This stands out because the contract can quietly roll into a new "
            "term unless someone remembers to cancel by a deadline that may be "
            "earlier than you think. Miss the window once and you are locked "
            "in again."
        ),
        patterns=[
            r"auto(?:matic[a-z]*|\-|\s)?renew[a-z]*",
            r"renew[s]?\s+for\s+(?:a\s+)?(?:successive|additional|another)\s+(?:\w+\s+)?term",
            r"extend[s]?\s+(?:this\s+agreement|the\s+term|its\s+term)\s+(?:automatically|for\s+(?:the\s+)?same\s+term)",
            r"unless\s+(?:notice|written\s+notice|termination\s+notice)\s+(?:of\s+)?(?:non-?renewal\s+)?is\s+(?:given|provided)",
            r"evergreen",
        ],
        questions=[
            "What is the exact notice deadline and address to cancel before renewal?",
            "If I miss the renewal window, what is my way out — and what does it cost?",
        ],
    ),
    Heuristic(
        check_id="unilateral_change",
        title="One side can change the deal anytime",
        severity="high",
        why=(
            "This stands out because it lets one side rewrite the deal later "
            "without your agreement — rates, scope, or terms can shift while "
            "you are already doing the work."
        ),
        patterns=[
            r"(?:amend|modify|change|update|revise)[a-z]*\s+(?:this\s+agreement|these\s+terms|the\s+terms|this\s+agreement\s+and|any\s+part)[a-z\s]{0,60}(?:at\s+any\s+time|in\s+its\s+sole\s+discretion|without\s+(?:your|prior|the\s+client'?s?)\s+(?:consent|approval|notice))",
            r"may\s+(?:amend|modify|change|update|revise)[a-z]*\s+.{0,80}(?:at\s+any\s+time|in\s+its\s+sole\s+discretion)",
            r"(?:at\s+any\s+time|from\s+time\s+to\s+time)[a-z\s,]{0,40}(?:sole\s+discretion|without\s+your\s+consent)",
            r"changes?\s+to\s+(?:the\s+)?(?:terms|rates?|prices?|scope)\s+(?:may\s+)?(?:take\s+effect|apply)\s+(?:immediately|upon\s+posting)",
        ],
        questions=[
            "If terms change, do I have to agree in writing first — or does posting a new page count as my consent?",
            "What happens to already-booked, priced, or in-progress work if rates change mid-project?",
            "Is there any notice period before a change kicks in?",
        ],
    ),
    Heuristic(
        check_id="huge_liability",
        title="Skewed liability: cap for one side, all the risk for the other",
        severity="high",
        why=(
            "This stands out because one side appears to keep its risk tiny "
            "while the other side takes on broad or unlimited exposure — "
            "consequential damages, indemnity for the other side's own "
            "conduct, or a liability cap that skips one party."
        ),
        patterns=[
            r"in\s+no\s+event\s+shall\s+(?:.{0,60}?)(?:be\s+)?liable",
            r"shall\s+not\s+be\s+(?:responsible|liable)\s+(?:for|to).{0,60}(?:any\s+)?(?:damages|consequential|indirect|special|loss)",
            r"indemnif[a-z]+\s+(?:and\s+)?(?:forever\s+)?hold\s+harmless",
            r"hold\s+.{0,20}harmless\s+from\s+(?:any\s+and\s+all|all)",
            r"waiv[a-z]*\s+(?:.{0,40})?(?:consequential|indirect|special|punitive)\s+damages",
            r"all\s+(?:damages|claims|liabilit[a-z]+|losses)\s+of\s+(?:whatever|whatsoever)\s+nature",
            r"(?:unlimited|total|aggregate)\s+liability",
        ],
        questions=[
            "Whose liability is capped, and whose is unlimited?",
            "Am I indemnifying the client even for the client's own mistakes or negligent acts?",
            "Does my insurance actually cover the risk this clause puts on me?",
        ],
    ),
    Heuristic(
        check_id="vague_scope",
        title="Vague or open-ended scope of work",
        severity="medium",
        why=(
            "This stands out because the work can grow without the price "
            "growing with it. Open-ended scope words are how unpaid extras "
            "happen later."
        ),
        patterns=[
            r"services?\s+(?:as|deemed|when)\s+(?:needed|required|necessary|directed|requested)",
            r"such\s+other\s+(?:services|duties|tasks|work|assignments)",
            r"(?:other|additional)\s+(?:services|duties|tasks|work)\s+as\s+(?:may\s+be\s+)?(?:required|requested|directed|assigned)",
            r"from\s+time\s+to\s+time",
            r"as\s+(?:we|the\s+company|client)\s+may\s+(?:request|require|direct|determine)",
            r"scope\s+of\s+(?:work|services)\s+.{0,40}(?:including\s+but\s+not\s+limited\s+to|evolve|change)",
        ],
        questions=[
            "Can we list the concrete deliverables by name, with counts and formats?",
            "When extra work shows up, is there a written change order and a new price before I start it?",
            "What is explicitly NOT in scope?",
        ],
    ),
    Heuristic(
        check_id="one_sided_termination",
        title="Termination control that runs one way",
        severity="medium",
        why=(
            "This stands out because one party can end the relationship at "
            "will — often for convenience and often without paying out work "
            "already done."
        ),
        patterns=[
            r"(?:client|company|customer)\s+may\s+terminate\s+.{0,70}(?:at\s+any\s+time|without\s+cause|for\s+any\s+reason|for\s+convenience|without\s+prior\s+notice|effective\s+immediately)",
            r"terminate\s+(?:this\s+agreement\s+)?(?:at\s+any\s+time|for\s+convenience)\s+.{0,40}(?:without\s+(?:prior\s+)?(?:notice|cause|penalty)|with\s+(?:no|zero)\s+(?:notice|penalty))",
            r"upon\s+(?:.{0,20})?termination\s+.{0,40}(?:no\s+payment|no\s+further\s+payment|forfeiture|not\s+be\s+entitled\s+to\s+(?:any\s+)?(?:further\s+)?(?:payment|compensation))",
        ],
        questions=[
            "If the client ends the project early, am I paid for completed and in-progress work — including deposits and kill fees?",
            "Is the same right to terminate available to me, and on the same terms?",
            "How much notice is required on each side?",
        ],
    ),
    Heuristic(
        check_id="personnel_control",
        title="Dismissal/replacement control over your people",
        severity="medium",
        why=(
            "This stands out because the client wants the right to veto, "
            "remove, or replace the people you actually staff the work with. "
            "That mixes the client into how you run your own business and can "
            "put you on the hook for a hire you did not choose."
        ),
        patterns=[
            r"(?:remove|replace|reject|dismiss|disapprove)\s+.{0,60}(?:personnel|contractors?|employees?|subcontractors?|staff|workers?|individuals?)",
            r"prior\s+written\s+consent\s+.{0,60}(?:replace|substitute|subcontract|assign)",
            r"may\s+(?:require|direct)\s+.{0,40}(?:removal|replacement)\s+of",
            r"(?:reasonably\s+)?object\s+to\s+(?:.{0,40})?(?:personnel|contractors?|subcontractors?|staff|workers?)",
            r"subcontract[a-z]*\s+.{0,50}without\s+(?:.{0,30})?(?:prior\s+)?(?:written\s+)?(?:consent|approval)",
        ],
        questions=[
            "If the client asks me to remove or replace someone, who pays the cost of re-staffing and schedule slip?",
            "Is the removal right limited to reasonable, documented concerns?",
            "Can I choose my own subcontractors, or is approval required in advance?",
        ],
    ),
    Heuristic(
        check_id="payment_trap",
        title="Payment terms that cut against the freelancer",
        severity="medium",
        why=(
            "This stands out because the money mechanics tilt toward the "
            "payer: long payment windows, interest/penalty clocks pointed at "
            "you, or a license to withhold payment."
        ),
        patterns=[
            r"net\s+(?:60|90|120)",
            r"late\s+(?:fee|charge|penalty|interest)",
            r"interest\s+(?:at|of)\s+.{0,25}per\s+(?:annum|month)",
            r"withhold\s+(?:any\s+)?payment",
            r"settle\s+.{0,60}(?:at\s+its\s+sole\s+discretion|in\s+part|without\s+(?:interest|penalty))",
            r"liquidated\s+damages",
            r"retains?[^.]{0,30}(?:\d+%|percent)\s+.{0,30}(?:deposit|payment|fee)",
        ],
        questions=[
            "What is the payment due date, and what happens if it slips — does anything compensate me for waiting?",
            "Under what conditions can payment be withheld, and can I stop work or reclaim deliverables if it is?",
            "Are late fees or interest charged against me only, or against the payer too?",
        ],
    ),
    Heuristic(
        check_id="non_compete",
        title="Non-compete / non-solicit reach",
        severity="medium",
        why=(
            "This stands out because post-project restrictions can quietly "
            "block future income — other clients, whole markets, or people "
            "you already worked with."
        ),
        patterns=[
            r"non-?compete",
            r"shall\s+not\s*[,;]?\s*(?:directly\s+or\s+indirectly\s*[,;]?\s*)?compete",
            r"shall\s+not\s*[,;]?\s*(?:directly\s+or\s+indirectly\s*[,;]?\s*)?solicit",
            r"shall\s+not\s+(?:provide\s+services\s+to|work\s+for)\s+.{0,40}(?:competitors?|customers?|clients?)",
            r"refrain\s+from[^.]{0,40}(?:solicit|compete|engag)",
        ],
        questions=[
            "How long, in what geography, and covering exactly which clients or services?",
            "Does it survive after the contract ends, and does it apply to clients I already had?",
            "Is there a separate paid consideration for this restriction?",
        ],
    ),
    Heuristic(
        check_id="broad_ip_grab",
        title="Very broad IP assignment",
        severity="medium",
        why=(
            "This stands out because language like 'all work product', "
            "'in perpetuity', or 'whether or not created for the project' can "
            "hand over things you never intended to sell — your tools, "
            "templates, or prior work."
        ),
        patterns=[
            r"assign[s]?\s+.{0,80}all\s+right[s]?,\s+title\s+(?:and|&)\s+interest",
            r"all\s+work\s+product.{0,60}whether\s+or\s+not.{0,30}(?:created|developed|made)\s+(?:for|during|in\s+connection)",
            r"in\s+perpetuity",
            r"throughout\s+the\s+(?:universe|world)",
            r"existing\s+(?:work|ip|intellectual\s+property).{0,40}(?:assign|transfer|licen)",
            r"work\s+made\s+for\s+hire.{0,60}(?:including|and)\s+(?:all|any)\s+(?:derivative|pre-existing)",
        ],
        questions=[
            "Does my pre-existing IP — templates, code, articles, tooling — stay mine, with at most a license to the client?",
            "What exactly does the client get: full ownership of the deliverable, or usage rights for a stated purpose?",
            "Am I allowed to reuse techniques and general know-how on future projects?",
        ],
    ),
]

COMPILED: list[tuple[Heuristic, list[Pattern[str]]]] = [
    (h, h.compile()) for h in HEURISTICS
]


def scan(text: str) -> list[Finding]:
    normalized = _normalize(text)
    if not normalized:
        return []
    findings: list[Finding] = []
    for heuristic, patterns in COMPILED:
        seen_spans: set[tuple[int, int]] = set()
        excerpts: list[str] = []
        for pattern in patterns:
            for match in pattern.finditer(normalized):
                span = (match.start(), match.end())
                if span in seen_spans:
                    continue
                seen_spans.add(span)
                excerpts.append(
                    _sentence_around(normalized, match.start(), match.end())
                )
        if excerpts:
            findings.append(
                Finding(
                    check_id=heuristic.check_id,
                    title=heuristic.title,
                    severity=heuristic.severity,
                    why=heuristic.why,
                    excerpt=" || ".join(excerpts[:3]),
                    questions=list(heuristic.questions),
                )
            )
    findings.sort(key=lambda f: (SEVERITY_ORDER[f.severity], f.check_id))
    return findings


GENERIC_QUESTIONS = [
    "If the client cancels or pauses the project mid-way, exactly what am I paid — deposit, work done, kill fee?",
    "Who owns the deliverables if the deal falls apart before final payment?",
    "What is the single smallest word in this contract that costs me the most if I ignore it?",
    "Which clause would I refuse to sign with the roles reversed?",
    "If a dispute happens, where do I have to fight it, and who pays attorney fees?",
]
