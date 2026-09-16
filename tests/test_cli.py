from tabulint.cli import EXIT_ERROR, EXIT_ISSUES, EXIT_OK, main
from tabulint import check_file
from tabulint.report import format_report

CSV = "name,age\nAda,36\nGrace,45\n"
JSON = '[{"name": "Ada", "age": 36}, {"name": "Grace", "age": 45}]'
JSONL = '{"name": "Ada", "age": 36}\n{"name": "Grace", "age": 45}\n'


def test_clean_csv_exits_zero(write, capsys):
    assert main([write("people.csv", CSV)]) == EXIT_OK
    assert "no issues found" in capsys.readouterr().out


def test_clean_json_exits_zero(write):
    assert main([write("people.json", JSON)]) == EXIT_OK


def test_clean_jsonl_exits_zero(write):
    assert main([write("people.jsonl", JSONL)]) == EXIT_OK


def test_clean_ndjson_exits_zero(write):
    assert main([write("people.ndjson", JSONL)]) == EXIT_OK


def test_dataset_with_issues_exits_one(write, capsys):
    path = write("dupes.csv", "name,age\nAda,36\nAda,36\n")
    assert main([path]) == EXIT_ISSUES
    assert "duplicate-record" in capsys.readouterr().out


def test_ndjson_dataset_with_duplicates_exits_one(write, capsys):
    path = write("dupes.ndjson", '{"name": "Ada", "age": 36}\n{"name": "Ada", "age": 36}\n')
    assert main([path]) == EXIT_ISSUES
    assert "duplicate-record" in capsys.readouterr().out


def test_missing_file_exits_two(write, tmp_path, capsys):
    assert main([str(tmp_path / "nope.csv")]) == EXIT_ERROR
    assert "file not found" in capsys.readouterr().err


def test_malformed_json_exits_two(write, capsys):
    assert main([write("bad.json", "{oops")]) == EXIT_ERROR
    assert "error:" in capsys.readouterr().err


def test_malformed_jsonl_exits_two(write, capsys):
    path = write("bad.jsonl", '{"name": "Ada"}\n\n{oops}\n')
    assert main([path]) == EXIT_ERROR
    captured = capsys.readouterr()
    assert "line 3" in captured.err


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


def test_output_file_matches_rendered_report(write, tmp_path, capsys):
    path = write("people.csv", CSV)
    output = tmp_path / "report.txt"

    report = check_file(path)
    expected = format_report(report) + "\n"

    assert main([path, "--output", str(output)]) == EXIT_OK
    assert output.read_text(encoding="utf-8") == expected
    assert output.read_text(encoding="utf-8").endswith("\n")
    assert capsys.readouterr().out == expected


def test_short_output_flag_matches_long_form(write, tmp_path):
    path = write("people.csv", CSV)
    output = tmp_path / "report.txt"

    assert main([path, "-o", str(output)]) == EXIT_OK
    assert output.exists()


def test_output_file_uses_utf8_for_non_ascii_value(write, tmp_path):
    path = write("people.csv", "name,age\nAda,1\nGrace,é\n")
    output = tmp_path / "report.txt"

    assert main([path, "--output", str(output)]) == EXIT_ISSUES
    content = output.read_bytes()
    assert "é".encode("utf-8") in content
    assert content.endswith(b"\n")


def test_unwritable_output_path_exits_two(write, tmp_path, capsys):
    path = write("people.csv", CSV)
    output = tmp_path / "missing" / "report.txt"

    assert main([path, "--output", str(output)]) == EXIT_ERROR
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "could not write output file" in captured.err
    assert "Traceback" not in captured.err


def test_output_file_preserves_issue_exit_code(write, tmp_path, capsys):
    path = write("dupes.csv", "name,age\nAda,36\nAda,36\n")
    output = tmp_path / "report.txt"

    assert main([path, "--output", str(output)]) == EXIT_ISSUES
    assert "duplicate-record" in output.read_text(encoding="utf-8")
    assert "duplicate-record" in capsys.readouterr().out


def test_output_overwrites_existing_file(write, tmp_path):
    path = write("people.csv", CSV)
    output = tmp_path / "report.txt"
    output.write_text("old report\n", encoding="utf-8")

    assert main([path, "--output", str(output)]) == EXIT_OK
    assert "old report" not in output.read_text(encoding="utf-8")


def test_quiet_mode_clean_dataset_prints_nothing(write, capsys):
    assert main([write("people.csv", CSV), "--quiet"]) == EXIT_OK
    assert capsys.readouterr().out == ""


def test_quiet_mode_prints_one_summary_line(write, capsys):
    path = write("dupes.csv", "name,age\nAda,36\nAda,36\n")
    assert main([path, "--quiet"]) == EXIT_ISSUES
    assert capsys.readouterr().out == f"{path}: 0 error(s), 1 warning(s)\n"


def test_short_quiet_flag_matches_long_form(write, capsys):
    path = write("dupes.csv", "name,age\nAda,36\nAda,36\n")
    assert main([path, "-q"]) == EXIT_ISSUES
    assert capsys.readouterr().out == f"{path}: 0 error(s), 1 warning(s)\n"


def test_quiet_mode_with_output_writes_full_report(write, tmp_path, capsys):
    path = write("dupes.csv", "name,age\nAda,36\nAda,36\n")
    output = tmp_path / "report.txt"
    report = check_file(path)
    expected = format_report(report) + "\n"

    assert main([path, "--quiet", "--output", str(output)]) == EXIT_ISSUES
    assert output.read_text(encoding="utf-8") == expected
    assert capsys.readouterr().out == f"{path}: 0 error(s), 1 warning(s)\n"


def test_quiet_mode_still_reports_load_errors(tmp_path, capsys):
    assert main([str(tmp_path / "nope.csv"), "--quiet"]) == EXIT_ERROR
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "file not found" in captured.err


def test_quiet_mode_still_reports_invalid_bounds(write, capsys):
    assert main([write("people.csv", CSV), "--quiet", "--min", "age"]) == EXIT_ERROR
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "invalid bound" in captured.err


def test_quiet_mode_with_output_writes_no_file_on_load_error(tmp_path, capsys):
    output = tmp_path / "report.txt"
    assert main([str(tmp_path / "nope.csv"), "--quiet", "--output", str(output)]) == EXIT_ERROR
    assert not output.exists()
    assert capsys.readouterr().out == ""
