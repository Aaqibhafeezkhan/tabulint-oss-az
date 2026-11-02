import pytest

from tabulint import TabulintError, load_csv, load_dataset, load_json, load_jsonl

VALID_CSV = "name,age\nAda,36\nGrace,45\n"
VALID_JSON = '[{"name": "Ada", "age": 36}, {"name": "Grace", "age": 45}]'
VALID_JSONL = '{"name": "Ada", "age": 36}\n{"name": "Grace", "age": 45}\n'


@pytest.mark.parametrize("suffix,reader", [
    (".json", load_json), (".jsonl", load_jsonl), (".ndjson", load_jsonl),
])
@pytest.mark.parametrize("record,key", [
    ('{"x": 1, "x": 2}', "x"),
    ('{"x": null, "x": 2}', "x"),
    ('{"outer": {"x": 1, "x": 2}}', "x"),
    ('{"outer": [{"x": 1, "x": 2}]}', "x"),
    (r'{"x": 1, "\u0078": 2}', "x"),
    ('{"": 1, "": 2}', ""),
])
def test_json_readers_reject_duplicate_keys(write, suffix, reader, record, key):
    content = f"[{record}]" if suffix == ".json" else '\n{"ok": 0}\n  \n' + record + "\n"
    path = write("duplicate" + suffix, content)
    with pytest.raises(TabulintError) as error:
        reader(path)
    message = str(error.value)
    assert path in message
    assert "duplicate" in message
    assert repr(key) in message
    assert r"\u0078" not in message
    if suffix != ".json":
        assert "line 4" in message


@pytest.mark.parametrize("suffix", [".json", ".jsonl", ".ndjson"])
def test_load_dataset_rejects_duplicate_json_keys(write, suffix):
    record = '{"x": 1, "x": 2}'
    content = f"[{record}]" if suffix == ".json" else record + "\n"
    with pytest.raises(TabulintError, match="duplicate"):
        load_dataset(write("duplicate" + suffix, content))


@pytest.mark.parametrize("suffix", [".json", ".jsonl", ".ndjson"])
def test_duplicate_json_key_in_error_is_bounded(write, suffix):
    key = "x" * 400
    record = '{"' + key + '": 1, "' + key + '": 2}'
    path = write("duplicate" + suffix, f"[{record}]" if suffix == ".json" else record)
    with pytest.raises(TabulintError) as error:
        load_dataset(path)
    message = str(error.value)
    assert "duplicate JSON key" in message
    assert key not in message
    assert "..." in message
    assert len(message) < len(path) + 130


@pytest.mark.parametrize("suffix", [".json", ".jsonl", ".ndjson"])
def test_valid_nested_json_keeps_keys_scoped_to_each_object(write, suffix):
    record = '{"a": {"x": 1}, "b": [{"x": 2}, {"x": 3}], "X": 4, "x": 5}'
    content = f"[{record}, {record}]" if suffix == ".json" else record + "\n \n" + record + "\n"
    expected = {"a": {"x": 1}, "b": [{"x": 2}, {"x": 3}], "X": 4, "x": 5}
    assert load_dataset(write("valid" + suffix, content)) == [expected, expected]


@pytest.mark.parametrize("suffix", [".json", ".jsonl", ".ndjson"])
@pytest.mark.parametrize("encoding", ["cp1252", "utf-8-sig"])
def test_duplicate_key_validation_preserves_selected_encoding(write, suffix, encoding):
    duplicate = '{"caf\u00e9": 1, "caf\u00e9": 2}'
    valid = '{"caf\u00e9": 1}'
    bad_content = f"[{duplicate}]" if suffix == ".json" else "\n" + duplicate + "\n"
    good_content = f"[{valid}]" if suffix == ".json" else "\n" + valid + "\n"
    bad = write("bad" + suffix, bad_content, encoding=encoding)
    with pytest.raises(TabulintError) as error:
        load_dataset(bad, encoding=encoding)
    assert "'caf\u00e9'" in str(error.value)
    assert bad in str(error.value)
    if suffix != ".json":
        assert "line 2" in str(error.value)
    good = write("good" + suffix, good_content, encoding=encoding)
    assert load_dataset(good, encoding=encoding) == [{"caf\u00e9": 1}]


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


def test_malformed_json_names_line_column_and_excerpt(write):
    path = write("bad.json", '[\n  {"name": }\n]')
    with pytest.raises(TabulintError) as error:
        load_json(path)
    message = str(error.value)
    assert path in message
    assert "line 2, column 12" in message
    assert 'near \'  {"name": }\'' in message


@pytest.mark.parametrize("suffix,reader", [
    (".json", load_json), (".jsonl", load_jsonl), (".ndjson", load_jsonl),
])
def test_long_malformed_json_excerpt_is_bounded(write, suffix, reader):
    record = '{"payload": "' + "x" * 400 + '", "bad": }'
    path = write("long" + suffix, f"[{record}]" if suffix == ".json" else record)
    with pytest.raises(TabulintError) as error:
        reader(path)
    message = str(error.value)
    assert '"bad": }' in message
    assert "..." in message
    assert "x" * 100 not in message
    assert len(message) < len(path) + 200


@pytest.mark.parametrize("suffix", [".json", ".jsonl", ".ndjson"])
@pytest.mark.parametrize("parser_error", [RecursionError, ValueError])
def test_json_parser_limit_raises_tabulint_error(write, monkeypatch, suffix, parser_error):
    content = '[{"value": 1}]' if suffix == ".json" else '\n{"value": 1}'
    path = write("limited" + suffix, content)

    def reject_input(*args, **kwargs):
        raise parser_error("parser limit reached")

    with monkeypatch.context() as patch:
        patch.setattr("tabulint.loader.json.loads", reject_input)
        with pytest.raises(TabulintError, match="too deeply nested or large") as error:
            load_dataset(path)

    assert isinstance(error.value.__cause__, parser_error)
    assert path in str(error.value)
    if suffix != ".json":
        assert "line 2" in str(error.value)


def test_json_must_be_array_of_objects(write):
    with pytest.raises(TabulintError, match="array of objects"):
        load_json(write("obj.json", '{"name": "Ada"}'))
    with pytest.raises(TabulintError, match="not a JSON object"):
        load_json(write("mixed.json", '[{"name": "Ada"}, 42]'))


def test_jsonl_malformed_line_names_physical_line_number(write):
    content = '{"name": "Ada"}\n\n{oops}\n'
    with pytest.raises(TabulintError, match=r"line 3, column 2.*near '\{oops\}'"):
        load_jsonl(write("bad.jsonl", content))


def test_jsonl_non_object_line_names_physical_line_number(write):
    content = '{"name": "Ada"}\n\n[1, 2]\n'
    with pytest.raises(TabulintError, match=r"line 3.*not a JSON object"):
        load_jsonl(write("bad.jsonl", content))


def test_csv_with_extra_fields_raises(write):
    with pytest.raises(TabulintError, match=r"line 2 has 3 fields; header declares 2") as error:
        load_csv(write("ragged.csv", "name,age\nAda,36,extra\n"))
    assert "Check --delimiter" in str(error.value)


def test_ragged_csv_names_physical_line_after_multiline_field(write):
    path = write("ragged.csv", 'name,note\nAda,"first\nsecond"\nGrace,ok,extra\n')
    with pytest.raises(TabulintError, match=r"line 4 has 3 fields; header declares 2"):
        load_csv(path)


def test_one_column_csv_remains_valid(write):
    path = write("single.csv", "name;age\nAda;36\n")
    assert load_csv(path) == [{"name;age": "Ada;36"}]


def test_ragged_one_column_csv_suggests_delimiter(write):
    path = write("ragged.csv", "name;age\nAda,36\n")
    with pytest.raises(TabulintError, match=r"2 fields; header declares 1.*--delimiter"):
        load_csv(path)


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


@pytest.mark.parametrize("suffix", [".csv", ".json", ".jsonl", ".ndjson"])
def test_directory_read_failure_raises_tabulint_error(tmp_path, suffix):
    path = tmp_path / ("folder" + suffix)
    path.mkdir()
    with pytest.raises(TabulintError, match="directory.*not a regular file"):
        load_dataset(path)


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


LINE_BREAK_DELIMITERS = pytest.mark.parametrize(
    "delimiter", ["\r", "\n"], ids=["carriage-return", "line-feed"]
)


@LINE_BREAK_DELIMITERS
@pytest.mark.parametrize(
    "content",
    ["name,age\nAda,36\n", "", "  \n", "name,age\n"],
    ids=["records", "blank", "whitespace", "header-only"],
)
@pytest.mark.parametrize("loader", [load_csv, load_dataset])
def test_line_break_delimiter_raises(tmp_path, loader, delimiter, content):
    path = tmp_path / "people.csv"
    path.write_bytes(content.encode("utf-8"))
    with pytest.raises(TabulintError, match="CSV delimiter cannot be a line break") as exc:
        loader(path, delimiter=delimiter)
    assert str(path) in str(exc.value)
    assert repr(delimiter) in str(exc.value)


@pytest.mark.parametrize(
    ("delimiter", "content"),
    [
        ("\t", "name\tage\nAda\t36\n"),
        (";", "name;age\nAda;36\n"),
        ("\u00a7", "name\u00a7age\nAda\u00a736\n"),
        ("\0", "name\0age\nAda\x0036\n"),
    ],
    ids=["tab", "semicolon", "unicode", "nul"],
)
def test_unusual_but_valid_delimiters_still_load(tmp_path, delimiter, content):
    path = tmp_path / "people.csv"
    path.write_bytes(content.encode("utf-8"))
    assert load_csv(path, delimiter=delimiter) == [{"name": "Ada", "age": "36"}]


def test_single_column_csv_with_crlf_rows_remains_valid(tmp_path):
    path = tmp_path / "names.csv"
    path.write_bytes(b"name\r\nAda\r\nGrace\r\n")
    assert load_csv(path) == [{"name": "Ada"}, {"name": "Grace"}]


@LINE_BREAK_DELIMITERS
@pytest.mark.parametrize("suffix", [".json", ".jsonl", ".ndjson"])
def test_line_break_delimiter_is_ignored_for_json_formats(write, delimiter, suffix):
    content = '[{"name": "Ada"}]' if suffix == ".json" else '{"name": "Ada"}\n'
    path = write("people" + suffix, content)
    assert load_dataset(path, delimiter=delimiter) == [{"name": "Ada"}]



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


def test_unknown_encoding_name_in_error_is_bounded(write):
    encoding = "x" * 400
    path = write("people.csv", VALID_CSV)
    with pytest.raises(TabulintError) as error:
        load_csv(path, encoding=encoding)
    message = str(error.value)
    assert encoding not in message
    assert len(message) < len(path) + 120


@pytest.mark.parametrize("suffix,content", [
    (".csv", VALID_CSV), (".json", VALID_JSON),
    (".jsonl", VALID_JSONL), (".ndjson", VALID_JSONL),
])
@pytest.mark.parametrize("encoding", ["hex", "base64_codec", "rot_13"])
def test_non_text_encoding_raises_tabulint_error(write, suffix, content, encoding):
    path = write("people" + suffix, content)
    with pytest.raises(TabulintError, match="not a text encoding") as error:
        load_dataset(path, encoding=encoding)
    assert path in str(error.value)
    assert repr(encoding) in str(error.value)


@pytest.mark.parametrize("suffix,content", [
    (".csv", VALID_CSV), (".json", VALID_JSON),
    (".jsonl", VALID_JSONL), (".ndjson", VALID_JSONL),
])
@pytest.mark.parametrize("encoding", ["utf-16", "utf-32", "undefined"])
def test_plain_unicode_error_raises_tabulint_error(tmp_path, suffix, content, encoding):
    path = tmp_path / ("people" + suffix)
    byte_encoding = "utf-8" if encoding == "undefined" else encoding + "-le"
    path.write_bytes(content.encode(byte_encoding))
    with pytest.raises(TabulintError, match="could not decode file") as error:
        load_dataset(path, encoding=encoding)
    assert isinstance(error.value.__cause__, UnicodeError)
    assert str(path) in str(error.value)
    assert repr(encoding) in str(error.value)


@pytest.mark.parametrize("suffix", [".csv", ".json", ".jsonl", ".ndjson"])
def test_input_path_with_nul_raises_tabulint_error(tmp_path, suffix):
    path = str(tmp_path / ("invalid\0" + suffix))
    with pytest.raises(TabulintError, match="input path contains a NUL character") as error:
        load_dataset(path)
    assert "\0" not in str(error.value)


@pytest.mark.parametrize("suffix,content", [
    (".csv", VALID_CSV), (".json", VALID_JSON),
    (".jsonl", VALID_JSONL), (".ndjson", VALID_JSONL),
])
def test_encoding_with_nul_raises_tabulint_error(write, suffix, content):
    path = write("people" + suffix, content)
    with pytest.raises(TabulintError, match="invalid encoding") as error:
        load_dataset(path, encoding="utf-8\0")
    assert path in str(error.value)
    assert "\0" not in str(error.value)


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
