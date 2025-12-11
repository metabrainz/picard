# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2008, 2012 Lukáš Lalinský
# Copyright (C) 2008 Will
# Copyright (C) 2010, 2014, 2018-2020, 2023-2024 Philipp Wolfer
# Copyright (C) 2013 Michael Wiencek
# Copyright (C) 2013, 2017-2019, 2021, 2023-2024 Laurent Monin
# Copyright (C) 2016-2018 Sambhav Kothari
# Copyright (C) 2017 Sophist-UK
# Copyright (C) 2017 Ville Skyttä
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


from picard.formats.registry import FormatRegistry


def _format_key_desc_generator(registry: FormatRegistry):
    """Yield (file_format, key, desc) for formats with key and description.

    Ensures each FORMAT_KEY is yielded at most once.
    """
    seen = set()
    for file_format in registry:
        key = getattr(file_format, 'FORMAT_KEY', None)
        if key is None or key in seen:
            continue
        desc = getattr(file_format, 'FORMAT_DESCRIPTION', None)
        if desc is None:
            continue
        seen.add(key)
        yield file_format, key, desc


def date_sanitization_format_entries(registry: FormatRegistry) -> tuple[tuple[str, str], ...]:
    """Return registered format entries that support date-sanitization toggle.

    Returns
    -------
    tuple[tuple[str, str], ...]
        Sequence of ``(format_key, translated_description)`` pairs for
        all registered format families that allow toggling date sanitization.

    Notes
    -----
    This inspects registered format classes and includes only those where
    ``DATE_SANITIZATION_TOGGLEABLE`` is True. Duplicates are avoided by
    de-duplicating on ``FORMAT_KEY``.
    """
    entries = []
    for file_format, key, desc in _format_key_desc_generator(registry):
        toggleable = getattr(file_format, 'DATE_SANITIZATION_TOGGLEABLE', False)
        if toggleable:
            # dropping `_()` here as it's done in the UI, e.g. see `tags.py`
            entries.append((key, desc))
    return tuple(sorted(entries))
