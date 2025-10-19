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

"""Test the mbjson for artist/album/track name translations."""

from collections.abc import Callable
import types
from typing import Any

# Import the functions under test from the refactored module
import picard.mbjson as mbjson
from picard.metadata import Metadata
from picard.track import Track

import pytest


@pytest.fixture
def config() -> Any:
    """Provide a minimal mutable config-like object used by mbjson.

    Only settings accessed by the tested code are provided.
    """
    cfg = types.SimpleNamespace(
        setting={
            'translate_artist_names': True,
            'translate_album_titles': True,
            'translate_track_titles': True,
            'artist_locales': ['en'],
            'translate_artist_names_script_exception': False,
            'script_exceptions': [],
            'standardize_artists': False,
            'standardize_instruments': False,
            'standardize_vocals': False,
            'release_ars': True,
            'preferred_release_countries': [],
        }
    )
    return cfg


@pytest.fixture
def mock_get_config(monkeypatch: pytest.MonkeyPatch, config: Any) -> Callable[[], Any]:
    """Patch mbjson.get_config() to return our test config object."""
    monkeypatch.setattr(mbjson, 'get_config', lambda: config)
    return lambda: config


@pytest.mark.parametrize(
    ('aliases', 'expected_full', 'expected_root'),
    [
        (
            [
                {'locale': 'en_US', 'name': 'Color'},
                {'locale': 'en', 'name': 'Colour'},
                {'locale': 'fr', 'name': 'Couleur'},
            ],
            {'en_US': 'Color', 'en': 'Colour', 'fr': 'Couleur'},
            {'en': 'Colour', 'fr': 'Couleur'},
        ),
        (
            [
                {'locale': 'pt_BR', 'name': 'Título'},
                {'locale': 'pt', 'name': 'Título'},
            ],
            {'pt_BR': 'Título', 'pt': 'Título'},
            {'pt': 'Título'},
        ),
    ],
)
def test_build_alias_locale_maps(
    aliases: list[dict[str, str]], expected_full: dict[str, str], expected_root: dict[str, str]
) -> None:
    full, root = mbjson._build_alias_locale_maps(aliases)
    assert full == expected_full
    assert root == expected_root


@pytest.mark.parametrize(
    ('order', 'mapping', 'expected'),
    [
        (['b', 'a'], {'a': 'A', 'b': 'B'}, 'B'),
        (['x', 'y', 'a'], {'a': 'A'}, 'A'),
        (['x', 'y'], {'a': 'A'}, None),
    ],
)
def test_first_match_in_order(order: list[str], mapping: dict[str, str], expected: str | None) -> None:
    assert mbjson._first_match_in_order(order, mapping) == expected


@pytest.mark.parametrize(
    ('preferred', 'expected'),
    [
        (['en_US', 'en'], 'Color'),  # exact full-locale match
        (['de_DE', 'en'], 'Colour'),  # root language fallback
        (['de', 'es'], None),  # no match
    ],
)
def test_find_localized_alias_name(preferred: list[str], expected: str | None) -> None:
    aliases: list[dict[str, Any]] = [
        {'locale': 'en_US', 'name': 'Color'},
        {'locale': 'en', 'name': 'Colour'},
        {'locale': 'fr', 'name': 'Couleur'},
    ]
    assert mbjson._find_localized_alias_name(aliases, preferred) == expected


@pytest.mark.parametrize(
    ('enabled', 'detected', 'exceptions', 'expected'),
    [
        # disabled feature -> never skip
        (False, {'LATIN': 0.9}, [('LATIN', 10)], False),
        # enabled, above threshold -> skip
        (True, {'LATIN': 0.9}, [('LATIN', 10)], True),
        # enabled, below threshold -> do not skip
        (True, {'LATIN': 0.05}, [('LATIN', 10)], False),
        # enabled, different script detected -> do not skip
        (True, {'CYRILLIC': 0.9}, [('LATIN', 10)], False),
        # enabled, no exceptions configured -> do not skip
        (True, {'LATIN': 0.9}, [], False),
        # enabled, no detection -> do not skip
        (True, {}, [('LATIN', 10)], False),
    ],
)
def test_should_skip_translation_due_to_scripts(
    monkeypatch: pytest.MonkeyPatch,
    config: Any,
    enabled: bool,
    detected: dict[str, float],
    exceptions: list[tuple[str, int]],
    expected: bool,
) -> None:
    config.setting['translate_artist_names_script_exception'] = enabled
    config.setting['script_exceptions'] = exceptions
    # Patch detector to return our desired distribution
    monkeypatch.setattr(mbjson, 'detect_script_weighted', lambda _text: detected)
    result = mbjson._should_skip_translation_due_to_scripts('dummy', config=config)
    assert result is expected


@pytest.mark.parametrize('skip', [True, False])
def test_release_to_metadata_respects_script_exceptions(
    monkeypatch: pytest.MonkeyPatch,
    config: Any,
    mock_get_config: Callable[[], Any],
    skip: bool,
) -> None:
    # Arrange config and behavior
    config.setting['translate_album_titles'] = True
    config.setting['artist_locales'] = ['en']
    monkeypatch.setattr(mbjson, '_should_skip_translation_due_to_scripts', lambda _text, config=None: skip)

    # Album node with localized alias
    node = {
        'id': 'release-1',
        'title': 'العنوان',  # some non-latin characters
        'aliases': [
            {'locale': 'en', 'name': 'Album Title EN'},
        ],
    }
    m = Metadata()
    mbjson.release_to_metadata(node, m, album=None)

    if skip:
        # When skipping, alias should not override
        assert m.get('album') != 'Album Title EN'
    else:
        assert m['album'] == 'Album Title EN'


@pytest.mark.parametrize('skip', [True, False])
def test_recording_to_metadata_respects_script_exceptions(
    monkeypatch: pytest.MonkeyPatch,
    config: Any,
    mock_get_config: Callable[[], Any],
    skip: bool,
) -> None:
    # Arrange config and behavior
    config.setting['translate_track_titles'] = True
    config.setting['artist_locales'] = ['en']
    monkeypatch.setattr(mbjson, '_should_skip_translation_due_to_scripts', lambda _text, config=None: skip)

    node = {
        'id': 'rec-1',
        'title': 'タイトル',
        'aliases': [
            {'locale': 'en', 'name': 'Track Title EN'},
        ],
        'artist-credit': [],
    }
    m = Metadata()
    t = Track('1')
    mbjson.recording_to_metadata(node, m, track=t)

    if skip:
        # Alias should not be applied
        assert m.get('title') != 'Track Title EN'
    else:
        assert m['title'] == 'Track Title EN'


@pytest.mark.parametrize('toggle', [False, True])
def test_release_to_metadata_translation_toggle(
    monkeypatch: pytest.MonkeyPatch,
    config: Any,
    mock_get_config: Callable[[], Any],
    toggle: bool,
) -> None:
    config.setting['translate_album_titles'] = toggle
    config.setting['artist_locales'] = ['en']
    # Ensure exceptions do not interfere
    config.setting['translate_artist_names_script_exception'] = False
    monkeypatch.setattr(mbjson, '_should_skip_translation_due_to_scripts', lambda _text, config=None: False)

    node = {
        'id': 'release-1',
        'title': 'العنوان',
        'aliases': [
            {'locale': 'en', 'name': 'Album Title EN'},
        ],
    }
    m = Metadata()
    mbjson.release_to_metadata(node, m, album=None)

    if toggle:
        assert m['album'] == 'Album Title EN'
    else:
        assert m.get('album') != 'Album Title EN'


@pytest.mark.parametrize('toggle', [False, True])
def test_recording_to_metadata_translation_toggle(
    monkeypatch: pytest.MonkeyPatch,
    config: Any,
    mock_get_config: Callable[[], Any],
    toggle: bool,
) -> None:
    config.setting['translate_track_titles'] = toggle
    config.setting['artist_locales'] = ['en']
    config.setting['translate_artist_names_script_exception'] = False
    monkeypatch.setattr(mbjson, '_should_skip_translation_due_to_scripts', lambda _text, config=None: False)

    node = {
        'id': 'rec-1',
        'title': 'タイトル',
        'aliases': [
            {'locale': 'en', 'name': 'Track Title EN'},
        ],
        'artist-credit': [],
    }
    m = Metadata()
    t = Track('1')
    mbjson.recording_to_metadata(node, m, track=t)

    if toggle:
        assert m['title'] == 'Track Title EN'
    else:
        assert m.get('title') != 'Track Title EN'
