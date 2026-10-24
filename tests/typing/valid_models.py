from tabulint.analyzer import infer_type
from tabulint.models import FieldProfile, InferredType, Issue, Severity

severity: Severity = "warning"
inferred: InferredType = infer_type(12)
issue = Issue("example", severity, "example message")
profile = FieldProfile("age", inferred, {"integer": 1})
