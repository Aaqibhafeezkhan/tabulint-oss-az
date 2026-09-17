import pytest

from tabulint import TabulintError, load_csv, load_dataset, load_json, load_jsonl

VALID_CSV = "name,age\nAda,36\nGrace,45\n"
VALID_JSON = '[{"name": "Ada", "age": 36}, {"name": "Grace", "age": 45}]'
VALID_JSONL = '{"name": "Ada", "age": 36}\n{"name": "Grace", "age": 45}\n'


def test_load_valid_csv(write):
    rows = load_csv(write("people.csv", VALID_CSV))
    assert rows == [{"name": "Ada", "age": "36"}, {"name": "Grace", "age": "45"}]


def test_load_valid_json(write):
    rows = load_json(write("people.json", VALID_JSON))
    assert rows == [{"name": "Ada", "age": 36}, {"name": "Grace", "age": 45}]


def test_load_valid_jsonl(write):
    rows = load_jsonl(write("people.jsonl", VALID_JSONL))
    assert rows == [{"name": "Ada", "age": 36}, {"name": "Grace", "age": 45}]


def test_load_jsonl_skips_blank_lines(write):
    content = '{"name": "Ada"}\n\n  \n{"name": "Grace"}\n'
    assert load_jsonl(write("people.jsonl", content)) == [{"name": "Ada"}, {"name": "Grace"}]


def test_load_dataset_dispatches_on_extension(write):
    assert load_dataset(write("a.csv", VALID_CSV)) == load_csv(write("b.csv", VALID_CSV))
    assert load_dataset(write("a.json", VALID_JSON)) == load_json(write("b.json", VALID_JSON))
    assert load_dataset(write("a.jsonl", VALID_JSONL)) == load_jsonl(write("b.jsonl", VALID_JSONL))
    assert load_dataset(write("a.ndjson", VALID_JSONL)) == load_jsonl(write("b.ndjson", VALID_JSONL))


def test_empty_csv_has_no_rows(write):
    assert load_csv(write("empty.csv", "")) == []
    assert load_csv(write("header_only.csv", "name,age\n")) == []


def test_empty_json_array_has_no_rows(write):
    assert load_json(write("empty.json", "[]")) == []


def test_empty_jsonl_has_no_rows(write):
    assert load_jsonl(write("empty.jsonl", "\n  \n")) == []


def test_malformed_json_raises(write):
    with pytest.raises(TabulintError, match="malformed JSON"):
        load_json(write("bad.json", '[{"name": "Ada",}]'))


def test_json_must_be_array_of_objects(write):
    with pytest.raises(TabulintError, match="array of objects"):
        load_json(write("obj.json", '{"name": "Ada"}'))
    with pytest.raises(TabulintError, match="not a JSON object"):
        load_json(write("mixed.json", '[{"name": "Ada"}, 42]'))


def test_jsonl_malformed_line_names_physical_line_number(write):
    content = '{"name": "Ada"}\n\n{oops}\n'
    with pytest.raises(TabulintError, match=r"line 3"):
        load_jsonl(write("bad.jsonl", content))


def test_jsonl_non_object_line_names_physical_line_number(write):
    content = '{"name": "Ada"}\n\n[1, 2]\n'
    with pytest.raises(TabulintError, match=r"line 3.*not a JSON object"):
        load_jsonl(write("bad.jsonl", content))


def test_csv_with_extra_fields_raises(write):
    with pytest.raises(TabulintError, match="more fields than the header"):
        load_csv(write("ragged.csv", "name,age\nAda,36,extra\n"))


def test_csv_with_empty_header_name_raises(write):
    with pytest.raises(TabulintError, match="empty column name"):
        load_csv(write("blank.csv", "name,\nAda,36\n"))


def test_missing_file_raises(write, tmp_path):
    with pytest.raises(TabulintError, match="file not found"):
        load_dataset(str(tmp_path / "nope.csv"))


def test_unsupported_extension_raises(write):
    with pytest.raises(TabulintError, match="unsupported file type"):
        load_dataset(write("data.txt", "hello"))


def test_load_semicolon_delimited_csv(write):
    rows = load_csv(write("people.csv", "name;age\nAda;36\nGrace;45\n"), delimiter=";")
    assert rows == [{"name": "Ada", "age": "36"}, {"name": "Grace", "age": "45"}]


def test_load_comma_delimited_csv_without_option_is_unchanged(write):
    rows = load_csv(write("people.csv", VALID_CSV))
    assert rows == [{"name": "Ada", "age": "36"}, {"name": "Grace", "age": "45"}]


def test_multi_character_delimiter_raises(write):
    with pytest.raises(TabulintError, match="delimiter must be exactly one character"):
        load_csv(write("people.csv", VALID_CSV), delimiter="||")


def test_empty_delimiter_raises(write):
    with pytest.raises(TabulintError, match="delimiter must be exactly one character"):
        load_csv(write("people.csv", VALID_CSV), delimiter="")


def test_delimiter_is_ignored_for_json(write):
    rows = load_dataset(write("people.json", VALID_JSON), delimiter=";")
    assert rows == [{"name": "Ada", "age": 36}, {"name": "Grace", "age": 45}]
