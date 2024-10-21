from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def sample_testfile(pytester):
    code = """
        import pytest

        class BaseTest:
            @pytest.fixture
            def fixture_a(self):
                return None

            @pytest.fixture
            def fixture_b(self):
                return None

            @pytest.fixture
            def fixture_c(self):
                return None

        class TestImplementationUsesOne(BaseTest):
            def test_a(self, fixture_a):
                pass

        class TestImplementationUsesBoth(BaseTest):
            def test_a(self, fixture_a, fixture_b):
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
    result.assert_outcomes(passed=2)
    result.stdout.no_fnmatch_line("*duration top*")
    result.stdout.fnmatch_lines(
        [
            "*UNUSED FIXTURES*",
            "*fixtures defined from test_default*",
            "*fixture_c -- test_default.py:12*",
        ],
        consecutive=True,
    )


def test_option_context(pytester, sample_testfile):
    """
    test the option `--unused-fixtures-context`.
    """
    result = pytester.runpytest("--unused-fixtures", "--unused-fixtures-context", Path(__file__).parent)
    result.assert_outcomes(passed=2)
    result.stdout.no_fnmatch_line("*UNUSED FIXTURES*")


def test_fail_when_present(pytester, sample_testfile):
    result = pytester.runpytest("--unused-fixtures", "--unused-fixtures-fail-when-present")
    result.stdout.fnmatch_lines(["*ERROR: Unused fixtures failure: total of 1 unused fixtures*"])
    result.stdout.fnmatch_lines(
        [
            "*UNUSED FIXTURES*",
            "*fixtures defined from test_fail_when_present*",
            "*fixture_c -- test_fail_when_present.py:12*",
        ],
    )
    assert result.ret == pytest.ExitCode.TESTS_FAILED
