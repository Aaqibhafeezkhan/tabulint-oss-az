# Security Policy

## Supported versions

`tabulint` is pre-1.0. Security fixes target the latest published release and
the current `main` branch; older development snapshots are not supported.

| Version | Supported |
| --- | --- |
| 0.2.x / current main | Yes |
| older | No |

## Reporting a vulnerability

Please do **not** open a public issue for a security problem.

The maintainer's public security contact is
**ismayilbaxish+oss@gmail.com**. This address accepts private security reports
and scanner correspondence. You may use email or the GitHub channel below.

Report it privately through GitHub's
[private vulnerability reporting](https://github.com/ismayilzeynal/tabulint-oss-az/security/advisories/new)
on this repository. Include:

- what the problem is,
- the steps or input needed to reproduce it,
- the affected version and your Python version and operating system,
- the impact as you understand it.

You can expect an initial response within 7 days. If the report is confirmed, a
fix will be prepared and released, and you will be credited in the advisory
unless you prefer otherwise.

## Scope

`tabulint` reads local files supplied by the person running it. It opens no
network connections, executes nothing from the data it reads, and has no runtime
dependencies. The realistic risk areas are therefore:

- crashes, hangs, or unbounded memory use triggered by crafted CSV or JSON input,
- unintended file-system access through a user-supplied path,
- unsafe handling of file contents when a report is rendered.

Reports in these areas are in scope. A dataset that simply produces a wrong or
noisy data-quality report is a normal bug: open a public issue for it.

Dataset readers reject directories, device files, and other special files
before reading, and accept symbolic links to regular files. This is input
validation, not a sandbox: paths can still select any regular file accessible
to the current user, and the filesystem can change between validation and use.

For audit scope, reproducible offline test commands, and severity guidance,
see the [threat model](.oss-scanner/threat_model.md) and
[scanner environment](.oss-scanner/README.md).
