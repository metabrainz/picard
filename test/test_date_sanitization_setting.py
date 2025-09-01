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

from types import SimpleNamespace
from typing import Any, cast

from picard import config
from picard.formats import id3
from picard.formats.apev2 import APEv2File
from picard.formats.util import date_sanitization_format_entries
from picard.formats.vorbis import OggVorbisFile
from picard.metadata import Metadata
from picard.util import (
    sanitize_date,
)

import pytest


@pytest.fixture
def patched_get_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """Initialize minimal config and patch get_config(); no teardown needed."""
    fake = SimpleNamespace(setting={}, persist={}, profiles={})
    config.config = fake
    config.setting = fake.setting
    config.persist = fake.persist
    config.profiles = fake.profiles
    monkeypatch.setattr('picard.config.get_config', lambda: fake, raising=True)
    # Ensure default expected keys exist for extension point iteration
    fake.setting['enabled_plugins'] = []
    return None


@pytest.mark.parametrize(
    ('file_cls', 'format_key'),
    [
        (id3.ID3File, 'id3'),
        (OggVorbisFile, 'vorbis'),
        (APEv2File, 'apev2'),
    ],
)
@pytest.mark.parametrize(
    'disabled',
    [
        [],
        ['vorbis'],
        ['apev2'],
        ['id3'],
        ['vorbis', 'apev2'],
    ],
)
def test_instance_method_decision_matches_disabled_setting(
    patched_get_config: None, file_cls: Any, format_key: str, disabled: list[str]
) -> None:
    settings = cast(dict[str, Any], config.setting)
    settings['disable_date_sanitization_formats'] = disabled
    file_obj = file_cls.__new__(file_cls)
    assert file_obj.is_date_sanitization_enabled() is (format_key not in set(disabled))


@pytest.mark.parametrize(
    ('disabled', 'input_date', 'expected'),
    [
        ([], '2021-04', ['2021']),
        ([], '2021-04-01', ['2021-04-01']),
        (['id3'], '2021-04', ['2021-04']),
        (['id3'], '2021-04-01', ['2021-04-01']),
    ],
)
def test_id3_v23_date_coercion_respects_setting(
    patched_get_config: None, disabled: list[str], input_date: str, expected: list[str]
) -> None:
    # Arrange: configure setting and build an ID3File with v2.3 behavior
    settings = cast(dict[str, Any], config.setting)
    settings['disable_date_sanitization_formats'] = disabled
    # Avoid File.__init__ side effects by constructing without __init__
    test_file = id3.ID3File.__new__(id3.ID3File)
    metadata = Metadata()
    metadata['artist'] = ['a', 'b']
    metadata['originaldate'] = '2020-01-31'
    metadata['date'] = input_date
    settings['write_id3v23'] = True
    settings['id3v23_join_with'] = ' / '

    # Act + Assert: artist and originaldate keep legacy semantics, date depends on setting
    assert test_file.format_specific_metadata(metadata, 'artist') == ['a / b']
    assert test_file.format_specific_metadata(metadata, 'originaldate') == ['2020']
    assert test_file.format_specific_metadata(metadata, 'date') == expected


@pytest.mark.parametrize(
    ('date_in', 'expected_when_enabled'),
    [
        ('2005-12-00', '2005-12'),
        ('2005-00-00', '2005'),
        ('0000-00-00', ''),
        ('2005-00-12', '2005-00-12'),
        ('0000-00-12', '0000-00-12'),
    ],
)
def test_vorbis_dates_from_complaint_when_enabled(
    patched_get_config: None, date_in: str, expected_when_enabled: str
) -> None:
    settings = cast(dict[str, Any], config.setting)
    settings['disable_date_sanitization_formats'] = []
    # Simulate vorbis path: sanitize applied when enabled
    vorbis = OggVorbisFile.__new__(OggVorbisFile)
    assert vorbis.is_date_sanitization_enabled() is True
    assert sanitize_date(date_in) == expected_when_enabled


@pytest.mark.parametrize(
    'date_in',
    [
        '2005-12-00',
        '2005-00-00',
        '0000-00-00',
        '2005-00-12',
        '0000-00-12',
    ],
)
def test_vorbis_dates_from_complaint_when_disabled(patched_get_config: None, date_in: str) -> None:
    settings = cast(dict[str, Any], config.setting)
    settings['disable_date_sanitization_formats'] = ['vorbis']
    # Simulate vorbis path: sanitize skipped when disabled
    vorbis = OggVorbisFile.__new__(OggVorbisFile)
    assert vorbis.is_date_sanitization_enabled() is False
    # Gate sanitization like vorbis writer does
    output: str = date_in if not vorbis.is_date_sanitization_enabled() else sanitize_date(date_in)
    assert output == date_in


@pytest.mark.parametrize(
    ('file_cls', 'format_key'),
    [
        (id3.ID3File, 'id3'),
        (OggVorbisFile, 'vorbis'),
        (APEv2File, 'apev2'),
    ],
)
@pytest.mark.parametrize('disabled', [[], ['id3'], ['vorbis'], ['apev2'], ['vorbis', 'apev2']])
def test_instance_method_respects_config(
    patched_get_config: None, file_cls: Any, format_key: str, disabled: list[str]
) -> None:
    # Arrange
    settings = cast(dict[str, Any], config.setting)
    settings['disable_date_sanitization_formats'] = disabled
    file_obj = file_cls.__new__(file_cls)

    # Act
    enabled = file_obj.is_date_sanitization_enabled()

    # Assert
    expected_enabled = format_key not in set(disabled)
    assert enabled is expected_enabled


def test_entries_include_known_toggleable_families(patched_get_config: None) -> None:
    # Ensure deterministic plugin environment for extension point iteration
    settings = cast(dict[str, Any], config.setting)
    settings['enabled_plugins'] = []
    entries = dict(date_sanitization_format_entries())
    # These are provided by our built-in formats; presence is enough here
    assert 'id3' in entries and isinstance(entries['id3'], str)
    assert 'vorbis' in entries and isinstance(entries['vorbis'], str)
    assert 'apev2' in entries and isinstance(entries['apev2'], str)


def test_entries_are_unique_by_key(patched_get_config: None) -> None:
    # Ensure deterministic plugin environment for extension point iteration
    settings = cast(dict[str, Any], config.setting)
    settings['enabled_plugins'] = []
    entries = date_sanitization_format_entries()
    keys = [k for (k, _title) in entries]
    assert len(keys) == len(set(keys))
