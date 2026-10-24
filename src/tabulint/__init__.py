"""tabulint: practical data-quality checks for CSV and JSON datasets."""

import csv
from pathlib import Path

from .analyzer import analyze, infer_type, is_missing, profile_fields
from .loader import load_csv, load_dataset, load_json, load_jsonl
from .models import FieldProfile, Issue, Record, Report, TabulintError
from .report import format_report, format_report_json
from .validators import NumericRule, build_numeric_rules, check_numeric_rules, check_required_fields

__version__ = "0.1.0"

__all__ = [
    "FieldProfile",
    "Issue",
    "NumericRule",
    "Record",
    "Report",
    "TabulintError",
    "__version__",
    "analyze",
    "build_numeric_rules",
    "check_file",
    "check_numeric_rules",
    "check_records",
    "check_required_fields",
    "format_report",
    "format_report_json",
    "infer_type",
    "is_missing",
    "load_csv",
    "load_dataset",
    "load_json",
    "load_jsonl",
    "profile_fields",
]


def check_records(
    records: list[Record],
    rules: list[NumericRule] | None = None,
    path: str = "<records>",
    *,
    required_fields: list[str] | None = None,
) -> Report:
    """Run all checks against already-loaded records."""
    issues = analyze(records) + check_numeric_rules(records, rules or [])
    issues += check_required_fields(records, required_fields or [])
    if not records:
        issues.append(
            Issue(
                code="empty-dataset",
                severity="warning",
                message="dataset contains no records",
            )
        )
    profiles = profile_fields(records)
    return Report(
        path=path,
        row_count=len(records),
        field_names=[profile.name for profile in profiles],
        profiles=profiles,
        issues=issues,
    )


def check_file(
    path: str | Path,
    rules: list[NumericRule] | None = None,
    *,
    delimiter: str = ",",
    encoding: str = "utf-8",
    required_fields: list[str] | None = None,
) -> Report:
    """Load a CSV, JSON, or JSON Lines file and run all checks against it."""
    records = load_dataset(path, delimiter=delimiter, encoding=encoding)
    report = check_records(records, rules, path=str(path), required_fields=required_fields)
    if not records:
        source = Path(path)
        try:
            text = source.read_text(encoding=encoding)
        except (OSError, UnicodeError):
            text = None
        message = "dataset contains no records"
        if text is not None and not text.strip():
            message = "file is empty or contains only whitespace"
        elif source.suffix.lower() == ".csv" and text is not None:
            try:
                header = next(csv.reader(text.splitlines(), delimiter=delimiter), [])
            except csv.Error:
                header = []
            if header:
                report.field_names = header
                message = f"CSV header contains fields {header!r}, but no records were found"
        report.issues = [
            Issue(issue.code, issue.severity, message, issue.field_name, issue.row)
            if issue.code == "empty-dataset" else issue
            for issue in report.issues
        ]
    return report
