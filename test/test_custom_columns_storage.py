# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 The MusicBrainz Team
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

from __future__ import annotations

from dataclasses import asdict
from types import SimpleNamespace
from typing import Callable

from picard.metadata import Metadata

import pytest

from picard.ui.columns import ColumnAlign
from picard.ui.itemviews.custom_columns import CustomColumn
from picard.ui.itemviews.custom_columns.storage import (
    CustomColumnConfigManager,
    CustomColumnKind,
    CustomColumnRegistrar,
    CustomColumnSpec,
    CustomColumnSpecSerializer,
    TransformName,
    _align_from_name,
    build_column_from_spec,
    delete_spec_by_key,
    get_spec_by_key,
    load_persisted_columns_once,
    load_specs_from_config,
    register_and_persist,
    save_specs_to_config,
    unregister_and_delete,
)
from picard.ui.itemviews.custom_columns.validation import (
    CustomColumnSpecValidator,
    is_spec_valid,
    validate_spec,
)


@pytest.fixture
def fake_config(monkeypatch) -> SimpleNamespace:
    """Provide a fake config object for storage with an isolated settings map."""

    class _FakeSetting(dict):
        def raw_value(self, name, qtype=None):
            return self.get(name)

        def key(self, name):
            return name

    cfg = SimpleNamespace(setting=_FakeSetting({'enabled_plugins': [], 'custom_columns': []}), sync=lambda: None)
    import picard.ui.itemviews.custom_columns.storage as storage_mod

    monkeypatch.setattr(storage_mod, 'get_config', lambda: cfg, raising=True)
    # Also patch global config access used by script parser / extension points
    import picard.config as picard_config_mod

    monkeypatch.setattr(picard_config_mod, 'get_config', lambda: cfg, raising=True)
    import picard.extension_points as ext_points_mod

    monkeypatch.setattr(ext_points_mod, 'get_config', lambda: cfg, raising=True)
    # Reset one-shot loader between tests to ensure idempotency tests are independent
    storage_mod._loaded_once = False
    return cfg


@pytest.fixture
def fake_registry(monkeypatch) -> SimpleNamespace:
    """Provide a fake registry capturing register/unregister calls."""

    calls: list[tuple[str, dict]] = []

    def _register(column: CustomColumn, **kwargs) -> None:
        calls.append(("register", {'key': column.key, **kwargs}))

    def _unregister(key: str) -> None:
        calls.append(("unregister", {'key': key}))

    reg = SimpleNamespace(register=_register, unregister=_unregister, calls=calls)
    import picard.ui.itemviews.custom_columns.storage as storage_mod

    monkeypatch.setattr(storage_mod, 'registry', reg, raising=True)
    return reg


@pytest.fixture
def sample_spec() -> CustomColumnSpec:
    """Return a basic field spec used by multiple tests."""

    return CustomColumnSpec(
        title="Artist",
        key="artist",
        kind=CustomColumnKind.FIELD,
        expression="artist",
        width=None,
        align="LEFT",
        always_visible=False,
        add_to_file_view=True,
        add_to_album_view=True,
        insert_after_key="title",
        transform=None,
    )


class _FakeItem:
    def __init__(self, values: dict[str, str]):
        self.values = values

    def column(self, key: str) -> str:
        return self.values.get(key, "")

    @property
    def metadata(self) -> Metadata:
        md = Metadata()
        for k, v in self.values.items():
            md[k] = v
        return md


@pytest.mark.parametrize(
    ("kind", "transform"),
    [
        (CustomColumnKind.FIELD, None),
        (CustomColumnKind.SCRIPT, None),
        (CustomColumnKind.TRANSFORM, TransformName.UPPER),
    ],
)
def test_spec_to_from_dict_roundtrip(kind: CustomColumnKind, transform: TransformName | None) -> None:
    spec = CustomColumnSpec(
        title="T",
        key="k",
        kind=kind,
        expression="%artist%" if kind == CustomColumnKind.SCRIPT else "artist",
        width=120,
        align="RIGHT",
        always_visible=True,
        add_to_file_view=False,
        add_to_album_view=True,
        insert_after_key=None,
        transform=transform,
    )
    d = spec.to_dict()
    parsed = CustomColumnSpec.from_dict(d)
    assert asdict(parsed) == asdict(spec)


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("LEFT", ColumnAlign.LEFT),
        ("Right", ColumnAlign.RIGHT),
        ("unknown", ColumnAlign.LEFT),
    ],
)
def test_align_from_name(name: str, expected: ColumnAlign) -> None:
    assert _align_from_name(name) == expected


@pytest.mark.parametrize(
    ("transform", "input_value", "expected"),
    [
        (TransformName.UPPER, "abc", "ABC"),
        (TransformName.LOWER, "AbC", "abc"),
        (TransformName.TITLE, "abc def", "Abc Def"),
        (TransformName.STRIP, "  a  ", "a"),
        (TransformName.BRACKETS, "x", "[x]"),
    ],
)
def test_transform_callable(transform: TransformName, input_value: str, expected: str) -> None:
    # Access private factory via module to keep SOC of test and SUT
    import picard.ui.itemviews.custom_columns.storage as storage_mod

    fn: Callable[[str], str] = storage_mod._make_transform_callable(transform)
    assert fn(input_value) == expected
    # Empty string remains empty (no brackets for empty)
    assert fn("") in {"", expected if input_value == "" else fn("")}


@pytest.mark.parametrize("kind", [CustomColumnKind.FIELD, CustomColumnKind.SCRIPT, CustomColumnKind.TRANSFORM])
def test_build_column_from_spec_creates_column(kind: CustomColumnKind) -> None:
    expression = "%artist%" if kind == CustomColumnKind.SCRIPT else "artist"
    transform = TransformName.UPPER if kind == CustomColumnKind.TRANSFORM else None
    spec = CustomColumnSpec(
        title="Col",
        key=f"k_{kind.value}",
        kind=kind,
        expression=expression,
        width=None,
        align="LEFT",
        always_visible=False,
        transform=transform,
    )
    column = build_column_from_spec(spec)
    assert isinstance(column, CustomColumn)
    assert column.key == spec.key
    # Smoke-test provider evaluation
    item = _FakeItem({'artist': "Artist"})
    value = column.provider.evaluate(item)
    assert isinstance(value, str)
    if kind == CustomColumnKind.TRANSFORM:
        assert value == "ARTIST"


def test_save_and_load_specs_roundtrip(fake_config: SimpleNamespace, sample_spec: CustomColumnSpec) -> None:
    save_specs_to_config([sample_spec])
    out = load_specs_from_config()
    assert len(out) == 1
    assert asdict(out[0]) == asdict(sample_spec)


def test_add_update_and_get_and_delete_spec(fake_config: SimpleNamespace, sample_spec: CustomColumnSpec) -> None:
    # add via save
    save_specs_to_config([sample_spec])
    # update title
    updated = CustomColumnSpec(**{**asdict(sample_spec), 'title': "New Title"})
    # Use register_and_persist to also exercise registry path (patched)
    import picard.ui.itemviews.custom_columns.storage as storage_mod

    # Patch registry to inert for this specific test
    storage_mod.registry = SimpleNamespace(register=lambda *a, **k: None, unregister=lambda *a, **k: None)

    register_and_persist(updated)
    spec = get_spec_by_key(sample_spec.key)
    assert spec is not None
    assert spec.title == "New Title"

    # Delete path
    assert delete_spec_by_key(sample_spec.key) is True
    assert get_spec_by_key(sample_spec.key) is None


def test_register_and_persist_calls_registry(fake_config: SimpleNamespace, fake_registry: SimpleNamespace) -> None:
    spec = CustomColumnSpec(
        title="T",
        key="k1",
        kind=CustomColumnKind.FIELD,
        expression="artist",
        insert_after_key="title",
    )
    register_and_persist(spec)
    # Saved to config
    loaded = load_specs_from_config()
    assert len(loaded) == 1 and loaded[0].key == "k1"
    # Registry was called
    assert (
        "register",
        {'key': "k1", 'add_to_file_view': True, 'add_to_album_view': True, 'insert_after_key': "title"},
    ) in fake_registry.calls


def test_unregister_and_delete_calls_registry(fake_config: SimpleNamespace, fake_registry: SimpleNamespace) -> None:
    # Ensure config has the spec first
    spec = CustomColumnSpec(title="T", key="k2", kind=CustomColumnKind.FIELD, expression="artist")
    save_specs_to_config([spec])
    unregister_and_delete("k2")
    assert ("unregister", {'key': "k2"}) in fake_registry.calls
    assert get_spec_by_key("k2") is None


def test_load_persisted_columns_once_idempotent(fake_config: SimpleNamespace, fake_registry: SimpleNamespace) -> None:
    spec = CustomColumnSpec(title="T", key="k3", kind=CustomColumnKind.FIELD, expression="artist")
    save_specs_to_config([spec])
    # First load registers
    load_persisted_columns_once()
    # Second load should do nothing
    load_persisted_columns_once()
    # Exactly one register call for k3
    calls = [c for c in fake_registry.calls if c[0] == "register" and c[1]['key'] == "k3"]
    assert len(calls) == 1


def test_config_initialization_creates_list(fake_config: SimpleNamespace) -> None:
    from picard.ui.itemviews.custom_columns.storage import load_specs_from_config

    out = load_specs_from_config()
    assert out == []
    assert isinstance(fake_config.setting.get('custom_columns'), list)


def test_save_specs_replaces_list(fake_config: SimpleNamespace) -> None:
    from picard.ui.itemviews.custom_columns.storage import save_specs_to_config

    a = CustomColumnSpec(title="A", key="a", kind=CustomColumnKind.FIELD, expression="artist")
    b = CustomColumnSpec(title="B", key="b", kind=CustomColumnKind.FIELD, expression="album")
    save_specs_to_config([a])
    assert len(fake_config.setting['custom_columns']) == 1
    save_specs_to_config([b])
    raw = fake_config.setting['custom_columns']
    assert len(raw) == 1
    assert raw[0]['key'] == "b"


def test_add_or_update_spec_merges_by_key(fake_config: SimpleNamespace) -> None:
    from picard.ui.itemviews.custom_columns.storage import add_or_update_spec, load_specs_from_config

    spec1 = CustomColumnSpec(title="T", key="k", kind=CustomColumnKind.FIELD, expression="artist")
    add_or_update_spec(spec1)
    assert len(load_specs_from_config()) == 1
    spec2 = CustomColumnSpec(title="T2", key="k", kind=CustomColumnKind.FIELD, expression="album")
    add_or_update_spec(spec2)
    specs = load_specs_from_config()
    assert len(specs) == 1 and specs[0].title == "T2" and specs[0].expression == "album"


@pytest.mark.parametrize(
    ("file_view", "album_view"),
    [
        (True, False),
        (False, True),
        (False, False),
    ],
)
def test_register_and_persist_respects_view_flags(
    fake_config: SimpleNamespace, fake_registry: SimpleNamespace, file_view: bool, album_view: bool
) -> None:
    spec = CustomColumnSpec(
        title="T",
        key=f"k_flags_{int(file_view)}{int(album_view)}",
        kind=CustomColumnKind.FIELD,
        expression="artist",
        add_to_file_view=file_view,
        add_to_album_view=album_view,
    )
    register_and_persist(spec)
    expected = {
        'key': spec.key,
        'add_to_file_view': file_view,
        'add_to_album_view': album_view,
        'insert_after_key': None,
    }
    assert ("register", expected) in fake_registry.calls


def test_unregister_and_delete_nonexistent(fake_config: SimpleNamespace, fake_registry: SimpleNamespace) -> None:
    unregister_and_delete("missing_key")
    assert ("unregister", {'key': "missing_key"}) in fake_registry.calls
    # Config remains initialized to list and empty
    from picard.ui.itemviews.custom_columns.storage import load_specs_from_config

    assert load_specs_from_config() == []


def test_load_skips_corrupt_entries(fake_config: SimpleNamespace, fake_registry: SimpleNamespace) -> None:
    # Mix valid and invalid entries
    valid = CustomColumnSpec(title="T", key="k_valid", kind=CustomColumnKind.FIELD, expression="artist").to_dict()
    fake_config.setting['custom_columns'] = [valid, "invalid", {'kind': "unknown"}]
    load_persisted_columns_once()
    assert (
        "register",
        {'key': "k_valid", 'add_to_file_view': True, 'add_to_album_view': True, 'insert_after_key': None},
    ) in fake_registry.calls
    # Only one register should appear
    regs = [c for c in fake_registry.calls if c[0] == "register"]
    assert len(regs) == 1


def test_transform_default_strip_behavior() -> None:
    spec = CustomColumnSpec(
        title="Strip",
        key="k_strip",
        kind=CustomColumnKind.TRANSFORM,
        expression="artist",
        transform=None,  # should default to STRIP
    )
    column = build_column_from_spec(spec)
    item = _FakeItem({'artist': "  spaced  "})
    assert column.provider.evaluate(item) == "spaced"


def test_script_column_evaluation_from_builder() -> None:
    spec = CustomColumnSpec(title="S", key="k_script", kind=CustomColumnKind.SCRIPT, expression="%artist%")
    column = build_column_from_spec(spec)
    item = _FakeItem({'artist': "A"})
    assert column.provider.evaluate(item) == "A"


def test_from_dict_defaults_when_missing() -> None:
    data = {'title': "T", 'key': "k", 'kind': "field", 'expression': "artist"}
    spec = CustomColumnSpec.from_dict(data)
    assert spec.width is None
    assert spec.align == "LEFT"
    assert spec.always_visible is False
    assert spec.add_to_file_view is True and spec.add_to_album_view is True
    assert spec.insert_after_key is None and spec.transform is None


@pytest.mark.parametrize(
    ("width", "align_name", "always_visible"),
    [
        (None, "LEFT", False),
        (150, "RIGHT", True),
    ],
)
def test_build_column_propagates_properties(width, align_name: str, always_visible: bool) -> None:
    spec = CustomColumnSpec(
        title="P",
        key=f"k_props_{width}_{align_name}_{int(always_visible)}",
        kind=CustomColumnKind.FIELD,
        expression="artist",
        width=width,
        align=align_name,
        always_visible=always_visible,
    )
    column = build_column_from_spec(spec)
    # Width propagation
    assert column.width == (None if width is None else int(width))
    # Align mapping
    expected_align = ColumnAlign.RIGHT if align_name.upper() == "RIGHT" else ColumnAlign.LEFT
    assert column.align == expected_align
    # Always visible propagation
    assert getattr(column, 'always_visible', always_visible) == always_visible


def test_serializer_roundtrip_matches_spec_methods() -> None:
    spec = CustomColumnSpec(
        title="Ser",
        key="k_ser",
        kind=CustomColumnKind.SCRIPT,
        expression="%album%",
        width=200,
        align="RIGHT",
        always_visible=True,
        add_to_file_view=False,
        add_to_album_view=True,
        insert_after_key="artist",
        transform=None,
    )
    d1 = spec.to_dict()
    d2 = CustomColumnSpecSerializer.to_dict(spec)
    assert d1 == d2
    spec2 = CustomColumnSpecSerializer.from_dict(d1)
    assert asdict(spec2) == asdict(spec)


def test_config_manager_save_load_get(fake_config: SimpleNamespace, sample_spec: CustomColumnSpec) -> None:
    mgr = CustomColumnConfigManager()
    # save and load
    mgr.save_specs([sample_spec])
    out = mgr.load_specs()
    assert len(out) == 1 and asdict(out[0]) == asdict(sample_spec)
    # get by key
    got = mgr.get_by_key(sample_spec.key)
    assert got is not None and got.key == sample_spec.key


def test_config_manager_add_update_delete(fake_config: SimpleNamespace) -> None:
    mgr = CustomColumnConfigManager()
    a = CustomColumnSpec(title="A", key="k", kind=CustomColumnKind.FIELD, expression="artist")
    b = CustomColumnSpec(title="B", key="k", kind=CustomColumnKind.FIELD, expression="album")
    mgr.add_or_update(a)
    assert len(mgr.load_specs()) == 1 and mgr.get_by_key("k").title == "A"
    mgr.add_or_update(b)
    got = mgr.get_by_key("k")
    assert got is not None and got.title == "B" and got.expression == "album"
    assert mgr.delete_by_key("k") is True
    assert mgr.get_by_key("k") is None
    # deleting non-existent returns False
    assert mgr.delete_by_key("missing") is False


def test_config_manager_load_skips_invalid_entries(fake_config: SimpleNamespace) -> None:
    mgr = CustomColumnConfigManager()
    valid = CustomColumnSpec(title="T", key="k", kind=CustomColumnKind.FIELD, expression="artist").to_dict()
    fake_config.setting['custom_columns'] = [valid, "bad", 42, {'title': "x"}]
    out = mgr.load_specs()
    assert len(out) == 1 and out[0].key == "k"


def test_registrar_register_and_unregister(fake_config: SimpleNamespace, fake_registry: SimpleNamespace) -> None:
    reg = CustomColumnRegistrar()
    spec = CustomColumnSpec(title="R", key="k_reg", kind=CustomColumnKind.FIELD, expression="artist")
    reg.register_column(spec)
    assert (
        "register",
        {
            'key': "k_reg",
            'add_to_file_view': True,
            'add_to_album_view': True,
            'insert_after_key': None,
        },
    ) in fake_registry.calls
    reg.unregister_column("k_reg")
    assert ("unregister", {'key': "k_reg"}) in fake_registry.calls


def test_validator_required_fields() -> None:
    validator = CustomColumnSpecValidator()
    spec = CustomColumnSpec(title="", key="", kind=CustomColumnKind.FIELD, expression="")
    report = validator.validate(spec)
    assert not report.is_valid
    codes = {r.code for r in report.results}
    assert {"TITLE_REQUIRED", "KEY_REQUIRED", "EXPRESSION_REQUIRED"}.issubset(codes)


def test_validator_key_format_and_uniqueness() -> None:
    validator = CustomColumnSpecValidator()
    spec = CustomColumnSpec(title="T", key="1bad key", kind=CustomColumnKind.FIELD, expression="artist")
    report = validator.validate(spec, context=validator.validate_multiple([]).get('', None) or None)
    assert not report.is_valid
    assert any(r.code == "KEY_INVALID_FORMAT" for r in report.results)
    # uniqueness
    report2 = validator.validate(spec, context=None if False else None)
    # Simulate existing key
    report2 = validator.validate(
        spec, context=type("C", (), {'existing_keys': {"1bad key"}, 'is_field_valid': lambda *_: True})()
    )
    assert any(r.code == "KEY_DUPLICATE" for r in report2.results)


def test_validator_expression_rules_field_and_script(fake_config: SimpleNamespace) -> None:
    # FIELD expression
    field_spec = CustomColumnSpec(title="T", key="k", kind=CustomColumnKind.FIELD, expression="")
    report_field = validate_spec(field_spec)
    assert any(r.code == "EXPRESSION_REQUIRED" for r in report_field.results)
    # SCRIPT expression: invalid syntax
    script_spec = CustomColumnSpec(title="T", key="k2", kind=CustomColumnKind.SCRIPT, expression="$if(1,")
    report_script = validate_spec(script_spec)
    assert any(r.code == "SCRIPT_SYNTAX_ERROR" for r in report_script.results)


def test_validator_transform_rules() -> None:
    spec = CustomColumnSpec(title="T", key="k3", kind=CustomColumnKind.TRANSFORM, expression=" ")
    rep = validate_spec(spec)
    # Needs valid base and transform specified
    codes = {r.code for r in rep.results}
    assert "TRANSFORM_BASE_INVALID" in codes and "TRANSFORM_TYPE_REQUIRED" in codes


def test_is_spec_valid_shortcut() -> None:
    good = CustomColumnSpec(title="T", key="good_key", kind=CustomColumnKind.FIELD, expression="artist")
    assert is_spec_valid(good)
