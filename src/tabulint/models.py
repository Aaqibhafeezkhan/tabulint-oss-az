"""Core data structures shared across tabulint modules."""

from dataclasses import dataclass, field

Record = dict[str, object]

SEVERITIES = ("error", "warning")


@dataclass(frozen=True)
class Issue:
    """A single data-quality problem found in a dataset."""

    code: str
    severity: str
    message: str
    field_name: str | None = None
    row: int | None = None


@dataclass
class FieldProfile:
    """Inferred type information for one field."""

    name: str
    dominant_type: str
    type_counts: dict[str, int] = field(default_factory=dict)
    missing_count: int = 0


@dataclass
class Report:
    """Result of analyzing a dataset."""

    path: str
    row_count: int
    field_names: list[str] = field(default_factory=list)
    profiles: list[FieldProfile] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "warning")

    @property
    def ok(self) -> bool:
        return not self.issues


class TabulintError(Exception):
    """Raised when a dataset cannot be loaded or a rule is invalid."""
