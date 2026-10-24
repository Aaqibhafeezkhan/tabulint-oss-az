import json
from pathlib import Path

import pytest

from tabulint import check_file, check_records, load_csv, load_dataset, load_json, load_jsonl
from tabulint.cli import main


@pytest.mark.parametrize("suffix", [".csv", ".json", ".jsonl", ".ndjson"])
@pytest.mark.parametrize("content", ["", " \t\r\n", " " * 20_000])
def test_blank_files_have_a_distinct_warning_and_plain_list_result(write, suffix, content):
    path = write("empty" + suffix, content)
    assert type(load_dataset(path)) is list
    assert load_dataset(path) == []
    report = check_file(path)
    assert report.row_count == 0
    assert report.field_names == []
    assert [(issue.code, issue.severity, issue.message) for issue in report.issues] == [
        ("empty-dataset", "warning", "input file is empty or contains only whitespace"),
    ]


@pytest.mark.parametrize("delimiter,encoding,content,names", [
    (",", "utf-8", "name,age\r\n", ["name", "age"]),
    (";", "cp1252", "café;age\n", ["café", "age"]),
    ("\t", "utf-8-sig", "name\tage\n", ["name", "age"]),
    (",", "utf-8", '"full,name",age\n', ["full,name", "age"]),
])
def test_header_only_csv_preserves_decoded_header_names(write, delimiter, encoding, content, names):
    path = write("header.csv", content, encoding=encoding)
    assert type(load_csv(path, delimiter=delimiter, encoding=encoding)) is list
    assert load_csv(path, delimiter=delimiter, encoding=encoding) == []
    report = check_file(path, delimiter=delimiter, encoding=encoding)
    assert report.field_names == names
    assert [profile.name for profile in report.profiles] == names
    assert all(profile.dominant_type == "null" and profile.missing_count == 0 for profile in report.profiles)
    assert "header but no records" in report.issues[0].message
    for name in names:
        assert repr(name) in report.issues[0].message


def test_empty_json_array_is_record_free_not_a_blank_file(write):
    path = write("empty.json", " \n[] \n")
    assert load_json(path) == []
    report = check_file(path)
    assert report.issues[0].message == "dataset contains no records"
    assert report.issues == check_records([]).issues


@pytest.mark.parametrize("reader,suffix", [(load_csv, ".csv"), (load_json, ".json"), (load_jsonl, ".jsonl")])
def test_public_readers_accept_blank_content_and_keep_plain_lists(write, reader, suffix):
    result = reader(write("blank" + suffix, " \n"))
    assert type(result) is list
    assert result == []


@pytest.mark.parametrize("suffix,content", [(".csv", "name,age\n"), (".json", "[]"), (".jsonl", "\n")])
def test_empty_metadata_comes_from_one_open_of_the_input(write, monkeypatch, suffix, content):
    path = Path(write("empty" + suffix, content))
    original_open = Path.open
    opened = []

    def tracked_open(self, *args, **kwargs):
        if self == path:
            opened.append(self)
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", tracked_open)
    assert check_file(path).row_count == 0
    assert opened == [path]


@pytest.mark.parametrize("suffix,content", [(".csv", ""), (".csv", "name,age\n"),
                                          (".json", "[]"), (".json", " \n"), (".ndjson", "\n")])
@pytest.mark.parametrize("fail_on,default_code", [("warning", 1), ("error", 0), ("never", 0)])
def test_allow_empty_suppresses_only_the_empty_warning(write, capsys, suffix, content, fail_on, default_code):
    path = write("empty" + suffix, content)
    args = [path, "--fail-on", fail_on]
    assert main(args) == default_code
    assert "empty-dataset" in capsys.readouterr().out
    assert main([*args, "--allow-empty"]) == 0
    captured = capsys.readouterr()
    assert "empty-dataset" not in captured.out
    assert "no issues found" in captured.out
    assert captured.err == ""


@pytest.mark.parametrize("allow", [False, True])
@pytest.mark.parametrize("fmt", ["text", "json"])
def test_header_only_names_remain_in_written_reports(write, tmp_path, capsys, allow, fmt):
    path = write("header.csv", "name,age\n")
    output = tmp_path / "report.txt"
    args = [path, "--format", fmt, "--output", str(output)] + (["--allow-empty"] if allow else [])
    assert main(args) == (0 if allow else 1)
    text = capsys.readouterr().out
    assert output.read_text(encoding="utf-8") == text
    if fmt == "json":
        document = json.loads(text)
        assert [profile["name"] for profile in document["profiles"]] == ["name", "age"]
        assert document["warning_count"] == (0 if allow else 1)
        assert document["ok"] is allow
    else:
        assert "name" in text and "age" in text


@pytest.mark.parametrize("content,options", [
    ("name,age\nAda,36\nGrace,45\n", []),
    ("name,age\nAda,36\nAda,36\n", []),
    ("name,age\nAda,200\n", ["--max", "age=120"]),
    ("name,age\nAda,\n", ["--required", "age"]),
])
def test_allow_empty_does_not_change_nonempty_output_or_findings(write, capsys, content, options):
    path = write("data.csv", content)
    code = main([path, *options])
    original = capsys.readouterr()
    assert main([path, *options, "--allow-empty"]) == code
    assert capsys.readouterr() == original


@pytest.mark.parametrize("fail_on", ["warning", "error", "never"])
@pytest.mark.parametrize("name,content", [("malformed.json", "[oops]"), ("duplicate.csv", "id,id\n"),
                                        ("bad.csv", 'name\n"unterminated'), ("unsupported.txt", "")])
def test_allow_empty_never_suppresses_input_failures(write, capsys, fail_on, name, content):
    path = write(name, content)
    assert main([path, "--allow-empty", "--fail-on", fail_on]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "error:" in captured.err


def test_allow_empty_does_not_accept_missing_files(tmp_path, capsys):
    assert main([str(tmp_path / "missing.csv"), "--allow-empty", "--fail-on", "never"]) == 2
    assert "file not found" in capsys.readouterr().err


def test_allow_empty_does_not_suppress_output_failure(write, tmp_path, capsys):
    path = write("empty.json", "[]")
    assert main([path, "--allow-empty", "--output", str(tmp_path / "missing" / "report.txt")]) == 2
    assert "could not write output file" in capsys.readouterr().err


def test_allow_empty_and_quiet_json_preserve_machine_output_contract(write, capsys):
    path = write("empty.csv", "name\n")
    assert main([path, "--allow-empty", "--quiet", "--format", "json"]) == 0
    assert capsys.readouterr().out == ""
