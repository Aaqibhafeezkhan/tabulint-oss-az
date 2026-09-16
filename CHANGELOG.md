# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Added `--output` and `-o` CLI options for UTF-8 report file output.
- Added `--quiet` and `-q` CLI options for summary-only stdout output.
- Added JSON Lines / NDJSON loading through `.jsonl` and `.ndjson` file extensions.

### Changed

- Improved boolean type inference to recognize `true`, `false`, `yes`, `no`, `y`, `n`, `t`, and `f` case-insensitively after stripping whitespace.

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
- Python API: `check_file`, `check_records`, `format_report`,
  `build_numeric_rules`, `load_csv`, `load_json`, `load_dataset`, `analyze`,
  `profile_fields`, `infer_type`.

[Unreleased]: https://github.com/ismayilzeynal/tabulint-oss-az/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/ismayilzeynal/tabulint-oss-az/releases/tag/v0.1.0
