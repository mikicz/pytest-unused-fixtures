from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def sample_testfile(pytester):
    code = """
        import pytest
        from pytest_unused_fixtures import ignore_unused_fixture

        class TestIgnore:
            @pytest.fixture
            def fixture_a(self):
                return None

            @pytest.fixture
            @ignore_unused_fixture
            def fixture_b(self):
                return None

            @pytest.fixture
            def fixture_c(self):
                return None

            def test_a(self, fixture_a):
                pass
    """
    pytester.makepyfile(code)


def test_default(pytester, sample_testfile):
    """Zero durations should disable plugin completely."""
    result = pytester.runpytest(
        "--unused-fixtures",
        "--unused-fixtures-ignore-path",
        Path(__file__).parents[1] / "venv",
        "--unused-fixtures-ignore-path",
        Path(__file__).parents[1] / ".tox",
    )
    result.assert_outcomes(passed=1)
    result.stdout.no_fnmatch_line("*duration top*")
    result.stdout.fnmatch_lines(
        [
            "*UNUSED FIXTURES*",
            "*fixtures defined from test_default*",
            "*fixture_c -- test_default.py:14*",
        ],
        consecutive=True,
    )
