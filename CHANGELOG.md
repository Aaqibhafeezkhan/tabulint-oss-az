# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- Reject duplicate CSV header names before reading records instead of silently dropping earlier column values.
- Infer nonfinite values as strings and accept integer values in dominant-float fields without noisy type-mismatch errors.
- Reject directories and device/special input files before reading, with readable errors for symlink loops and access failures.
- Verify CSV line endings, native paths, and legacy console encodings on Windows and Ubuntu in CI.
- Distinguish absent fields from nulls when finding duplicates and compare nested objects independently of key order.
- Prevent report output from overwriting the input dataset, escape unpaired Unicode surrogates, and support terminals with limited encodings.
- Report invalid input paths, non-text codecs, and missing encoding BOMs as readable errors with CLI exit code 2.
- Preserve integer precision in numeric rules, report nonfinite data as `not-numeric`, and validate directly constructed `NumericRule` bounds.
- Reject duplicate JSON object keys, including nested keys, instead of silently overwriting values; JSONL/NDJSON errors include the physical line number.
- Reject NaN and infinity values in `--min` and `--max` numeric bounds.

### Added

- Add repeatable `--min-length` and `--max-length` options and Python length rules
  to validate character counts while skipping missing values.
- Add repeatable `--required FIELD` and Python `required_fields` checks to report
  absent or empty required values as errors while preserving existing warnings.
- Add `--fail-on {error,warning,never}` to control whether warnings fail the
    command while keeping load and output failures at exit code 2.
- Added a per-field missing-value summary to text reports, including counts and percentages.
- Added `--output` and `-o` CLI options for UTF-8 report file output.
- Added `--quiet` and `-q` CLI options for summary-only stdout output.
- Added configurable CSV delimiters through the Python API and `--delimiter` CLI option.
- Added `--format {text,json}` and `format_report_json` for machine-readable JSON report output.
- Added JSON Lines / NDJSON loading through `.jsonl` and `.ndjson` file extensions.
- Added configurable input encoding through the Python API and `--encoding` CLI option for CSV, JSON, JSONL, and NDJSON input.

### Changed

- Report JSON syntax errors with line, column, and a bounded excerpt; report CSV ragged-row field counts and a delimiter hint.
- Improved boolean type inference to recognize `true`, `false`, `yes`, `no`, `y`, `n`, `t`, and `f` case-insensitively after stripping whitespace.
- Reject unterminated CSV quoting with `TabulintError` instead of accepting malformed records.
- Grouped duplicate-record reporting so each duplicated record produces one issue naming every repeated row, instead of one issue per repeat.

## [0.1.0] - 2026-09-14

Initial release.

### Added

- CSV loading (UTF-8, comma-delimited, header row required).
- JSON loading for a single array of objects.
- Field type inference: `integer`, `float`, `boolean`, `string`, `null`.
- Missing-value and absent-field detection.
- Duplicate-record detection.
- Detection of values inconsistent with a field's dominant inferred type.
- Numeric `--min` and `--max` validation.
- Empty-dataset detection.
- Plain-text terminal report.
- `tabulint` CLI with exit codes `0` (clean), `1` (issues found), `2` (error).
- Python API: `check_file`, `check_records`, `format_report`, `build_numeric_rules`,
  `load_csv`, `load_json`, `load_dataset`, `analyze`, `profile_fields`, `infer_type`.

[Unreleased]: https://github.com/ismayilzeynal/tabulint-oss-az/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/ismayilzeynal/tabulint-oss-az/releases/tag/v0.1.0
