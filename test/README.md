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

Imports use absolute package paths (`from test.picardtestcase import ...`) and test
data is located with `get_test_data_path()`, so a test's behaviour does not depend on
which directory the file lives in; moving a test between directories is safe.
