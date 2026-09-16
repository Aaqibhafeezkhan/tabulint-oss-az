"""tabulint: practical data-quality checks for CSV and JSON datasets."""

from pathlib import Path

from .analyzer import analyze, infer_type, is_missing, profile_fields
from .loader import load_csv, load_dataset, load_json, load_jsonl
from .models import FieldProfile, Issue, Record, Report, TabulintError
from .report import format_report
from .validators import NumericRule, build_numeric_rules, check_numeric_rules

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
    "format_report",
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
) -> Report:
    """Run all checks against already-loaded records."""
    issues = analyze(records) + check_numeric_rules(records, rules or [])
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


def check_file(path: str | Path, rules: list[NumericRule] | None = None) -> Report:
    """Load a CSV or JSON file and run all checks against it."""
    records = load_dataset(path)
    return check_records(records, rules, path=str(path))
