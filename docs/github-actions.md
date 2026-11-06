# GitHub Actions recipe: data-quality gate with JSON artifacts

Copy the workflow below into a downstream repository (for example
`.github/workflows/data-quality.yml`) to validate a dataset on every push
and pull request, keep the JSON report as a downloadable artifact even when
the gate fails, and fail the job on the validation's actual exit code.

The recipe uses only the current CLI (`python -m tabulint.cli`) and the
checked-in example dataset `examples/missing.csv`, which has one blank cell
(a `missing-value` warning). A downstream repository does not have this
project's `examples/` directory: when you copy the recipe, either copy the
example CSV files into your own repository or replace
`examples/missing.csv` (and `examples/clean.csv`, used in the table below)
with the paths to your own data.

## Complete workflow

```yaml
name: Data quality gate

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  tabulint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7

      - uses: actions/setup-python@v7
        with:
          python-version: "3.12"

      - name: Install tabulint from source
        run: python -m pip install "git+https://github.com/ismayilzeynal/tabulint-oss-az.git@0af5e041d5948daa63b601dec2652081f47d9f25"

      - name: Validate data
        id: validate
        shell: python
        env:
          DATASET_PATH: examples/missing.csv
        run: |
          import os
          import subprocess
          import sys
          from pathlib import Path

          # A load failure must not upload an old report from an earlier run.
          Path("tabulint-report.json").unlink(missing_ok=True)
          result = subprocess.run([
              sys.executable, "-m", "tabulint.cli", os.environ["DATASET_PATH"],
              "--format", "json", "--output", "tabulint-report.json", "--fail-on", "error",
          ])
          with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
              output.write(f"exit_code={result.returncode}\n")

      - name: Upload JSON report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: tabulint-report
          path: tabulint-report.json
          retention-days: 7
          if-no-files-found: warn

      - name: Apply the data-quality gate
        if: always()
        shell: python
        env:
          VALIDATION_EXIT_CODE: ${{ steps.validate.outputs.exit_code }}
        run: |
          import os
          import sys

          status = os.environ.get("VALIDATION_EXIT_CODE", "")
          if status not in {"0", "1", "2"}:
              print("Validation did not finish with a recognized exit code.", file=sys.stderr)
              sys.exit(2)
          sys.exit(int(status))
```

No PAT, secret, deployment, or elevated repository permission is needed:
the workflow only checks out code, installs a package, and uploads an
artifact.

## Installing tabulint

Do not use `pip install tabulint`: that PyPI name belongs to an unrelated
project. Install from this repository's source instead, pinned to a real
immutable revision — the full commit SHA in the `git+https://...` URL above.
A branch name or a short SHA is not a pin: branches move, and short SHAs can
be ambiguous.

To update the pin, replace the SHA with the full SHA of a newer commit on
`main` (open the commit on GitHub and copy its full SHA), then re-run the
local checks in [Local verification](#local-verification) before pushing.

## Reading the result

The `Validate data` step runs with `--fail-on error`, so warnings are
tolerated and only real errors fail the gate. `examples/missing.csv` has
one `missing-value` warning, so the step exits 0 and the gate passes —
even though the JSON report's `ok` is still `false`. The gate follows the
CLI's actual exit code, not the report's `ok` field. The validation script
stores that code as a step output and allows artifact upload to run before
the final gate applies it. The `Upload JSON
report` step still runs because of `if: always()`, so the JSON report is
available as the `tabulint-report` artifact (kept for 7 days) whether the
gate passes or fails. The final step then fails the job using the
stored exit code (0, 1, or 2), instead of masking failures with
`|| true`.

The final gate runs even if upload fails. A missing or unexpected validation
exit code fails with 2; installation or artifact-upload failures still fail
their own steps. Before validation, any old report is removed so a load
failure cannot upload a stale report. `if-no-files-found: warn` handles the
expected absence of JSON after a load failure.

Exit codes below are for the workflow's `--fail-on error` gate unless
noted.

| Result | Exit code | What it means |
| --- | --- | --- |
| Clean dataset (`examples/clean.csv`) | 0 | The dataset loaded and no issue was found. |
| Warning-only dataset (`examples/missing.csv`) | 0 | The dataset loaded and a warning was found; warnings are tolerated under `--fail-on error`, so the gate passes. The JSON report's `ok` is still `false`. |
| Error dataset (`examples/missing.csv --required age`) | 1 | The dataset loaded and an error (`required-missing`) was found. |
| Bad input (a path that does not exist) | 2 | The dataset could not be loaded. No report file is written, so there is nothing to upload; read the loader error in the `Validate data` step's log. |
| Warning-only dataset (`examples/missing.csv`) under the default `--fail-on warning` | 1 | Contrast: without `--fail-on error`, the same warning fails the gate. |

For contrast, the default threshold is `--fail-on warning`: without the
flag, the same warning-only file fails the gate:

```bash
python -m tabulint.cli examples/missing.csv --format json --output tabulint-report.json
```

With the default, the warning-only `examples/missing.csv` exits 1. See
[Exit-code contract](exit-codes.md) for the complete behavior, including
`--fail-on never`.

## Local verification

The commands in the recipe can be checked locally without GitHub. From the
repository root, after installing the project (`python -m pip install -e .`
or `PYTHONPATH=src`):

```bash
rm -f tabulint-report.json
python -m tabulint.cli examples/clean.csv --fail-on error --format json --output tabulint-report.json
echo $?  # 0: clean dataset

rm -f tabulint-report.json
python -m tabulint.cli examples/missing.csv --fail-on error --format json --output tabulint-report.json
echo $?  # 0: warning-only dataset, warnings tolerated under --fail-on error

rm -f tabulint-report.json
python -m tabulint.cli examples/missing.csv --format json --output tabulint-report.json
echo $?  # 1: warning-only dataset under the default threshold

rm -f tabulint-report.json
python -m tabulint.cli examples/missing.csv --required age --fail-on error --format json --output tabulint-report.json
echo $?  # 1: dataset with a required-missing error

rm -f tabulint-report.json
python -m tabulint.cli examples/does-not-exist.csv --format json --output tabulint-report.json
echo $?  # 2: load failure, no report file is written
```

Each `--output` file is a JSON report: parse it with any JSON parser, or
validate it against [`schemas/report-v1.schema.json`](../schemas/report-v1.schema.json).
These checks are covered by `tests/test_github_actions_recipe.py`.

Local checks verify the commands; running the workflow itself still needs
GitHub. After copying the recipe, confirm the first hosted run shows the
`tabulint-report` artifact and the expected outcome for the example file
(the gate passes on the warning-only dataset) before relying on it.
