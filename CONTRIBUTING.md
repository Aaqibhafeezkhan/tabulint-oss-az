# Contributing to tabulint

Thanks for considering a contribution. `tabulint` is deliberately small: standard
library only, simple functions, small modules. Contributions that keep it that way
are the most welcome kind.

You do **not** need write access to this repository. Every contribution goes
through a fork and a pull request.

## 1. Fork the repository

Use the **Fork** button on <https://github.com/ismayilzeynal/tabulint-oss-az>,
or the GitHub CLI:

```bash
gh repo fork ismayilzeynal/tabulint-oss-az --clone=false
```

## 2. Clone your fork

```bash
git clone https://github.com/<your-username>/tabulint-oss-az.git
cd tabulint-oss-az
```

## 3. Add the upstream remote

This lets you keep your fork in sync with the original project.

```bash
git remote add upstream https://github.com/ismayilzeynal/tabulint-oss-az.git
git remote -v
```

Before starting new work, refresh your `main`:

```bash
git fetch upstream
git checkout main
git merge --ff-only upstream/main
```

## 4. Set up a development environment

Python 3.11 or newer is required.

```bash
python -m venv .venv
```

Activate the environment for your shell:

```bash
# Linux or macOS (bash/zsh)
source .venv/bin/activate
```

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

```bat
REM Windows Command Prompt
.venv\Scripts\activate.bat
```

Then install the project and run its tests:

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

The development dependencies also include mypy. Check the focused core model
and analyzer typing contract with:

```bash
python -m mypy
```

The `pyproject.toml` configuration enables strict checks for these two modules;
the rest of the package is outside this typing task's scope.

CI runs the full suite and CLI smoke test on Ubuntu and Windows with Python
3.11, 3.12, and 3.13. Windows needs no extra setup beyond the PowerShell or
Command Prompt virtual-environment activation shown above. Symbolic-link tests
skip when the local account cannot create links.

## 5. Create a focused branch

Use one branch per issue, with a short descriptive name. Replace `123` in the
examples below with your issue number:

```bash
git checkout -b issue-123-short-description
```

## 6. Implement one focused issue

Pick an issue from the [issue tracker](https://github.com/ismayilzeynal/tabulint-oss-az/issues).
Check its discussion, assignee, and linked pull requests, then comment with
your intended approach before starting. Some issues have a longer description
in [CONTRIBUTOR_TASKS.md](CONTRIBUTOR_TASKS.md). Follow the issue's acceptance
criteria and keep unrelated changes out of the pull request.

Style notes:

- Standard library only; do not add runtime dependencies.
- Prefer a plain function over a new class or abstraction.
- Match the surrounding code: short modules, short functions, few comments.
- Update `README.md` when you change user-visible behavior.
- For user-visible behavior changes, add a brief entry under `Unreleased` in
  `CHANGELOG.md`. Documentation-only, test-only, and internal maintenance changes
  generally do not need an entry.
- Code assistants are welcome. Review the diff yourself, run the tests, and be
  able to explain the change you submit.

### Changelog entries

For a user-visible change, add one short bullet under `## [Unreleased]` in
`CHANGELOG.md`. Put a new feature under `### Added`, a behavior change under
`### Changed`, a deprecation under `### Deprecated`, a removed feature under
`### Removed`, a bug fix under `### Fixed`, or a security fix under
`### Security`. Add the heading if it is missing. Describe the effect for users
in the present tense; leave version numbers and release dates to the maintainer.
For example, a fix for an error that used to be hidden could be:

```markdown
### Fixed

- Report malformed CSV quoting as an error instead of accepting an incomplete record.
```

Documentation-only, test-only, and internal maintenance changes generally do
not need a changelog entry. Maintainers move the `Unreleased` entries into a
dated release section when they publish a release; see [RELEASING.md](RELEASING.md).

## 7. Run the tests

Run one test while iterating, then its file and the full suite before pushing:

```bash
python -m pytest tests/test_cli.py::test_clean_csv_exits_zero
python -m pytest tests/test_cli.py
python -m pytest
```

After the editable install, try the CLI from the checkout:

```bash
tabulint --help
python -m tabulint.cli --help
```

The second command works when the `tabulint` console script is not on `PATH`.

### Setup problems

- If installation rejects your Python version, run `python --version` and
  recreate `.venv` using Python 3.11 or newer.
- If `tabulint` is missing or Python cannot import it, activate `.venv` and
  rerun `python -m pip install -e ".[dev]"`; use `python -m tabulint.cli --help`
  if only the console script is missing.
- If PowerShell blocks `Activate.ps1`, run
  `Set-ExecutionPolicy -Scope Process RemoteSigned` and activate it again.

When asking for help, include your Python version, platform, failing command,
and complete error output.

## 8. Commit

Write a commit message that describes the software change:

```bash
git add .
git commit -m "Describe the change clearly"
```

Good subjects are imperative and specific: `Add allowed-values validation`,
`Improve malformed JSON errors`, `Fix boolean inference for yes/no`. Avoid
`update`, `fix stuff`, or `wip`. Do not add attribution trailers for tooling you
used; commit under your own Git identity.

## 9. Push to your fork

```bash
git push -u origin issue-123-short-description
```

## 10. Open a pull request against upstream `main`

```bash
gh pr create --repo ismayilzeynal/tabulint-oss-az --base main
```

Or use the "Compare & pull request" button GitHub shows after the push.

In the pull-request description, state the problem, the change you made, and the
tests you ran. Reference the issue so it closes on merge:

```
Closes #123
```

## Review

A maintainer will review the pull request and may ask for changes. Push new
commits to the same branch; the pull request updates automatically.

## Reporting bugs and ideas

Open an issue using one of the templates in
[.github/ISSUE_TEMPLATE](.github/ISSUE_TEMPLATE). For anything security-related,
follow [SECURITY.md](SECURITY.md) instead of opening a public issue.
