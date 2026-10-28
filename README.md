# plain-contract-checker-cli

Paste in a freelancer or vendor contract, get a plain-English read in
seconds — fully offline, right in your terminal. It points at clauses that
stand out (auto-renewal, "we can change the deal anytime", skewed
liability, vague scope, one-sided termination, people-removal control,
payment traps, non-compete reach, broad IP grabs) and hands you a list of
questions to ask before you sign.

Made by [Asdale Dynamics, LLC](https://dylanasdale.github.io) — Dylan
Asdale's shop for beginner-friendly AI tools that explain things "like a
friend would."

**Not legal advice.** Nothing in this tool says a clause is valid,
invalid, or enforceable. A finding only means: *this stands out, take a
closer look.* Its sibling and equally unofficial name for this behavior:
no trap claims, just raised eyebrows.

## Quick start

```bash
cd plain-contract-checker-cli
pip install -e .

# paste straight into the pipe
cat my-contract.txt | contract-checker

# or point at a file
contract-checker --file my-contract.txt

# machine-readable output
contract-checker --file my-contract.txt --json
```

That's it — the core scan is 100% offline: regex heuristics on your own
machine, no network calls, nothing leaves your computer.

Example of a finding:

```
1. [HIGH] One side can change the deal anytime
   Why it stands out: This stands out because it lets one side rewrite
   the deal later without your agreement — rates, scope, or terms can
   shift while you are already doing the work.

   Matched text: "Company may amend this agreement at any time in its
   sole discretion."
   Q: If terms change, do I have to agree in writing first — or does
   posting a new page count as my consent?
```

Every finding ends with questions to ask, plus a consolidated
questions-to-ask list at the bottom.

## Optional: AI review pass with a local model (Ollama)

The heuristics are dumb on purpose (fast, offline, no dependencies). For a
second opinion, add `--review` and the tool will send the contract to an
**OpenAI-compatible endpoint of your choice** — default is a local Ollama
server. Install [Ollama](https://ollama.com), pull a small model, and
serve it:

```bash
ollama pull llama3.2
ollama serve

contract-checker --file my-contract.txt --review
```

Any OpenAI-compatible base URL works, not just Ollama:

```bash
contract-checker --file my-contract.txt --review \
  --base-url http://localhost:1234/v1 \
  --model my-local-model
```

Privacy and honesty rules baked into the review pass:

- **No API keys, ever.** The tool never reads an API key from the
  environment or your files, and never sends one. It only talks to the
  base URL you give it (which points at your own machine by default —
  `http://localhost:11434/v1`). A fixed placeholder `Authorization:
  Bearer ollama` header is sent because some OpenAI-compatible servers
  require the header shape; it contains no secret.
- The review pass is clearly labeled in the output and still ends with
  "Not legal advice."
- If the endpoint is down or slow, the tool tells you and the offline
  scan still runs.

## What it looks for (offline heuristics)

| Check | Severity | What stands out |
| --- | --- | --- |
| `auto_renew` | medium | Auto-renewal / evergreen terms with easy-to-miss cancel windows |
| `unilateral_change` | high | One side can amend terms, rates, or scope at will |
| `huge_liability` | high | Indemnify-and-hold-harmless, waived consequential damages, caps for one side only |
| `vague_scope` | medium | "Services as needed", "such other duties", open-ended work |
| `one_sided_termination` | medium | Terminate-anytime-for-any-reason rights that run one way |
| `personnel_control` | medium | Client can dismiss/replace/reject your people and subs |
| `payment_trap` | medium | Net-60/90, late fees against you, payment withholding |
| `non_compete` | medium | Post-project non-compete / non-solicit reach |
| `broad_ip_grab` | medium | "All right, title and interest", "in perpetuity", pre-existing IP swept in |

Heuristics are intentionally conservative: better a false "take a look"
than a false "you're fine." No match does NOT mean a safe contract.

## Run the tests

```bash
pip install -e .
pytest
```

The test suite uses short sample clauses (found in `tests/`) covering
every check, benign text that should stay quiet, JSON output, and the
review endpoint plumbing — including the never-send-a-key rule.

## Status

See [STATUS.md](STATUS.md) for build/verification details and known gaps.

## License

MIT — Copyright (c) 2026 Asdale Dynamics, LLC
