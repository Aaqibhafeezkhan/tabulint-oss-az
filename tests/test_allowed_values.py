import json

import pytest

from tabulint import (
    AllowedValuesRule, TabulintError, build_allowed_values_rules,
    check_allowed_values_rules, check_file, check_records,
)
from tabulint.cli import main


def test_disallowed_value_has_actionable_error_and_location():
    rule = AllowedValuesRule("status", frozenset({"inactive", "active"}))
    issues = check_allowed_values_rules([{"status": "activee"}], [rule])
    assert len(issues) == 1
    issue = issues[0]
    assert (issue.code, issue.severity, issue.field_name, issue.row) == (
        "not-allowed", "error", "status", 1,
    )
    assert issue.message == (
        "field 'status' value 'activee' is not allowed; allowed values: 'active', 'inactive'"
    )


@pytest.mark.parametrize("value", ["active", "inactive", "əla", "active,paused", " active "])
def test_python_api_accepts_exact_allowed_strings_including_commas(value):
    rule = AllowedValuesRule("status", frozenset({value}))
    assert check_allowed_values_rules([{"status": value}], [rule]) == []


@pytest.mark.parametrize("value", ["Active", "ACTIVE", " active", "active "])
def test_comparison_is_case_sensitive_and_does_not_strip_values(value):
    issues = check_allowed_values_rules(
        [{"status": value}], build_allowed_values_rules(["status=active"]),
    )
    assert [issue.code for issue in issues] == ["not-allowed"]


@pytest.mark.parametrize("record", [{}, {"status": None}, {"status": ""}, {"status": " \t"}])
def test_missing_values_and_fields_are_skipped(record):
    assert check_allowed_values_rules([record], build_allowed_values_rules(["status=active"])) == []


@pytest.mark.parametrize("value,text", [(0, "0"), (False, "False"), (12.5, "12.5")])
def test_non_string_values_are_compared_as_strings(value, text):
    assert check_allowed_values_rules(
        [{"status": value}], [AllowedValuesRule("status", frozenset({text}))],
    ) == []


def test_builder_repeated_fields_replace_values_without_changing_order():
    assert build_allowed_values_rules([" status =active", "tier=free", "status=inactive,paused"]) == [
        AllowedValuesRule("status", frozenset({"inactive", "paused"})),
        AllowedValuesRule("tier", frozenset({"free"})),
    ]
    assert build_allowed_values_rules() == []


@pytest.mark.parametrize("option", ["status", "=active", " =active", "status=", "status= ",
                                       "status=,active", "status=active,", "status=a,,b"])
def test_builder_rejects_invalid_or_empty_allowed_values(option):
    with pytest.raises(TabulintError):
        build_allowed_values_rules([option])


@pytest.mark.parametrize("values", [frozenset(), set(), "active", frozenset({1})])
def test_direct_rule_rejects_empty_or_non_string_sets(values):
    with pytest.raises(TabulintError):
        AllowedValuesRule("status", values)


def test_rule_copies_mutable_set_and_diagnostics_are_deterministic():
    values = {"z", "a"}
    rule = AllowedValuesRule("status", values)
    values.clear()
    issues = check_allowed_values_rules([{"status": "bad"}], [rule])
    assert issues[0].message.endswith("'a', 'z'")


@pytest.mark.parametrize("suffix,content", [
    (".csv", "status\nactivee\n"),
    (".json", '[{"status":"activee"}]'),
    (".jsonl", '{"status":"activee"}\n'),
])
def test_file_and_record_apis_apply_rules(write, suffix, content):
    rules = build_allowed_values_rules(["status=active,inactive"])
    path = write("data" + suffix, content)
    report = check_file(path, allowed_values_rules=rules)
    assert [issue.code for issue in report.issues] == ["not-allowed"]
    assert report.issues == check_records([{"status": "activee"}], allowed_values_rules=rules).issues


@pytest.mark.parametrize("fail_on,expected", [("warning", 1), ("error", 1), ("never", 0)])
def test_cli_violations_preserve_report_and_exit_contract(write, capsys, fail_on, expected):
    path = write("data.csv", "status\nactivee\n")
    assert main([path, "--allowed", "status=active,inactive", "--fail-on", fail_on,
                 "--format", "json"]) == expected
    report = json.loads(capsys.readouterr().out)
    assert report["issues"][0]["code"] == "not-allowed"
    assert report["error_count"] == 1


def test_cli_accepts_every_allowed_value_and_repeatable_fields(write):
    path = write("data.csv", "status,tier\nactive,free\ninactive,pro\n")
    assert main([path, "--allowed", "status=active,inactive", "--allowed", "tier=free,pro"]) == 0


def test_cli_without_rules_keeps_existing_behavior(write):
    assert main([write("data.csv", "status\nactivee\n")]) == 0


@pytest.mark.parametrize("fail_on", ["error", "warning", "never"])
def test_invalid_allowed_option_is_never_suppressed(write, capsys, fail_on):
    path = write("data.csv", "status\nactive\n")
    assert main([path, "--allowed", "status=", "--fail-on", fail_on]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "allowed values cannot be empty" in captured.err


def test_validation_order_is_rule_then_record_order():
    records = [{"status": "bad", "tier": "bad"}, {"status": "bad", "tier": "bad"}]
    issues = check_allowed_values_rules(records, build_allowed_values_rules(["tier=pro", "status=ok"]))
    assert [(issue.field_name, issue.row) for issue in issues] == [
        ("tier", 1), ("tier", 2), ("status", 1), ("status", 2),
    ]
