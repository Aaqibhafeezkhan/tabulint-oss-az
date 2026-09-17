import json

from tabulint.models import FieldProfile, Issue, Report
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
        "  issues: 1\n"
        "    [warning] row 2: missing-value: age is missing\n"
        "  summary: 0 error(s), 1 warning(s)"
    )
