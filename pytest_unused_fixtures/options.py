from __future__ import annotations

from typing import TYPE_CHECKING, NoReturn

if TYPE_CHECKING:
    from _pytest.config import Config, PytestPluginManager
    from _pytest.config.argparsing import Parser


def pytest_addoption(parser: Parser, pluginmanager: PytestPluginManager) -> NoReturn:
    group = parser.getgroup("pytest-unused-fixtures")
    group.addoption("--unused-fixtures", action="store_true", default=False, help="Try to identify unused fixtures.")
    group.addoption(
        "--unused-fixtures-ignore-path",
        metavar="PATH",
        type=str,
        default=None,
        action="append",
        help="Ignore fixtures in PATHs from unused fixtures report.",
    )
    group.addoption(
        "--unused-fixtures-fail-when-present",
        action="store_true",
        default=False,
        help="Exit the pytest session with a failure code if unused fixtures are found",
    )
    group.addoption(
        "--unused-fixtures-context",
        metavar="PATH",
        type=str,
        nargs="+",
        default=None,
        help="Limit the scope of which to look for unused fixtures to these directories",
    )


def pytest_configure(config: Config) -> NoReturn:
    if not config.getoption("--unused-fixtures"):
        return

    from pytest_unused_fixtures.plugin import PytestUnusedFixturesPlugin

    pluginmanager = config.pluginmanager

    plugin = PytestUnusedFixturesPlugin
    if pluginmanager.hasplugin("xdist"):
        from pytest_unused_fixtures.xdist import PytestUnusedFixturesPluginXdist

        plugin = PytestUnusedFixturesPluginXdist

    paths_ignore = config.getoption("--unused-fixtures-ignore-path")
    unused_fixture_context = config.getoption("--unused-fixtures-context")
    pluginmanager.register(plugin(paths_ignore, unused_fixture_context))
