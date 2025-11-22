from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from .plugin import IGNORE_ATTR_NAME

if TYPE_CHECKING:
    from _pytest.fixtures import FixtureFunction, FixtureFunctionDefinition

    Fixture = TypeVar("Fixture", bound=FixtureFunctionDefinition)


def ignore_unused_fixture(func_or_fixture: FixtureFunction | Fixture) -> FixtureFunction | Fixture:
    if hasattr(func_or_fixture, "_get_wrapped_function"):
        func = func_or_fixture._get_wrapped_function()
    else:
        func = func_or_fixture

    setattr(func, IGNORE_ATTR_NAME, True)

    return func_or_fixture
