import pytest

from tabulint import LengthRule, check_file, check_records
from tabulint.cli import main


@pytest.mark.parametrize("file_input", [False, True])
def test_length_rules_integrate_with_public_apis(write, file_input):
    rules = [LengthRule("code", 2, 2)]
    if file_input:
        report = check_file(write("codes.json", '[{"code": "ABC"}]'), length_rules=rules)
    else:
        report = check_records([{"code": "ABC"}], length_rules=rules)
    assert [(issue.code, issue.severity, issue.field_name, issue.row) for issue in report.issues] == [
        ("above-max-length", "error", "code", 1)
    ]


@pytest.mark.parametrize("fail_on,expected", [("warning", 1), ("error", 1), ("never", 0)])
def test_length_errors_follow_fail_on_contract(write, capsys, fail_on, expected):
    path = write("codes.csv", "code\nA\n")
    assert main([path, "--min-length", "code=2", "--fail-on", fail_on]) == expected
    assert "below-min-length" in capsys.readouterr().out


@pytest.mark.parametrize("args", [
    ["--min-length", "code=1.5"],
    ["--min-length", "code=4", "--max-length", "code=2"],
    ["--max-length", "=2"],
])
def test_invalid_length_options_exit_two(write, capsys, args):
    path = write("codes.csv", "code\nAB\n")
    assert main([path, *args]) == 2
    assert "length" in capsys.readouterr().err
