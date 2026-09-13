import pytest

from tabulint import TabulintError, build_numeric_rules, check_numeric_rules
from tabulint.validators import NumericRule


def test_build_rules_from_bounds():
    rules = build_numeric_rules(["age=0"], ["age=120", "score=10"])
    assert rules == [NumericRule("age", 0.0, 120.0), NumericRule("score", None, 10.0)]


def test_invalid_bound_raises():
    with pytest.raises(TabulintError, match="expected field=number"):
        build_numeric_rules(["age"], None)
    with pytest.raises(TabulintError, match="not a number"):
        build_numeric_rules(["age=old"], None)


def test_inverted_bounds_raise():
    with pytest.raises(TabulintError, match="greater than maximum"):
        build_numeric_rules(["age=50"], ["age=10"])


def test_values_within_bounds_pass():
    records = [{"age": "30"}, {"age": 45}, {"age": "0"}]
    assert check_numeric_rules(records, build_numeric_rules(["age=0"], ["age=120"])) == []


def test_value_below_minimum():
    issues = check_numeric_rules([{"age": "-1"}], build_numeric_rules(["age=0"], None))
    assert issues[0].code == "below-minimum"
    assert issues[0].row == 1


def test_value_above_maximum():
    issues = check_numeric_rules([{"age": 500}], build_numeric_rules(None, ["age=120"]))
    assert issues[0].code == "above-maximum"


def test_non_numeric_value_is_reported():
    issues = check_numeric_rules([{"age": "old"}], build_numeric_rules(["age=0"], None))
    assert issues[0].code == "not-numeric"


def test_missing_values_and_absent_fields_are_skipped():
    records = [{"age": ""}, {"name": "Ada"}]
    assert check_numeric_rules(records, build_numeric_rules(["age=0"], None)) == []
