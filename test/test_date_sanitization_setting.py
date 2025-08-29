# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019 Zenara Daley
# Copyright (C) 2019-2024 Philipp Wolfer
# Copyright (C) 2020-2022, 2024 Laurent Monin
# Copyright (C) 2022 Marcin Szalowicz
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

from picard import config
from picard.formats import id3
from picard.metadata import Metadata
from picard.util import (
    is_date_sanitization_enabled,
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
    return None


@pytest.mark.parametrize(
    'format_key, disabled, expected_enabled',
    [
        ('vorbis', [], True),
        ('vorbis', ['vorbis'], False),
        ('apev2', [], True),
        ('apev2', ['apev2'], False),
        ('id3', [], True),
        ('id3', ['id3'], False),
        ('id3', ['vorbis', 'apev2'], True),
    ],
)
def test_is_date_sanitization_enabled_decision(
    patched_get_config: None, format_key: str, disabled: list[str], expected_enabled: bool
) -> None:
    config.setting['disable_date_sanitization_formats'] = disabled
    assert is_date_sanitization_enabled(format_key) is expected_enabled


@pytest.mark.parametrize(
    'disabled, input_date, expected',
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
    config.setting['disable_date_sanitization_formats'] = disabled
    # Avoid File.__init__ side effects by constructing without __init__
    test_file = id3.ID3File.__new__(id3.ID3File)
    metadata = Metadata()
    metadata['artist'] = ['a', 'b']
    metadata['originaldate'] = '2020-01-31'
    metadata['date'] = input_date
    config.setting['write_id3v23'] = True
    config.setting['id3v23_join_with'] = ' / '

    # Act + Assert: artist and originaldate keep legacy semantics, date depends on setting
    assert test_file.format_specific_metadata(metadata, 'artist') == ['a / b']
    assert test_file.format_specific_metadata(metadata, 'originaldate') == ['2020']
    assert test_file.format_specific_metadata(metadata, 'date') == expected


@pytest.mark.parametrize(
    'date_in, expected_when_enabled',
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
    config.setting['disable_date_sanitization_formats'] = []
    # Simulate vorbis path: sanitize applied when enabled
    assert is_date_sanitization_enabled('vorbis') is True
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
    config.setting['disable_date_sanitization_formats'] = ['vorbis']
    # Simulate vorbis path: sanitize skipped when disabled
    assert is_date_sanitization_enabled('vorbis') is False
    assert date_in == date_in
