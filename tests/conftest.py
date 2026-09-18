import pytest


@pytest.fixture
def write(tmp_path):
    def _write(name: str, content: str, encoding: str = "utf-8") -> str:
        path = tmp_path / name
        path.write_text(content, encoding=encoding)
        return str(path)

    return _write
