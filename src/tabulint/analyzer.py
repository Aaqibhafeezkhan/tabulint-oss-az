"""Type inference and the built-in structural checks."""

from collections import Counter

from .models import FieldProfile, Issue, Record

BOOLEAN_LITERALS = {"true", "false"}


def is_missing(value: object) -> bool:
    """Return True for values that count as missing/null."""
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    return False


def infer_type(value: object) -> str:
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
        return "float"
    if not isinstance(value, str):
        return "string"

    text = value.strip()
    if text.lower() in BOOLEAN_LITERALS:
        return "boolean"
    try:
        int(text)
        return "integer"
    except ValueError:
        pass
    try:
        float(text)
        return "float"
    except ValueError:
        return "string"


def field_names(records: list[Record]) -> list[str]:
    """Collect field names in first-seen order across all records."""
    names: list[str] = []
    for record in records:
        for name in record:
            if name not in names:
                names.append(name)
    return names


def profile_fields(records: list[Record]) -> list[FieldProfile]:
    """Build a FieldProfile for every field in the dataset."""
    profiles = []
    for name in field_names(records):
        counts: Counter[str] = Counter()
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


def _record_key(record: Record, names: list[str]) -> tuple[str, ...]:
    return tuple(repr(record.get(name)) for name in names)


def check_duplicates(records: list[Record]) -> list[Issue]:
    """Report records identical to an earlier record."""
    names = field_names(records)
    seen: dict[tuple[str, ...], int] = {}
    issues = []
    for row, record in enumerate(records, start=1):
        key = _record_key(record, names)
        first = seen.get(key)
        if first is None:
            seen[key] = row
        else:
            issues.append(
                Issue(
                    code="duplicate-record",
                    severity="warning",
                    message=f"record is a duplicate of row {first}",
                    row=row,
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
            issues.append(
                Issue(
                    code="type-mismatch",
                    severity="error",
                    message=(
                        f"field '{name}' expects {profile.dominant_type} "
                        f"but value {value!r} looks like {actual}"
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
