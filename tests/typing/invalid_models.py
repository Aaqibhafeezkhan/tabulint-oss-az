from tabulint.models import FieldProfile, InferredType, Issue

Issue("example", "fatal", "invalid severity")
FieldProfile("age", "number")
FieldProfile("age", "integer", {"number": 1})


def invalid_type_name() -> InferredType:
    return "number"
