# tabulint

[![CI](https://github.com/ismayilzeynal/tabulint-oss-az/actions/workflows/ci.yml/badge.svg)](https://github.com/ismayilzeynal/tabulint-oss-az/actions/workflows/ci.yml)

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
tabulint examples/missing.csv
```

```
tabulint: examples/missing.csv
  records: 3
  fields:
    item_id  string
    age      integer (1 missing)
  missing values:
    age: 1 missing (33%)
  issues: 1
    [warning] row 2: missing-value: field 'age' has a missing value
  summary: 0 error(s), 1 warning(s)
```

The command exits with code 1 because it found a data-quality issue. See
[all example datasets](examples/README.md) for clean and problematic inputs.

## CLI examples

```bash
# Check a CSV file
tabulint examples/clean.csv

# Check a JSON array of objects
tabulint examples/clean.json

# Check a JSON Lines file
tabulint examples/clean.jsonl

# JSON Lines also supports the .ndjson extension
tabulint examples/clean.ndjson

# Emit a machine-readable JSON report
tabulint examples/clean.csv --format json

# Require fields to be present and non-empty in every record
tabulint examples/clean.csv --required item_id --required age

# Require a numeric field to stay within a range
tabulint examples/clean.csv --min age=0 --max age=120

# Bounds are repeatable and independent
tabulint examples/clean.csv --min score=0 --max score=100 --max attempts=3

# Require a stringified value to be between 2 and 12 characters
tabulint examples/clean.csv --min-length item_id=2 --max-length item_id=12

# Restrict a field to exact allowed values
tabulint data.csv --allowed status=active,inactive --allowed tier=free,pro

# Set the CSV delimiter explicitly
tabulint examples/clean.csv --delimiter ","

# Write the report to a UTF-8 file while also printing it to stdout
tabulint examples/clean.csv --output report.txt

# The short output flag is equivalent
tabulint examples/clean.csv -o report.txt

# Suppress normal output and report only a summary when issues are found
tabulint examples/missing.csv --quiet

# JSON output stays clean when quiet mode is enabled
tabulint examples/missing.csv --quiet --format json

# The short quiet flag is equivalent
tabulint examples/missing.csv -q

# Version
tabulint --version
```

`--allowed FIELD=a,b,c` is repeatable. Values are compared as case-sensitive
strings without trimming whitespace. Missing values and absent fields are
skipped; use `--required` to require their presence. Field names are stripped,
and the last option for a repeated field replaces its earlier allowed set.
Empty sets or blank entries are errors (exit 2). Commas always separate values
in the CLI; quoting or escaping cannot include a comma in a value. Use Python's
`AllowedValuesRule` for values containing commas.

Bounds must be finite numbers. Values such as `nan`, `inf`, and `-inf` are rejected.
Integer bounds and integer values are compared without rounding, including
integers larger than a floating-point number can represent exactly. Decimal
and exponent notation uses Python floating-point numbers. When a numeric rule
is applied, nonfinite data values produce a `not-numeric` error.
Python's integer-string conversion limit still applies: over-limit integer
bounds are rejected and over-limit integer data is reported as `not-numeric`,
instead of being rounded through floating-point conversion.

`--required FIELD` is repeatable. Names match exactly, including case and
whitespace; repeated names are checked once in first-requested order. A missing
key, `None`, empty string, or whitespace-only string produces a `required-missing`
error. `0` and `False` count as present. For nonempty datasets, a required field
absent from every record produces one dataset-level error with no row; otherwise
each missing required value is reported at its one-based record row.

Existing `missing-value` warnings and `missing-field` errors remain, so a required
field can produce both its existing finding and a `required-missing` error.
Zero-row inputs, including header-only CSVs, keep only the existing `empty-dataset`
warning. Without `--required`, checks are unchanged. Required errors exit 1 by
default; `--fail-on never` still reports them but exits 0 after successful loading
and report output. Load and output failures continue to exit 2.

The `--delimiter` option applies to CSV input and accepts exactly one character.
Use `\t` for a tab. The option is ignored for JSON input. An empty or
multi-character delimiter is rejected with exit code 2.
Malformed CSV quoting, including unterminated quoted fields, also exits with code 2.
An overlong CSV row reports its physical line and the actual and expected field
counts, with a reminder to check `--delimiter`. A valid single-column CSV still
loads normally.

Malformed JSON, JSONL, and NDJSON input exits with code 2 and reports the line,
column, and a short excerpt near the error. The excerpt is bounded even when the
input line is very long. JSONL and NDJSON line numbers count blank lines.

JSON, JSONL, and NDJSON input rejects duplicate keys within any object, including
nested objects. Keys are compared after decoding JSON escapes, so `"x"` and
`"\u0078"` are the same key. The Python readers raise `TabulintError`, and the CLI
exits with code 2, naming the file and duplicate key. JSONL/NDJSON errors also name
the physical line number, counting blank lines. Reusing a key in separate objects
or records remains valid.

The `--encoding` option applies to CSV, JSON, JSONL, and NDJSON input and
defaults to `utf-8`. Encoding names are resolved by Python's standard codec
registry, so aliases such as `latin-1` are accepted. An unknown encoding name
exits with code 2 and a readable error. Decode failures name both the input file
and the encoding that was attempted. Use `utf-8-sig` when reading UTF-8 files
with a byte-order mark; this strips the BOM before parsing so it does not become
part of the first field name.
Only text encodings are supported; codecs such as `hex` are rejected. A missing
BOM for an encoding that requires one is also reported as a decode failure.
Input paths containing a NUL character are rejected with exit code 2.

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
The output path must differ from the input dataset, including symbolic-link
and hard-link aliases; otherwise the command exits 2 and preserves the input.
Invalid output paths are also reported with exit code 2.

Text reports escape unpaired Unicode surrogates from JSON so the report remains
valid UTF-8. On terminals with limited encodings, unsupported characters are
printed as backslash escapes; output files still use UTF-8. JSON reports retain
their normal JSON escaping.

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
report = check_file("examples/clean.csv", rules)

print(report.row_count, report.error_count, report.warning_count)
for issue in report.issues:
    print(issue.row, issue.code, issue.message)

print(format_report(report))
print(format_report_json(report))
```

To select an input encoding in the Python API, pass it to `check_file`, for
example `check_file("examples/clean.csv", rules, encoding="cp1252")`.

To require fields, pass keyword-only `required_fields`, for example
`check_file("examples/clean.csv", rules, required_fields=["item_id"])` or
`check_records([{"name": "Ada"}], required_fields=["name"])`. The public
`check_required_fields(records, names)` helper returns only the required-field
issues; the complete check functions preserve all existing checks.

Working with records you already have in memory:

```python
from tabulint import check_records

report = check_records([{"name": "Ada", "age": 36}, {"name": "Ada", "age": 36}])
assert not report.ok
```

`NumericRule` also validates bounds when constructed directly: bounds must be
finite numbers, and a minimum cannot exceed its maximum. Invalid rules raise
`TabulintError`.

In-memory records must not contain cyclic dictionaries or lists; these raise
`TabulintError` during duplicate detection.

See the [Python API reference](docs/api.md) for every public name, signatures,
return values, exceptions, result fields, and a worked pipeline example.

## Supported formats

CSV header names must be nonempty and unique. Duplicate names are rejected
before data rows are read, with the file path and duplicate name in the error;
the CLI exits 2. Names match exactly, including case and whitespace, and this
check also applies to header-only files and custom delimiters.

Input must be a regular file. Symbolic links to readable regular files work;
directories, devices, special files, and symlink loops produce a readable error
and CLI exit code 2. Path errors display the supplied path without resolving it
to an absolute path.

| Format | Notes |
| --- | --- |
| `.csv` | UTF-8 by default, configurable encoding and delimiter, first row is the header |
| `.json` | A single JSON array of objects; configurable encoding; the CSV delimiter option is ignored |
| `.jsonl` | One JSON object per line; configurable encoding; blank lines are skipped |
| `.ndjson` | Alias for `.jsonl` with the same encoding behavior |

The reader is chosen from the file extension.

## Checks

Nonfinite numbers and numeric strings such as `NaN`, `inf`, and `infinity`
(including signed and mixed-case forms) infer as `string`. Numeric validation
still rejects them as `not-numeric`. Leading signs and valid underscore
separators are supported: `+5` and `1_000` infer as integers. Integers are
compatible with a dominant `float` field; floats in a dominant `integer` field
remain mismatches, including whole-valued floats such as `3.0`. Dominant types
use the most frequent type with first appearance breaking ties, and profile
counts retain the original integer/float distinction.

| Code | Severity | Meaning |
| --- | --- | --- |
| `missing-value` | warning | A field is present but empty or null |
| `missing-field` | error | A record does not contain a field other records have |
| `required-missing` | error | A requested required field is absent or has a missing value |
| `duplicate-record` | warning | A group of identical records, reported once |
| `type-mismatch` | error | A value does not match the field's dominant inferred type |
| `below-minimum` | error | A value is below a `--min` bound |
| `above-maximum` | error | A value is above an `--max` bound |
| `below-min-length` | error | A value is shorter than a `--min-length` bound |
| `above-max-length` | error | A value is longer than a `--max-length` bound |
| `not-allowed` | error | A value is outside a field's `--allowed` set |
| `not-numeric` | error | A `--min`/`--max` bound was given for a non-numeric value |
| `empty-dataset` | warning | The dataset contains no records |

Each `duplicate-record` warning names the first occurrence and up to 10
repeated row numbers. Larger groups end with an `and N more` count. The issue's
row number is the first repeated row.
An absent field is distinct from a field explicitly set to `null`. Object key
order does not affect duplicate detection, including for nested objects; array
order and value types remain significant.

Inferred types are `integer`, `float`, `boolean`, `string`, and `null`. Strings
are parsed, so the CSV text `12` and the JSON number `12` both infer as
`integer`. Boolean strings are recognized case-insensitively after stripping
whitespace: `true`, `false`, `yes`, `no`, `y`, `n`, `t`, and `f`.

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Dataset loaded and no issue meets the selected `--fail-on` threshold |
| `1` | Dataset loaded and at least one issue meets the selected `--fail-on` threshold |
| `2` | The dataset could not be loaded, the arguments were invalid, or the report could not be written |

See [Exit-code contract](docs/exit-codes.md) for the complete behavior. In
brief, exit codes are identical for text and JSON output, and `--fail-on`
controls which loaded datasets fail:

- `--fail-on warning` is the default and exits 1 when any issue is found.
- `--fail-on error` exits 1 only when at least one error is found; warning-only
  datasets exit 0.
- `--fail-on never` exits 0 whenever the dataset loads, while still printing
  the report.

Load, argument, and report-write failures always exit 2, regardless of
`--fail-on`.

This makes `tabulint` usable as a CI gate:

```bash
tabulint examples/clean.csv --min age=0 || exit 1
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
- Numeric `min`/`max`, string-length, required-field, and allowed-values validation are available.
- JSON output is intended for machine consumption; CSV, SARIF, JUnit, and file-specific report formats are not available yet.
- Type inference is deliberately simple and has no date/time or currency
  awareness.
