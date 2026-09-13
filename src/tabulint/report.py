"""Rendering a Report as plain text for the terminal."""

from .models import Report

MAX_ISSUES_SHOWN = 50


def _location(row: int | None) -> str:
    return f"row {row}" if row is not None else "dataset"


def format_report(report: Report) -> str:
    """Render a report as plain text."""
    lines = [f"tabulint: {report.path}", f"  records: {report.row_count}"]

    if report.profiles:
        lines.append("  fields:")
        width = max(len(p.name) for p in report.profiles)
        for profile in report.profiles:
            note = f" ({profile.missing_count} missing)" if profile.missing_count else ""
            lines.append(f"    {profile.name.ljust(width)}  {profile.dominant_type}{note}")

    if report.ok:
        lines.append("  no issues found")
        return "\n".join(lines)

    lines.append(f"  issues: {len(report.issues)}")
    shown = sorted(report.issues, key=lambda i: (i.row or 0, i.code))[:MAX_ISSUES_SHOWN]
    for issue in shown:
        lines.append(f"    [{issue.severity}] {_location(issue.row)}: {issue.code}: {issue.message}")
    hidden = len(report.issues) - len(shown)
    if hidden > 0:
        lines.append(f"    ... and {hidden} more")

    lines.append(f"  summary: {report.error_count} error(s), {report.warning_count} warning(s)")
    return "\n".join(lines)
