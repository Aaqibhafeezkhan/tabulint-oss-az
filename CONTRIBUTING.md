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
# Linux / macOS
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1

python -m pip install -e ".[dev]"
python -m pytest
```

## 5. Create a focused branch

One branch per issue. Name it after the task ID you are working on:

```bash
git checkout -b task-03-csv-delimiter
```

## 6. Implement exactly one issue

Pick an issue from the [issue tracker](https://github.com/ismayilzeynal/tabulint-oss-az/issues).
Each issue maps to a task in [CONTRIBUTOR_TASKS.md](CONTRIBUTOR_TASKS.md), which
lists the goal, the likely files, the acceptance criteria, the required tests,
and what is out of scope. Stay inside that scope; unrelated refactors make a pull
request much harder to review.

Style notes:

- Standard library only; do not add runtime dependencies.
- Prefer a plain function over a new class or abstraction.
- Match the surrounding code: short modules, short functions, few comments.
- Update `README.md` when you change user-visible behavior.
- Add an entry to the `Unreleased` section of `CHANGELOG.md`.

## 7. Run the tests

```bash
python -m pytest
```

Run the whole suite before you push, not only the tests you added. Every pull
request must leave the suite green.

## 8. Commit

Write a commit message that describes the software change:

```bash
git add .
git commit -m "Add CSV delimiter option"
```

Good subjects are imperative and specific: `Add allowed-values validation`,
`Improve malformed JSON errors`, `Fix boolean inference for yes/no`. Avoid
`update`, `fix stuff`, or `wip`. Do not add attribution trailers for tooling you
used; commit under your own Git identity.

## 9. Push to your fork

```bash
git push -u origin task-03-csv-delimiter
```

## 10. Open a pull request against upstream `main`

```bash
gh pr create --repo ismayilzeynal/tabulint-oss-az --base main
```

Or use the "Compare & pull request" button GitHub shows after the push.

In the pull-request description, state the problem, the change you made, and the
tests you ran. Reference the issue so it closes on merge:

```
Closes #12
```

## Review

A maintainer will review the pull request and may ask for changes. Push new
commits to the same branch; the pull request updates automatically.

## Reporting bugs and ideas

Open an issue using one of the templates in
[.github/ISSUE_TEMPLATE](.github/ISSUE_TEMPLATE). For anything security-related,
follow [SECURITY.md](SECURITY.md) instead of opening a public issue.
