"""Command-line interface for the plain contract checker.

Usage examples:
    contract-checker --file contract.txt
    cat contract.txt | contract-checker
    contract-checker --file contract.txt --review
    contract-checker --file contract.txt --json
    contract-checker --file contract.txt --review --base-url http://localhost:11434/v1 --model llama3.2
"""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .heuristics import scan
from .questions import build_questions
from .report import render_json, render_report
from .review import (
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    ReviewError,
    review_contract,
)

PROG = "contract-checker"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROG,
        description=(
            "Plain-English pattern check for freelancer/vendor contracts. "
            "Offline heuristics flag clauses that stand out (auto-renewal, "
            "unilateral changes, liability skew, vague scope, one-sided "
            "termination, personnel removal control, payment traps, "
            "non-compete reach, broad IP grabs), then list questions to "
            "ask. NOT LEGAL ADVICE."
        ),
    )
    parser.add_argument(
        "contract",
        nargs="?",
        help="contract text pasted directly (quote it)",
    )
    parser.add_argument(
        "--file",
        "-f",
        help="read the contract from a UTF-8 text file (.txt / .md)",
    )
    parser.add_argument(
        "--review",
        action="store_true",
        help=(
            "also run an optional AI review pass through an "
            "OpenAI-compatible endpoint (default: Ollama at "
            f"{DEFAULT_BASE_URL}). Never sends an API key."
        ),
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"OpenAI-compatible base URL (default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"model name for the review pass (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="seconds to wait for the review endpoint (default: 120)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON instead of the friendly report",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def load_contract(args: argparse.Namespace) -> str | None:
    if args.file:
        try:
            with open(args.file, encoding="utf-8") as handle:
                return handle.read()
        except OSError as exc:
            print(f"error: cannot read {args.file}: {exc}", file=sys.stderr)
            return None
        except UnicodeDecodeError as exc:
            print(
                f"error: {args.file} is not valid UTF-8 text: {exc}",
                file=sys.stderr,
            )
            return None
    if args.contract:
        return args.contract
    if not sys.stdin.isatty():
        return sys.stdin.read()
    print(
        f"error: no contract given. Paste text via stdin "
        f"({'cat contract.txt | ' + PROG}), use --file, or pass text "
        f"as an argument.",
        file=sys.stderr,
    )
    return None


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    contract_text = load_contract(args)
    if contract_text is None:
        return 2
    contract_text = contract_text.strip()
    if not contract_text:
        print("error: the contract text is empty.", file=sys.stderr)
        return 2

    findings = scan(contract_text)
    questions = build_questions(findings)

    if args.json:
        print(render_json(findings, questions))
        return 0

    findings_summary = (
        ", ".join(finding.check_id for finding in findings)
        if findings
        else "none"
    )
    review_text: str | None = None
    if args.review:
        try:
            review_text = review_contract(
                contract_text,
                findings_summary,
                base_url=args.base_url,
                model=args.model,
                timeout=args.timeout,
            )
        except ReviewError as exc:
            print(
                f"note: optional AI review skipped ({exc}). "
                "The offline scan below still applies.",
                file=sys.stderr,
            )

    source = args.file if args.file else "stdin/argument"
    print(render_report(findings, questions, review_text, source))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
