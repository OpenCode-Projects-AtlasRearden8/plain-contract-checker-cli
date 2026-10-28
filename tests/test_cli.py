"""End-to-end CLI tests that run without any network."""

import json
import subprocess
import sys

from contract_checker.cli import build_parser, main

from .samples import (
    AUTO_RENEW,
    BENIGN,
    HUGE_LIABILITY,
    UNILATERAL_CHANGE,
)

FULL_CONTRACT = "\n\n".join(
    [UNILATERAL_CHANGE, HUGE_LIABILITY, AUTO_RENEW, BENIGN]
)


def test_parser_defaults_point_at_localhost():
    parser = build_parser()
    args = parser.parse_args([])
    assert args.base_url == "http://localhost:11434/v1"
    assert args.review is False
    assert args.json is False


def run_cli(args, input_text=None):
    return subprocess.run(
        [sys.executable, "-m", "contract_checker", *args],
        input=input_text,
        capture_output=True,
        text=True,
        cwd=".",
    )


def test_cli_main_json_output(capsys):
    exit_code = main(["--json", FULL_CONTRACT])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert exit_code == 0
    assert data["not_legal_advice"] is True
    ids = {finding["check_id"] for finding in data["findings"]}
    assert {"unilateral_change", "huge_liability", "auto_renew"} <= ids
    assert data["questions"]
    assert "not_legal_advice: no secrets" not in json.dumps(data)


def test_cli_main_text_report(capsys):
    exit_code = main([FULL_CONTRACT])
    captured = capsys.readouterr()
    assert exit_code == 0
    out = captured.out
    assert "One side can change the deal anytime" in out
    assert "Questions to ask" in out
    assert "NOT LEGAL ADVICE" in out
    assert "This stands out" in out


def test_cli_main_read_from_stdin(monkeypatch, capsys):
    class FakeStdin:
        isatty = staticmethod(lambda: False)

        @staticmethod
        def read():
            return UNILATERAL_CHANGE

    monkeypatch.setattr(sys, "stdin", FakeStdin)
    exit_code = main([])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "One side can change the deal anytime" in captured.out


def test_cli_main_empty_contract_fails(capsys):
    exit_code = main(["   "])
    captured = capsys.readouterr()
    assert exit_code == 2
    assert "empty" in captured.err.lower()


def test_cli_main_file_workflow(tmp_path, capsys):
    path = tmp_path / "tiny-contract.txt"
    path.write_text(UNILATERAL_CHANGE, encoding="utf-8")
    exit_code = main(["--file", str(path), "--json"])
    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["findings"][0]["check_id"] == "unilateral_change"


def test_cli_module_runs_as_script():
    result = run_cli(["--json"], FULL_CONTRACT)
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["not_legal_advice"] is True
