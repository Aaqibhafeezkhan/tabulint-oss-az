from tabulint import analyze, infer_type, is_missing, profile_fields
from tabulint.analyzer import check_duplicates, check_missing_values, check_type_consistency


def codes(issues):
    return sorted(issue.code for issue in issues)


def test_is_missing():
    assert is_missing(None)
    assert is_missing("")
    assert is_missing("   ")
    assert not is_missing(0)
    assert not is_missing("0")
    assert not is_missing(False)


def test_infer_type_from_strings():
    assert infer_type("") == "null"
    assert infer_type("true") == "boolean"
    assert infer_type("FALSE") == "boolean"
    assert infer_type("42") == "integer"
    assert infer_type("-7") == "integer"
    assert infer_type("3.5") == "float"
    assert infer_type("Ada") == "string"


def test_infer_type_from_boolean_literals():
    for literal in ("yes", "no", "y", "n", "t", "f"):
        assert infer_type(literal) == "boolean"
        assert infer_type(literal.upper()) == "boolean"
        assert infer_type(f"  {literal}  ") == "boolean"
        assert infer_type(f"  {literal.upper()}  ") == "boolean"


def test_numeric_literals_remain_integers():
    assert infer_type("1") == "integer"
    assert infer_type("0") == "integer"


def test_mixed_boolean_spellings_have_no_type_mismatch():
    records = [{"active": "yes"}, {"active": "true"}, {"active": "N"}, {"active": "false"}]
    assert profile_fields(records)[0].dominant_type == "boolean"
    assert check_type_consistency(records) == []


def test_unrelated_string_is_not_boolean():
    assert infer_type("maybe") == "string"


def test_infer_type_from_native_values():
    assert infer_type(None) == "null"
    assert infer_type(True) == "boolean"
    assert infer_type(9) == "integer"
    assert infer_type(1.5) == "float"
    assert infer_type(["x"]) == "string"


def test_profile_fields_reports_dominant_type_and_missing():
    records = [
        {"age": "30", "name": "Ada"},
        {"age": "31", "name": ""},
        {"age": "x", "name": "Grace"},
    ]
    profiles = {p.name: p for p in profile_fields(records)}
    assert profiles["age"].dominant_type == "integer"
    assert profiles["age"].type_counts == {"integer": 2, "string": 1}
    assert profiles["name"].dominant_type == "string"
    assert profiles["name"].missing_count == 1


def test_clean_dataset_has_no_issues():
    records = [{"name": "Ada", "age": "36"}, {"name": "Grace", "age": "45"}]
    assert analyze(records) == []


def test_missing_values_are_reported():
    issues = check_missing_values([{"name": "Ada", "age": ""}, {"name": None, "age": "9"}])
    assert codes(issues) == ["missing-value", "missing-value"]
    assert issues[0].row == 1 and issues[0].field_name == "age"


def test_absent_field_is_an_error():
    issues = check_missing_values([{"name": "Ada", "age": "36"}, {"name": "Grace"}])
    assert codes(issues) == ["missing-field"]
    assert issues[0].severity == "error"
    assert issues[0].row == 2


def test_duplicate_records_are_reported():
    records = [{"a": "1"}, {"a": "2"}, {"a": "1"}, {"a": "1"}]
    issues = check_duplicates(records)
    assert [issue.row for issue in issues] == [3, 4]
    assert all(issue.code == "duplicate-record" for issue in issues)
    assert "row 1" in issues[0].message


def test_distinct_records_are_not_duplicates():
    assert check_duplicates([{"a": "1"}, {"a": "2"}]) == []


def test_inconsistent_types_are_reported():
    records = [{"age": "30"}, {"age": "31"}, {"age": "thirty"}]
    issues = check_type_consistency(records)
    assert len(issues) == 1
    assert issues[0].code == "type-mismatch"
    assert issues[0].row == 3
    assert issues[0].severity == "error"


def test_missing_values_do_not_count_as_type_mismatch():
    records = [{"age": "30"}, {"age": ""}, {"age": "31"}]
    assert check_type_consistency(records) == []


def test_single_type_field_has_no_mismatch():
    assert check_type_consistency([{"age": "30"}, {"age": "31"}]) == []
