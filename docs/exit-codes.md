# Exit-code contract

`tabulint` uses three exit codes. Codes 0 and 1 apply after the dataset loads
and the report is rendered; code 2 is reserved for failures that prevent a
successful run or report write.

| Code | Meaning |
| --- | --- |
| `0` | The dataset loaded and no issue meets the selected `--fail-on` threshold. |
| `1` | The dataset loaded and at least one issue meets the selected `--fail-on` threshold. |
| `2` | The dataset could not be loaded, the arguments were invalid, or the report could not be written. |

## `--fail-on`

The option accepts `warning`, `error`, or `never` and defaults to `warning`.

- `--fail-on warning` returns 1 when the report contains any warning or error.
  This is the default and preserves the original behavior.
- `--fail-on error` returns 1 only when the report contains an error. A
  warning-only report returns 0.
- `--fail-on never` returns 0 for every dataset that loads, including reports
  containing warnings or errors. The report is still printed or written as
  requested.

Load failures, invalid arguments, and output-write failures always return 2,
regardless of `--fail-on`.

`--allow-empty` removes only the `empty-dataset` warning before applying this
threshold and rendering the report. Blank files, header-only CSVs, and empty
JSON arrays can therefore exit 0. Other warnings/errors are still evaluated,
and load, argument, or output-write failures still exit 2.
