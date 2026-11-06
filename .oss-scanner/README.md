# Security scanner environment

This directory prepares tabulint for an offline security audit. Its presence
does not mean Anthropic has accepted, scanned, or endorsed the project.

Build and exercise the environment from the repository root:

```sh
docker build -f .oss-scanner/Dockerfile -t tabulint-audit:local .
docker run --rm --network none tabulint-audit:local python -m pytest -q
docker run --rm --network none tabulint-audit:local python -m mypy
```

The base image is pinned by digest, and development dependencies are constrained
in `constraints.txt`. All installation/build steps run during image construction;
the tests above need no network. Refresh pins only after rebuilding and running
the offline checks. Source lives at `/src`; built distributions are available
at `/opt/tabulint-dist`.

The scope and severity guidance is in [threat_model.md](threat_model.md).
An OSS Scanner enrollment should reference `.oss-scanner/Dockerfile` and
`.oss-scanner/threat_model.md` using the official
[project template](https://github.com/anthropics/oss-scanner/blob/main/templates/project.yaml).
It also needs a working public contact address. Enrollment is reviewed by
Anthropic; build success alone establishes no eligibility decision.

[project.yaml.example](project.yaml.example) is the prepared configuration
using the maintainer's public security contact in [SECURITY.md](../SECURITY.md).
Copy it as the only `project.yaml` in an enrollment directory; the Dockerfile
and threat model are referenced from this repository, not duplicated beside it.
This is a template, not a record of an accepted enrollment. Email reports are
configured; GitHub advisory delivery is left disabled in this template until
the separate trusted-reporter setup is deliberately enabled.
