# tabulint

A lightweight open-source CLI and Python library for practical CSV/JSON data-quality checks.

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

# Require a numeric field to stay within a range
tabulint data/people.csv --min age=0 --max age=120

# Bounds are repeatable and independent
tabulint data/scores.csv --min score=0 --max score=100 --max attempts=3

# Write the report to a UTF-8 file while also printing it to stdout
tabulint data/people.csv --output report.txt

# The short output flag is equivalent
tabulint data/people.csv -o report.txt

# Suppress normal output and report only a summary when issues are found
tabulint data/people.csv --quiet

# The short quiet flag is equivalent
tabulint data/people.csv -q

# Version
tabulint --version
```

The `--output` / `-o` option overwrites an existing file rather than appending,
and does not create missing parent directories. Reports are written with
explicit UTF-8 encoding and Unix-style `\n` line endings. The report is also
printed to stdout. A write failure is reported on stderr and exits with code 2.

The `--quiet` / `-q` option controls stdout only. When issues are found, it
prints one summary line containing the input path and error/warning counts;
when the dataset is clean, it prints nothing. When `--quiet` and `--output`
are used together, the complete report is still written to the output file
while only the quiet summary is printed to stdout.

## Python API

```python
from tabulint import build_numeric_rules, check_file, format_report

rules = build_numeric_rules(minimums=["age=0"], maximums=["age=120"])
report = check_file("people.csv", rules)

print(report.row_count, report.error_count, report.warning_count)
for issue in report.issues:
    print(issue.row, issue.code, issue.message)

print(format_report(report))
```

Working with records you already have in memory:

```python
from tabulint import check_records

report = check_records([{"name": "Ada", "age": 36}, {"name": "Ada", "age": 36}])
assert not report.ok
```

Main public names: `check_file`, `check_records`, `format_report`,
`build_numeric_rules`, `check_numeric_rules`, `load_csv`, `load_json`,
`load_dataset`, `analyze`, `profile_fields`, `infer_type`, and the
`Report`, `Issue`, `FieldProfile`, `NumericRule`, `TabulintError` types.

## Supported formats

| Format | Notes |
| --- | --- |
| `.csv` | UTF-8, comma-delimited, first row is the header |
| `.json` | A single JSON array of objects |

The reader is chosen from the file extension.

## Checks

| Code | Severity | Meaning |
| --- | --- | --- |
| `missing-value` | warning | A field is present but empty or null |
| `missing-field` | error | A record does not contain a field other records have |
| `duplicate-record` | warning | A record is identical to an earlier record |
| `type-mismatch` | error | A value does not match the field's dominant inferred type |
| `below-minimum` | error | A value is below a `--min` bound |
| `above-maximum` | error | A value is above a `--max` bound |
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

A successful report write does not change the data-quality exit code. For
example, a dataset with issues still exits with code 1 when `--output` is used.

This makes `tabulint` usable as a CI gate:

```bash
tabulint data/people.csv --min age=0 || exit 1
```

## Contributing

Contributions are welcome. Start with [CONTRIBUTING.md](CONTRIBUTING.md) for the
fork-and-pull-request workflow, then pick an open issue. The planned work is
listed in [CONTRIBUTOR_TASKS.md](CONTRIBUTOR_TASKS.md), and
[ISSUE_MAP.md](ISSUE_MAP.md) maps each task ID to its GitHub issue.

## Limitations

These are the known boundaries of the current release, not bugs:

- Only `.csv` and `.json` are supported. JSON Lines / NDJSON is not.
- CSV is read as UTF-8 with a comma delimiter; neither is configurable yet.
- Datasets are loaded fully into memory, so very large files are limited by RAM.
- Only numeric `min`/`max` validation is available; no string-length,
  allowed-values, or required-field rules yet.
- Report output is plain text only; machine-readable formats are not available yet.
- Type inference is deliberately simple and has no date/time or currency
  awareness.
