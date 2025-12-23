from __future__ import annotations

import dataclasses
import itertools
from pathlib import Path
from typing import TYPE_CHECKING, Any, NoReturn

import pytest
from _pytest.compat import getlocation

if TYPE_CHECKING:
    from _pytest.config import Config, ExitCode
    from _pytest.fixtures import FixtureDef, SubRequest
    from _pytest.main import Session
    from _pytest.terminal import TerminalReporter

IGNORE_ATTR_NAME = "_ignore_unused_fixture"


@dataclasses.dataclass(frozen=True, eq=True)
class FixtureInfo:
    module: str
    argname: str
    scope: str
    location: str
    lineno: int

    def __lt__(self, other):
        return (self.module, self.location, self.argname) < (other.module, other.location, other.argname)

    @property
    def location_path(self):
        return Path(self.location.split(":")[0]).resolve()

    @property
    def pretty_path(self):
        cwd = Path.cwd().resolve()
        try:
            return self.location_path.relative_to(cwd)
        except ValueError:
            return self.location_path


class PytestUnusedFixturesPlugin:
    def __init__(self, ignore_paths: list[str | Path] | None = None, context: list[str | Path] | None = None):
        self.ignore_paths: list[Path] = [Path(x).resolve() for x in (ignore_paths or [])]
        self.used_fixtures: set[FixtureInfo] = set()
        self.available_fixtures: set[FixtureInfo] = set()
        self.curdir = Path().cwd()
        self.context = context or []
        self._shouldfail = False

    def get_fixture_info(self, fixturedef: FixtureDef) -> FixtureInfo:
        return FixtureInfo(
            module=fixturedef.func.__module__,
            argname=fixturedef.argname,
            scope=fixturedef.scope,
            location=getlocation(fixturedef.func, self.curdir),
            lineno=fixturedef.func.__code__.co_firstlineno,
        )

    @pytest.hookimpl(hookwrapper=True)
    def pytest_fixture_setup(self, fixturedef: FixtureDef, request: SubRequest) -> Any | None:
        self.used_fixtures.add(self.get_fixture_info(fixturedef))

        yield

    def pytest_collection_finish(self, session: Session) -> None:
        self.available_fixtures = {
            self.get_fixture_info(fixturedef)
            for fixturedef in itertools.chain(*session._fixturemanager._arg2fixturedefs.values())
            if (
                # if fixture is not in available fixtures, it won't be marked as unused
                not hasattr(fixturedef, IGNORE_ATTR_NAME)
                and not hasattr(fixturedef.func, IGNORE_ATTR_NAME)
                # baseid = '' when fixture comes from other plugins
                and getattr(fixturedef, "baseid", None) != ""
            )
        }

    def _write_fixtures(self, config: Config, terminalreporter: TerminalReporter, fixtures: set[FixtureInfo]):
        verbose = config.getvalue("verbose")
        tw = terminalreporter

        available: list[FixtureInfo] = []
        seen: set[tuple[str, str]] = set()

        fixture: FixtureInfo
        for fixture in fixtures:
            if (fixture.argname, fixture.location) in seen:
                continue
            seen.add((fixture.argname, fixture.location))
            available.append(fixture)

        available.sort()
        current_module = None
        for fixture in available:
            if current_module != fixture.module and not fixture.module.startswith("_pytest."):
                tw.write_sep("-", f"fixtures defined from {fixture.module}")
                current_module = fixture.module
            if verbose <= 0 and fixture.argname.startswith("_"):
                continue
            tw.write(f"{fixture.argname}", green=True)
            if fixture.scope != "function":
                tw.write(f" [{fixture.scope} scope]", cyan=True)
            tw.write(f" -- {fixture.pretty_path}:{fixture.lineno}", yellow=True)
            tw.write("\n")

    def pytest_terminal_summary(
        self,
        terminalreporter: TerminalReporter,
        exitstatus: ExitCode,
        config: Config,
    ) -> NoReturn:
        """Add the fixture time report."""
        fullwidth = config.get_terminal_writer().fullwidth
        unused_fixtures = self._get_unused_fixtures()

        # print fixtures
        if unused_fixtures:
            terminalreporter.write_sep(sep="=", title="UNUSED FIXTURES", fullwidth=fullwidth)
            self._write_fixtures(config, terminalreporter, unused_fixtures)

    def _get_unused_fixtures(self) -> set[FixtureInfo]:
        # do a simple set operation to get the unused fixtures
        unused_fixtures = self.available_fixtures - self.used_fixtures

        # ignore unused fixtures from ignored paths
        fixture: FixtureInfo
        non_ignored_unused_fixtures = set()
        for fixture in unused_fixtures:
            if any(fixture.location_path.is_relative_to(x) or fixture.location_path == x for x in self.ignore_paths):
                continue
            fixtures_in_context = [
                fixture.location_path.is_relative_to(x) for x in [Path(i).resolve() for i in self.context]
            ]
            if fixtures_in_context and not any(fixtures_in_context):
                continue
            non_ignored_unused_fixtures.add(fixture)

        return non_ignored_unused_fixtures

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtestloop(self, session: Session):
        yield

        if not session.config.getoption("--unused-fixtures-fail-when-present", False):
            return

        unused_fixtures = self._get_unused_fixtures()
        has_unused = unused_fixtures != set()

        if has_unused:
            message = f"Unused fixtures failure: total of {len(unused_fixtures)} unused fixtures"
            session.config.pluginmanager.getplugin("terminalreporter").write(
                f"\nERROR: {message}\n", red=True, bold=True
            )
            self._shouldfail = True

    def pytest_sessionfinish(self, session: Session, exitstatus: int | ExitCode) -> None:
        if self._shouldfail:
            session.exitstatus = pytest.ExitCode.TESTS_FAILED
