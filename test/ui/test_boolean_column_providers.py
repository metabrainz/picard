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


import pytest

from picard.ui.itemviews.custom_columns import boolean_providers
from picard.ui.itemviews.custom_columns.boolean_providers import (
    BoolColumnState,
    BooleanAlbumColumnProvider,
)


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
def modified_provider() -> BooleanAlbumColumnProvider:
    return BooleanAlbumColumnProvider(
        predicate=lambda o: BoolColumnState(BoolColumnState.YES if o.is_modified() else BoolColumnState.NO),
        applies=_applies_fake,
    )


def test_display_is_yes_no_for_album(modified_provider: BooleanAlbumColumnProvider) -> None:
    assert modified_provider.evaluate(_FakeAlbum(modified=True)) == "Yes"
    assert modified_provider.evaluate(_FakeAlbum(modified=False)) == "No"


def test_display_empty_for_non_album(modified_provider: BooleanAlbumColumnProvider) -> None:
    assert modified_provider.evaluate(object()) == ""


def test_sort_key_is_stable_integer(modified_provider: BooleanAlbumColumnProvider) -> None:
    assert modified_provider.sort_key(_FakeAlbum(modified=True)) == int(BoolColumnState.YES)
    assert modified_provider.sort_key(_FakeAlbum(modified=False)) == int(BoolColumnState.NO)
    assert modified_provider.sort_key(object()) == int(BoolColumnState.NOT_APPLICABLE)


def test_sort_order_na_before_no_before_yes() -> None:
    # The whole point: non-applicable < No < Yes, as integers.
    assert int(BoolColumnState.NOT_APPLICABLE) < int(BoolColumnState.NO) < int(BoolColumnState.YES)


def test_sort_key_independent_of_display_language(
    monkeypatch: pytest.MonkeyPatch, modified_provider: BooleanAlbumColumnProvider
) -> None:
    """The sort key must not change when the display language changes.

    This is the core regression guard for the original bug where the NAT
    column sorted on the (translatable) displayed text, making sort order
    locale-dependent (e.g. "Ja"/"Nein" reversing relative to "Yes"/"No").
    """
    yes_album = _FakeAlbum(modified=True)
    no_album = _FakeAlbum(modified=False)

    # Baseline (identity translation): keys and display in English.
    monkeypatch.setattr(boolean_providers, "_", lambda s: s)
    base_yes_key = modified_provider.sort_key(yes_album)
    base_no_key = modified_provider.sort_key(no_album)
    assert modified_provider.evaluate(yes_album) == "Yes"
    assert base_yes_key > base_no_key  # modified sorts after unmodified

    # Simulate a German locale where "Ja" < "Nein" alphabetically, i.e. the
    # reverse of the desired boolean order. If sorting depended on the text,
    # the relative order would flip. It must not.
    german = {"Yes": "Ja", "No": "Nein"}
    monkeypatch.setattr(boolean_providers, "_", lambda s: german.get(s, s))
    assert modified_provider.evaluate(yes_album) == "Ja"
    assert modified_provider.evaluate(no_album) == "Nein"
    assert modified_provider.sort_key(yes_album) == base_yes_key
    assert modified_provider.sort_key(no_album) == base_no_key
    assert modified_provider.sort_key(yes_album) > modified_provider.sort_key(no_album)


def test_predicate_only_called_when_applicable() -> None:
    calls: list[object] = []

    def predicate(obj: object) -> BoolColumnState:
        calls.append(obj)
        return BoolColumnState(BoolColumnState.YES)

    provider = BooleanAlbumColumnProvider(predicate=predicate, applies=_applies_fake)
    # Non-applicable object: predicate must not be invoked.
    assert provider.evaluate(object()) == ""
    provider.sort_key(object())
    assert calls == []
    # Applicable object: predicate is used.
    album = _FakeAlbum()
    assert provider.evaluate(album) == BoolColumnState(BoolColumnState.YES).display()
    assert calls == [album]


def test_state_is_single_source_of_truth(modified_provider: BooleanAlbumColumnProvider) -> None:
    # The public state() drives both display and sort, so a future icon /
    # checkbox renderer can rely on it without re-deriving from text.
    yes_album = _FakeAlbum(modified=True)
    no_album = _FakeAlbum(modified=False)
    assert modified_provider.state(yes_album).value() == BoolColumnState.YES
    assert modified_provider.state(no_album).value() == BoolColumnState.NO
    assert modified_provider.state(object()).value() == BoolColumnState.NOT_APPLICABLE
    # evaluate() / sort_key() stay consistent with state().
    assert modified_provider.evaluate(yes_album) == BoolColumnState(BoolColumnState.YES).display()
    assert modified_provider.sort_key(no_album) == int(BoolColumnState.NO)
