"""Validate real serializer output against the published structural contract."""

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from tabulint import build_numeric_rules, check_file, check_records, format_report_json


SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "report-v1.schema.json"


@pytest.fixture(scope="module")
def validator():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


@pytest.fixture
def document():
    report = check_records([{"age": 200}, {"age": None}],
                           build_numeric_rules([], ["age=120"]))
    return json.loads(format_report_json(report))


@pytest.mark.parametrize("name,content", [
    ("clean.csv", "name,age\nAda,36\nGrace,45\n"),
    ("issues.csv", "name,age\nAda,200\n,36\n"),
    ("header-only.csv", "name,age\n"),
    ("blank.json", " \n"),
    ("empty.json", "[]"),
    ("clean.jsonl", '{"name":"Ada","age":36}\n'),
])
def test_emitted_file_reports_match_schema(validator, write, name, content):
    path = write(name, content)
    report = check_file(path, build_numeric_rules([], ["age=120"]))
    data = json.loads(format_report_json(report))
    validator.validate(data)
    if name == "issues.csv":
        assert data["error_count"] > 0 and data["warning_count"] > 0
    if name == "header-only.csv":
        assert data["profiles"]
        assert all(p["dominant_type"] == "null" for p in data["profiles"])
    if name == "blank.json":
        assert data["issues"][0]["field"] is None
        assert data["issues"][0]["row"] is None


def test_emitted_json_keeps_more_than_fifty_issues(validator):
    report = check_records([{"age": None} for _ in range(60)])
    data = json.loads(format_report_json(report))
    assert len(data["issues"]) > 50
    assert len(data["issues"]) == len(report.issues)
    validator.validate(data)


@pytest.mark.parametrize("value,type_name", [
    (None, "null"), (True, "boolean"), (1, "integer"),
    (1.5, "float"), ("Ada", "string"),
])
def test_emitted_inferred_type_names(validator, value, type_name):
    data = json.loads(format_report_json(check_records([{"value": value}])))
    assert data["profiles"][0]["dominant_type"] == type_name
    validator.validate(data)


@pytest.mark.parametrize("section,key", [
    *[("report", key) for key in
      ("path", "row_count", "profiles", "issues", "error_count", "warning_count", "ok")],
    *[("profile", key) for key in ("name", "dominant_type", "missing_count")],
    *[("issue", key) for key in ("code", "severity", "message", "field", "row")],
])
def test_all_emitted_properties_are_required(validator, document, section, key):
    target = {"report": document, "profile": document["profiles"][0],
              "issue": document["issues"][0]}[section]
    del target[key]
    assert not validator.is_valid(document)


@pytest.mark.parametrize("path,value", [
    (("row_count",), -1), (("error_count",), -1), (("warning_count",), -1),
    (("row_count",), True), (("ok",), "true"), (("path",), None),
    (("profiles",), {}), (("issues",), {}),
    (("profiles", 0, "missing_count"), -1),
    (("profiles", 0, "dominant_type"), None),
    (("profiles", 0, "dominant_type"), "number"),
    (("issues", 0, "severity"), "info"),
    (("issues", 0, "row"), 0), (("issues", 0, "row"), -1),
    (("issues", 0, "row"), 1.5), (("issues", 0, "row"), "1"),
    (("issues", 0, "row"), True), (("issues", 0, "field"), 1),
])
def test_invalid_property_values_are_rejected(validator, document, path, value):
    target = document
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    assert not validator.is_valid(document)


def test_additive_properties_and_new_issue_codes_are_compatible(validator, document):
    document["future_metadata"] = {"version": 2}
    document["profiles"][0]["future_metadata"] = []
    document["issues"][0]["future_metadata"] = None
    document["issues"][0]["code"] = "future-check"
    document["issues"][0]["message"] = "Wording can evolve."
    validator.validate(document)


def test_cross_field_consistency_is_outside_structural_validation(validator, document):
    inconsistent = copy.deepcopy(document)
    inconsistent["error_count"] = 999
    inconsistent["ok"] = True
    # Counts and verdict must be checked semantically by consumers, not inferred
    # from structural schema success. Draft 2020-12 has no sibling-value arithmetic.
    validator.validate(inconsistent)
