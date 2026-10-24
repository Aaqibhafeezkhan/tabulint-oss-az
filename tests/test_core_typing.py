from pathlib import Path
import subprocess
import sys
from typing import get_args

import pytest

from tabulint import check_records, infer_type, profile_fields
from tabulint.models import InferredType, SEVERITIES, Severity


ROOT = Path(__file__).resolve().parents[1]


def test_declared_type_names_match_inference_and_profiles():
    values = [None, True, 12, 1.5, "text"]
    emitted = {infer_type(value) for value in values}
    assert emitted == set(get_args(InferredType))
    profiles = profile_fields([{f"field_{index}": value for index, value in enumerate(values)}])
    assert {profile.dominant_type for profile in profiles} == emitted
    assert {name for profile in profiles for name in profile.type_counts} == emitted - {"null"}


def test_declared_severities_match_emitted_issues():
    report = check_records([{"name": "Ada", "age": 36}, {"name": "", "age": "old"}])
    assert {issue.severity for issue in report.issues} == set(SEVERITIES) == set(get_args(Severity))


@pytest.mark.parametrize("fixture,expected_code", [("valid_models.py", 0), ("invalid_models.py", 1)])
def test_mypy_checks_valid_and_invalid_model_contracts(fixture, expected_code):
    result = subprocess.run(
        [sys.executable, "-m", "mypy", "--strict", "--no-incremental",
         "--show-error-codes", str(ROOT / "tests" / "typing" / fixture)],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.returncode == expected_code, result.stdout + result.stderr
    if expected_code:
        assert result.stdout.count("error:") == 4, result.stdout
        for code in ("[arg-type]", "[dict-item]", "[return-value]"):
            assert code in result.stdout
