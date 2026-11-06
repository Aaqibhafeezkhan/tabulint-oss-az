"""Execute the GitHub Actions recipe's validation commands locally.

The recipe in ``docs/github-actions.md`` is a copyable workflow; its hosted
execution on GitHub cannot be verified from here, but every validation
command it runs can. These tests run those exact commands
(``python -m tabulint.cli ...``) as subprocesses and check their exit codes
and JSON reports.
"""

import json
import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
DOCUMENT = ROOT / "docs" / "github-actions.md"
SCHEMA_PATH = ROOT / "schemas" / "report-v1.schema.json"

PIN = "0af5e041d5948daa63b601dec2652081f47d9f25"


@pytest.fixture(scope="module")
def validator():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


@pytest.fixture(scope="module")
def document_text():
    return DOCUMENT.read_text(encoding="utf-8")


def _run_cli(args, tmp_path):
    """Run the recipe's command exactly as written: ``python -m tabulint.cli``."""
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src")
    return subprocess.run(
        [sys.executable, "-m", "tabulint.cli", *args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _run_recipe_command(args, tmp_path, validator):
    """Run one recipe validation command and return its parsed JSON report."""
    output = tmp_path / "tabulint-report.json"
    result = _run_cli([*args, "--format", "json", "--output", str(output)], tmp_path)
    return result, output, json.loads(output.read_text(encoding="utf-8"))


def test_recipe_document_names_artifact_retention_and_pin(document_text):
    assert "name: tabulint-report" in document_text
    assert "retention-days: 7" in document_text
    assert "if: always()" in document_text
    assert PIN in document_text
    assert (
        "git+https://github.com/ismayilzeynal/tabulint-oss-az.git@" + PIN
        in document_text
    )


def test_recipe_document_uses_missing_csv_and_fail_on_error(document_text):
    assert "examples/missing.csv" in document_text
    assert "--fail-on error" in document_text
    # The PyPI name must never appear as an install command, only in the
    # sentence that tells readers not to use it.
    assert document_text.count("pip install tabulint") == 1
    assert "Do not use `pip install tabulint`" in document_text


def test_clean_dataset_passes_under_error_threshold(tmp_path, validator):
    result, _, data = _run_recipe_command(
        ["examples/clean.csv", "--fail-on", "error"], tmp_path, validator
    )
    assert result.returncode == 0
    validator.validate(data)
    assert data["ok"] is True
    assert data["issues"] == []


def test_warning_only_dataset_passes_under_error_threshold(tmp_path, validator):
    result, _, data = _run_recipe_command(
        ["examples/missing.csv", "--fail-on", "error"], tmp_path, validator
    )
    assert result.returncode == 0
    validator.validate(data)
    assert data["ok"] is False
    assert data["error_count"] == 0
    assert [issue["code"] for issue in data["issues"]] == ["missing-value"]


def test_recipe_workflow_gate_step_uses_fail_on_error(document_text):
    yaml_block = document_text.split("```yaml", 1)[1].split("```", 1)[0]
    # The gate step itself must use --fail-on error: the warning-only
    # examples/missing.csv then exits 0 and the gate passes, failing only
    # on a real error. The default threshold is shown only as a contrast
    # elsewhere in the guide, never in the workflow.
    assert '"--fail-on", "error"' in yaml_block
    assert "DATASET_PATH: examples/missing.csv" in yaml_block
    assert "steps.validate.outputs.exit_code" in yaml_block
    assert "|| true" not in yaml_block


def test_warning_only_dataset_fails_under_default_threshold(tmp_path, validator):
    # Contrast only: the default --fail-on warning makes the same
    # warning-only file exit 1. The recipe's gate step uses --fail-on
    # error instead (see test_recipe_workflow_gate_step_uses_fail_on_error),
    # so this is not the gate's behaviour.
    result, _, data = _run_recipe_command(["examples/missing.csv"], tmp_path, validator)
    assert result.returncode == 1
    validator.validate(data)
    assert data["warning_count"] == 1


def test_error_dataset_fails_under_error_threshold(tmp_path, validator):
    # --required age turns the blank age cell in examples/missing.csv into a
    # required-missing error, so the gate still fails with --fail-on error.
    result, _, data = _run_recipe_command(
        ["examples/missing.csv", "--required", "age", "--fail-on", "error"],
        tmp_path,
        validator,
    )
    assert result.returncode == 1
    validator.validate(data)
    assert data["error_count"] == 1
    assert any(
        issue["code"] == "required-missing" and issue["severity"] == "error"
        for issue in data["issues"]
    )


def test_load_failure_exits_two_and_writes_no_report(tmp_path):
    output = tmp_path / "tabulint-report.json"
    result = _run_cli(
        [
            "examples/does-not-exist.csv",
            "--fail-on",
            "error",
            "--format",
            "json",
            "--output",
            str(output),
        ],
        tmp_path,
    )
    assert result.returncode == 2
    assert "file not found" in result.stderr
    assert not output.exists()


def _documented_script(document_text, step_name):
    workflow = document_text.split("```yaml", 1)[1].split("```", 1)[0]
    section = workflow.split(f"      - name: {step_name}\n", 1)[1]
    match = re.search(r"        run: \|\n((?:          [^\n]*\n|\n)+)", section)
    assert match, f"No Python run block for {step_name}"
    return textwrap.dedent(match.group(1))


@pytest.mark.parametrize("kind,expected", [("clean", 0), ("warning", 0), ("error", 1), ("bad", 2)])
def test_documented_scripts_preserve_exit_and_remove_stale_report(document_text, tmp_path, validator, kind, expected):
    dataset = tmp_path / "input.json"
    content = {
        "clean": '[{"a": 1, "b": 2}]',
        "warning": '[{"a": null}]',
        "error": '[{"a": 1, "b": 2}, {"a": 3}]',
        "bad": '[{',
    }[kind]
    dataset.write_text(content, encoding="utf-8")
    report = tmp_path / "tabulint-report.json"
    report.write_text('{"stale": true}', encoding="utf-8")
    output = tmp_path / "github-output"
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"), DATASET_PATH=str(dataset), GITHUB_OUTPUT=str(output))
    capture = subprocess.run([sys.executable, "-c", _documented_script(document_text, "Validate data")],
                             cwd=tmp_path, env=env, capture_output=True, text=True)
    assert capture.returncode == 0, capture.stderr
    status = output.read_text(encoding="utf-8").strip().split("=", 1)[1]
    assert status == str(expected)
    if expected == 2:
        assert not report.exists()
    else:
        validator.validate(json.loads(report.read_text(encoding="utf-8")))
    env["VALIDATION_EXIT_CODE"] = status
    gate = subprocess.run([sys.executable, "-c", _documented_script(document_text, "Apply the data-quality gate")],
                          cwd=tmp_path, env=env, capture_output=True, text=True)
    assert gate.returncode == expected


@pytest.mark.parametrize("status", ["", "3", "not-a-code"])
def test_documented_gate_rejects_missing_or_unknown_status(document_text, status, tmp_path):
    env = dict(os.environ, VALIDATION_EXIT_CODE=status)
    gate = subprocess.run([sys.executable, "-c", _documented_script(document_text, "Apply the data-quality gate")],
                          cwd=tmp_path, env=env, capture_output=True, text=True)
    assert gate.returncode == 2
    assert "did not finish" in gate.stderr
