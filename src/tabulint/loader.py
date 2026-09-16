"""Loading CSV, JSON, and JSON Lines datasets into a list of records."""

import csv
import json
from pathlib import Path

from .models import Record, TabulintError


def load_csv(path: str | Path) -> list[Record]:
    """Read a CSV file with a header row into a list of dicts."""
    path = Path(path)
    try:
        with path.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                return []
            if any(name is None or name == "" for name in reader.fieldnames):
                raise TabulintError(f"{path}: CSV header contains an empty column name")
            rows: list[Record] = []
            for line_number, row in enumerate(reader, start=2):
                if None in row:
                    raise TabulintError(
                        f"{path}: line {line_number} has more fields than the header"
                    )
                rows.append(dict(row))
            return rows
    except FileNotFoundError as exc:
        raise TabulintError(f"{path}: file not found") from exc
    except UnicodeDecodeError as exc:
        raise TabulintError(f"{path}: file is not valid UTF-8") from exc
    except csv.Error as exc:
        raise TabulintError(f"{path}: malformed CSV ({exc})") from exc


def load_json(path: str | Path) -> list[Record]:
    """Read a JSON file containing an array of objects into a list of dicts."""
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise TabulintError(f"{path}: file not found") from exc
    except UnicodeDecodeError as exc:
        raise TabulintError(f"{path}: file is not valid UTF-8") from exc

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise TabulintError(f"{path}: malformed JSON ({exc.msg} at line {exc.lineno})") from exc

    if not isinstance(data, list):
        raise TabulintError(f"{path}: expected a JSON array of objects")
    for index, item in enumerate(data):
        if not isinstance(item, dict):
            raise TabulintError(f"{path}: item {index} is not a JSON object")
    return [dict(item) for item in data]


def load_jsonl(path: str | Path) -> list[Record]:
    """Read a JSON Lines file containing one JSON object per line."""
    path = Path(path)
    rows: list[Record] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise TabulintError(
                        f"{path}: malformed JSON on line {line_number} ({exc.msg})"
                    ) from exc
                if not isinstance(item, dict):
                    raise TabulintError(f"{path}: line {line_number} is not a JSON object")
                rows.append(dict(item))
    except FileNotFoundError as exc:
        raise TabulintError(f"{path}: file not found") from exc
    except UnicodeDecodeError as exc:
        raise TabulintError(f"{path}: file is not valid UTF-8") from exc
    return rows


def load_dataset(path: str | Path) -> list[Record]:
    """Load a dataset, choosing the reader from the file extension."""
    suffix = Path(path).suffix.lower()
    if suffix == ".csv":
        return load_csv(path)
    if suffix == ".json":
        return load_json(path)
    if suffix in {".jsonl", ".ndjson"}:
        return load_jsonl(path)
    raise TabulintError(
        f"{path}: unsupported file type '{suffix or 'none'}' "
        "(expected .csv, .json, .jsonl, or .ndjson)"
    )
