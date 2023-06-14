# pytest-unused-fixtures

A pytest plugin to list unused fixtures after a test run.

The plugin watches all fixtures which are used in a test run, and then compares it to all the fixtures available in the same test collection. It then prints out all the fixtures which were not used, groupped by where they were defined.

Running the tests is required to accurately record which fixtures are used, as pytest provides ways of dynamically requesting fixtures, and pure static analysis will not catch those.

## Installation

```shell
$ pip install pytest-unused-fixtures
```

## Usage

After installing the package, the plugin is enabled by adding the switch `--unused-fixtures`.

Paths of fixtures can be ignored with one or multiple `--unused-fixtures-ignore-path` arguments. For example `--unused-fixtures-ignore-path=venv` will ignore all fixtures defined in the `venv` folder.

### Ignoring specific fixtures from report

Sometimes there will be fixture which are unused on purpose, for example when used in tests which are skipped by default. A decorator is provided for ignoring fixtures from the unused report. See the example for usage:

```python
import pytest
from pytest_unused_fixtures import ignore_unused_fixture

@pytest.fixture
@ignore_unused_fixture
def ignored_fixture():
    pass
```

## Development

[Poetry](https://python-poetry.org/) (dependencies) and [pre-commit](https://pre-commit.com/) (coding standards) are required for development. Ther are some tests, obviously written in [pytest](https://pytest.org/).

```shell
$ poetry install
$ pre-commit install
$ pytest tests
```

## Thanks

Many thanks to

 - [pytest-deadfixtures](https://github.com/jllorencetti/pytest-deadfixtures) for inspiration for this project
 - [pytest-durations](https://github.com/blake-r/pytest-durations) for inspirations in parts of the implementation

## Changelog

### 0.1.0 (Jun 14, 2023)

* First Release
