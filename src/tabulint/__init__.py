"""tabulint: practical data-quality checks for CSV and JSON datasets."""

from pathlib import Path

from .analyzer import analyze, infer_type, is_missing, profile_fields
from .loader import load_csv, load_dataset, load_json, load_jsonl
from .models import FieldProfile, Issue, Record, Report, TabulintError
from .report import format_report, format_report_json
from .validators import LengthRule, NumericRule, build_length_rules, build_numeric_rules, check_length_rules, check_numeric_rules, check_required_fields

__version__ = "0.1.0"

__all__ = [
    "FieldProfile",
    "Issue",
    "LengthRule",
    "NumericRule",
    "Record",
    "Report",
    "TabulintError",
    "__version__",
    "analyze",
    "build_numeric_rules",
    "build_length_rules",
    "check_file",
    "check_numeric_rules",
    "check_length_rules",
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
    length_rules: list[LengthRule] | None = None,
    required_fields: list[str] | None = None,
) -> Report:
    """Run all checks against already-loaded records."""
    issues = analyze(records) + check_numeric_rules(records, rules or []) + check_length_rules(records, length_rules or [])
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
    length_rules: list[LengthRule] | None = None,
    *,
    delimiter: str = ",",
    encoding: str = "utf-8",
    required_fields: list[str] | None = None,
) -> Report:
    """Load a CSV, JSON, or JSON Lines file and run all checks against it."""
    records = load_dataset(path, delimiter=delimiter, encoding=encoding)
    return check_records(records, rules, path=str(path), length_rules=length_rules, required_fields=required_fields)
