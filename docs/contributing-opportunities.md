# Contribution opportunities

`tabulint` is a small Python CLI and library for checking CSV, JSON, and JSON
Lines data. New contributors are welcome from anywhere; you do not need an
invitation or an existing connection to the maintainer.

Start with the [open good first issues](https://github.com/ismayilzeynal/tabulint-oss-az/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22+-label%3Aclaimed)
or [all unclaimed help wanted issues](https://github.com/ismayilzeynal/tabulint-oss-az/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22+-label%3Aclaimed).
The issue discussion and assignment are the source of truth for availability;
the table below is a roadmap snapshot from 2026-10-25.

## Choose a task

| Issue | User benefit | Starting level |
| --- | --- | --- |
| [#66: Reject CR/LF delimiters](https://github.com/ismayilzeynal/tabulint-oss-az/issues/66) | Prevent a misleading single-column CSV result from an unusable field delimiter. | Good first issue |
| [#67: Reject non-standard JSON constants](https://github.com/ismayilzeynal/tabulint-oss-az/issues/67) | Catch malformed NaN/Infinity tokens while keeping quoted text valid. | Good first issue |
| [#68: Configure text issue limits](https://github.com/ismayilzeynal/tabulint-oss-az/issues/68) | Inspect findings beyond the current 50-issue text limit. | Good first issue |
| [#69: Verify installed distributions](https://github.com/ismayilzeynal/tabulint-oss-az/issues/69) | Test real wheel/sdist installs and support the conventional module entry point. | Some packaging/CI experience |
| [#70: Test a GitHub Actions recipe](https://github.com/ismayilzeynal/tabulint-oss-az/issues/70) | Adopt a data-quality gate that retains JSON reports when checks fail. | Good first issue; documentation/CI |
| [#71: Publish a JSON report schema](https://github.com/ismayilzeynal/tabulint-oss-az/issues/71) | Give report consumers a machine-readable validation contract. | Good first issue; JSON Schema knowledge |
| [#72: Add regex validation](https://github.com/ismayilzeynal/tabulint-oss-az/issues/72) | Validate identifier formats without enumerating every allowed value. | Some Python experience |
| [#73: Validate unique keys](https://github.com/ismayilzeynal/tabulint-oss-az/issues/73) | Find repeated IDs/composite keys even when other columns differ. | Some Python experience |
| [#74: Write reports atomically](https://github.com/ismayilzeynal/tabulint-oss-az/issues/74) | Preserve a complete previous report when writing a replacement fails. | File-system and cross-platform experience |
| [#75: Read gzip inputs](https://github.com/ismayilzeynal/tabulint-oss-az/issues/75) | Check compressed ETL exports without creating a decompressed copy. | Some Python I/O experience |

Each issue explains the current gap, accepted scope, code pointers, edge cases,
and tests. `size: small` describes a bounded implementation surface, not a
guaranteed completion time. Medium tasks are suitable for developers new to
this repository who already know the relevant Python or integration concepts.

## Claim and submit

1. Read [CONTRIBUTING.md](../CONTRIBUTING.md), check comments and linked PRs,
   and choose one unclaimed issue.
2. Comment with your approach and wait for maintainer confirmation before
   implementing. The maintainer marks confirmed claims with `claimed` and an
   assignee so others can choose different work.
3. Use one focused branch and PR. Follow the acceptance criteria, include
   meaningful tests, and reference the issue with `Closes #N`.
4. Run `python -m pytest -q`, `python -m mypy`, and `git diff --check`.
   Explain what changed and what you verified; respond to review on the same PR.

The `new contributors` issues in this onboarding batch are reserved for people
making their first contribution to this repository, with one task per person.
Prior contributors are welcome to report bugs, reproduce problems, review work,
and suggest improvements outside this batch.

If you cannot continue, leave a comment releasing your claim. If there has been
no contributor update for seven days, a maintainer may ask for an update and
release the claim so another person can help. Waiting on a maintainer review
does not count as contributor inactivity.

AI assistance is welcome: understand the implementation, review the complete
diff, and describe the assistance in the PR. Submit from your own account and
use your own Git identity. Starring, following, donations, and invitations are
not required to claim a task or have a PR reviewed or merged.

## Run the project

Python 3.11 or newer and Git are enough to get started. Create a fork on GitHub
first, then clone your fork:

```sh
git clone https://github.com/<your-username>/tabulint-oss-az.git
cd tabulint-oss-az
python -m venv .venv
```

Activate the environment for your shell as shown in
[the setup instructions](../CONTRIBUTING.md#4-set-up-a-development-environment),
then run:

```sh
python -m pip install -e ".[dev]"
python -m pytest -q
python -m mypy
python -m tabulint.cli examples/clean.csv
```

The full fork, upstream-remote, branch, and PR workflow is in CONTRIBUTING.md. Ask task questions
in the issue so the answers help the next contributor too.
