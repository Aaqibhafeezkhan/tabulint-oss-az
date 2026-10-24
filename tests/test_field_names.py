from tabulint import check_records
from tabulint.analyzer import check_missing_values, field_names


def test_field_names_preserve_first_appearance_across_sparse_reordered_records():
    records = [{"z": 1, "a": 2}, {"a": 3, "b": 4}, {}, {"b": 5, "z": 6, "A": 7}]
    assert field_names(records) == ["z", "a", "b", "A"]
    assert field_names([]) == []
    assert field_names([{}, {}]) == []


def test_missing_field_issue_order_and_messages_follow_first_seen_fields():
    issues = check_missing_values([{"z": 1, "a": 2}, {"b": 3}])
    assert [(issue.code, issue.row, issue.field_name, issue.message) for issue in issues] == [
        ("missing-field", 1, "b", "field 'b' is absent from this record"),
        ("missing-field", 2, "z", "field 'z' is absent from this record"),
        ("missing-field", 2, "a", "field 'a' is absent from this record"),
    ]


def test_generated_wide_dataset_retains_profiles_and_expected_issue_counts():
    names = [f"field_{index}" for index in range(32)]
    records = [dict.fromkeys(names, row) for row in range(2_000)]
    records[-1].pop("field_1")
    records[-1]["field_2"] = None
    report = check_records(records)
    assert report.field_names == names
    assert report.row_count == 2_000
    assert (report.error_count, report.warning_count) == (1, 1)
    assert [(issue.code, issue.row, issue.field_name) for issue in report.issues] == [
        ("missing-field", 2_000, "field_1"), ("missing-value", 2_000, "field_2"),
    ]
    assert report.profiles[0].type_counts == {"integer": 2_000}
    assert report.profiles[1].missing_count == 1
    assert report.profiles[2].missing_count == 1
