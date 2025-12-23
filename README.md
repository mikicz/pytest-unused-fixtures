# pytest-unused-fixtures

A pytest plugin to list unused fixtures after a test run.

The plugin watches all fixtures which are used in a test run, and then compares it to all the fixtures available in the same test collection. It then prints out all the fixtures which were not used, groupped by where they were defined.

Running the tests is required to accurately record which fixtures are used, as pytest provides ways of dynamically requesting fixtures, and pure static analysis will not catch those.

## Installation

```shell
$ pip install pytest-unused-fixtures
```

## Options

| Option Name                           | Type             | Description                                                    |
|---------------------------------------|------------------|----------------------------------------------------------------|
| `--unused-fixtures`                   | switch           | Enable plugin                                                  |
| `--unused-fixtures-ignore-path`       | string*          | Ignore paths for consideration of unused fixtures              |
| `--unused-fixtures-context`           | array\<string\>  | Only consider fixtures missing if defined in these directories |
| `--unused-fixtures-fail-when-present` | switch           | Fail pytest session if unused fixtures are present             |


## Usage

After installing the package, the plugin is enabled by adding the switch `--unused-fixtures`.

Paths of fixtures can be ignored with one or multiple `--unused-fixtures-ignore-path` arguments. For example `--unused-fixtures-ignore-path=venv` will ignore all fixtures defined in the `venv` folder.

Alternatively, you can limit the scope in which the plugin looks for unused fixtures to a specific directory or directories. For example:

**Limit scope to one directory**
This example will only display unused fixtures that were defined in the `tests` folder
```shell
pytest tests --unused-fixtures --unused-fixtures-context tests
```

**Limit scope to multiple directories**
This example will only display unused fixtures that were defined in the `directory1` and `directory2/sub-directory` folders
```shell
pytest tests --unused-fixtures --unused-fixtures-context directory1 directory2/sub-directory
```

**Fail test session**
By default, when you use the `--unused-fixtures` switch, the plugin will exit with the same exit code pytest
would have used if running without the plugin. Add the switch `--unused-fixtures-fail-when-present` and the
pytest session will return a non-zero exit code if there are unused fixtures.

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

Alternatively, if you prefer module imports:

```python
import pytest
import pytest_unused_fixtures

@pytest.fixture
@pytest_unused_fixtures.ignore
def ignored_fixture():
    pass
```


## Development

[Poetry](https://python-poetry.org/) (dependencies) and [pre-commit](https://pre-commit.com/) (coding standards) are required for development. There are some tests, obviously written in [pytest](https://pytest.org/).

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

### 0.3.1 (Dec 23, 2025)

* Default available_fixtures to an empty set (#28)

### 0.3.0 (Dec 2, 2025)

* Allow decorating fixtures with ignore_unused_fixture (#24)

### 0.2.1 (Nov 10, 2025)

* Support Python 3.14
* Drop support for 3.9

### 0.2.0 (Mar 15, 2025)

* Test only on Pytest 8
* Add `--unused-fixtures-context`
* Add `--unused-fixtures-fail-when-present`
* Support Python 3.13

### 0.1.5 (Apr 8, 2024)

* Support Pytest 8

### 0.1.4 (Aug 8, 2023)

* Bump versions, add CI

### 0.1.3 (Jun 30, 2023)

* Print line number
* Support Python 3.9

### 0.1.2 (Jun 15, 2023)

* Fix typo, add repository to PyPI
* Update location handling with respect to showing fixture locations and ignoring paths

### 0.1.1 (Jun 14, 2023)

* Fix location handling
* Add decorator for ignoring fixtures from report

### 0.1.0 (Jun 14, 2023)

* First Release
