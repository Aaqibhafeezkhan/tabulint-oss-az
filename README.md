# tabulint

A lightweight open-source CLI and Python library for practical CSV, JSON, and JSON Lines data-quality checks.

`tabulint` loads a dataset, infers what each field looks like, and reports the
problems that actually bite in practice: missing values, duplicate records,
values that do not match the rest of their column, and numbers outside the range
you expect. No configuration files, no runtime dependencies, no database.

## Install

Requires Python 3.11 or newer.

```bash
pip install .
```

Development install (editable, with the test dependencies):

```bash
git clone https://github.com/ismayilzeynal/tabulint-oss-az.git
cd tabulint-oss-az
python -m pip install -e ".[dev]"
python -m pytest
```

## Quickstart

```bash
tabulint people.csv
```

```
tabulint: people.csv
  records: 4
  fields:
    name  string
    age   integer (1 missing)
  issues: 2
    [warning] row 3: missing-value: field 'age' has a missing value
    [error] row 4: type-mismatch: field 'age' expects integer but value 'old' looks like string
  summary: 1 error(s), 1 warning(s)
```

## CLI examples

```bash
# Check a CSV file
tabulint data/people.csv

# Check a JSON array of objects
tabulint data/people.json

# Check a JSON Lines file
tabulint data/events.jsonl

# JSON Lines also supports the .ndjson extension
tabulint data/events.ndjson

# Emit a machine-readable JSON report
tabulint data/people.csv --format json

# Require a numeric field to stay within a range
tabulint data/people.csv --min age=0 --max age=120

# Bounds are repeatable and independent
tabulint data/scores.csv --min score=0 --max score=100 --max attempts=3

# Use a semicolon-delimited CSV
tabulint data/people.csv --delimiter ";"

# Use the readable tab spelling for a tab-delimited CSV
tabulint data/people.csv --delimiter "\t"

# Write the report to a UTF-8 file while also printing it to stdout
tabulint data/people.csv --output report.txt

# The short output flag is equivalent
tabulint data/people.csv -o report.txt

# Suppress normal output and report only a summary when issues are found
tabulint data/people.csv --quiet

# JSON output stays clean when quiet mode is enabled
tabulint data/people.csv --quiet --format json

# The short quiet flag is equivalent
tabulint data/people.csv -q

# Version
tabulint --version
```

Bounds must be finite numbers. Values such as `nan`, `inf`, and `-inf` are rejected.

The `--delimiter` option applies to CSV input and accepts exactly one character.
Use `\t` for a tab. The option is ignored for JSON input. An empty or
multi-character delimiter is rejected with exit code 2.
Malformed CSV quoting, including unterminated quoted fields, also exits with code 2.

The `--encoding` option applies to CSV, JSON, JSONL, and NDJSON input and
defaults to `utf-8`. Encoding names are resolved by Python's standard codec
registry, so aliases such as `latin-1` are accepted. An unknown encoding name
exits with code 2 and a readable error. Decode failures name both the input file
and the encoding that was attempted. Use `utf-8-sig` when reading UTF-8 files
with a byte-order mark; this strips the BOM before parsing so it does not become
part of the first field name.

The `--format` option chooses the report representation: `text` is the default,
and `json` emits a pretty-printed JSON document. JSON stdout contains only the
JSON document, with no summary line mixed in. With `--quiet --format json`,
stdout is empty when issues are found; the exit code and any `--output` file
still carry the result.

The JSON report has a stable top-level shape containing the input path, record
count, field profiles, every issue, error/warning counts, and the `ok` flag. Each
profile contains `name`, `dominant_type`, and `missing_count`. Each issue
contains `code`, `severity`, `message`, `field`, and `row`.

For example:

```json
{
  "path": "people.csv",
  "row_count": 2,
  "profiles": [
    {"name": "age", "dominant_type": "integer", "missing_count": 0}
  ],
  "issues": [
    {
      "code": "above-maximum",
      "severity": "error",
      "message": "field 'age' value 200 is above maximum 120",
      "field": "age",
      "row": 2
    }
  ],
  "error_count": 1,
  "warning_count": 0,
  "ok": false
}
```

The `--output` / `-o` option overwrites an existing file rather than appending,
and does not create missing parent directories. Reports are written with
explicit UTF-8 encoding and Unix-style `\n` line endings. The report is also
printed to stdout. A write failure is reported on stderr and exits with code 2.

The `--quiet` / `-q` option controls stdout only. When issues are found with the
default text format, it prints one summary line containing the input path and
error/warning counts; when the dataset is clean, it prints nothing. When
`--quiet` and `--output` are used together, the complete report is still written
to the output file while only the quiet summary is printed to stdout. With JSON
format, quiet mode leaves stdout empty so the JSON contract remains intact.

## Python API

```python
from tabulint import build_numeric_rules, check_file, format_report, format_report_json

rules = build_numeric_rules(minimums=["age=0"], maximums=["age=120"])
report = check_file("people.csv", rules)

print(report.row_count, report.error_count, report.warning_count)
for issue in report.issues:
    print(issue.row, issue.code, issue.message)

print(format_report(report))
print(format_report_json(report))
```

For a non-UTF-8 file, pass an encoding to the Python API, for example
`check_file("people.csv", rules, encoding="cp1252")`.

Working with records you already have in memory:

```python
from tabulint import check_records

report = check_records([{"name": "Ada", "age": 36}, {"name": "Ada", "age": 36}])
assert not report.ok
```

Main public names: `check_file`, `check_records`, `format_report`,
`format_report_json`, `build_numeric_rules`, `check_numeric_rules`, `load_csv`,
`load_json`, `load_jsonl`, `load_dataset`, `analyze`, `profile_fields`,
`infer_type`, and the
`Report`, `Issue`, `FieldProfile`, `NumericRule`, `TabulintError` types.

## Supported formats

| Format | Notes |
| --- | --- |
| `.csv` | UTF-8 by default, configurable encoding and delimiter, first row is the header |
| `.json` | A single JSON array of objects; configurable encoding; the CSV delimiter option is ignored |
| `.jsonl` | One JSON object per line; configurable encoding; blank lines are skipped |
| `.ndjson` | Alias for `.jsonl` with the same encoding behavior |

The reader is chosen from the file extension.

## Checks

| Code | Severity | Meaning |
| --- | --- | --- |
| `missing-value` | warning | A field is present but empty or null |
| `missing-field` | error | A record does not contain a field other records have |
| `duplicate-record` | warning | A record is identical to an earlier record |
| `type-mismatch` | error | A value does not match the field's dominant inferred type |
| `below-minimum` | error | A value is below a `--min` bound |
| `above-maximum` | error | A value is above an `--max` bound |
| `not-numeric` | error | A `--min`/`--max` bound was given for a non-numeric value |
| `empty-dataset` | warning | The dataset contains no records |

Inferred types are `integer`, `float`, `boolean`, `string`, and `null`. Strings
are parsed, so the CSV text `12` and the JSON number `12` both infer as
`integer`. Boolean strings are recognized case-insensitively after stripping
whitespace: `true`, `false`, `yes`, `no`, `y`, `n`, `t`, and `f`.

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Dataset loaded and no issues found |
| `1` | Dataset loaded and at least one issue was found |
| `2` | The dataset could not be loaded, the arguments were invalid, or the report could not be written |

Exit codes are identical for text and JSON output. A successful report write
does not change the data-quality exit code. For example, a dataset with issues
still exits with code 1 when `--output` is used.

This makes `tabulint` usable as a CI gate:

```bash
tabulint data/people.csv --min age=0 || exit 1
```

## Contributing

Contributions are welcome. To get started:

1. Pick an [open issue](https://github.com/ismayilzeynal/tabulint-oss-az/issues),
   or browse issues marked [`good first issue`](https://github.com/ismayilzeynal/tabulint-oss-az/labels/good%20first%20issue).
   Check the discussion and linked pull requests before starting, then comment
   to say what you plan to work on.
2. Follow [CONTRIBUTING.md](CONTRIBUTING.md) to fork the repository, run the
   tests, and open a focused pull request. Mention the issue in the PR.

The issue tracker shows what is currently available. The more detailed
[contributor task descriptions](CONTRIBUTOR_TASKS.md) are useful background for
issues that have a task ID.

## Limitations

These are the known boundaries of the current release, not bugs:

- CSV is read as UTF-8 by default with configurable encoding and delimiter; automatic delimiter sniffing is not available.
- Datasets are loaded fully into memory, so very large files are limited by RAM.
- Only numeric `min`/`max` validation is available; no string-length,
  allowed-values, or required-field rules yet.
- JSON output is intended for machine consumption; CSV, SARIF, JUnit, and file-specific report formats are not available yet.
- Type inference is deliberately simple and has no date/time or currency
  awareness.
