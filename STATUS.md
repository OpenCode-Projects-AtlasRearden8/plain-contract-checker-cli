# STATUS.md — plain-contract-checker-cli

## What was built

A stdlib-only (zero runtime dependencies) Python CLI that gives a
plain-English pass over a freelancer or vendor contract you paste in.

- **Offline heuristic scan** (`contract_checker/heuristics.py`): 9 regex
  checks flag one-sided patterns — auto-renewal, unilateral changes,
  huge/skewed liability, vague scope, one-sided termination, client
  dismissal/replacement control over your people and subs, payment traps
  (net-90, late fees, withholding), non-compete/non-solicit reach, and
  very broad IP assignment. Each finding comes with a plain-English "why
  this stands out", the matched excerpt, and targeted questions.
- **Questions-to-ask list** (`contract_checker/questions.py`): the
  per-finding questions plus 5 baseline questions, deduplicated.
- **Optional AI review pass** (`contract_checker/review.py`): send the
  contract to any OpenAI-compatible chat/completions endpoint. Default is
  a local Ollama server (`http://localhost:11434/v1`, model `llama3.2`);
  any `--base-url` works. **Never reads or sends an API key** — only a
  fixed placeholder `Authorization: Bearer ollama` header, which contains
  no secret (needed because some OpenAI-compatible servers require the
  header shape). Graceful degradation: if the endpoint is unreachable,
  the tool says so and the offline scan still runs.
- **CLI** (`contract_checker/cli.py`): argument text, `--file`, or stdin;
  `--json` for machine-readable output; `--review`, `--base-url`,
  `--model`, `--timeout`; `--version`.
- "**Not legal advice**" is everywhere: CLI description, report footer,
  JSON `disclaimer` field, README, and the AI review prompt (which ends
  with a required "Not legal advice" sentence).

Tone/delivery notes: findings only say *this stands out* — the tool never
calls a clause "a trap" or claims invalidity, per the "no trap claims"
rule. It never contacts anything except the base URL you give it;
contract text and results stay on your machine unless you opt into
`--review` against your own endpoint.

## How to run it

```bash
pip install -e .            # from this folder
contract-checker --file my-contract.txt     # offline scan
cat my-contract.txt | contract-checker      # via stdin
contract-checker "text to check"            # as an argument
contract-checker --file my-contract.txt --json
contract-checker --file my-contract.txt --review   # needs local Ollama
contract-checker --file my-contract.txt --review \
  --base-url http://localhost:1234/v1 --model my-model   # any endpoint
python -m contract_checker                # without installing
```

## Verification results

- `python3 -m pytest` — **27 passed** (Python 3.13, pytest 9.1.1).
  Suite covers: every check firing on its sample clause and staying
  quiet on a benign clause, severity ordering, newline-tolerant
  matching, empty input, question dedup, JSON vs text output, stdin
  path, file path (tmp_path), `python -m` end-to-end run, and the review
  pass against in-process fake HTTP servers (success, HTTP 500,
  unreachable endpoint, empty text, no-API-key-sent assertion).
- Installed entry point smoke tests: full fictional 9-clause contract
  produced all 9 findings + 31 questions; `--json` parses cleanly;
  `--review` against a dead port prints a note to stderr and still
  exits 0 with the offline report.
- LICENSE copyright line verified exactly:
  `Copyright (c) 2026 Asdale Dynamics, LLC`.

## Known gaps

- Regex heuristics: no clause segmentation or party disambiguation — a
  benign clause with flagged vocabulary can match (by design: better an
  extra "look here" than a false "you're fine"), while skillful
  paraphrases could be missed entirely. No PDF/DOCX parsing — paste the
  text (UTF-8 `.txt`/`.md` files or stdin).
- One-sidedness is detected by wording, not by who is "you" in the
  contract; the questions are written to surface the real direction.
- The review pass truncates contract text at ~12,000 characters.
- The review pass sends a fixed placeholder bearer header; servers that
  hard-require a *real* key are out of scope on purpose (no keys, ever).
- English only.
- Not legal advice — by design, the tool categorically avoids judging
  validity, enforceability, or risk levels beyond severity ordering.
