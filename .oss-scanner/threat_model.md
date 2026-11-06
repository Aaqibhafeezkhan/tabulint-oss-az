# tabulint threat model

## Purpose and trust boundaries

tabulint is a local Python CLI/library that loads CSV, JSON, JSONL and NDJSON
files and reports data-quality findings. It has no runtime dependencies, opens
no network connections, and executes no code from input data. There is no
authentication system, remote service, plugin loader, or database.

Treat file bytes, JSON keys/values, CSV headers, field names, paths, encodings,
and CLI rule arguments as potentially hostile. The immediate caller chooses
the input and output paths. A downstream application may pass files received
from somebody else; that is a possible integration, not evidence of existing
production deployments.

The tool is not a filesystem sandbox or a streaming/bounded-resource parser.
It may read any regular file accessible to the caller. Symlinks to regular
files are allowed, and the filesystem can change between checking a path and
using it. Report output deliberately overwrites the selected output file;
input/output aliases are rejected as a data-loss safeguard, not a complete
defence against an attacker who controls the filesystem concurrently.

## Components to examine

- `src/tabulint/loader.py`: CSV quoting/headers/delimiters, JSON object hooks,
  decoding, deep nesting, oversized values, blank inputs, special files and
  error paths. Duplicate keys/headers must not cause silent overwrites.
- `analyzer.py`, `_numbers.py`, `validators.py`: adversarial nested values,
  duplicate grouping, integer/float boundaries, and CPU or memory amplification.
- `report.py`, `cli.py`: hostile field names, paths and messages rendered as
  terminal text or JSON; output alias checks, encoding failures, and partial
  output writes. This release does not promise atomic output replacement.
- Public API calls can supply native Python values as well as file-derived
  records. Distinguish documented input types from arbitrary Python objects
  whose methods already execute caller-controlled code.

The scan is for this repository's code. Report standard-library or development
dependency issues to their own maintainers unless tabulint's integration adds
a concrete, independently exploitable problem.

## Exercising the checkout offline

The image installs the development environment and builds a wheel/sdist during
the online Docker build. Source and examples remain at `/src`; artifacts are
under `/opt/tabulint-dist`. From `/src`, with networking disabled:

```sh
python -m pytest -q
python -m mypy
python -m tabulint.cli examples/clean.csv
python -m tabulint.cli examples/missing.csv --format json --fail-on error
```

See `tests/test_input_paths.py`, `test_output_safety.py`, `test_loader.py`,
`test_loader_failures_cli.py`, `test_numeric_inference.py`, and
`test_duplicate_records_api.py` for focused regressions. Tests for Windows
console/path behaviour are meaningful on Windows; unsupported platform tests
may skip in the Linux image.

Run resource-exhaustion reproducers with explicit OS memory/CPU/time limits.
Do not send test traffic to external services or access personal files. Use
temporary directories and synthetic data for path/output demonstrations.

## Severity and useful findings

Rate impact in the documented local execution model. Arbitrary code execution
or unintended disclosure/overwrite outside the caller-selected boundaries is
more serious than a malformed-input crash. An availability issue needs the
input size, observed CPU/memory cost and a plausible untrusted-file workflow;
the mere fact that a huge file uses memory is not enough to establish severity.

Wrong validation results without a security consequence are ordinary bugs.
Network/remote severity should not be assumed for this local tool. Unsupported
native API objects or an attacker who already has equivalent local privileges
do not establish a new privilege boundary by themselves.

Provide a minimal reproducer, expected/observed behaviour, Python/OS versions,
affected code, and resource measurements where relevant. Suggested patches
should preserve documented CLI exit codes and include a focused regression.
Group reports with the same root cause; send security findings through the
channel in `SECURITY.md`.
