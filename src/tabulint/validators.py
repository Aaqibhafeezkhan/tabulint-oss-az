"""User-supplied validation rules."""

from dataclasses import dataclass
import math

from .analyzer import is_missing
from .models import Issue, Record, TabulintError


@dataclass(frozen=True)
class NumericRule:
    """A minimum and/or maximum bound for one numeric field."""

    field_name: str
    minimum: float | None = None
    maximum: float | None = None


def parse_bound(text: str) -> tuple[str, float]:
    """Parse a `field=number` command-line bound."""
    name, separator, raw = text.partition("=")
    if not separator or not name.strip():
        raise TabulintError(f"invalid bound '{text}' (expected field=number)")
    try:
        value = float(raw)
    except ValueError as exc:
        raise TabulintError(f"invalid bound '{text}' ('{raw}' is not a number)") from exc
    if not math.isfinite(value):
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
        if rule.minimum is not None and rule.maximum is not None and rule.minimum > rule.maximum:
            raise TabulintError(
                f"field '{name}': minimum {rule.minimum} is greater than maximum {rule.maximum}"
            )
        rules.append(rule)
    return rules


def _as_number(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
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
                        message=f"field '{rule.field_name}' value {number:g} is below minimum {rule.minimum:g}",
                        field_name=rule.field_name,
                        row=row,
                    )
                )
            if rule.maximum is not None and number > rule.maximum:
                issues.append(
                    Issue(
                        code="above-maximum",
                        severity="error",
                        message=f"field '{rule.field_name}' value {number:g} is above maximum {rule.maximum:g}",
                        field_name=rule.field_name,
                        row=row,
                    )
                )
    return issues
