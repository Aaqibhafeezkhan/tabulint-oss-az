from pathlib import Path
import re

import pytest

import tabulint


ROOT = Path(__file__).resolve().parents[1]
API_DOCUMENT = ROOT / "docs" / "api.md"
API_TEXT = API_DOCUMENT.read_text(encoding="utf-8")
EXAMPLES = re.findall(r"^```python\n(.*?)^```$", API_TEXT, re.MULTILINE | re.DOTALL)


def _documented_issue_pairs(text):
    return set(re.findall(r"^\| `([^`]+)` \| (error|warning) \|", text, re.MULTILINE))


def test_every_public_export_is_importable_and_documented():
    imported = {}
    exec("from tabulint import *", imported)
    documented = set(re.findall(r"^### `([^`]+)`$", API_TEXT, re.MULTILINE))

    assert documented == set(tabulint.__all__)
    for name in tabulint.__all__:
        assert imported[name] is getattr(tabulint, name)


def test_documented_issue_codes_and_severities_match_emitted_checks():
    records = [
        {"name": "Ada", "age": 36},
        {"name": "Ada", "age": 36},
        {"name": "", "age": "old"},
        {"age": -1},
        {"name": "Grace", "age": 200},
    ]
    rules = tabulint.build_numeric_rules(["age=0"], ["age=120"])
    length_rules = tabulint.build_length_rules(["name=4"], ["name=4"])
    allowed_rules = tabulint.build_allowed_values_rules(["name=Ada"])
    reports = [
        tabulint.check_records(records, rules, length_rules=length_rules,
                               required_fields=["name"], allowed_values_rules=allowed_rules),
        tabulint.check_records([]),
    ]
    emitted = {(issue.code, issue.severity) for report in reports for issue in report.issues}

    assert _documented_issue_pairs(API_TEXT) == emitted
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert _documented_issue_pairs(readme) == emitted


def test_api_reference_contains_runnable_examples():
    assert EXAMPLES


@pytest.mark.parametrize(
    "source", EXAMPLES, ids=[f"example-{i}" for i in range(1, len(EXAMPLES) + 1)]
)
def test_api_reference_examples_run(source, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    exec(compile(source, str(API_DOCUMENT), "exec"), {})
