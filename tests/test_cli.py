from tabulint.cli import EXIT_ERROR, EXIT_ISSUES, EXIT_OK, main

CSV = "name,age\nAda,36\nGrace,45\n"
JSON = '[{"name": "Ada", "age": 36}, {"name": "Grace", "age": 45}]'


def test_clean_csv_exits_zero(write, capsys):
    assert main([write("people.csv", CSV)]) == EXIT_OK
    assert "no issues found" in capsys.readouterr().out


def test_clean_json_exits_zero(write):
    assert main([write("people.json", JSON)]) == EXIT_OK


def test_dataset_with_issues_exits_one(write, capsys):
    path = write("dupes.csv", "name,age\nAda,36\nAda,36\n")
    assert main([path]) == EXIT_ISSUES
    assert "duplicate-record" in capsys.readouterr().out


def test_missing_file_exits_two(write, tmp_path, capsys):
    assert main([str(tmp_path / "nope.csv")]) == EXIT_ERROR
    assert "file not found" in capsys.readouterr().err


def test_malformed_json_exits_two(write, capsys):
    assert main([write("bad.json", "{oops")]) == EXIT_ERROR
    assert "error:" in capsys.readouterr().err


def test_numeric_rule_violation_exits_one(write, capsys):
    path = write("ages.csv", "name,age\nAda,200\n")
    assert main([path, "--max", "age=120"]) == EXIT_ISSUES
    assert "above-maximum" in capsys.readouterr().out


def test_numeric_rule_satisfied_exits_zero(write):
    path = write("ages.csv", "name,age\nAda,36\nGrace,45\n")
    assert main([path, "--min", "age=0", "--max", "age=120"]) == EXIT_OK


def test_invalid_bound_exits_two(write, capsys):
    assert main([write("ages.csv", CSV), "--min", "age"]) == EXIT_ERROR
    assert "invalid bound" in capsys.readouterr().err


def test_unsupported_extension_exits_two(write):
    assert main([write("data.txt", "hello")]) == EXIT_ERROR


def test_empty_dataset_exits_one(write, capsys):
    assert main([write("empty.json", "[]")]) == EXIT_ISSUES
    assert "empty-dataset" in capsys.readouterr().out
