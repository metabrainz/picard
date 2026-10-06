# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Laurent Monin
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


from typing import override
from unittest.mock import patch

import pytest

from picard.ui.itemviews.custom_columns.multi_state_providers import MultiColumnStateBase, MultiStateAlbumColumnProvider


def _(input):
    return input


class _FakeStatusState(MultiColumnStateBase):
    SILVER = 0
    SILVER_STAR = 5
    GOLD = 10
    GOLD_STAR = 15

    @override
    def display(self) -> str:
        """Returns empty
        Due to this column having status_icon=True
        it automatically gets populated with the correct status
        icons in the AlbumItem.update method
        """
        if self._current_value == _FakeStatusState.SILVER:
            return _("Unmodified and Incomplete")
        elif self._current_value == _FakeStatusState.SILVER_STAR:
            return _("Modified and Incomplete")
        elif self._current_value == _FakeStatusState.GOLD:
            return _("Unmodified and Complete")
        else:
            return _("Modified and Complete")


class _FakeAlbum:
    """Album-like object exposing the boolean predicates used by the columns."""

    def __init__(self, modified: bool = False, complete: bool = False) -> None:
        self._modified = modified
        self._complete = complete

    def is_modified(self) -> bool:
        return self._modified

    def is_complete(self) -> bool:
        return self._complete


def _applies_fake(obj: object) -> bool:
    return isinstance(obj, _FakeAlbum)


@pytest.fixture
def modified_provider() -> MultiStateAlbumColumnProvider:
    def predicate(obj) -> _FakeStatusState:
        is_modified = obj.is_modified()
        is_complete = obj.is_complete()
        if not is_modified and not is_complete:
            return _FakeStatusState(_FakeStatusState.SILVER)
        elif is_modified and not is_complete:
            return _FakeStatusState(_FakeStatusState.SILVER_STAR)
        elif not is_modified and is_complete:
            return _FakeStatusState(_FakeStatusState.GOLD)
        else:
            return _FakeStatusState(_FakeStatusState.GOLD_STAR)

    return MultiStateAlbumColumnProvider(
        predicate=predicate,
        applies=_applies_fake,
    )


def test_display_is_yes_no_for_album(modified_provider: MultiStateAlbumColumnProvider) -> None:
    assert modified_provider.evaluate(_FakeAlbum(modified=False, complete=False)) == "Unmodified and Incomplete"
    assert modified_provider.evaluate(_FakeAlbum(modified=True, complete=False)) == "Modified and Incomplete"
    assert modified_provider.evaluate(_FakeAlbum(modified=False, complete=True)) == "Unmodified and Complete"
    assert modified_provider.evaluate(_FakeAlbum(modified=True, complete=True)) == "Modified and Complete"


def test_display_empty_for_non_album(modified_provider: MultiStateAlbumColumnProvider) -> None:
    assert modified_provider.evaluate(object()) == ""


def test_sort_key_is_stable_integer(modified_provider: MultiStateAlbumColumnProvider) -> None:
    assert modified_provider.sort_key(_FakeAlbum(modified=False, complete=False)) == int(_FakeStatusState.SILVER)
    assert modified_provider.sort_key(_FakeAlbum(modified=True, complete=False)) == int(_FakeStatusState.SILVER_STAR)
    assert modified_provider.sort_key(_FakeAlbum(modified=False, complete=True)) == int(_FakeStatusState.GOLD)
    assert modified_provider.sort_key(_FakeAlbum(modified=True, complete=True)) == int(_FakeStatusState.GOLD_STAR)
    assert modified_provider.sort_key(object()) == int(_FakeStatusState.NOT_APPLICABLE)


def test_sort_order_na_before_other_states() -> None:
    # The whole point: non-applicable < No < Yes, as integers.
    assert (
        int(_FakeStatusState.NOT_APPLICABLE)
        < int(_FakeStatusState.SILVER)
        < int(_FakeStatusState.SILVER_STAR)
        < int(_FakeStatusState.GOLD)
        < int(_FakeStatusState.GOLD_STAR)
    )


def test_sort_key_independent_of_display_language(
    monkeypatch: pytest.MonkeyPatch, modified_provider: MultiStateAlbumColumnProvider
) -> None:
    """The sort key must not change when the display language changes.

    This is the core regression guard for the original bug where the NAT
    column sorted on the (translatable) displayed text, making sort order
    locale-dependent (e.g. "Ja"/"Nein" reversing relative to "Yes"/"No").
    """
    unmodified_album = _FakeAlbum(modified=False, complete=False)
    modified_album = _FakeAlbum(modified=True, complete=False)
    complete_album = _FakeAlbum(modified=False, complete=True)
    modified_and_complete_album = _FakeAlbum(modified=True, complete=True)

    # Baseline (identity translation): keys and display in English.
    base_unmodified_album_key = modified_provider.sort_key(unmodified_album)
    base_modified_album_key = modified_provider.sort_key(modified_album)
    base_complete_album_key = modified_provider.sort_key(complete_album)
    base_modified_and_complete_album_key = modified_provider.sort_key(modified_and_complete_album)
    assert modified_provider.evaluate(unmodified_album) == "Unmodified and Incomplete"
    assert modified_provider.evaluate(modified_album) == "Modified and Incomplete"
    assert modified_provider.evaluate(complete_album) == "Unmodified and Complete"
    assert modified_provider.evaluate(modified_and_complete_album) == "Modified and Complete"
    assert (
        base_modified_and_complete_album_key
        > base_complete_album_key
        > base_modified_album_key
        > base_unmodified_album_key
    )  # modified sorts after unmodified

    # Simulate a locale where the display strings do not sort in the same order alphabetically, i.e. the
    # reverse of the desired multi-state order. If sorting depended on the text,
    # the relative order would flip. It must not.
    locale = {
        "Unmodified and Incomplete": "A",
        "Modified and Incomplete": "C",
        "Unmodified and Complete": "E",
        "Modified and Complete": "D",
    }

    with patch(
        'test.ui.test_multi_state_column_providers._', side_effect=lambda s: locale.get(s, s)
    ) as _patch_translate:
        assert modified_provider.evaluate(unmodified_album) == "A"
        assert modified_provider.evaluate(modified_album) == "C"
        assert modified_provider.evaluate(complete_album) == "E"
        assert modified_provider.evaluate(modified_and_complete_album) == "D"

        assert modified_provider.sort_key(unmodified_album) == base_unmodified_album_key
        assert modified_provider.sort_key(modified_album) == base_modified_album_key
        assert modified_provider.sort_key(complete_album) == base_complete_album_key
        assert modified_provider.sort_key(modified_and_complete_album) == base_modified_and_complete_album_key
        assert (
            modified_provider.sort_key(modified_and_complete_album)
            > modified_provider.sort_key(complete_album)
            > modified_provider.sort_key(modified_album)
            > modified_provider.sort_key(unmodified_album)
        )


def test_predicate_only_called_when_applicable() -> None:
    calls: list[object] = []

    def predicate(obj: object) -> _FakeStatusState:
        calls.append(obj)
        return _FakeStatusState(_FakeStatusState.SILVER)

    provider = MultiStateAlbumColumnProvider(predicate=predicate, applies=_applies_fake)
    # Non-applicable object: predicate must not be invoked.
    assert provider.evaluate(object()) == ""
    provider.sort_key(object())
    assert calls == []
    # Applicable object: predicate is used.
    album = _FakeAlbum()
    assert provider.evaluate(album) == _FakeStatusState(_FakeStatusState.SILVER).display()
    assert calls == [album]


def test_state_is_single_source_of_truth(modified_provider: MultiStateAlbumColumnProvider) -> None:
    # The public state() drives both display and sort, so a future icon /
    # checkbox renderer can rely on it without re-deriving from text.
    unmodified_album = _FakeAlbum(modified=False, complete=False)
    modified_album = _FakeAlbum(modified=True, complete=False)
    complete_album = _FakeAlbum(modified=False, complete=True)
    modified_and_complete_album = _FakeAlbum(modified=True, complete=True)
    assert modified_provider.state(unmodified_album).value() == _FakeStatusState.SILVER
    assert modified_provider.state(modified_album).value() == _FakeStatusState.SILVER_STAR
    assert modified_provider.state(complete_album).value() == _FakeStatusState.GOLD
    assert modified_provider.state(modified_and_complete_album).value() == _FakeStatusState.GOLD_STAR
    assert modified_provider.state(object()).value() == _FakeStatusState.NOT_APPLICABLE
    # evaluate() / sort_key() stay consistent with state().
    assert modified_provider.evaluate(unmodified_album) == _FakeStatusState(_FakeStatusState.SILVER).display()
    assert modified_provider.sort_key(modified_album) == int(_FakeStatusState.SILVER_STAR)
