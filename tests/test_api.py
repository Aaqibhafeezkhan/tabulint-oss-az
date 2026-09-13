from tabulint import check_file, check_records, format_report

CSV = "name,age\nAda,36\nGrace,45\n"
JSON = '[{"name": "Ada", "age": 36}, {"name": "Grace", "age": 45}]'


def test_check_file_on_clean_csv(write):
    report = check_file(write("people.csv", CSV))
    assert report.ok
    assert report.row_count == 2
    assert report.field_names == ["name", "age"]


def test_check_file_on_clean_json(write):
    report = check_file(write("people.json", JSON))
    assert report.ok
    assert [p.dominant_type for p in report.profiles] == ["string", "integer"]


def test_check_records_collects_all_issue_kinds():
    records = [
        {"name": "Ada", "age": "36"},
        {"name": "Ada", "age": "36"},
        {"name": "", "age": "old"},
    ]
    report = check_records(records)
    found = {issue.code for issue in report.issues}
    assert {"duplicate-record", "missing-value", "type-mismatch"} <= found
    assert report.error_count > 0
    assert report.warning_count > 0
    assert not report.ok


def test_empty_dataset_is_flagged(write):
    report = check_file(write("empty.csv", "name,age\n"))
    assert report.row_count == 0
    assert [issue.code for issue in report.issues] == ["empty-dataset"]


def test_format_report_mentions_counts_and_issues():
    text = format_report(check_records([{"a": "1"}, {"a": "1"}], path="x.csv"))
    assert "x.csv" in text
    assert "records: 2" in text
    assert "duplicate-record" in text
    assert "summary:" in text


def test_format_report_for_clean_dataset():
    text = format_report(check_records([{"a": "1"}, {"a": "2"}]))
    assert "no issues found" in text
