# Python API reference

Import the names below from `tabulint`. They are the complete public API listed
in `tabulint.__all__`; other module helpers are implementation details.
This reference describes the current pre-1.0 API. Public does not yet mean
unchanging: breaking changes and new features increment the minor version,
while compatible fixes increment the patch version. See the
[version policy](../RELEASING.md#version-policy) and review the changelog when
upgrading. Human-readable messages may change; use issue codes and severities
when making programmatic decisions.

Signatures use `Path` from `pathlib`. A `*` marks keyword-only arguments.
`<factory>` means a fresh empty list or dictionary is created for each instance.
Annotations describe supported inputs; `NumericRule` and `LengthRule` validate their bounds
at runtime. Unless an entry names a `TabulintError`, it has no intentional
domain-error exception for supported inputs. Ordinary Python exceptions from
invalid argument types, custom objects, or resource limits can still propagate.

## Checking datasets

### `check_file`

```text
check_file(path: str | Path, rules: list[NumericRule] | None = None,
           length_rules: list[LengthRule] | None = None, *,
           delimiter: str = ",", encoding: str = "utf-8",
           required_fields: list[str] | None = None) -> Report
```

Loads a file with `load_dataset`, then returns the same complete report as
`check_records`. The report's path is `str(path)`. `delimiter` applies only to
CSV; `encoding` applies to every supported format. The whole dataset is loaded
into memory. Raises `TabulintError` for the loading failures described below.
Data-quality findings become issues in the returned report, not exceptions.
`length_rules` applies optional character-length bounds; `required_fields` applies the optional presence checks described below.

### `check_records`

```text
check_records(records: list[Record], rules: list[NumericRule] | None = None,
              path: str = "<records>",
              *, length_rules: list[LengthRule] | None = None,
              required_fields: list[str] | None = None) -> Report
```

Returns structural issues, optional numeric-rule, length-rule, and required-field issues,
field profiles, and record counts. `path` is a display label; no file is opened. Fields are collected
in first-seen order across all records. An empty list produces one
`empty-dataset` warning. This is also the result for a header-only CSV passed to
`check_file`; headers are not retained when there are no records. Cyclic
dictionaries or lists raise `TabulintError` during duplicate detection. Supply
valid `NumericRule` objects, preferably from `build_numeric_rules`, and optional
`LengthRule` objects, preferably from `build_length_rules`.

`required_fields` defaults to `None` (no required-field checks); an empty list
also leaves behavior unchanged. Names follow `check_required_fields` semantics.
Required-field issues are appended after the existing checks without removing
`missing-value` warnings or `missing-field` errors. Zero-row inputs retain only
the existing empty-dataset warning even when fields are required.

### `analyze`

```text
analyze(records: list[Record]) -> list[Issue]
```

Returns missing-field/value, duplicate-record, and type-mismatch issues, in that
check order. It does not apply numeric or required-field rules, create profiles
for the caller, or add an empty-dataset warning; `analyze([])` returns `[]`.
Duplicates use typed structure: absent keys differ from explicit nulls, list
order matters, and object-key insertion order does not. Cyclic dictionaries or
lists raise `TabulintError`; shared containers without a cycle are accepted.

### `profile_fields`

```text
profile_fields(records: list[Record]) -> list[FieldProfile]
```

Returns one profile per field in first-seen order, or `[]` for no fields.
Absent keys and missing values both contribute to `missing_count`. Nulls are
excluded from `type_counts`; the dominant type is the most frequent nonmissing
type, with ties resolved by first appearance. An entirely missing field has
dominant type `"null"`. No intentional `TabulintError` is raised.

### `infer_type`

```text
infer_type(value: object) -> str
```

Returns `"null"`, `"boolean"`, `"integer"`, `"float"`, or `"string"`.
Missing values are null; booleans are checked before integers. Strings are
stripped, then checked for boolean words, integers, and floats in that order.
Boolean words are `true`, `false`, `yes`, `no`, `y`, `n`, `t`, and `f`, ignoring
case. Other objects, including lists and dictionaries, infer as `"string"`.
Nonfinite floats and numeric strings (NaN, infinity, or overflow to infinity)
infer as `"string"`. Leading signs and valid underscore separators are accepted,
including `"+5"` and `"1_000"`. Integers are compatible with a dominant `"float"`
field; a float in a dominant `"integer"` field remains a type mismatch, including
whole-valued floats such as `3.0`. Dominant types still use frequency and
first-appearance ties; this compatibility rule does not change profile counts.
This classifies values without converting them in the input records. No
intentional `TabulintError` is raised.

### `is_missing`

```text
is_missing(value: object) -> bool
```

Returns `True` for `None` and empty or whitespace-only strings, otherwise
`False`. In particular, `0`, `False`, empty lists, and empty dictionaries are
not missing. No intentional `TabulintError` is raised.

## Reading files

Readers return a new `list[Record]` and perform no data-quality checks.
Direct calls to `load_csv`, `load_json`, and `load_jsonl` ignore filename
extensions; only `load_dataset` and `check_file` dispatch by extension.
Readers accept regular files, including symbolic links to them. Directories,
devices, and special files are rejected before reading. They raise
`TabulintError` for these inputs, symlink loops, missing or unreadable files, NUL-containing paths,
unknown or invalid encoding names, non-text codecs, and Unicode decoding
failures (including a missing byte-order mark for an encoding that requires it).
Use a text encoding such as `utf-8`, `cp1252`, or `utf-8-sig`; the last strips a
UTF-8 byte-order mark.
Each reader also has the format-specific errors listed below.

### `load_dataset`

```text
load_dataset(path: str | Path, *, delimiter: str = ",",
             encoding: str = "utf-8") -> list[Record]
```

Chooses `load_csv`, `load_json`, or `load_jsonl` from the case-insensitive file
extension. `.ndjson` uses the JSON Lines reader. Returns that reader's records
and propagates its `TabulintError`; an unsupported or missing extension also
raises `TabulintError`. The delimiter is ignored for JSON and JSON Lines.

### `load_csv`

```text
load_csv(path: str | Path, *, delimiter: str = ",",
         encoding: str = "utf-8") -> list[Record]
```

Returns records whose keys come from the header and whose values are strings.
A row shorter than the header receives `None` for its trailing missing fields.
An empty or header-only file returns `[]`. Quoted multiline fields are supported.
Pass an actual tab character (`"\t"`) for tab-separated input; the CLI's literal
backslash-t shortcut is not interpreted by this function.

In addition to the common reader errors, raises `TabulintError` for an empty or
multi-character delimiter, an empty or duplicate header name, malformed quoting, or a row
with more fields than the header. Header names are not stripped or normalized.

### `load_json`

```text
load_json(path: str | Path, *, encoding: str = "utf-8") -> list[Record]
```

Returns records from a JSON array of objects, preserving decoded JSON values.
`[]` returns no records; an empty file is malformed JSON. Raises `TabulintError`
for invalid syntax, a non-array root, non-object array items, duplicate decoded
keys in any object (including nested objects), and parser nesting or integer
size limits, as well as the common reader errors. Syntax diagnostics include
line, column, and a bounded excerpt. Array-item diagnostics use zero-based
indexes; these are different from `Issue.row`.

### `load_jsonl`

```text
load_jsonl(path: str | Path, *, encoding: str = "utf-8") -> list[Record]
```

Returns one decoded object per nonblank line. Blank lines are skipped, and an
empty or whitespace-only file returns `[]`. Raises `TabulintError` for invalid
JSON, a non-object line, duplicate keys (including nested objects), and parser
limits, as well as common reader errors. Syntax and object-validation errors
identify the physical input line, counting blank lines.

## Numeric rules

### `NumericRule`

```text
NumericRule(field_name: str, minimum: int | float | None = None,
            maximum: int | float | None = None) -> NumericRule
```

Returns a frozen data class with these fields:

| Field | Meaning |
| --- | --- |
| `field_name: str` | Exact name of the field to check. |
| `minimum: int \| float \| None` | Inclusive lower bound; `None` leaves it unset. |
| `maximum: int \| float \| None` | Inclusive upper bound; `None` leaves it unset. |

The constructor raises `TabulintError` for bounds that are not integers or finite
floats (including booleans), or a minimum greater than its maximum.

### `LengthRule`

```text
LengthRule(field_name: str, minimum: int | None = None,
           maximum: int | None = None) -> LengthRule
```

Returns a frozen data class describing inclusive minimum and/or maximum character
lengths for a field. Bounds must be non-negative integers, and the minimum cannot
exceed the maximum. Invalid bounds raise `TabulintError` when created through
`build_length_rules`; the direct data-class constructor stores its supplied values.

### `build_length_rules`

```text
build_length_rules(minimums: list[str] | None = None,
                   maximums: list[str] | None = None) -> list[LengthRule]
```

Parses repeatable `field=integer` bounds, strips field names, and combines each
field's minimum and maximum into one rule. The last bound for a repeated field
wins. Rules follow the minimum fields' first-seen order, then maximum-only fields.
Negative, non-integer, missing, or inverted bounds raise `TabulintError`.
Omitting both lists returns an empty list.

### `check_length_rules`

```text
check_length_rules(records: list[Record], rules: list[LengthRule]) -> list[Issue]
```

Checks `len(str(value))` in rule order, then record order. Missing fields and
values considered missing by `is_missing` are skipped. Violations produce
`below-min-length` or `above-max-length` errors with the field and one-based
record row. No input records or rules are modified.

### `build_numeric_rules`

```text
build_numeric_rules(minimums: list[str] | None = None,
                    maximums: list[str] | None = None) -> list[NumericRule]
```

Returns rules parsed from entries such as `"age=0"` and `"age=120"`. Field names
are stripped. Plain integer bounds are parsed exactly as integers; decimal and
exponent forms use floats. Signs and valid underscore separators are accepted.
Python's integer digit limit still applies after redundant leading zeros are
removed. Minimum and maximum lists are
independent; the last entry for a repeated field in either list wins. Rules
follow the minimum fields' first-seen order, then maximum-only fields.
Omitting both lists returns `[]`.

Raises `TabulintError` for a missing `=`, a blank field name, an invalid or
non-finite number, or a minimum greater than its maximum.

### `check_numeric_rules`

```text
check_numeric_rules(records: list[Record], rules: list[NumericRule]) -> list[Issue]
```

Returns numeric issues in rule order, then record order. Bounds are inclusive.
Absent fields and missing values are skipped; structural checks handle those.
Integers and plain integer strings retain exact precision. Decimal and exponent
strings use floats and their precision limits. Booleans, nonfinite numbers
(including NaN and infinity), and unparseable strings produce `not-numeric`.
A rule with neither bound still reports these values. Rules are validated by
`NumericRule` construction; this check has no intentional `TabulintError`.

### `check_required_fields`

```text
check_required_fields(records: list[Record], names: list[str]) -> list[Issue]
```

Returns `required-missing` errors for required fields that are absent or have
values considered missing by `is_missing`. `0` and `False` remain present.
Names match exactly, including case and whitespace, and repeated names are
checked once in first-requested order, then record order. For nonempty datasets,
a field absent from every record produces one dataset-level issue (`row=None`);
otherwise each absent or missing value gets a one-based record-row issue.
Records and names are not modified. An empty record list or name list returns `[]`.
This helper does not run structural checks or add an empty-dataset warning.
No intentional `TabulintError` is raised.

## Data and result types

### `Record`

```text
Record = dict[str, object]
```

A type alias for a record dictionary, not a validating model. Keys are field
names; values are the original Python or decoded file values. Ordinary
dictionary construction returns a dictionary and follows Python's `dict`
exception behavior; the alias adds no `TabulintError` handling.

### `Issue`

```text
Issue(code: str, severity: str, message: str,
      field_name: str | None = None, row: int | None = None) -> Issue
```

Returns a frozen data class. Construction does not validate fields or raise
`TabulintError`.

| Field | Meaning |
| --- | --- |
| `code: str` | Machine-readable code from the issue table below. |
| `severity: str` | `"error"` or `"warning"` for built-in checks. |
| `message: str` | Human-readable description. |
| `field_name: str \| None` | Affected field, or `None` for a record/dataset issue. |
| `row: int \| None` | One-based loaded record number, or `None` for a dataset issue. |

Record numbers exclude CSV headers and skipped JSON Lines blank lines; they
are not physical file lines. A duplicate-group issue points to its first
repeated record. Its message names the original record and up to ten repeats.

### `FieldProfile`

```text
FieldProfile(name: str, dominant_type: str,
             type_counts: dict[str, int] = <factory>,
             missing_count: int = 0) -> FieldProfile
```

Returns a mutable data class. Construction does not validate fields or raise
`TabulintError`.

| Field | Meaning |
| --- | --- |
| `name: str` | Field name. |
| `dominant_type: str` | Dominant inferred type, or `"null"` when all values are missing. |
| `type_counts: dict[str, int]` | Counts of each nonmissing inferred type; defaults to a new empty dictionary. |
| `missing_count: int` | Number of records with a missing value or absent key; defaults to zero. |

### `Report`

```text
Report(path: str, row_count: int, field_names: list[str] = <factory>,
       profiles: list[FieldProfile] = <factory>,
       issues: list[Issue] = <factory>) -> Report
```

Returns a mutable data class. The constructor only stores its arguments; use
`check_file` or `check_records` to populate calculated results. Construction
does not validate fields or raise `TabulintError`.

| Field or property | Meaning |
| --- | --- |
| `path: str` | Source path or display label. |
| `row_count: int` | Number of loaded records. |
| `field_names: list[str]` | Field names in first-seen order; defaults to a new empty list. |
| `profiles: list[FieldProfile]` | Per-field profiles; defaults to a new empty list. |
| `issues: list[Issue]` | All findings; defaults to a new empty list. |
| `error_count: int` | Read-only property counting issues whose severity is `"error"`. |
| `warning_count: int` | Read-only property counting issues whose severity is `"warning"`. |
| `ok: bool` | Read-only property: `True` only when `issues` is empty. |

Properties are computed from the current issues each time they are read.
A warning makes `ok` false even when `error_count` is zero. No intentional
`TabulintError` is raised when reading these properties.

### `TabulintError`

```text
TabulintError(*args: object) -> TabulintError
```

An `Exception` subclass representing a loading, rule-configuration, or cyclic
in-memory record failure.
Construction returns an exception instance with ordinary `Exception` argument
and message behavior; it does not itself raise the exception. Catch it around
`check_file`, `check_records`, `analyze`, readers, `NumericRule`, or
`build_numeric_rules`. Data-quality findings are
returned as `Issue` objects instead.

### `__version__`

```text
__version__: str
```

The package version string, also used by the CLI's `--version` output. Reading
this constant returns a string and raises no `TabulintError`.

## Rendering

### `format_report`

```text
format_report(report: Report) -> str
```

Returns text with record counts, field profiles, a missing-value summary when
needed, and issues. Unpaired Unicode surrogates are escaped so the returned text
can be written as UTF-8. The CLI also escapes characters unsupported by its
console encoding; report files retain UTF-8 characters. Issues are sorted by row and code, with at most 50 shown;
the summary still counts every issue. It adds no trailing newline and does not
print or write a file. No intentional `TabulintError` is raised.

### `format_report_json`

```text
format_report_json(report: Report) -> str
```

Returns an indented JSON string, with no trailing newline, printing, or file
writes. It includes every issue in report order. Top-level keys are `path`,
`row_count`, `profiles`, `issues`, `error_count`, `warning_count`, and `ok`.
Profiles include `name`, `dominant_type`, and `missing_count`; issues include
`code`, `severity`, `message`, `field`, and `row`. `field` corresponds to
`Issue.field_name`. Optional `None` values become JSON `null`.
`Report.field_names` and `FieldProfile.type_counts` are not serialized. No
intentional `TabulintError` is raised; manually supplied non-serializable
model fields can cause Python's `TypeError`.

## Issue codes and severities

These are all codes emitted by the built-in checks, including numeric and
required-field rules and the empty-input check in `check_records`. They match the
[README checks table](../README.md#checks).

| Code | Severity | Meaning |
| --- | --- | --- |
| `missing-value` | warning | A present value is `None`, empty, or whitespace-only. |
| `missing-field` | error | A field found in other records is absent from this record. |
| `required-missing` | error | A requested required field is absent or has a missing value. |
| `duplicate-record` | warning | A repeated-record group, reported once. |
| `type-mismatch` | error | A nonmissing value differs from the dominant inferred type. |
| `below-minimum` | error | A numeric value is below an inclusive minimum. |
| `above-maximum` | error | A numeric value is above an inclusive maximum. |\n| `below-min-length` | error | A stringified value is shorter than its minimum character length. |\n| `above-max-length` | error | A stringified value is longer than its maximum character length. |
| `not-numeric` | error | A value checked by a numeric rule cannot be treated as numeric. |
| `empty-dataset` | warning | No records were loaded or supplied. |

## Worked examples

Each example is self-contained and can be run after installing the package.
This pipeline keeps missing-value warnings available for review while failing
only when an error is present:

```python
import json

from tabulint import build_numeric_rules, check_records, format_report_json

rules = build_numeric_rules(minimums=["age=0"], maximums=["age=120"])
records = [
    {"name": "Ada", "age": 36},
    {"name": "Grace", "age": 200},
    {"name": "Linus", "age": None},
]
report = check_records(records, rules, path="incoming people")
missing = [issue for issue in report.issues if issue.code == "missing-value"]
pipeline_passes = report.error_count == 0

assert [(issue.row, issue.field_name) for issue in missing] == [(3, "age")]
assert report.error_count == 1
assert not pipeline_passes

document = json.loads(format_report_json(report))
assert document["warning_count"] == 1
assert document["row_count"] == 3

warning_only = check_records([{"name": "Linus", "age": None}], rules)
assert not warning_only.ok
assert warning_only.error_count == 0  # This batch can pass an errors-only gate.
```

Loading failures are separate from findings. This example uses a temporary
directory so it does not depend on repository fixtures or existing files:

```python
from pathlib import Path
from tempfile import TemporaryDirectory

from tabulint import TabulintError, check_file

with TemporaryDirectory() as directory:
    path = Path(directory) / "people.jsonl"
    path.write_text('{"name": "Ada"}\n\n{"name": "Grace"}\n', encoding="utf-8")
    report = check_file(path)
    assert report.ok and report.row_count == 2

    path.write_text('{"name": }\n', encoding="utf-8")
    try:
        check_file(path)
    except TabulintError as error:
        assert "line 1" in str(error)
    else:
        raise AssertionError("Malformed JSON must raise TabulintError")
```
