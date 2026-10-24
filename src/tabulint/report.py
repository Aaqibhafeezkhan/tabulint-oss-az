"""Rendering Reports as text and JSON."""

import json

from .models import Report

MAX_ISSUES_SHOWN = 50


def _safe_text(text: str) -> str:
    """Escape unpaired JSON surrogates so text reports remain valid UTF-8."""
    return text.encode("utf-8", errors="backslashreplace").decode("utf-8")


def _location(row: int | None) -> str:
    return f"row {row}" if row is not None else "dataset"


def format_report(report: Report) -> str:
    """Render a report as plain text."""
    lines = [f"tabulint: {report.path}", f"  records: {report.row_count}"]

    if report.profiles:
        lines.append("  fields:")
        width = max(len(_safe_text(p.name)) for p in report.profiles)
        for profile in report.profiles:
            note = f" ({profile.missing_count} missing)" if profile.missing_count else ""
            lines.append(f"    {_safe_text(profile.name).ljust(width)}  {profile.dominant_type}{note}")
    elif report.field_names:
        lines.append("  fields:")
        lines.extend(f"    {_safe_text(name)}" for name in report.field_names)

    missing_profiles = sorted(
        (profile for profile in report.profiles if profile.missing_count),
        key=lambda profile: (-profile.missing_count, profile.name),
    )
    if missing_profiles:
        lines.append("  missing values:")
        for profile in missing_profiles:
            percentage = profile.missing_count / report.row_count if report.row_count else 0
            lines.append(
                f"    {profile.name}: {profile.missing_count} missing ({percentage:.0%})"
            )

    if report.ok:
        lines.append("  no issues found")
        return _safe_text("\n".join(lines))

    lines.append(f"  issues: {len(report.issues)}")
    shown = sorted(report.issues, key=lambda i: (i.row or 0, i.code))[:MAX_ISSUES_SHOWN]
    for issue in shown:
        lines.append(f"    [{issue.severity}] {_location(issue.row)}: {issue.code}: {issue.message}")
    hidden = len(report.issues) - len(shown)
    if hidden > 0:
        lines.append(f"    ... and {hidden} more")

    lines.append(f"  summary: {report.error_count} error(s), {report.warning_count} warning(s)")
    return _safe_text("\n".join(lines))


def format_report_json(report: Report) -> str:
    """Render a report as machine-readable JSON."""
    document = {
        "path": report.path,
        "row_count": report.row_count,
        "profiles": [
            {
                "name": profile.name,
                "dominant_type": profile.dominant_type,
                "missing_count": profile.missing_count,
            }
            for profile in report.profiles
        ],
        "issues": [
            {
                "code": issue.code,
                "severity": issue.severity,
                "message": issue.message,
                "field": issue.field_name,
                "row": issue.row,
            }
            for issue in report.issues
        ],
        "error_count": report.error_count,
        "warning_count": report.warning_count,
        "ok": report.ok,
    }
    return json.dumps(document, indent=2)
