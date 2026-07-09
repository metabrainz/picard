# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025-2026 Laurent Monin
# Copyright (C) 2026 Philipp Wolfer
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

from dataclasses import (
    dataclass,
    field,
)
from typing import TYPE_CHECKING

from PyQt6 import QtCore

from picard import log


if TYPE_CHECKING:
    from picard.tagger import Tagger


# Translator priority constants (higher = installed later = searched first)
TRANSLATOR_PRIORITY_QT_BASE = 100  # Qt base translations (highest priority)
TRANSLATOR_PRIORITY_PLUGIN = 0  # Plugin translations (lower priority)


@dataclass(init=True, order=True, kw_only=True)
class Translator:
    sort_index: int = TRANSLATOR_PRIORITY_QT_BASE
    installed: bool = field(default=False, compare=False)
    instance: QtCore.QTranslator = field(compare=False)
    comment: str = field(default='', compare=False)

    def __str__(self):
        if self.sort_index == TRANSLATOR_PRIORITY_QT_BASE:
            prefix = "Picard"
        elif self.sort_index == TRANSLATOR_PRIORITY_PLUGIN:
            prefix = "plugin"
        else:
            prefix = "unknown"
        return f"{prefix} {self.comment}"


class Translators:
    def __init__(self, tagger: 'Tagger'):
        self.tagger = tagger
        self.tagger._qt_translators_updated.connect(self.reinstall)
        self._translators = []
        self._changed = False
        self.add_default_translators()

    def add_default_translators(self) -> None:
        translator = QtCore.QTranslator(self.tagger)
        locale = QtCore.QLocale()
        translation_path = QtCore.QLibraryInfo.path(QtCore.QLibraryInfo.LibraryPath.TranslationsPath)
        log.debug("Looking for Qt locale %s in %s", locale.name(), translation_path)
        if translator.load(locale, 'qtbase_', directory=translation_path):
            t = Translator(sort_index=TRANSLATOR_PRIORITY_QT_BASE, instance=translator, comment='Qt Base')
            self._translators.append(t)
            self._changed = True
        else:
            log.debug("Qt locale %s not available", locale.name())

    def add_translator(self, translator: QtCore.QTranslator) -> None:
        plugin_id = getattr(translator, 'plugin_id', '')
        comment = plugin_id if plugin_id else repr(translator)
        if translator.isEmpty():
            # this shouldn't happen with plugins, but safer
            log.debug("Not adding empty translator for %s", comment)
            return
        t = Translator(sort_index=TRANSLATOR_PRIORITY_PLUGIN, instance=translator, comment=comment)
        self._translators.append(t)
        self._changed = True

    def remove_translator(self, translator: QtCore.QTranslator) -> None:
        for t in self._translators[:]:
            if t.instance == translator:
                if t.installed:
                    log.debug("Remove translator: %s", t)
                    self.tagger.removeTranslator(t.instance)
                self._translators.remove(t)
                self._changed = True
                break

    def reinstall(self) -> None:
        if not self._changed:
            return
        self._changed = False

        # Translations are searched for in the reverse order in which they were installed,
        # so the most recently installed translation file is searched for translations first
        # and the earliest translation file is searched last.
        # The search stops as soon as a translation containing a matching string is found.

        # First, remove installed translators
        for t in self._translators:
            if t.installed:
                self.tagger.removeTranslator(t.instance)
                t.installed = False

        # Now install new ones (higher sort_index installed last, used first)
        installed_count = 0
        for t in sorted(self._translators):
            t.installed = self.tagger.installTranslator(t.instance)
            if t.installed:
                installed_count += 1

        log.debug("%d/%d Qt Translators installed", installed_count, len(self._translators))
        installed_index = 0
        last = installed_count - 1
        prefix = "Qt Translator"
        # Iterate in reverse order, since "the most recently installed translation file is searched for translations first"
        for t in sorted(self._translators, reverse=True):
            if not t.installed:
                log.debug("%s: %s failed to install", prefix, t)
                continue
            if installed_count > 1 and installed_index == 0:
                log.debug("%s: %s installed (searched first)", prefix, t)
            elif installed_count > 1 and installed_index == last:
                log.debug("%s: %s installed (searched last)", prefix, t)
            else:
                log.debug("%s: %s installed", prefix, t)
            installed_index += 1
