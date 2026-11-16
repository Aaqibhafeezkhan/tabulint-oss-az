import json

import pytest

from tabulint.models import FieldProfile, Issue, Report, TabulintError
from tabulint.report import format_report, format_report_json


def test_json_report_contains_expected_shape():
    report = Report(
        path="people.csv",
        row_count=2,
        profiles=[FieldProfile("age", "integer", missing_count=1)],
        issues=[Issue("missing-value", "warning", "age is missing", "age", 2)],
    )

    data = json.loads(format_report_json(report))

    assert set(data) == {
        "path",
        "row_count",
        "profiles",
        "issues",
        "error_count",
        "warning_count",
        "ok",
    }
    assert data["path"] == "people.csv"
    assert data["row_count"] == 2
    assert data["profiles"] == [
        {"name": "age", "dominant_type": "integer", "missing_count": 1}
    ]
    assert data["error_count"] == 0
    assert data["warning_count"] == 1
    assert data["ok"] is False


def test_json_report_includes_every_issue():
    issues = [
        Issue("missing-value", "warning", "age is missing", "age", 2),
        Issue("above-maximum", "error", "age is too high", "age", 3),
        Issue("missing-field", "error", "name is missing", "name", 4),
    ]
    report = Report(path="people.csv", row_count=4, issues=issues)

    data = json.loads(format_report_json(report))

    assert data["issues"] == [
        {
            "code": issue.code,
            "severity": issue.severity,
            "message": issue.message,
            "field": issue.field_name,
            "row": issue.row,
        }
        for issue in issues
    ]
    assert data["error_count"] == 2
    assert data["warning_count"] == 1


def test_clean_json_report_has_empty_issues():
    report = Report(path="people.csv", row_count=2)

    data = json.loads(format_report_json(report))

    assert data["issues"] == []
    assert data["error_count"] == 0
    assert data["warning_count"] == 0
    assert data["ok"] is True


def test_json_report_does_not_truncate_issues():
    issues = [
        Issue("missing-value", "warning", f"value {row}", "field", row)
        for row in range(1, 61)
    ]
    report = Report(path="large.csv", row_count=60, issues=issues)

    data = json.loads(format_report_json(report))

    assert len(data["issues"]) == 60
    assert data["issues"][-1]["row"] == 60
    assert "and 10 more" not in format_report_json(report)


def test_text_report_is_unchanged():
    report = Report(
        path="people.csv",
        row_count=2,
        profiles=[FieldProfile("age", "integer", missing_count=1)],
        issues=[Issue("missing-value", "warning", "age is missing", "age", 2)],
    )

    assert format_report(report) == (
        "tabulint: people.csv\n"
        "  records: 2\n"
        "  fields:\n"
        "    age  integer (1 missing)\n"
        "  missing values:\n"
        "    age: 1 missing (50%)\n"
        "  issues: 1\n"
        "    [warning] row 2: missing-value: age is missing\n"
        "  summary: 0 error(s), 1 warning(s)"
    )


def test_text_report_summarizes_missing_values_in_sorted_order():
    report = Report(
        path="people.csv",
        row_count=3,
        profiles=[
            FieldProfile("age", "integer", missing_count=1),
            FieldProfile("city", "string", missing_count=1),
            FieldProfile("email", "string", missing_count=2),
            FieldProfile("name", "string"),
        ],
        issues=[
            Issue("missing-value", "warning", "age is missing", "age", 1),
            Issue("missing-value", "warning", "email is missing", "email", 1),
            Issue("missing-value", "warning", "email is missing", "email", 2),
        ],
    )

    text = format_report(report)

    assert "  missing values:\n" in text
    assert text.index("    email: 2 missing (67%)") < text.index("    age: 1 missing (33%)")
    assert text.index("    age: 1 missing (33%)") < text.index("    city: 1 missing (33%)")
    assert "    name:" not in text


def test_text_report_omits_missing_summary_for_complete_dataset():
    report = Report(
        path="people.csv",
        row_count=2,
        profiles=[
            FieldProfile("age", "integer"),
            FieldProfile("name", "string"),
        ],
    )

    text = format_report(report)

    assert "missing values:" not in text


def test_text_report_defaults_to_50_issues():
    issues = [
        Issue("missing-value", "warning", f"value {row}", "field", row)
        for row in range(1, 61)
    ]
    report = Report(path="people.csv", row_count=60, issues=issues)

    text = format_report(report)

    assert text.count("[warning]") == 50
    assert "[warning] row 50:" in text
    assert "[warning] row 51:" not in text
    assert "... and 10 more" in text
    assert "  issues: 60\n" in text
    assert "  summary: 0 error(s), 60 warning(s)" in text


def test_text_report_respects_custom_limit():
    issues = [
        Issue("missing-value", "warning", f"value {row}", "field", row)
        for row in range(60, 0, -1)
    ]
    report = Report(path="people.csv", row_count=60, issues=issues)
    original_issues = report.issues.copy()
    text = format_report(report, max_issues=3)

    assert text.count("[warning]") == 3
    assert "[warning] row 3:" in text
    assert "[warning] row 4:" not in text
    assert "... and 57 more" in text
    assert "  issues: 60\n" in text
    assert "summary: 0 error(s), 60 warning(s)" in text
    assert text.index("[warning] row 1:") < text.index("[warning] row 2:")
    assert text.index("[warning] row 2:") < text.index("[warning] row 3:")
    assert report.issues == original_issues


def test_text_report_zero_limit_shows_all_issues():
    issues = [
        Issue("missing-value", "warning", f"value {row}", "field", row)
        for row in range(1, 61)
    ]
    report = Report(path="people.csv", row_count=60, issues=issues)

    text = format_report(report, max_issues=0)

    assert text.count("[warning]") == 60
    assert "[warning] row 60:" in text
    assert "... and " not in text
    assert "  issues: 60\n" in text
    assert "summary: 0 error(s), 60 warning(s)" in text


def test_text_report_rejects_negative_limit():
    report = Report(path="people.csv", row_count=0)

    with pytest.raises(TabulintError):
        format_report(report, max_issues=-1)


def test_text_report_rejects_boolean_limit():
    report = Report(path="people.csv", row_count=0)

    with pytest.raises(TabulintError):
        format_report(report, max_issues=True)

    with pytest.raises(TabulintError):
        format_report(report, max_issues=False)


def test_text_report_rejects_non_integer_limits():
    report = Report(path="people.csv", row_count=0)

    with pytest.raises(TabulintError):
        format_report(report, max_issues=1.5)

    with pytest.raises(TabulintError):
        format_report(report, max_issues=None)

    with pytest.raises(TabulintError):
        format_report(report, max_issues="Fifty")
