import itertools
from pathlib import Path
from typing import TYPE_CHECKING, Any, NoReturn

import pytest
from _pytest.compat import getlocation
from _pytest.python import _pretty_fixture_path

if TYPE_CHECKING:
    from _pytest.config import Config, ExitCode
    from _pytest.fixtures import FixtureDef, SubRequest
    from _pytest.main import Session
    from _pytest.terminal import TerminalReporter


class PytestUnusedFixturesPlugin:
    def __init__(self, ignore_paths=None):
        self.ignore_paths: list[str] | None = ignore_paths
        self.used_fixtures = set()
        self.available_fixtures = None

    @pytest.hookimpl(hookwrapper=True)
    def pytest_fixture_setup(self, fixturedef: "FixtureDef", request: "SubRequest") -> Any | None:
        self.used_fixtures.add(fixturedef)

        yield

    def pytest_sessionfinish(self, session: "Session", exitstatus):
        fm = session._fixturemanager
        available_fixtures = set(itertools.chain(*fm._arg2fixturedefs.values()))
        self.available_fixtures = available_fixtures

    def _write_fixtures(self, config: "Config", terminalreporter: "TerminalReporter", fixtures: set):
        verbose = config.getvalue("verbose")
        tw = terminalreporter
        curdir = Path.cwd()

        available = []
        seen: set[tuple[str, str]] = set()

        for fixturedef in fixtures:
            loc = getlocation(fixturedef.func, str(curdir))
            if (fixturedef.argname, loc) in seen:
                continue
            seen.add((fixturedef.argname, loc))
            fixture_path = _pretty_fixture_path(fixturedef.func)

            available.append(
                (
                    fixturedef.func.__module__,
                    len(fixturedef.baseid),
                    fixture_path,
                    fixturedef.argname,
                    fixturedef,
                )
            )

        available.sort()
        currentmodule = None
        for module, _baseid, prettypath, argname, fixturedef in available:
            if currentmodule != module and not module.startswith("_pytest."):
                tw.write_sep("-", f"fixtures defined from {module}")
                currentmodule = module
            if verbose <= 0 and argname.startswith("_"):
                continue
            tw.write(f"{argname}", green=True)
            if fixturedef.scope != "function":
                tw.write(" [%s scope]" % fixturedef.scope, cyan=True)
            tw.write(f" -- {prettypath}", yellow=True)
            tw.write("\n")

    def pytest_terminal_summary(
        self,
        terminalreporter: "TerminalReporter",
        exitstatus: "ExitCode",
        config: "Config",
    ) -> NoReturn:
        """Add the fixture time report."""
        fullwidth = config.get_terminal_writer().fullwidth

        unused_fixtures = self.available_fixtures - self.used_fixtures
        non_ignored_unused_fixtures = []
        for fixturedef in unused_fixtures:
            if fixturedef is None:
                continue
            fixture_path = _pretty_fixture_path(fixturedef.func)

            if any(fixture_path.startswith(x) for x in (self.ignore_paths or [])):
                continue
            non_ignored_unused_fixtures.append(fixturedef)

        if non_ignored_unused_fixtures:
            terminalreporter.write_sep(sep="=", title="UNUSED FIXTURES", fullwidth=fullwidth)
            self._write_fixtures(config, terminalreporter, non_ignored_unused_fixtures)
