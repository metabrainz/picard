<!-- pyml disable-next-line first-line-heading-->
# Writing Picard tests

Tests live in this directory and use pytest. A shared `test/conftest.py` provides
session-wide fixtures and config defaults. Run them with:

```bash
pytest -n auto          # in an activated virtual environment
uv run pytest -n auto   # otherwise
```

## Two styles coexist

Most of the older suite subclasses `PicardTestCase` (`test/picardtestcase.py`),
which provides helpers such as `set_config_values()`, `patch_tagger_instance()`
and `mktmpdir()`. Newer subsystems (`test/session/`, `test/script_text_edit/`, the
custom columns and theme tests) are written as plain pytest functions with
fixtures. Both are supported. Match the style of the file you are editing, and do
not convert existing tests from one style to the other as part of an unrelated
change.

## Table-driven tests

`@pytest.mark.parametrize` cannot be used on `PicardTestCase` subclasses — pytest
does not inject the parameter, so the test errors with a missing-argument
`TypeError`. Use the `subtest_cases` decorator instead, which reads like
`parametrize` but injects the arguments itself, running each case in its own
`subTest` so that one failing case neither hides the others nor stops the run:

```python
from test.picardtestcase import (
    PicardTestCase,
    subtest_cases,
)


class ScriptTest(PicardTestCase):
    @subtest_cases(
        "expression,expected",
        [
            ("$gt(10,4)", "1"),
            ("$gt(6,6)", ""),
        ],
    )
    def test_gt(self, expression, expected):
        self.assertScriptResultEquals(expression, expected)
```

`argvalues` may also be a mapping of `label -> args`, for cases whose arguments do
not describe themselves:

```python
class SatisfiedTest(PicardTestCase):
    @subtest_cases(
        "overrides,expected",
        {
            'tags want all images': ({'embed_only_front': False}, False),
            'both want only the front': ({}, True),
        },
    )
    def test_satisfied(self, overrides, expected):
        self.assertEqual(is_satisfied(overrides), expected)
```

Unlike `parametrize` this stays a single test as far as pytest is concerned, so an
individual case cannot be selected with `-k`.

Plain-pytest test files use `@pytest.mark.parametrize` directly; `subtest_cases` is
only needed for `PicardTestCase` subclasses.

## Qt widget tests

A session-scoped `qapp` fixture in `conftest.py` provides a `QApplication` instance
that lives for the entire test run. Tests that create Qt widgets must request it as
a dependency:

```python
@pytest.fixture()
def my_widget(qapp):
    from picard.ui.widgets.mywidget import MyWidget

    return MyWidget()
```

Do **not** create your own `QApplication` or `QCoreApplication` in tests — doing so
causes crashes when `pytest-randomly` reorders tests. Always reuse the shared `qapp`
fixture. If a unittest-based test needs a Qt event loop, call
`QCoreApplication.instance()` and only create a new one if it returns `None`.

## Directory layout and file naming

Tests are grouped into subdirectories that mirror the code they cover, for example:

- `test/ui/` — user interface code (`picard/ui/`)
- `test/formats/` — audio format handlers (`picard/formats/`)
- `test/plugins3/` — the v3 plugin system (`picard/plugin3/`)
- `test/util/` — utilities (`picard/util/`)

Files are named `test_<subject>.py`. Inside a subdirectory, do **not** repeat the
directory name in the file name: a UI test lives at `test/ui/test_ratingwidget.py`,
not `test/ui/test_ui_ratingwidget.py`, just as a format test is
`test/formats/test_mp4.py`. Tests that do not belong to a specific subsystem stay at
the top level of `test/`.

The subject is the module under test, so `<subject>` is the module name with the
`.py` stripped. A test that covers the package's own `__init__.py` (rather than one
of its submodules) is therefore named `test_init.py`: tests for `picard/disc/__init__.py`
live in `test/disc/test_init.py`, and tests for `picard/webservice/__init__.py` live
in `test/webservice/test_init.py`. When a single existing file bundles tests for the
package `__init__.py` together with tests for its submodules, split it so each file
maps to one module (`test_init.py` for the package, `test_<submodule>.py` for each
submodule) rather than naming the whole thing `test_init.py`.

Imports use absolute package paths (`from test.picardtestcase import ...`) and test
data is located with `get_test_data_path()`, so a test's behaviour does not depend on
which directory the file lives in; moving a test between directories is safe.

## Test subpackages (`__init__.py`)

Every test subdirectory is a Python package: it contains an `__init__.py`. This is
not optional. Under pytest's default `prepend` import mode a bare `.py` file is
imported as a top-level module named after its basename, so two files that share a
basename across different directories — for example `test/disc/test_init.py` and
`test/coverart/test_init.py`, or `test/disc/test_utils.py` and
`test/coverart/test_utils.py` — collide in `sys.modules` and collection fails with an
"import file mismatch" error. Making each directory a package qualifies the module
name with its package path (`test.disc.test_init` vs `test.coverart.test_init`), which
removes the clash. This is also why the `test_init.py` / `test_utils.py` naming above
is safe.

The `__init__.py` normally just carries the license header and a one-line docstring,
but it is a regular module and may hold shared helpers for that subpackage — fixtures,
factory functions, fake objects, constants — imported by the tests via the absolute
path, e.g. `from test.coverart import make_image`. Keep such helpers small and
specific to the subpackage; cross-cutting helpers belong in `test/picardtestcase.py`
or a dedicated module. Larger shared scaffolding is often placed in a sibling
`helpers.py` or `conftest.py` instead (see `test/plugins3/helpers.py` and the
`conftest.py` files under `test/session/` and `test/script_text_edit/`); use
`__init__.py` for helpers only when they are genuinely tied to the package itself.
