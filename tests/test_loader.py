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


def test_csv_with_unterminated_quote_raises(write):
    with pytest.raises(TabulintError, match="malformed CSV"):
        load_csv(write("unterminated.csv", 'name,age\nAda,"36\n'))


def test_csv_with_valid_multiline_field(tmp_path):
    content = 'name,bio\nAda,"First computer\nprogrammer"\n'
    path = tmp_path / "multiline.csv"
    path.write_bytes(content.encode("utf-8"))
    rows = load_csv(path)
    assert rows == [{"name": "Ada", "bio": "First computer\nprogrammer"}]


def test_csv_with_escaped_quotes_and_commas(write):
    content = 'name,note\nAda,"Hello, ""World"""\n'
    rows = load_csv(write("escaped.csv", content))
    assert rows == [{"name": "Ada", "note": 'Hello, "World"'}]


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



def test_cp1252_csv_loads_with_selected_encoding(write):
    path = write("people.csv", "name,city\nZoë,München\n", encoding="cp1252")
    assert load_csv(path, encoding="cp1252") == [{"name": "Zoë", "city": "München"}]


def test_selected_encoding_loads_json(write):
    path = write("people.json", '[{"name": "Zoë"}]', encoding="cp1252")
    assert load_json(path, encoding="cp1252") == [{"name": "Zoë"}]


def test_selected_encoding_loads_jsonl_and_ndjson(write):
    content = '{"name": "Zoë"}\n'
    jsonl = write("people.jsonl", content, encoding="cp1252")
    ndjson = write("people.ndjson", content, encoding="cp1252")
    expected = [{"name": "Zoë"}]
    assert load_jsonl(jsonl, encoding="cp1252") == expected
    assert load_dataset(ndjson, encoding="cp1252") == expected


def test_encoding_is_threaded_through_load_dataset(write):
    path = write("people.csv", "name\nZoë\n", encoding="cp1252")
    assert load_dataset(path, encoding="cp1252") == [{"name": "Zoë"}]


def test_unknown_encoding_raises_tabulint_error(write):
    with pytest.raises(TabulintError, match="unknown encoding 'not-a-real-encoding'"):
        load_csv(write("people.csv", VALID_CSV), encoding="not-a-real-encoding")


def test_decode_failure_names_file_and_encoding(tmp_path):
    path = tmp_path / "people.csv"
    path.write_bytes("name\nMünchen\n".encode("cp1252"))
    with pytest.raises(TabulintError, match=r"people\.csv.*encoding 'utf-8'"):
        load_csv(path)


def test_utf8_bom_is_stripped_with_utf8_sig(write):
    path = write("people.csv", "\ufeffname,age\nAda,36\n", encoding="utf-8")
    assert load_csv(path, encoding="utf-8-sig") == [{"name": "Ada", "age": "36"}]


def test_utf8_bom_is_stripped_for_json_and_jsonl(write):
    json_path = write("people.json", '\ufeff[{"name": "Ada"}]', encoding="utf-8")
    jsonl_path = write("people.jsonl", '\ufeff{"name": "Ada"}\n', encoding="utf-8")
    assert load_json(json_path, encoding="utf-8-sig") == [{"name": "Ada"}]
    assert load_jsonl(jsonl_path, encoding="utf-8-sig") == [{"name": "Ada"}]
