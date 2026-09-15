# Contributor Tasks

This file is the planned work for `tabulint`. Every task here has a matching
GitHub issue; [ISSUE_MAP.md](ISSUE_MAP.md) maps each task ID to its issue number
and URL.

Each task is independently useful and can be implemented on its own. None of them
is a prerequisite for another, though a few are natural neighbours and say so.

**None of these tasks is implemented yet.** The `Status` line on each task is the
source of truth in this file; the GitHub issue is the source of truth overall.

Before you start, read [CONTRIBUTING.md](CONTRIBUTING.md) for the fork and
pull-request workflow. Claim a task by commenting on its issue, then open one
pull request per task.

A task marked `CLAIMED` already has someone working on it, and one marked `DONE`
has already shipped. Pick a task that is still `OPEN`, or ask on the issue before
starting, so two people do not write the same patch.

House rules that apply to every task:

- Standard library only. No new runtime dependencies.
- Prefer a plain function over a new class or abstraction.
- Add tests for the behavior you change; the suite must stay green.
- Update `README.md` when user-visible behavior changes.
- Add a `CHANGELOG.md` entry under `Unreleased`.

## Tasks

### [TASK-01] Improve missing-value summary

**Status:** OPEN
**GitHub issue:** [#1](https://github.com/ismayilzeynal/tabulint-oss-az/issues/1)
**Labels:** `enhancement`, `good first issue`

**Goal**

Add a per-field missing-value summary to the report instead of relying only on one line per missing cell.

**Why useful**

A dataset with 5,000 blank cells currently produces 5,000 near-identical lines. A reader wants to know which fields are incomplete and how badly, and only then look at individual rows.

**Likely files**

- `src/tabulint/report.py`
- `src/tabulint/models.py`
- `tests/test_api.py`

**Requirements**

- Add a missing-value summary section to `format_report` listing each field that has at least one missing value.
- For each such field show the absolute count and the percentage of records, for example `age: 3 missing (60%)`.
- Sort the summary by missing count, highest first, then by field name for a stable order.
- `FieldProfile.missing_count` already exists; use it rather than recomputing.
- Keep the existing per-row `missing-value` issues; this task adds a summary, it does not remove detail.
- Fields with zero missing values must not appear in the summary.
- Omit the whole section when no field has missing values.

**Acceptance criteria**

- Running the CLI on a dataset with missing values prints a summary section with counts and percentages.
- Running the CLI on a complete dataset prints no summary section and is otherwise unchanged.
- Exit codes are unchanged.

**Tests required**

- A report for a dataset with missing values in two fields contains both fields with correct counts.
- Percentages are correct for a non-round case, for example 1 of 3 records.
- A complete dataset produces no summary section.
- The summary is ordered by missing count, highest first.

**Out of scope**

- Changing issue codes or severities.
- Machine-readable output, which is TASK-13.
- Changing how missing values are detected.

### [TASK-02] Improve duplicate-record reporting

**Status:** OPEN
**GitHub issue:** [#2](https://github.com/ismayilzeynal/tabulint-oss-az/issues/2)
**Labels:** `enhancement`, `good first issue`

**Goal**

Group duplicate records so each repeated record is reported once with all of its row numbers, rather than one issue per repeat.

**Why useful**

A record repeated 40 times currently produces 39 separate issues that all say the same thing. Grouping makes the real shape of the problem visible.

**Likely files**

- `src/tabulint/analyzer.py`
- `src/tabulint/report.py`
- `tests/test_analyzer.py`

**Requirements**

- Change `check_duplicates` to emit one issue per duplicated record group rather than one per repeated row.
- The message must name the first occurrence and list the duplicate rows, for example `record from row 1 is repeated at rows 3, 7, 9`.
- Keep `Issue.row` set to the first duplicate row so the existing sorting in the report still works.
- Truncate the listed rows after a reasonable limit, for example 10, and append `and N more` rather than printing thousands of numbers.
- Records that appear exactly once must still produce no issue.

**Acceptance criteria**

- A record appearing 4 times produces exactly one `duplicate-record` issue naming all 3 repeat rows.
- Two different duplicated records produce two separate issues.
- A dataset with no duplicates produces no duplicate issues.

**Tests required**

- Four identical records produce one issue listing rows 2, 3 and 4.
- Two distinct duplicate groups produce two issues.
- A long duplicate group truncates the row list and reports the remainder.
- A dataset with all-distinct records produces no issues.

**Out of scope**

- Detecting near-duplicates or fuzzy matches.
- Duplicate detection on a subset of key fields.
- Deduplicating or rewriting the input file.

### [TASK-03] Add CSV delimiter option

**Status:** OPEN
**GitHub issue:** [#3](https://github.com/ismayilzeynal/tabulint-oss-az/issues/3)
**Labels:** `enhancement`, `cli`, `data-format`

**Goal**

Let the user choose the CSV delimiter instead of hard-coding a comma.

**Why useful**

Semicolon-delimited and tab-delimited exports are extremely common, especially from European spreadsheet locales. Today they load as a single malformed column.

**Likely files**

- `src/tabulint/loader.py`
- `src/tabulint/cli.py`
- `src/tabulint/__init__.py`
- `tests/test_loader.py`
- `tests/test_cli.py`
- `README.md`

**Requirements**

- Add a `delimiter` parameter to `load_csv` defaulting to a comma.
- Thread the delimiter through `load_dataset` and `check_file` so the library API can set it too.
- Add a `--delimiter` CLI option. Accept a single character, and accept the two-character spelling `\t` as a readable way to say tab.
- Reject a multi-character delimiter with a clear `TabulintError` and exit code 2.
- The delimiter must be ignored for JSON input rather than causing an error.
- Document the option in the README CLI examples and supported-formats section.

**Acceptance criteria**

- Running with `--delimiter ;` parses a semicolon-delimited file into the correct fields.
- Running with the tab spelling parses a tab-delimited file.
- The default behavior with no option is unchanged.
- An invalid delimiter exits with code 2 and a readable message.

**Tests required**

- A semicolon file parses correctly through `load_csv`.
- A tab file parses correctly via the CLI tab spelling.
- A multi-character delimiter raises `TabulintError`.
- A comma file with no option set still parses correctly.

**Out of scope**

- Automatic delimiter sniffing.
- Quote-character or escape-character options.
- Encoding options, which are TASK-04.

### [TASK-04] Add configurable CSV encoding

**Status:** OPEN
**GitHub issue:** [#4](https://github.com/ismayilzeynal/tabulint-oss-az/issues/4)
**Labels:** `enhancement`, `cli`, `data-format`

**Goal**

Allow the CSV and JSON readers to use an encoding other than UTF-8.

**Why useful**

Legacy exports are often cp1252, latin-1, or UTF-8 with a byte-order mark. Those files currently fail to load at all, which is a hard stop rather than a data-quality finding.

**Likely files**

- `src/tabulint/loader.py`
- `src/tabulint/cli.py`
- `src/tabulint/__init__.py`
- `tests/test_loader.py`
- `tests/test_cli.py`
- `README.md`

**Requirements**

- Add an `encoding` parameter to `load_csv` and `load_json`, defaulting to `utf-8`.
- Thread it through `load_dataset` and `check_file`.
- Add an `--encoding` CLI option.
- An unknown encoding name must raise `TabulintError` with a clear message rather than a raw `LookupError`.
- A decode failure must keep naming the file and also name the encoding that was attempted.
- Consider `utf-8-sig` handling so a byte-order mark does not end up inside the first field name; document whichever behavior you choose.

**Acceptance criteria**

- A cp1252 file loads correctly with `--encoding cp1252`.
- A UTF-8 file still loads with no option set.
- An unknown encoding name exits with code 2 and a readable message.
- A decode failure message names both the file and the encoding.

**Tests required**

- A cp1252-encoded CSV with an accented character loads correctly.
- An unknown encoding raises `TabulintError`.
- Decoding a non-UTF-8 file as UTF-8 raises a message naming the encoding.
- A UTF-8 file with a byte-order mark behaves as documented.

**Out of scope**

- Automatic encoding detection.
- Adding a dependency such as chardet.
- Re-encoding or rewriting input files.

### [TASK-05] Add JSON Lines / NDJSON support

**Status:** OPEN
**GitHub issue:** [#5](https://github.com/ismayilzeynal/tabulint-oss-az/issues/5)
**Labels:** `enhancement`, `data-format`

**Goal**

Support newline-delimited JSON, where each line of a file is one JSON object.

**Why useful**

JSON Lines is the standard interchange format for log exports and streaming datasets. It is the most obvious format gap after CSV and JSON, and it is currently rejected outright.

**Likely files**

- `src/tabulint/loader.py`
- `src/tabulint/cli.py`
- `src/tabulint/__init__.py`
- `tests/test_loader.py`
- `tests/test_cli.py`
- `README.md`
- `CHANGELOG.md`

**Requirements**

- Add `load_jsonl(path)` which reads one JSON object per line and returns the same list-of-records shape as the existing loaders.
- Dispatch the `.jsonl` and `.ndjson` extensions to it from `load_dataset`.
- Skip blank lines silently; they are normal at the end of such files.
- A line that is not valid JSON must raise `TabulintError` naming the line number.
- A line that parses but is not an object must raise `TabulintError` naming the line number.
- Export `load_jsonl` from the package `__init__` and add it to `__all__`.
- Update the supported-formats table in the README and remove the matching bullet from the limitations section.

**Acceptance criteria**

- Running the CLI on a `.jsonl` file runs every existing check and returns the normal exit codes.
- `.ndjson` behaves identically to `.jsonl`.
- A malformed line exits with code 2 and a message naming the line number.
- Existing `.csv` and `.json` behavior is unchanged.

**Tests required**

- A valid `.jsonl` file loads into the expected records.
- Trailing and interior blank lines are skipped.
- A malformed line raises `TabulintError` naming the line number.
- A line holding a JSON array rather than an object raises `TabulintError`.
- The CLI exits 0 on a clean `.ndjson` file and 1 on one with duplicates.

**Out of scope**

- Streaming or chunked processing, which is TASK-16.
- Compressed input such as `.jsonl.gz`.
- Writing JSON Lines output.

### [TASK-06] Improve empty-dataset handling

**Status:** OPEN
**GitHub issue:** [#6](https://github.com/ismayilzeynal/tabulint-oss-az/issues/6)
**Labels:** `enhancement`, `cli`

**Goal**

Distinguish the different kinds of empty input, and let the user decide whether an empty dataset is a failure.

**Why useful**

An empty file, a CSV with only a header, and a JSON empty array are three different situations. Today they all produce the same generic warning, and there is no way to accept an empty dataset in a pipeline that legitimately produces one.

**Likely files**

- `src/tabulint/__init__.py`
- `src/tabulint/loader.py`
- `src/tabulint/cli.py`
- `tests/test_api.py`
- `tests/test_cli.py`
- `README.md`

**Requirements**

- Distinguish a zero-byte or whitespace-only file from a structurally valid but record-free dataset, and use different messages for them.
- A CSV with a header and no data rows must report that it has a header but no records, and list the field names it found.
- Add an `--allow-empty` CLI flag that suppresses the `empty-dataset` issue so an empty dataset exits 0.
- Keep the current default: with no flag, an empty dataset is still a warning and still exits 1.
- Document the flag and the distinction in the README.

**Acceptance criteria**

- A header-only CSV reports its field names and that no records were found.
- A zero-byte file reports that the file is empty, with a different message.
- `--allow-empty` makes both cases exit 0.
- A non-empty dataset is unaffected by the flag.

**Tests required**

- A header-only CSV report names the header fields.
- A zero-byte file produces the distinct empty-file message.
- A JSON empty array produces the record-free message.
- The CLI exits 1 without `--allow-empty` and 0 with it.

**Out of scope**

- Changing the exit-code numbering, which is TASK-23.
- Treating a missing file as empty; that stays an error.

### [TASK-07] Improve boolean type inference

**Status:** DONE (issue #7, merged in #26)
**GitHub issue:** [#7](https://github.com/ismayilzeynal/tabulint-oss-az/issues/7)
**Labels:** `enhancement`, `validation`, `good first issue`

**Goal**

Recognize the common textual spellings of booleans beyond `true` and `false`.

**Why useful**

Real CSV exports spell booleans as yes/no, y/n, and t/f. Today an `active` column full of `yes` and `no` infers as `string`, so no type inconsistency inside it can ever be detected.

**Likely files**

- `src/tabulint/analyzer.py`
- `tests/test_analyzer.py`
- `README.md`

**Requirements**

- Extend the boolean literal set to include at least `yes`, `no`, `y`, `n`, `t`, `f`, matched case-insensitively after stripping whitespace.
- Do not treat `1` and `0` as boolean by default; they are already valid integers and reclassifying them would silently change integer columns. If you support them at all, it must be behind an explicit opt-in and documented as such.
- A field must not be reported as type-inconsistent purely because it mixes boolean spellings, for example `yes` in one row and `true` in another.
- Document the recognized spellings in the README checks section.

**Acceptance criteria**

- `infer_type` returns `boolean` for `yes` and for `N`.
- `infer_type` still returns `integer` for `1`.
- A column of yes/no values profiles as `boolean`.
- A column mixing `yes` and `true` produces no type-mismatch issue.

**Tests required**

- Each newly recognized spelling infers as boolean, in both cases and with surrounding whitespace.
- `1` and `0` still infer as integer.
- A mixed-spelling boolean column produces no type-mismatch issue.
- An unrelated string such as `maybe` still infers as string.

**Out of scope**

- Locale-specific words such as oui or ja.
- Converting or normalizing values in the output.
- Numeric inference changes, which are TASK-08.

### [TASK-08] Improve numeric type-inference edge cases

**Status:** OPEN
**GitHub issue:** [#8](https://github.com/ismayilzeynal/tabulint-oss-az/issues/8)
**Labels:** `enhancement`, `validation`

**Goal**

Handle the numeric edge cases that current inference gets wrong or handles surprisingly.

**Why useful**

Python's `float()` accepts `nan` and `inf`, so those strings currently infer as `float`. Meanwhile a column of integers containing one decimal value produces a type-mismatch error that is usually noise rather than a real defect.

**Likely files**

- `src/tabulint/analyzer.py`
- `tests/test_analyzer.py`
- `README.md`

**Requirements**

- Do not infer the strings `nan`, `inf`, `infinity` or their signed and mixed-case variants as `float`; decide and document whether they are `string` or a distinct classification.
- Treat an integer as compatible with a dominant `float` type, so a column of 1.5, 2.5 and 3 does not report the 3 as a mismatch.
- Decide and document the reverse direction, whether a float inside a dominant-integer column is a mismatch. Whichever you choose, make it deliberate and tested rather than incidental.
- Handle underscore separators such as `1_000` explicitly; Python's `int()` accepts them, so state whether that is intended.
- A leading-plus value such as `+5` must infer as integer.
- Do not silently change how genuinely non-numeric strings are classified.

**Acceptance criteria**

- `infer_type` no longer returns `float` for `nan`.
- A float column containing whole numbers produces no type-mismatch issues.
- The README documents the integer and float compatibility rule.
- Existing inference tests still pass.

**Tests required**

- `nan`, `inf`, negative infinity and mixed-case variants classify as documented.
- A dominant-float column with an integer value produces no mismatch.
- The dominant-integer-with-float case behaves as documented.
- `+5` infers as integer and `1_000` behaves as documented.

**Out of scope**

- Currency, percentage, or thousands-separator parsing.
- Date and time inference.
- Decimal or fixed-point precision handling.

### [TASK-09] Add string-length validation

**Status:** OPEN
**GitHub issue:** [#9](https://github.com/ismayilzeynal/tabulint-oss-az/issues/9)
**Labels:** `enhancement`, `validation`, `cli`

**Goal**

Let the user assert a minimum and maximum length for a text field.

**Why useful**

Length limits are one of the most common real constraints on text data: country codes must be 2 characters, a database column is VARCHAR(50), an identifier has a fixed width. tabulint can validate numbers but not text.

**Likely files**

- `src/tabulint/validators.py`
- `src/tabulint/cli.py`
- `src/tabulint/__init__.py`
- `tests/test_validators.py`
- `tests/test_cli.py`
- `README.md`

**Requirements**

- Add a `LengthRule` dataclass with a field name and optional minimum and maximum lengths.
- Add `build_length_rules` and `check_length_rules` mirroring the existing numeric-rule functions.
- Add repeatable `--min-length FIELD=N` and `--max-length FIELD=N` CLI options.
- Length is measured in characters on the string form of the value.
- Skip missing values, exactly as the numeric rules do.
- Emit new issue codes `below-min-length` and `above-max-length` with severity `error`.
- Reject a negative length or a non-integer length with `TabulintError`.
- Reject a minimum greater than a maximum, as the numeric rules already do.
- Wire the rules into `check_records` and `check_file` and document them in the README checks table.

**Acceptance criteria**

- Running with `--max-length code=2` flags a 3-character code and exits 1.
- A dataset satisfying the bounds exits 0.
- Missing values are not flagged by a length rule.
- An invalid bound exits 2 with a readable message.

**Tests required**

- A value shorter than the minimum produces `below-min-length`.
- A value longer than the maximum produces `above-max-length`.
- A value exactly at each boundary passes.
- Missing values and absent fields are skipped.
- A negative or non-integer bound raises `TabulintError`.
- The CLI exit codes are correct for the pass and fail cases.

**Out of scope**

- Regular-expression or pattern validation.
- Byte-length rather than character-length measurement.
- Trimming or normalizing values.

### [TASK-10] Add allowed-values validation

**Status:** OPEN
**GitHub issue:** [#10](https://github.com/ismayilzeynal/tabulint-oss-az/issues/10)
**Labels:** `enhancement`, `validation`, `cli`

**Goal**

Let the user restrict a field to a fixed set of allowed values.

**Why useful**

Categorical fields such as status, country, or tier are where typos and stray categories actually hide. Type inference cannot catch `activee` in a column of `active` and `inactive`, because both are strings.

**Likely files**

- `src/tabulint/validators.py`
- `src/tabulint/cli.py`
- `src/tabulint/__init__.py`
- `tests/test_validators.py`
- `tests/test_cli.py`
- `README.md`

**Requirements**

- Add an `AllowedValuesRule` dataclass holding a field name and the permitted values.
- Add `build_allowed_values_rules` and `check_allowed_values_rules`.
- Add a repeatable `--allowed FIELD=a,b,c` CLI option.
- Comparison is on the string form of the value and is case-sensitive by default.
- Emit a `not-allowed` issue with severity `error`, and include the offending value plus the allowed set in the message.
- Skip missing values; presence requirements are TASK-11.
- Reject an empty allowed set with `TabulintError`.
- Decide and document how a value containing a comma can be expressed, or state plainly that it cannot.
- Wire the rules into `check_records` and `check_file` and document the option in the README.

**Acceptance criteria**

- Running with `--allowed status=active,inactive` flags `activee` and exits 1.
- A dataset using only allowed values exits 0.
- An empty allowed set exits 2 with a readable message.
- The error message names both the bad value and the allowed set.

**Tests required**

- A disallowed value produces `not-allowed`.
- Every allowed value passes.
- Case sensitivity behaves as documented.
- Missing values and absent fields are skipped.
- An empty allowed set raises `TabulintError`.

**Out of scope**

- Loading the allowed set from a file.
- Case-insensitive matching unless you add and document an explicit flag.
- Suggesting the nearest allowed value.

### [TASK-11] Add required-field validation

**Status:** OPEN
**GitHub issue:** [#11](https://github.com/ismayilzeynal/tabulint-oss-az/issues/11)
**Labels:** `enhancement`, `validation`, `cli`

**Goal**

Let the user declare that a field must be present and non-empty in every record.

**Why useful**

Today a missing value is a warning everywhere, because tabulint cannot know which fields matter. A primary key or a required identifier should be a hard error, and a column that is optional by design should not raise the same alarm.

**Likely files**

- `src/tabulint/validators.py`
- `src/tabulint/cli.py`
- `src/tabulint/__init__.py`
- `tests/test_validators.py`
- `tests/test_cli.py`
- `README.md`

**Requirements**

- Add a repeatable `--required FIELD` CLI option.
- Add `check_required_fields(records, names)` in `validators.py`.
- Emit a `required-missing` issue with severity `error` when a required field is absent from a record or holds a missing value.
- Report a required field that is absent from every record once, as a dataset-level issue with no row, rather than once per record.
- A required field that is present and non-empty everywhere produces no issue.
- Do not remove the existing `missing-value` warnings. A required field may produce both, so state the intended behavior in the README and keep it consistent.
- Wire the check into `check_records` and `check_file`.

**Acceptance criteria**

- Running with `--required email` exits 1 when any record has a blank email.
- A field required but absent from the whole dataset yields one dataset-level error.
- A fully populated required field exits 0.
- Datasets checked without `--required` behave exactly as before.

**Tests required**

- A blank required value produces `required-missing` with the right row.
- An absent required key in one record produces `required-missing`.
- A field absent from every record produces exactly one issue with no row.
- A fully populated required field produces no issue.
- The CLI exits 1 on violation and 0 when satisfied.

**Out of scope**

- Rule configuration files.
- Uniqueness or primary-key constraints.
- Cross-field conditional requirements.

### [TASK-12] Add CLI quiet mode

**Status:** DONE (issue #12, merged in #27)
**GitHub issue:** [#12](https://github.com/ismayilzeynal/tabulint-oss-az/issues/12)
**Labels:** `enhancement`, `cli`, `good first issue`

**Goal**

Add a quiet flag that suppresses normal output and communicates the result through the exit code alone.

**Why useful**

In a CI pipeline or a shell loop over hundreds of files the full report is noise. The caller wants the exit code, and at most a single line when something is wrong.

**Likely files**

- `src/tabulint/cli.py`
- `tests/test_cli.py`
- `README.md`

**Requirements**

- Add `--quiet` with a `-q` short form to the argument parser.
- In quiet mode print nothing to stdout when the dataset is clean.
- In quiet mode print at most one summary line when issues are found, for example `people.csv: 2 error(s), 1 warning(s)`.
- Load errors and argument errors must still print to stderr in quiet mode; silencing real failures would be dangerous.
- Exit codes must be identical to non-quiet mode.
- Document the flag in the README CLI examples.

**Acceptance criteria**

- A clean dataset in quiet mode prints nothing and exits 0.
- A dataset with issues in quiet mode prints one line and exits 1.
- A missing file in quiet mode still prints an error to stderr and exits 2.
- Behavior without the flag is unchanged.

**Tests required**

- Quiet mode on a clean dataset produces empty stdout and exit 0.
- Quiet mode on a dataset with issues produces exactly one stdout line and exit 1.
- Quiet mode still writes load errors to stderr and exits 2.
- The short `-q` spelling behaves identically.

**Out of scope**

- A verbose or debug mode.
- Log levels.
- Changing the default report format.

### [TASK-13] Add machine-readable JSON report output

**Status:** OPEN
**GitHub issue:** [#13](https://github.com/ismayilzeynal/tabulint-oss-az/issues/13)
**Labels:** `enhancement`, `cli`

**Goal**

Add a JSON output format so other tools can consume a tabulint report.

**Why useful**

The plain-text report is for humans. A CI job, a dashboard, or a script that wants to count errors per field has to parse prose today, which is fragile. A stable JSON shape makes tabulint composable.

**Likely files**

- `src/tabulint/report.py`
- `src/tabulint/cli.py`
- `src/tabulint/__init__.py`
- `tests/test_api.py`
- `tests/test_cli.py`
- `README.md`

**Requirements**

- Add `format_report_json(report)` returning a JSON string, next to the existing `format_report`.
- Add a `--format {text,json}` CLI option defaulting to `text`.
- The JSON document must include the dataset path, the record count, the field profiles with dominant type and missing count, and every issue with its code, severity, message, field and row.
- Include the error and warning counts so a consumer does not have to recount.
- Do not truncate the issue list in JSON output; truncation is a human-readability concern only.
- Output must be valid JSON on stdout with nothing else mixed in, so it can be piped straight into another tool.
- Export the new function from the package `__init__` and add it to `__all__`.
- Document the shape in the README with a short example.

**Acceptance criteria**

- Running with `--format json` emits valid JSON that round-trips through `json.loads`.
- The JSON contains every issue the text report describes.
- The default text output is byte-for-byte unchanged.
- Exit codes are identical in both formats.

**Tests required**

- JSON output parses and contains the expected top-level keys.
- Every issue appears in the JSON with its code, severity and row.
- A clean dataset produces JSON with an empty issue list and exit 0.
- A large issue count is not truncated in JSON output.

**Out of scope**

- CSV, SARIF, or JUnit output formats.
- Writing to a file, which is TASK-14.
- Changing the text report layout.

### [TASK-14] Add report output-file option

**Status:** DONE (issue #14, merged in #28)
**GitHub issue:** [#14](https://github.com/ismayilzeynal/tabulint-oss-az/issues/14)
**Labels:** `enhancement`, `cli`, `good first issue`

**Goal**

Let the user write the report to a file instead of stdout.

**Why useful**

Shell redirection works for one invocation, but a CI job that wants to keep the report as a build artifact while still showing progress on the console needs the tool itself to write the file. It also avoids encoding surprises with redirection on Windows.

**Likely files**

- `src/tabulint/cli.py`
- `tests/test_cli.py`
- `README.md`

**Requirements**

- Add an `--output PATH` / `-o PATH` CLI option.
- Write the rendered report to the file using UTF-8 explicitly, not the platform default encoding.
- The file must end with a trailing newline.
- Overwrite an existing file rather than appending, and document that clearly.
- If the file cannot be written, report a clear error on stderr and exit 2 without a traceback.
- Exit codes must still reflect the data-quality result, not whether the file was written, except for the write-failure case above.
- Decide and document whether the report is also printed to stdout when an output file is given.

**Acceptance criteria**

- Running with `--output report.txt` creates a file containing the report.
- The exit code still reflects whether issues were found.
- An unwritable path exits 2 with a readable message.
- Behavior without the flag is unchanged.

**Tests required**

- The output file is created and its contents match the rendered report.
- The file is written as UTF-8 and contains a non-ASCII value correctly.
- An unwritable path exits 2 and prints to stderr.
- The exit code for a dataset with issues is still 1 when writing to a file.

**Out of scope**

- Appending to an existing report.
- Creating missing parent directories.
- Choosing the format, which is TASK-13.

### [TASK-15] Improve malformed-input errors

**Status:** OPEN
**GitHub issue:** [#15](https://github.com/ismayilzeynal/tabulint-oss-az/issues/15)
**Labels:** `enhancement`, `documentation`

**Goal**

Make load failures point precisely at the problem and suggest the likely fix.

**Why useful**

A message such as `malformed JSON (Expecting value at line 1)` tells the user something is wrong but not what to do. A person staring at a 40,000-line export needs the location, a glimpse of the offending text, and a hint.

**Likely files**

- `src/tabulint/loader.py`
- `tests/test_loader.py`
- `README.md`

**Requirements**

- Include the column as well as the line number in JSON parse errors, both of which `json.JSONDecodeError` already provides.
- Include a short excerpt of the offending line, truncated to a sensible width, so the user can see the problem without opening the file.
- For the CSV ragged-row error, report how many fields were found against how many the header declared.
- Add a short actionable hint to the most common failures, for example suggesting a delimiter check when a CSV parses as a single column.
- Never include the whole file or an unbounded amount of data in an error message.
- Keep `TabulintError` as the single exception type raised to callers, so the CLI contract does not change.

**Acceptance criteria**

- A malformed JSON file produces a message naming the line, the column, and an excerpt.
- A ragged CSV row reports the expected and actual field counts.
- All load failures still exit with code 2.
- Existing loader tests still pass, adjusted only for the improved wording.

**Tests required**

- A malformed JSON message contains the line and column numbers.
- A very long malformed line produces a truncated excerpt, not the entire line.
- The ragged-CSV message names both field counts.
- Every failure path still raises `TabulintError`.

**Out of scope**

- Recovering from or repairing malformed input.
- A tolerant mode that skips bad rows.
- Changing the exception hierarchy.

### [TASK-16] Reduce one avoidable large-file memory cost

**Status:** OPEN
**GitHub issue:** [#16](https://github.com/ismayilzeynal/tabulint-oss-az/issues/16)
**Labels:** `performance`

**Goal**

Remove one concrete, measurable source of avoidable memory use when checking a large dataset.

**Why useful**

Every record is held in memory and then walked several times, and duplicate detection additionally keeps a full key tuple per record. On a multi-gigabyte export that is the difference between a tool that runs and one that is killed. This task is deliberately scoped to one improvement, not a rewrite.

**Likely files**

- `src/tabulint/analyzer.py`
- `src/tabulint/loader.py`
- `tests/test_analyzer.py`

**Requirements**

- Pick exactly one avoidable cost and fix it. Good candidates: storing a hash of each record key instead of the full tuple in `check_duplicates`, or walking the records once instead of once per check.
- Measure before and after on a generated dataset of at least 100,000 records, and put the numbers in the pull-request description.
- Behavior must not change: the same issues, in the same order, with the same messages.
- If you hash record keys, document the collision consequence honestly and keep the false-positive risk negligible.
- Do not add a dependency, and do not introduce a streaming architecture; that is a much larger change.
- Keep the code readable. A small, clearly explained win is worth more here than a clever one.

**Acceptance criteria**

- A measurable reduction in peak memory or allocations is demonstrated with numbers.
- The full test suite passes with no behavior change.
- No new dependency is added.
- The pull-request description states the measurement method.

**Tests required**

- Existing duplicate and analyzer tests still pass unchanged.
- A test covering the specific structure you changed, for example that hashed keys still detect duplicates correctly.
- A moderately large generated dataset still produces the expected issue counts.

**Out of scope**

- Full streaming or chunked processing of input files.
- Parallelism or multiprocessing.
- Adding numpy, pandas, or any other dependency.

### [TASK-17] Improve public Python API documentation

**Status:** OPEN
**GitHub issue:** [#17](https://github.com/ismayilzeynal/tabulint-oss-az/issues/17)
**Labels:** `documentation`, `good first issue`

**Goal**

Document the public Python API properly, so tabulint is usable as a library and not only as a command.

**Why useful**

The README shows two short snippets. Someone embedding tabulint in a data pipeline needs to know what `Report` and `Issue` actually carry, which names are stable, and what raises `TabulintError`.

**Likely files**

- `README.md`
- `src/tabulint/__init__.py`
- `src/tabulint/models.py`

**Requirements**

- Add an API reference section to the README, or a separate `docs/api.md` linked from the README.
- Document every name in `__all__`: its signature, what it returns, and what it raises.
- Document the fields of `Report`, `Issue` and `FieldProfile`, including the `ok`, `error_count` and `warning_count` properties.
- List the issue codes and severities in one place and keep them consistent with the README checks table.
- State the stability promise plainly: which names are public and what pre-1.0 means for them.
- Include at least one worked example beyond the existing snippets, for example filtering issues by code or failing a pipeline on errors only.
- Fix any docstring that is now inaccurate; do not add docstrings to code you did not otherwise touch.

**Acceptance criteria**

- Every name exported in `__all__` appears in the documentation.
- The documented issue codes match the codes the implementation actually emits.
- Every documented example runs correctly against the current code.
- The README stays readable and does not turn into a wall of generated text.

**Tests required**

- A test asserting that every name in `__all__` is importable from the package.
- A test asserting that the set of issue codes the checks emit matches the documented list.

**Out of scope**

- Setting up Sphinx, MkDocs, or a documentation site.
- Changing the API itself.
- Adding type stubs.

### [TASK-18] Add tiny example datasets

**Status:** OPEN
**GitHub issue:** [#18](https://github.com/ismayilzeynal/tabulint-oss-az/issues/18)
**Labels:** `documentation`, `testing`, `good first issue`

**Goal**

Add a small set of example datasets so a new user can run tabulint immediately and see each kind of finding.

**Why useful**

The README shows commands against files that do not exist in the repository. A newcomer has to invent test data before they can see what the tool does, and a contributor has no shared fixture to reason about.

**Likely files**

- `examples/`
- `README.md`
- `tests/test_examples.py`

**Requirements**

- Create an `examples/` directory with a handful of tiny files, each under roughly 20 rows.
- Include at least: a clean CSV, a CSV with missing values, a CSV with duplicate records, a CSV with mixed types in one column, and a clean JSON array.
- Use obviously synthetic data. No real names, no real email addresses, no personal data of any kind.
- Add a short `examples/README.md` saying what each file demonstrates and which command to run against it.
- Update the main README so its CLI examples reference these real paths.
- Add a test that runs the checks over every example file and asserts the expected exit code, so the examples cannot silently rot.

**Acceptance criteria**

- Every command in the README works verbatim after a clone.
- The clean examples exit 0 and the problematic ones exit 1.
- Each example file demonstrates a distinct check.
- No example contains real personal data.

**Tests required**

- A test iterating over `examples/` that asserts each file loads without a `TabulintError`.
- A test asserting the clean examples produce no issues.
- A test asserting each problematic example produces its intended issue code.

**Out of scope**

- Large or realistic benchmark datasets.
- A data generator script.
- Binary or compressed example files.

### [TASK-19] Improve Windows compatibility

**Status:** OPEN
**GitHub issue:** [#19](https://github.com/ismayilzeynal/tabulint-oss-az/issues/19)
**Labels:** `cross-platform`, `testing`

**Goal**

Make sure tabulint behaves correctly on Windows, and prove it in CI.

**Why useful**

CSV files on Windows arrive with CRLF line endings and are often written by Excel, and console output there is not always UTF-8. Right now nothing verifies any of this: CI runs on Linux only, so a Windows regression would ship unnoticed.

**Likely files**

- `.github/workflows/ci.yml`
- `src/tabulint/loader.py`
- `src/tabulint/cli.py`
- `tests/test_loader.py`
- `CONTRIBUTING.md`

**Requirements**

- Add `windows-latest` to the CI job matrix so the suite runs there on every push and pull request.
- Verify that CRLF line endings do not leak into the last field of a CSV row, and add a regression test.
- Make sure report output does not raise `UnicodeEncodeError` on a console using a legacy code page when a dataset holds non-ASCII values.
- Check that Windows path forms, including backslashes and drive letters, are handled correctly in messages and arguments.
- Confirm that the tests do not assume POSIX path separators or that a temporary file can be reopened while held.
- Note any Windows-specific setup step in CONTRIBUTING.md if you find one is needed.

**Acceptance criteria**

- CI runs and passes on both Ubuntu and Windows.
- A CRLF CSV produces exactly the same records as the LF equivalent.
- A dataset with non-ASCII values prints without raising on Windows.
- No test asserts a POSIX-only path shape.

**Tests required**

- A CRLF fixture parses identically to the LF version.
- A report containing non-ASCII values renders without error.
- A path-handling test that passes on both platforms.

**Out of scope**

- Windows installers or packaging.
- PowerShell-specific integrations.
- The Python version matrix, which is TASK-20.

### [TASK-20] Add supported-Python CI matrix

**Status:** OPEN
**GitHub issue:** [#20](https://github.com/ismayilzeynal/tabulint-oss-az/issues/20)
**Labels:** `ci`, `testing`

**Goal**

Run the test suite against every Python version the project claims to support.

**Why useful**

`pyproject.toml` declares support for 3.11 and newer and the classifiers list 3.11, 3.12 and 3.13, but CI only ever runs 3.11. A version-specific break in 3.12 or 3.13 would reach users before anyone noticed.

**Likely files**

- `.github/workflows/ci.yml`
- `pyproject.toml`
- `README.md`

**Requirements**

- Add a `python-version` matrix covering at least 3.11, 3.12 and 3.13.
- Use `fail-fast: false` so one failing version does not hide the others.
- Give the job a name that includes the version, so failures are identifiable at a glance.
- Make sure the declared `requires-python` and the classifier list agree with the matrix.
- Add a CI status badge to the README if there is not one already.
- Keep the workflow readable; do not split it into reusable workflows for a project this size.

**Acceptance criteria**

- CI runs the suite on each listed Python version.
- A failure on one version does not cancel the others.
- The project metadata matches the tested versions.
- The workflow file stays under roughly 60 lines.

**Tests required**

- No new unit tests are required; the deliverable is the passing matrix itself.
- If a version-specific incompatibility is found, add a regression test covering it.

**Out of scope**

- Adding operating systems to the matrix, which is TASK-19.
- Coverage reporting or upload.
- Release or publishing automation.

### [TASK-21] Improve contributor setup instructions

**Status:** OPEN
**GitHub issue:** [#21](https://github.com/ismayilzeynal/tabulint-oss-az/issues/21)
**Labels:** `documentation`, `good first issue`

**Goal**

Make the contributor setup instructions work first time on every supported platform, and add the troubleshooting a newcomer actually needs.

**Why useful**

Setup friction is where most first contributions are lost. The current instructions are correct but thin: they do not cover what to do when `tabulint` is not on PATH after an editable install, or how to run a single test while iterating.

**Likely files**

- `CONTRIBUTING.md`
- `README.md`

**Requirements**

- Verify every command in CONTRIBUTING.md on at least one platform and fix anything that does not work verbatim.
- Give the virtual-environment activation command for Linux, macOS, Windows PowerShell and Windows cmd.
- Explain how to run a single test file, a single test, and the full suite.
- Explain how to run the CLI from a source checkout, including the `python -m tabulint.cli` fallback when the console script is not on PATH.
- Add a short troubleshooting section covering the two or three failures a newcomer actually hits, such as a Python version that is too old or a stale editable install.
- State the minimum Python version in one place and make the README and CONTRIBUTING.md agree with `pyproject.toml`.
- Keep it concise. This is a setup guide, not a tutorial.

**Acceptance criteria**

- A newcomer can go from clone to a passing test run using only the documented commands.
- Activation instructions exist for all four shells listed.
- The stated minimum Python version matches `pyproject.toml`.
- CONTRIBUTING.md remains readable and does not balloon in length.

**Tests required**

- No automated tests are required.
- The pull-request description must state which platform the instructions were verified on.

**Out of scope**

- Adding tox, nox, pre-commit, or a Makefile.
- A code-of-conduct document.
- Continuous-integration changes.

### [TASK-22] Harden user-provided file-path handling

**Status:** OPEN
**GitHub issue:** [#22](https://github.com/ismayilzeynal/tabulint-oss-az/issues/22)
**Labels:** `security`, `enhancement`

**Goal**

Handle unusual and hostile file paths safely and predictably, with clear errors instead of tracebacks.

**Why useful**

The path comes straight from the command line and goes straight to `open`. A directory, a symlink loop, a device file such as `/dev/stdin` or `NUL`, or a file with no read permission currently surfaces as an unhandled `OSError` traceback, which is both unfriendly and a poor security posture for a tool that will be pointed at untrusted paths in CI.

**Likely files**

- `src/tabulint/loader.py`
- `tests/test_loader.py`
- `SECURITY.md`

**Requirements**

- Catch `IsADirectoryError`, `PermissionError` and `OSError` in the loaders and re-raise them as `TabulintError` with a clear message.
- Check explicitly that the path refers to a regular file, and reject directories and device or special files with a specific message.
- Handle a symlink loop without hanging or producing a traceback.
- Never print the resolved absolute path when the user gave a relative one; echo back what they typed, so a report cannot leak more of the file-system layout than the user already knew.
- Do not silently follow or block symlinks in general; a symlink to a normal readable file must keep working.
- Confirm that a path is never passed to a shell and never interpolated into one anywhere in the codebase.
- Update the scope section of SECURITY.md if this changes what is in scope.

**Acceptance criteria**

- Passing a directory exits 2 with a clear message and no traceback.
- Passing an unreadable file exits 2 with a clear message and no traceback.
- A symlink to a valid dataset still loads normally.
- No code path leaks a traceback to the user for a path problem.

**Tests required**

- Loading a directory raises `TabulintError`.
- Loading a file with permissions removed raises `TabulintError`, skipped on platforms where that cannot be arranged.
- A symlinked dataset loads correctly, skipped where symlinks are unavailable.
- The CLI exits 2 rather than raising for each of these cases.

**Out of scope**

- Sandboxing or dropping privileges.
- Restricting reads to a specific directory root.
- Auditing file contents for malicious payloads.

### [TASK-23] Formalize CLI exit-code behavior

**Status:** OPEN
**GitHub issue:** [#23](https://github.com/ismayilzeynal/tabulint-oss-az/issues/23)
**Labels:** `cli`, `documentation`, `testing`

**Goal**

Turn the exit codes into a documented, tested contract, and separate errors from warnings.

**Why useful**

Exit codes are the whole interface when tabulint runs in a pipeline. Today code 1 covers both a fatal type mismatch and a single informational warning, so there is no way to fail a build on errors while tolerating warnings.

**Likely files**

- `src/tabulint/cli.py`
- `tests/test_cli.py`
- `README.md`

**Requirements**

- Document the exit codes in one authoritative place and reference it from the README.
- Keep the existing meanings: 0 clean, 1 issues found, 2 could not run.
- Add a `--fail-on {error,warning,never}` option, defaulting to `warning` so current behavior is preserved exactly.
- With `--fail-on error`, a dataset with only warnings exits 0.
- With `--fail-on never`, the report is still printed but the exit code is 0 whenever the dataset loaded.
- Code 2 must never be suppressed by `--fail-on`; a tool that cannot run has to say so.
- Add a test for every documented exit code so the contract cannot drift silently.

**Acceptance criteria**

- The README documents each exit code and the flag.
- The default behavior is byte-for-byte identical to today.
- `--fail-on error` exits 0 on a warning-only dataset and 1 when an error is present.
- `--fail-on never` still exits 2 for a missing file.

**Tests required**

- Each exit code has at least one dedicated test.
- Each `--fail-on` value is tested against warning-only, error-present and clean datasets.
- A load failure exits 2 under every `--fail-on` value.

**Out of scope**

- Adding more exit codes for specific failure kinds.
- Per-check severity configuration.
- Changing the default severity of any existing check.

### [TASK-24] Improve type hints in one core area

**Status:** OPEN
**GitHub issue:** [#24](https://github.com/ismayilzeynal/tabulint-oss-az/issues/24)
**Labels:** `enhancement`, `documentation`

**Goal**

Tighten the type hints in one module so the intent is checkable rather than merely described.

**Why useful**

`Record` is `dict[str, object]` and issue codes and severities are bare strings, so a typo in a severity is invisible until a test catches it. Precise types in one focused area make the contract real without turning the codebase into a type-theory exercise.

**Likely files**

- `src/tabulint/models.py`
- `src/tabulint/analyzer.py`
- `pyproject.toml`
- `tests/test_analyzer.py`

**Requirements**

- Pick one area and do it properly. The strongest candidate is `models.py` plus the code that constructs `Issue`.
- Replace the bare severity string with a `Literal` type or an enum, and do the same for the inferred type names returned by `infer_type`.
- If you introduce an enum, keep the rendered report output identical; this is an internal typing change, not a user-visible one.
- Make sure `mypy --strict` passes on the module you changed, and add the configuration for it to `pyproject.toml`.
- Do not add type hints to code you did not otherwise touch, and do not annotate every function in the codebase.
- Add mypy as a dev-only dependency; it must never become a runtime dependency.
- Optionally add a type-check step to CI, but only if it passes cleanly for the whole checked area.

**Acceptance criteria**

- `mypy --strict` passes on the chosen module.
- An invalid severity or type name is a type error rather than a silent bug.
- Report output and every existing test are unchanged.
- No runtime dependency is added.

**Tests required**

- Existing tests pass unchanged.
- If an enum is introduced, a test asserting the rendered output is unchanged.
- A test asserting the valid severity and type-name sets match what the checks actually emit.

**Out of scope**

- Annotating the entire codebase.
- Adding pydantic or another validation library.
- Runtime type enforcement.

### [TASK-25] Improve changelog and release instructions

**Status:** OPEN
**GitHub issue:** [#25](https://github.com/ismayilzeynal/tabulint-oss-az/issues/25)
**Labels:** `documentation`, `ci`

**Goal**

Write down how a release is actually cut, and make the changelog convention explicit enough to follow.

**Why useful**

There is a CHANGELOG.md with an Unreleased section and a version number in two places, but nothing explains who bumps them, in what order, or how a tag becomes a release. Without that, the changelog quietly stops being accurate after a few merges.

**Likely files**

- `CHANGELOG.md`
- `CONTRIBUTING.md`
- `RELEASING.md`
- `pyproject.toml`

**Requirements**

- Add a short `RELEASING.md` with the exact ordered steps: update the changelog, bump the version, commit, tag, push the tag, build, publish.
- Document where the version number lives and every place that must be updated together.
- State the versioning policy for a pre-1.0 project, in particular what a breaking change means before 1.0.
- Add a section to CONTRIBUTING.md explaining what a contributor should add to the `Unreleased` section and under which Keep a Changelog heading.
- Give an example changelog entry so the convention is copyable rather than merely described.
- Document the tag format, matching the `v0.1.0` link already used at the bottom of CHANGELOG.md.
- Keep the process manual if that is honest. Do not add release automation as part of this task.

**Acceptance criteria**

- RELEASING.md exists and its steps can be followed end to end without guessing.
- CONTRIBUTING.md tells a contributor exactly what changelog entry to write.
- Every place holding a version number is listed.
- The documented tag format matches the existing links in CHANGELOG.md.

**Tests required**

- Optionally a test asserting that the package `__version__` matches the version in `pyproject.toml`, which prevents the two drifting apart.

**Out of scope**

- Automated publishing to PyPI.
- Release-drafting bots or changelog generators.
- Signed releases or provenance attestation.
