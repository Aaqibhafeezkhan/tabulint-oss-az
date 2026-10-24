import sys

import pytest

from tabulint import (
    TabulintError, build_length_rules, build_numeric_rules,
    check_length_rules, check_numeric_rules,
)
from tabulint.validators import LengthRule, NumericRule


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


@pytest.mark.parametrize("bound", ["age=nan", "age=inf", "age=-inf", "age=+inf", "age=NaN"])
def test_non_finite_minimum_bound_raises(bound):
    with pytest.raises(TabulintError, match="not a finite number"):
        build_numeric_rules([bound], None)


@pytest.mark.parametrize("bound", ["score=nan", "score=inf", "score=-inf"])
def test_non_finite_maximum_bound_raises(bound):
    with pytest.raises(TabulintError, match="not a finite number"):
        build_numeric_rules(None, [bound])


def test_finite_negative_and_decimal_bounds_still_work():
    rules = build_numeric_rules(["temp=-12.5"], ["temp=40"])
    assert rules == [NumericRule("temp", -12.5, 40.0)]
    records = [{"temp": "-12.5"}, {"temp": "0"}, {"temp": "40"}]
    assert check_numeric_rules(records, rules) == []


@pytest.mark.parametrize("value", [
    "nan", "NaN", "inf", "-inf", "1e400", "-1e400",
    float("nan"), float("inf"), float("-inf"),
])
@pytest.mark.parametrize("rule", [NumericRule("age", minimum=0), NumericRule("age", maximum=120)])
def test_non_finite_values_are_reported_with_one_sided_bounds(value, rule):
    issues = check_numeric_rules([{"age": value}], [rule])
    assert len(issues) == 1
    assert issues[0].code == "not-numeric"
    assert issues[0].severity == "error"
    assert issues[0].field_name == "age"
    assert issues[0].row == 1


@pytest.mark.parametrize("bound_name", ["minimum", "maximum"])
@pytest.mark.parametrize("bound", [float("nan"), float("inf"), float("-inf"), True, "10"])
def test_direct_numeric_rule_rejects_invalid_bounds(bound_name, bound):
    with pytest.raises(TabulintError, match="not a finite number"):
        NumericRule("age", **{bound_name: bound})


def test_direct_numeric_rule_rejects_inverted_bounds():
    with pytest.raises(TabulintError, match="greater than maximum"):
        NumericRule("age", minimum=50, maximum=10)


@pytest.mark.parametrize("bound", [2**53 + 1, 10**400])
@pytest.mark.parametrize("as_text", [False, True])
def test_integer_minimum_is_exact_for_large_values(bound, as_text):
    values = [bound - 1, bound, bound + 1]
    records = [{"n": str(value) if as_text else value} for value in values]
    rules = build_numeric_rules([f"n={bound}"])
    assert rules[0].minimum == bound

    issues = check_numeric_rules(records, rules)

    assert len(issues) == 1
    assert issues[0].code == "below-minimum"
    assert issues[0].row == 1
    assert issues[0].message == f"field 'n' value {bound - 1} is below minimum {bound}"


@pytest.mark.parametrize("bound", [2**53 + 1, 10**400])
@pytest.mark.parametrize("as_text", [False, True])
def test_integer_maximum_is_exact_for_large_values(bound, as_text):
    values = [bound - 1, bound, bound + 1]
    records = [{"n": str(value) if as_text else value} for value in values]
    rules = build_numeric_rules(maximums=[f"n={bound}"])
    assert rules[0].maximum == bound

    issues = check_numeric_rules(records, rules)

    assert len(issues) == 1
    assert issues[0].code == "above-maximum"
    assert issues[0].row == 3
    assert issues[0].message == f"field 'n' value {bound + 1} is above maximum {bound}"


def test_huge_negative_integer_can_be_reported_without_float_overflow():
    value = -(10**400)
    issues = check_numeric_rules([{"n": value}], [NumericRule("n", minimum=0)])
    assert issues[0].code == "below-minimum"
    assert issues[0].message == f"field 'n' value {value} is below minimum 0"


def test_large_inverted_integer_bounds_are_not_rounded_to_equality():
    with pytest.raises(TabulintError, match="greater than maximum"):
        build_numeric_rules([f"n={2**53 + 1}"], [f"n={2**53}"])


def test_direct_numeric_rule_supports_huge_finite_integer_bounds():
    rule = NumericRule("n", minimum=10**400, maximum=10**400 + 1)
    assert check_numeric_rules([{"n": 10**400}], [rule]) == []


def test_decimal_and_exponent_numbers_remain_supported():
    rules = build_numeric_rules(["n=-1.5e1"], ["n=1e2"])
    assert check_numeric_rules([{"n": "-15.0"}, {"n": "1e2"}, {"n": 1.5}], rules) == []


@pytest.mark.parametrize("prefix", ["", "+", "-"])
def test_zero_padded_integers_remain_exact_beyond_digit_limit(prefix):
    integer = 2**53 + 1
    padded = prefix + "0" * (sys.get_int_max_str_digits() + 4300) + str(integer)
    expected = -integer if prefix == "-" else integer
    rules = build_numeric_rules([f"n={padded}"], [f"n={padded}"])
    assert rules[0].minimum == rules[0].maximum == expected
    assert check_numeric_rules([{"n": padded}], rules) == []
    assert check_numeric_rules([{"n": expected - 1}], rules)[0].code == "below-minimum"


def test_underscored_zero_padded_integers_remain_exact():
    padded = "0_" * (sys.get_int_max_str_digits() + 4300) + "9007199254740993"
    rules = build_numeric_rules(maximums=["n=9007199254740992"])
    issues = check_numeric_rules([{"n": padded}], rules)
    assert issues[0].code == "above-maximum"


def test_over_limit_integer_text_is_rejected_without_float_fallback():
    limit = sys.get_int_max_str_digits()
    if not limit:
        pytest.skip("Python integer string conversion limit is disabled")
    oversized = "1" * (limit + 1)
    with pytest.raises(TabulintError, match="not a number"):
        build_numeric_rules([f"n={oversized}"])
    issues = check_numeric_rules([{"n": oversized}], [NumericRule("n", minimum=0)])
    assert issues[0].code == "not-numeric"
    assert sys.get_int_max_str_digits() == limit


@pytest.mark.parametrize("sign,code", [(1, "above-maximum"), (-1, "below-minimum")])
def test_oversized_native_integer_diagnostics_are_bounded(sign, code):
    limit = sys.get_int_max_str_digits()
    if not limit:
        pytest.skip("Python integer string conversion limit is disabled")
    value = sign * 10 ** (limit + 10)
    issues = check_numeric_rules([{"n": value}], [NumericRule("n", minimum=0, maximum=0)])
    assert len(issues) == 1
    assert issues[0].code == code
    assert f"integer with {value.bit_length()} bits" in issues[0].message
    assert len(issues[0].message) < 150
    assert sys.get_int_max_str_digits() == limit


def test_oversized_native_integer_bounds_have_bounded_diagnostics():
    limit = sys.get_int_max_str_digits()
    if not limit:
        pytest.skip("Python integer string conversion limit is disabled")
    bound = 10 ** (limit + 10)
    issues = check_numeric_rules([{"n": 0}], [NumericRule("n", minimum=bound)])
    assert issues[0].code == "below-minimum"
    assert "positive integer with" in issues[0].message
    assert len(issues[0].message) < 150
    with pytest.raises(TabulintError, match="greater than maximum") as caught:
        NumericRule("n", minimum=bound, maximum=-bound)
    assert len(str(caught.value)) < 200


def test_build_length_rules():
    assert build_length_rules(["code=2"], ["code=4", "name=10"]) == [
        LengthRule("code", 2, 4), LengthRule("name", None, 10)
    ]


def test_length_rule_violations_include_codes_and_rows():
    issues = check_length_rules([{"code": "A"}, {"code": "ABCDE"}], build_length_rules(["code=2"], ["code=4"]))
    assert [issue.code for issue in issues] == ["below-min-length", "above-max-length"]
    assert [issue.row for issue in issues] == [1, 2]


def test_length_boundaries_and_missing_values_pass():
    records = [{"code": "AB"}, {"code": "WXYZ"}, {"code": ""}, {"other": "value"}]
    assert check_length_rules(records, build_length_rules(["code=2"], ["code=4"])) == []


@pytest.mark.parametrize("bound", ["code=-1", "code=one", "code=1.5"])
def test_invalid_length_bound_raises(bound):
    with pytest.raises(TabulintError, match="length bound"):
        build_length_rules([bound], None)


def test_inverted_length_bounds_raise():
    with pytest.raises(TabulintError, match="greater than maximum length"):
        build_length_rules(["code=5"], ["code=2"])


@pytest.mark.parametrize("name", ["minimum", "maximum"])
@pytest.mark.parametrize("bound", [-1, 1.5, True, False, "2", float("inf")])
def test_direct_length_rule_rejects_invalid_bounds(name, bound):
    with pytest.raises(TabulintError, match="non-negative integer"):
        LengthRule("code", **{name: bound})


def test_direct_length_rule_rejects_inverted_bounds():
    with pytest.raises(TabulintError, match="greater than maximum length"):
        LengthRule("code", minimum=3, maximum=2)


@pytest.mark.parametrize("value", [None, "", " ", "\t"])
def test_length_rules_skip_all_missing_values(value):
    assert check_length_rules([{"code": value}], [LengthRule("code", 2, 4)]) == []


@pytest.mark.parametrize("value,length", [("ə🙂", 2), (" A ", 3), (12, 2), (False, 5)])
def test_length_rules_count_string_characters_without_trimming(value, length):
    assert check_length_rules([{"code": value}], [LengthRule("code", length, length)]) == []


def test_repeated_length_bounds_keep_last_value_and_field_order():
    assert build_length_rules([" code =1", "name=2", "code=3"], ["other=9"]) == [
        LengthRule("code", 3), LengthRule("name", 2), LengthRule("other", maximum=9),
    ]


def test_large_length_bound_has_readable_diagnostics():
    limit = sys.get_int_max_str_digits()
    if not limit:
        pytest.skip("Python integer string conversion limit is disabled")
    bound = 10 ** (limit + 10)
    issues = check_length_rules([{"code": "A"}], [LengthRule("code", minimum=bound)])
    assert issues[0].code == "below-min-length"
    assert "integer with" in issues[0].message
    assert len(issues[0].message) < 180
    with pytest.raises(TabulintError, match="greater than maximum length"):
        LengthRule("code", minimum=bound, maximum=1)
