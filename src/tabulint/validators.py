"""User-supplied validation rules."""

from dataclasses import dataclass
import math

from ._numbers import _format_number, _parse_number
from .analyzer import is_missing
from .models import Issue, Record, TabulintError


def _is_finite_number(value: object) -> bool:
    if isinstance(value, bool):
        return False
    return isinstance(value, int) or isinstance(value, float) and math.isfinite(value)


def check_required_fields(records: list[Record], names: list[str]) -> list[Issue]:
    """Check required fields in first-requested order, then record order."""
    issues = []
    if not records:
        return issues
    for name in dict.fromkeys(names):
        if not any(name in record for record in records):
            issues.append(
                Issue(
                    code="required-missing",
                    severity="error",
                    message=f"required field '{name}' is absent from every record",
                    field_name=name,
                )
            )
            continue
        for row, record in enumerate(records, start=1):
            if is_missing(record.get(name)):
                issues.append(
                    Issue(
                        code="required-missing",
                        severity="error",
                        message=f"required field '{name}' is absent or has a missing value",
                        field_name=name,
                        row=row,
                    )
                )
    return issues


@dataclass(frozen=True)
class NumericRule:
    """A minimum and/or maximum bound for one numeric field."""

    field_name: str
    minimum: int | float | None = None
    maximum: int | float | None = None

    def __post_init__(self) -> None:
        for name, bound in (("minimum", self.minimum), ("maximum", self.maximum)):
            if bound is not None and not _is_finite_number(bound):
                raise TabulintError(
                    f"field '{self.field_name}': {name} {bound!r} is not a finite number"
                )
        if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
            raise TabulintError(
                f"field '{self.field_name}': minimum {_format_number(self.minimum)} "
                f"is greater than maximum {_format_number(self.maximum)}"
            )


def parse_bound(text: str) -> tuple[str, int | float]:
    """Parse a `field=number` command-line bound."""
    name, separator, raw = text.partition("=")
    if not separator or not name.strip():
        raise TabulintError(f"invalid bound '{text}' (expected field=number)")
    try:
        value = _parse_number(raw)
    except ValueError as exc:
        raise TabulintError(f"invalid bound '{text}' ('{raw}' is not a number)") from exc
    if not _is_finite_number(value):
        raise TabulintError(
            f"invalid bound '{text}' ('{raw.strip()}' is not a finite number)"
        )
    return name.strip(), value


def build_numeric_rules(
    minimums: list[str] | None = None,
    maximums: list[str] | None = None,
) -> list[NumericRule]:
    """Turn `field=number` bounds into one NumericRule per field."""
    low = dict(parse_bound(item) for item in minimums or [])
    high = dict(parse_bound(item) for item in maximums or [])
    rules = []
    for name in list(low) + [n for n in high if n not in low]:
        rule = NumericRule(name, low.get(name), high.get(name))
        rules.append(rule)
    return rules


def _as_number(value: object) -> int | float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, str):
        try:
            value = _parse_number(value.strip())
        except ValueError:
            return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return value
    return None


def check_numeric_rules(records: list[Record], rules: list[NumericRule]) -> list[Issue]:
    """Check numeric bounds against every record."""
    issues = []
    for rule in rules:
        for row, record in enumerate(records, start=1):
            if rule.field_name not in record:
                continue
            value = record[rule.field_name]
            if is_missing(value):
                continue
            number = _as_number(value)
            if number is None:
                issues.append(
                    Issue(
                        code="not-numeric",
                        severity="error",
                        message=f"field '{rule.field_name}' has non-numeric value {value!r}",
                        field_name=rule.field_name,
                        row=row,
                    )
                )
                continue
            if rule.minimum is not None and number < rule.minimum:
                issues.append(
                    Issue(
                        code="below-minimum",
                        severity="error",
                        message=(
                            f"field '{rule.field_name}' value {_format_number(number)} "
                            f"is below minimum {_format_number(rule.minimum)}"
                        ),
                        field_name=rule.field_name,
                        row=row,
                    )
                )
            if rule.maximum is not None and number > rule.maximum:
                issues.append(
                    Issue(
                        code="above-maximum",
                        severity="error",
                        message=(
                            f"field '{rule.field_name}' value {_format_number(number)} "
                            f"is above maximum {_format_number(rule.maximum)}"
                        ),
                        field_name=rule.field_name,
                        row=row,
                    )
                )
    return issues


@dataclass(frozen=True)
class LengthRule:
    """A minimum and/or maximum character length for one field."""

    field_name: str
    minimum: int | None = None
    maximum: int | None = None


def parse_length_bound(text: str) -> tuple[str, int]:
    """Parse a non-negative integer field length bound."""
    name, separator, raw = text.partition("=")
    if not separator or not name.strip():
        raise TabulintError(f"invalid length bound '{text}' (expected field=integer)")
    try:
        value = int(raw)
    except ValueError as exc:
        raise TabulintError(f"invalid length bound '{text}' ('{raw}' is not an integer)") from exc
    if value < 0:
        raise TabulintError(f"invalid length bound '{text}' (length cannot be negative)")
    return name.strip(), value


def build_length_rules(
    minimums: list[str] | None = None,
    maximums: list[str] | None = None,
) -> list[LengthRule]:
    """Build one length rule per field from repeatable bounds."""
    low = dict(parse_length_bound(item) for item in minimums or [])
    high = dict(parse_length_bound(item) for item in maximums or [])
    rules = []
    for name in list(low) + [n for n in high if n not in low]:
        rule = LengthRule(name, low.get(name), high.get(name))
        if rule.minimum is not None and rule.maximum is not None and rule.minimum > rule.maximum:
            raise TabulintError(
                f"field '{name}': minimum length {rule.minimum} is greater than maximum length {rule.maximum}"
            )
        rules.append(rule)
    return rules


def check_length_rules(records: list[Record], rules: list[LengthRule]) -> list[Issue]:
    """Check character lengths on the string form of each non-missing value."""
    issues = []
    for rule in rules:
        for row, record in enumerate(records, start=1):
            if rule.field_name not in record:
                continue
            value = record[rule.field_name]
            if is_missing(value):
                continue
            length = len(str(value))
            if rule.minimum is not None and length < rule.minimum:
                issues.append(Issue(
                    code="below-min-length", severity="error",
                    message=f"field '{rule.field_name}' length {length} is below minimum length {rule.minimum}",
                    field_name=rule.field_name, row=row,
                ))
            if rule.maximum is not None and length > rule.maximum:
                issues.append(Issue(
                    code="above-max-length", severity="error",
                    message=f"field '{rule.field_name}' length {length} is above maximum length {rule.maximum}",
                    field_name=rule.field_name, row=row,
                ))
    return issues
