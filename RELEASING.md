# Releasing tabulint

Releases are published manually to GitHub with a wheel, source distribution,
and SHA-256 checksums. The PyPI name `tabulint` belongs to an unrelated project;
never upload this distribution to that name or tell users to install it from
PyPI. Publishing there would require a distinct distribution name and a separate
release process.

## Release history

`0.1.0` in the changelog is the initial development baseline, not a previously
published GitHub Release. There was no `v0.1.0` tag. The first published release
is `v0.2.0`; do not create a backdated release or move tags to make the historical
changelog look published.

## Prepare the release

1. Confirm a clean checkout and the upstream remote. Fetch the latest `main`
   and inspect existing tags/releases before choosing a version:

   ```sh
   git status --short
   git remote -v
   git fetch origin main --tags
   git tag --list
   gh release list --repo ismayilzeynal/tabulint-oss-az
   ```

2. Use Semantic Versioning. Before 1.0, compatible features and breaking changes
   bump the minor version; compatible bug fixes bump the patch. For example,
   the next feature release after 0.2.0 would be 0.3.0. Update `pyproject.toml`,
   `src/tabulint/__init__.py`, the dated changelog section and link references,
   and the supported-version table in `SECURITY.md`. Keep an empty Unreleased
   section. Use the actual publication date.

3. Open a focused release-preparation PR. Run the full suite, mypy, and
   `git diff --check`; wait for all applicable CI before merging. The scanner
   environment workflow also builds the audit image and runs tests offline
   when its relevant files change.

4. Build from the final, clean merged commit in an isolated environment:

   ```sh
   python -m venv .release-venv
   # Activate using the instructions for your shell in CONTRIBUTING.md.
   python -m pip install build twine
   python -m build --outdir release-dist
   python -m twine check release-dist/*
   ```

   Use a new output directory for each release. Do not accidentally upload old
   artifacts. Test the wheel and source distribution in separate fresh virtual
   environments, outside the checkout: check `tabulint --version`,
   `python -m tabulint.cli --version`, and clean/warning/error CLI examples.
   The installed package metadata and Python `__version__` must agree.
   This manual release verification does not replace the broader installed
   distribution CI work tracked in #69.

5. Produce a `SHA256SUMS` file covering the exact wheel and source archive.
   Inspect their contents for expected package files and unintended material.
   Record the final commit and test results in the release notes.

## Publish and verify

Create one annotated tag on that merged commit and push it. For the first
release:

```sh
git tag -a v0.2.0 <verified-release-commit> -m "Release 0.2.0"
git push origin v0.2.0
gh release create v0.2.0 <wheel-file> <source-archive> <SHA256SUMS-file> --repo ismayilzeynal/tabulint-oss-az --verify-tag --title "v0.2.0" --notes-file <release-notes-file>
```

For later releases, replace the version and use the verified new commit.
Do not overwrite an existing tag or use `--clobber` on published artifacts.

Download the published artifacts into a fresh directory, compare SHA-256
checksums and smoke-test the downloaded wheel. Confirm the release points to
its intended main-branch commit, both distributions are attached, and changelog
links resolve. Give users the GitHub Release URL and explicit wheel/source
installation instructions.