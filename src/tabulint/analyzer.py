"""Type inference and the built-in structural checks."""

from collections import Counter
import math

from ._numbers import _format_number, _parse_number
from .models import FieldProfile, InferredType, Issue, Record, TabulintError

BOOLEAN_LITERALS = {"true", "false", "yes", "no", "y", "n", "t", "f"}


def is_missing(value: object) -> bool:
    """Return True for values that count as missing/null."""
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    return False


def infer_type(value: object) -> InferredType:
    """Infer one of: null, boolean, integer, float, string.

    Strings are parsed, so the CSV text "12" and the JSON number 12 both
    infer as integer.
    """
    if is_missing(value):
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "float" if math.isfinite(value) else "string"
    if not isinstance(value, str):
        return "string"

    text = value.strip()
    if text.lower() in BOOLEAN_LITERALS:
        return "boolean"
    try:
        number = _parse_number(text)
    except ValueError:
        return "string"
    if isinstance(number, int):
        return "integer"
    return "float" if math.isfinite(number) else "string"


def field_names(records: list[Record]) -> list[str]:
    """Collect field names in first-seen order across all records."""
    names: list[str] = []
    seen: set[str] = set()
    for record in records:
        for name in record:
            if name not in seen:
                seen.add(name)
                names.append(name)
    return names


def profile_fields(records: list[Record]) -> list[FieldProfile]:
    """Build a FieldProfile for every field in the dataset."""
    profiles = []
    for name in field_names(records):
        counts: Counter[InferredType] = Counter()
        for record in records:
            counts[infer_type(record.get(name))] += 1
        missing = counts.pop("null", 0)
        dominant = counts.most_common(1)[0][0] if counts else "null"
        profiles.append(
            FieldProfile(
                name=name,
                dominant_type=dominant,
                type_counts=dict(counts),
                missing_count=missing,
            )
        )
    return profiles


def check_missing_values(records: list[Record]) -> list[Issue]:
    """Report every missing value, and fields absent from a record."""
    issues = []
    names = field_names(records)
    for row, record in enumerate(records, start=1):
        for name in names:
            if name not in record:
                issues.append(
                    Issue(
                        code="missing-field",
                        severity="error",
                        message=f"field '{name}' is absent from this record",
                        field_name=name,
                        row=row,
                    )
                )
            elif is_missing(record[name]):
                issues.append(
                    Issue(
                        code="missing-value",
                        severity="warning",
                        message=f"field '{name}' has a missing value",
                        field_name=name,
                        row=row,
                    )
                )
    return issues


def _record_key(record: Record) -> tuple[object, ...]:
    """Build a flat, typed key without depending on object insertion order.

    Container lengths delimit their contents. An explicit stack also keeps
    deeply nested JSON safe during both traversal and hashing of the key.
    """
    key: list[object] = []
    pending: list[tuple[object, bool]] = [(record, False)]
    active: set[int] = set()
    while pending:
        value, finished = pending.pop()
        if finished:
            active.remove(id(value))
        elif isinstance(value, (dict, list)):
            if id(value) in active:
                raise TabulintError("records cannot contain cyclic objects or lists")
            active.add(id(value))
            key.extend((type(value), len(value)))
            pending.append((value, True))
            if isinstance(value, dict):
                for name in sorted(
                    value,
                    key=lambda name: (
                        type(name).__module__, type(name).__qualname__,
                        name if isinstance(name, int) else repr(name),
                    ),
                    reverse=True,
                ):
                    pending.append((value[name], False))
                    pending.append((name, False))
            else:
                pending.extend((item, False) for item in reversed(value))
        else:
            key.extend((type(value), value if isinstance(value, int) else repr(value)))
    return tuple(key)


DUPLICATE_ROWS_LIMIT = 10


def _format_duplicate_rows(rows: list[int]) -> str:
    shown = rows[:DUPLICATE_ROWS_LIMIT]
    text = ", ".join(str(row) for row in shown)
    remaining = len(rows) - len(shown)
    if remaining > 0:
        text += f", and {remaining} more"
    return text


def check_duplicates(records: list[Record]) -> list[Issue]:
    """Report each group of identical records once, listing every occurrence."""
    first_rows: dict[tuple[object, ...], int] = {}
    duplicate_rows: dict[tuple[object, ...], list[int]] = {}
    for row, record in enumerate(records, start=1):
        key = _record_key(record)
        first = first_rows.get(key)
        if first is None:
            first_rows[key] = row
        else:
            duplicate_rows.setdefault(key, []).append(row)

    issues = []
    for key, rows in duplicate_rows.items():
        first = first_rows[key]
        issues.append(
            Issue(
                code="duplicate-record",
                severity="warning",
                message=(
                    f"record from row {first} is repeated at rows "
                    f"{_format_duplicate_rows(rows)}"
                ),
                row=rows[0],
            )
        )
    return issues


def check_type_consistency(records: list[Record]) -> list[Issue]:
    """Report values whose type differs from the field's dominant type."""
    issues = []
    for profile in profile_fields(records):
        if profile.dominant_type == "null" or len(profile.type_counts) < 2:
            continue
        name = profile.name
        for row, record in enumerate(records, start=1):
            value = record.get(name)
            actual = infer_type(value)
            if actual in ("null", profile.dominant_type):
                continue
            if profile.dominant_type == "float" and actual == "integer":
                continue
            displayed_value = _format_number(value) if isinstance(value, int) else repr(value)
            issues.append(
                Issue(
                    code="type-mismatch",
                    severity="error",
                    message=(
                        f"field '{name}' expects {profile.dominant_type} "
                        f"but value {displayed_value} looks like {actual}"
                    ),
                    field_name=name,
                    row=row,
                )
            )
    return issues


def analyze(records: list[Record]) -> list[Issue]:
    """Run every built-in structural check."""
    return (
        check_missing_values(records)
        + check_duplicates(records)
        + check_type_consistency(records)
    )
