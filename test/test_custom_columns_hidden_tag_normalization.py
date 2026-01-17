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

from dataclasses import dataclass
from types import SimpleNamespace

from picard.item import Item
from picard.metadata import Metadata

import pytest  # type: ignore[import-not-found]

from picard.ui.itemviews.custom_columns import (
    make_field_column,
    make_script_column,
)


@pytest.fixture(autouse=True)
def _fake_script_config(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Provide minimal config so script parser can load functions without KeyError."""

    class _FakeSetting(dict):
        def raw_value(self, name, qtype=None):
            return self.get(name)

        def key(self, name):
            return name

    cfg = SimpleNamespace(setting=_FakeSetting({'enabled_plugins': []}), sync=lambda: None)
    import picard.config as picard_config_mod
    import picard.extension_points as ext_points_mod

    monkeypatch.setattr(picard_config_mod, 'get_config', lambda: cfg, raising=True)
    monkeypatch.setattr(ext_points_mod, 'get_config', lambda: cfg, raising=True)
    return cfg


@dataclass(eq=False)
class _Item(Item):
    values: dict[str, str]

    def column(self, key: str) -> str:
        return self.values.get(key, "")

    @property
    def metadata(self) -> Metadata:
        md = Metadata()
        for k, v in self.values.items():
            md[k] = v
        return md


@pytest.mark.parametrize(
    ("tag", "value"),
    [
        ("bitrate", "192 kbps"),
        ("filesize", "1.5 MB"),
        ("length", "3:45"),
        ("format", "MP3"),
        ("albumartists_countries", "US; GB"),
        ("artists_sort", "Lastname, Firstname"),
        ("bits_per_sample", "24"),
    ],
)
@pytest.mark.parametrize("expr", ["%_bitrate%"], ids=["underscore"])  # expr pattern will be rebuilt per tag
def test_script_column_normalizes_hidden_tag(tag: str, value: str, expr: str) -> None:
    # Build expression for current tag
    expr_for_tag: str = expr.replace("bitrate", tag)
    item: _Item = _Item(values={f"~{tag}": value})
    col = make_script_column("HiddenTag", "hidden_script", expr_for_tag)
    assert col.provider.evaluate(item) == value


@pytest.mark.parametrize(
    ("tag", "value"),
    [
        ("bitrate", "192 kbps"),
        ("filesize", "1.5 MB"),
        ("length", "3:45"),
        ("format", "MP3"),
        ("albumartists_countries", "US; GB"),
        ("artists_sort", "Lastname, Firstname"),
        ("bits_per_sample", "24"),
    ],
)
@pytest.mark.parametrize(
    "field_key", ["%_bitrate%", "_bitrate", "~bitrate"], ids=["percent_underscore", "underscore", "tilde"]
)  # key pattern rebuilt per tag
def test_field_column_normalizes_hidden_tag(tag: str, value: str, field_key: str) -> None:
    key_for_tag: str = field_key.replace("bitrate", tag)
    item: _Item = _Item(values={f"~{tag}": value})
    col = make_field_column("HiddenTag", key_for_tag)
    assert col.provider.evaluate(item) == value


@pytest.mark.parametrize(("tag", "value"), [("artist", "Artist X"), ("title", "Title Y"), ("album", "Album Z")])
@pytest.mark.parametrize(
    "expr", ["%artist%", "%title%", "%album%"], ids=["artist", "title", "album"]
)  # rebuilt per tag
def test_script_column_regular_tags_still_work(tag: str, value: str, expr: str) -> None:
    expr_for_tag: str = expr.replace("artist", tag).replace("title", tag).replace("album", tag)
    item: _Item = _Item(values={tag: value})
    col = make_script_column("RegularTag", "regular_script", expr_for_tag)
    assert col.provider.evaluate(item) == value


@pytest.mark.parametrize(("tag", "value"), [("artist", "Artist X"), ("title", "Title Y"), ("album", "Album Z")])
@pytest.mark.parametrize("field_key", ["artist", "%artist%"], ids=["plain", "percent"])  # rebuilt per tag
def test_field_column_regular_tags_still_work(tag: str, value: str, field_key: str) -> None:
    key_for_tag: str = field_key.replace("artist", tag)
    item: _Item = _Item(values={tag: value})
    col = make_field_column("RegularTag", key_for_tag)
    assert col.provider.evaluate(item) == value
