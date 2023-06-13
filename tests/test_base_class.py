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
    result = pytester.runpytest("--unused-fixtures", "--unused-fixtures-ignore-path", ".../")
    result.assert_outcomes(passed=2)
    result.stdout.no_fnmatch_line("*duration top*")
    result.stdout.fnmatch_lines(
        [
            "*UNUSED FIXTURES*",
            "*fixtures defined from test_default*",
            "*fixture_c -- test_default.py:13*",
        ],
        consecutive=True,
    )
