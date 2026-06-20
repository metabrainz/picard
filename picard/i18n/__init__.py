# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2012 Frederik “Freso” S. Olesen
# Copyright (C) 2013-2014, 2018-2024 Laurent Monin
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2017-2024 Philipp Wolfer
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


from collections.abc import Callable

from picard.i18n.collate import (
    setup_collator,
    sort_key,
)
from picard.i18n.gettext import (
    N_,
    _,
    gettext,
    gettext_attributes,
    gettext_constants,
    gettext_countries,
    ngettext,
    pgettext_attributes,
    setup_gettext,
)


__all__ = [
    'N_',
    '_',
    'gettext',
    'gettext_attributes',
    'gettext_constants',
    'gettext_countries',
    'ngettext',
    'pgettext_attributes',
    'setup_i18n',
    'sort_key',
]


def setup_i18n(localedir: str | None, ui_language: str | None = None, logger: Callable | None = None):
    logger = _init_logger(logger)

    # Setup gettext translations
    setup_gettext(localedir, ui_language, logger)

    # Setup collator
    setup_collator(logger)


def _init_logger(logger: Callable | None) -> Callable:
    if not logger:
        logger = lambda *a, **b: None  # noqa: E731
    return logger
