"""Command-line interface for tabulint."""

import argparse
import sys

from . import __version__, check_file
from .models import TabulintError
from .report import format_report, format_report_json
from .validators import build_numeric_rules

EXIT_OK = 0
EXIT_ISSUES = 1
EXIT_ERROR = 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tabulint",
        description="Check CSV, JSON, and JSON Lines datasets for common data-quality problems.",
    )
    parser.add_argument("path", help="path to a .csv, .json, .jsonl, or .ndjson dataset")
    parser.add_argument(
        "--min",
        dest="minimums",
        action="append",
        metavar="FIELD=NUMBER",
        help="require FIELD to be at least NUMBER (repeatable)",
    )
    parser.add_argument(
        "--max",
        dest="maximums",
        action="append",
        metavar="FIELD=NUMBER",
        help="require FIELD to be at most NUMBER (repeatable)",
    )
    parser.add_argument(
        "--output",
        "-o",
        metavar="PATH",
        help="write the report to PATH as UTF-8, overwriting an existing file",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="suppress normal output and print only a summary when issues are found",
    )
    parser.add_argument(
        "--delimiter",
        metavar="CHAR",
        default=",",
        help="CSV delimiter character; use \\t for a tab",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="report format for stdout and --output (default: text)",
    )
    parser.add_argument("--version", action="version", version=f"tabulint {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and return an exit code."""
    args = build_parser().parse_args(argv)
    delimiter = "\t" if args.delimiter == r"\t" else args.delimiter
    try:
        rules = build_numeric_rules(args.minimums, args.maximums)
        report = check_file(args.path, rules, delimiter=delimiter)
    except TabulintError as exc:
        print(f"tabulint: error: {exc}", file=sys.stderr)
        return EXIT_ERROR

    formatter = format_report_json if args.format == "json" else format_report
    rendered = formatter(report) + "\n"

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8", newline="\n") as output_file:
                output_file.write(rendered)
        except OSError as exc:
            print(f"tabulint: error: could not write output file '{args.output}': {exc}", file=sys.stderr)
            return EXIT_ERROR

    if args.quiet:
        if not report.ok and args.format == "text":
            print(f"{report.path}: {report.error_count} error(s), {report.warning_count} warning(s)")
    else:
        print(rendered, end="")

    return EXIT_OK if report.ok else EXIT_ISSUES


if __name__ == "__main__":
    raise SystemExit(main())
