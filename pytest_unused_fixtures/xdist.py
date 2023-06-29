from __future__ import annotations

from dataclasses import asdict
from typing import TYPE_CHECKING, Any, NoReturn

from pytest_unused_fixtures.plugin import FixtureInfo, PytestUnusedFixturesPlugin

if TYPE_CHECKING:
    from _pytest.config import ExitCode
    from _pytest.main import Session
    from xdist.workermanage import WorkerController

_WORKEROUTPUT_KEY_USED = "pytest_unused_fixtures_used"
_WORKEROUTPUT_KEY_AVAILABLE = "pytest_unused_fixtures_available"


class PytestUnusedFixturesPluginXdist(PytestUnusedFixturesPlugin):
    def pytest_sessionfinish(self, session: Session, exitstatus: int | ExitCode) -> None:
        # send used & available fixtures
        if (workeroutput := getattr(session.config, "workeroutput", None)) is not None:
            workeroutput[_WORKEROUTPUT_KEY_AVAILABLE] = list(map(asdict, self.available_fixtures))
            workeroutput[_WORKEROUTPUT_KEY_USED] = list(map(asdict, self.used_fixtures))

    def pytest_testnodedown(self, node: WorkerController, error: Any | None) -> NoReturn:
        if (workeroutput := getattr(node, "workeroutput", None)) is not None:
            # add used & available fixtures from nodes
            if self.available_fixtures is None:
                self.available_fixtures = set()
            self.available_fixtures.update(
                FixtureInfo(**x) for x in workeroutput.get(_WORKEROUTPUT_KEY_AVAILABLE, set())
            )
            self.used_fixtures.update(FixtureInfo(**x) for x in workeroutput.get(_WORKEROUTPUT_KEY_USED, set()))
