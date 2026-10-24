"""Command-line interface for tabulint."""

import argparse
import sys
from pathlib import Path
from typing import TextIO

from . import __version__, check_file
from .models import TabulintError
from .report import format_report, format_report_json
from .validators import build_length_rules, build_numeric_rules

EXIT_OK = 0
EXIT_ISSUES = 1
EXIT_ERROR = 2


def _print_console(text: str, *, stream: TextIO, end: str = "\n") -> None:
    """Keep reports and errors readable on terminals with limited encodings."""
    encoding = stream.encoding or "utf-8"
    printable = text.encode(encoding, errors="backslashreplace").decode(encoding)
    print(printable, file=stream, end=end)


def _issue_exit_code(report, fail_on: str) -> int:
    if fail_on == "never":
        return EXIT_OK
    if fail_on == "error":
        return EXIT_ISSUES if report.error_count else EXIT_OK
    return EXIT_OK if report.ok else EXIT_ISSUES


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tabulint",
        description="Check CSV, JSON, and JSON Lines datasets for common data-quality problems.",
    )
    parser.add_argument("path", help="path to a .csv, .json, .jsonl, or .ndjson dataset")
    parser.add_argument(
        "--required",
        action="append",
        metavar="FIELD",
        help="require FIELD to be present and non-empty in every record (repeatable)",
    )
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
        "--min-length", dest="minimum_lengths", action="append", metavar="FIELD=N",
        help="require FIELD to have at least N characters (repeatable)",
    )
    parser.add_argument(
        "--max-length", dest="maximum_lengths", action="append", metavar="FIELD=N",
        help="require FIELD to have at most N characters (repeatable)",
    )
    parser.add_argument(
        "--output",
        "-o",
        metavar="PATH",
        help="write the report to PATH as UTF-8, overwriting an existing file",
    )
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="accept datasets with no records and suppress the empty-dataset warning",
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
        "--encoding",
        metavar="NAME",
        default="utf-8",
        help="input file encoding (default: utf-8); use utf-8-sig to strip a UTF-8 BOM",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="report format for stdout and --output (default: text)",
    )
    parser.add_argument(
        "--fail-on",
        choices=("error", "warning", "never"),
        default="warning",
        help="exit 1 for errors, any issues, or never (default: warning)",
    )
    parser.add_argument("--version", action="version", version=f"tabulint {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and return an exit code."""
    args = build_parser().parse_args(argv)
    delimiter = "\t" if args.delimiter == r"\t" else args.delimiter
    try:
        rules = build_numeric_rules(args.minimums, args.maximums)
        length_rules = build_length_rules(args.minimum_lengths, args.maximum_lengths)
        report = check_file(
            args.path, rules, length_rules=length_rules, delimiter=delimiter,
            encoding=args.encoding, required_fields=args.required,
        )
    except TabulintError as exc:
        _print_console(f"tabulint: error: {exc}", stream=sys.stderr)
        return EXIT_ERROR

    if args.allow_empty:
        report.issues = [issue for issue in report.issues if issue.code != "empty-dataset"]

    formatter = format_report_json if args.format == "json" else format_report
    rendered = formatter(report) + "\n"

    if args.output is not None:
        try:
            output_path = Path(args.output)
            input_path = Path(args.path)
            if output_path.resolve() == input_path.resolve() or (
                output_path.exists() and output_path.samefile(input_path)
            ):
                raise ValueError("output path refers to the input dataset")
            with open(args.output, "w", encoding="utf-8", newline="\n") as output_file:
                output_file.write(rendered)
        except (OSError, ValueError, RuntimeError) as exc:
            _print_console(
                f"tabulint: error: could not write output file '{args.output}': {exc}",
                stream=sys.stderr,
            )
            return EXIT_ERROR

    if args.quiet:
        if not report.ok and args.format == "text":
            _print_console(
                f"{report.path}: {report.error_count} error(s), {report.warning_count} warning(s)",
                stream=sys.stdout,
            )
    else:
        _print_console(rendered, stream=sys.stdout, end="")

    return _issue_exit_code(report, args.fail_on)


if __name__ == "__main__":
    raise SystemExit(main())
