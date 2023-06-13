import functools
import inspect
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


def get_class_that_defined_method(meth):
    """
    Thank you very much https://stackoverflow.com/a/25959545/3697325
    """
    if isinstance(meth, functools.partial):
        return get_class_that_defined_method(meth.func)
    if inspect.ismethod(meth) or (
        inspect.isbuiltin(meth)
        and getattr(meth, "__self__", None) is not None
        and getattr(meth.__self__, "__class__", None)
    ):
        for cls in inspect.getmro(meth.__self__.__class__):
            if meth.__name__ in cls.__dict__:
                return cls
        meth = getattr(meth, "__func__", meth)  # fallback to __qualname__ parsing
    if inspect.isfunction(meth):
        cls = getattr(
            inspect.getmodule(meth),
            meth.__qualname__.split(".<locals>", 1)[0].rsplit(".", 1)[0],
            None,
        )
        if isinstance(cls, type):
            return cls
    return getattr(meth, "__objclass__", None)  # handle special descriptor objects


class PytestUnusedFixturesPlugin:
    def __init__(self, ignore_paths=None):
        self.ignore_paths: list[str] | None = ignore_paths
        self.used_fixtures = set()
        self.available_fixtures: None | set["FixtureDef"] = None

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

        # do a simple set operation to get the unused fixtures
        unused_fixtures = self.available_fixtures - self.used_fixtures

        # ignore unused fixtures from ignored paths
        non_ignored_unused_fixtures = []
        for fixturedef in unused_fixtures:
            if fixturedef is None:
                continue
            fixture_path = _pretty_fixture_path(fixturedef.func)

            if any(fixture_path.startswith(x) for x in (self.ignore_paths or [])):
                continue
            non_ignored_unused_fixtures.append(fixturedef)
        unused_fixtures = non_ignored_unused_fixtures

        # handle fixtures in class-inheritance
        unused_fixtures_without_class_inheritance = []
        concrete_used_methods = set()
        for fixturedef in self.used_fixtures:
            cls = get_class_that_defined_method(fixturedef.func)
            if cls is not None:
                concrete_used_methods.add(getattr(cls, fixturedef.argname))

        for fixturedef in unused_fixtures:
            # can't find base class -> must be unused
            cls = get_class_that_defined_method(fixturedef.func)
            if cls is None or getattr(cls, fixturedef.argname) not in concrete_used_methods:
                unused_fixtures_without_class_inheritance.append(fixturedef)

        unused_fixtures = unused_fixtures_without_class_inheritance

        # print fixtures
        if unused_fixtures:
            terminalreporter.write_sep(sep="=", title="UNUSED FIXTURES", fullwidth=fullwidth)
            self._write_fixtures(config, terminalreporter, unused_fixtures)
