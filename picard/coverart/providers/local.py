# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2015, 2018-2021, 2023-2026 Laurent Monin
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2017 Ville Skyttä
# Copyright (C) 2019-2021, 2025-2026 Philipp Wolfer
# Copyright (C) 2026 Bob Swift
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


import os
import re
from typing import ClassVar

from PyQt6.QtCore import QSignalBlocker
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QStyle,
    QToolButton,
)

from picard.config import get_config
from picard.coverart.image import LocalFileCoverArtImage
from picard.coverart.providers.provider import (
    CoverArtProvider,
    ProviderOptions,
)
from picard.coverart.utils import CAA_TYPES
from picard.extension_points.local_cover_art_modes import (
    LocalCoverArtMode,
    get_local_cover_art_mode,
    local_cover_art_modes,
    register_local_cover_art_mode,
)
from picard.i18n import (
    N_,
    gettext as _,
)

from picard.ui.forms.ui_provider_options_local import Ui_LocalOptions
from picard.ui.options import PageOptionConfigs
from picard.ui.playground import Playground


# Identifier of the built-in regular-expression mode, also used as the default
# value of the ``local_cover_match_mode`` setting.
REGEX_MODE_ID = 'regex'


class ProviderOptionsLocal(ProviderOptions):
    """
    Options for Local Files cover art provider.

    The page is driven entirely by the registered local cover art matching
    modes (see :mod:`picard.extension_points.local_cover_art_modes`): a selector
    lists the available modes and the single input field, its label, note,
    placeholder, playground and documentation button all adapt to the active
    mode's descriptor. Each mode owns its value (via ``get_value`` /
    ``set_value``), so switching modes in the dialog is lossless and a mode
    provided by a plugin can store its value wherever it likes.

    The active mode id is stored in ``local_cover_match_mode`` and defaults to
    the built-in regular-expression mode, so existing configurations keep the
    previous behavior. Adding a new way to select cover art requires registering
    a new mode, with no change to this page.
    """

    NAME = "provider_local"
    HELP_URL = '/config/options_local_files.html'

    OPTIONS: ClassVar[PageOptionConfigs] = {
        'local_cover_regex': {'widgets': ['local_cover_regex_edit']},
        'local_cover_match_mode': {'widgets': []},
    }

    _options_ui = Ui_LocalOptions

    def __init__(self, parent=None):
        super().__init__(parent)

        # In-memory value per mode id, so switching modes in the dialog does not
        # discard the other modes' values before the page is saved.
        self._mode_values: dict[str, str] = {}
        self._current_mode_id: str | None = None

        # Build a mode selector at the top of the page. Populated in load()
        # from the registered modes so plugin-provided modes appear
        # automatically.
        self._mode_selector = QComboBox(self)
        self._mode_label = QLabel(_("Match cover art files using:"), self)
        selector_row = QHBoxLayout()
        selector_row.addWidget(self._mode_label)
        selector_row.addWidget(self._mode_selector, 1)
        self.ui.verticalLayout.insertLayout(0, selector_row)

        # Place a documentation icon button next to the input field, shown only
        # for modes that provide a documentation callable.
        self._doc_button = QToolButton(self)
        self._doc_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxQuestion))
        self._doc_button.setVisible(False)
        field_index = self.ui.verticalLayout.indexOf(self.ui.local_cover_regex_edit)
        self.ui.verticalLayout.removeWidget(self.ui.local_cover_regex_edit)
        field_row = QHBoxLayout()
        field_row.addWidget(self.ui.local_cover_regex_edit)
        field_row.addWidget(self._doc_button)
        self.ui.verticalLayout.insertLayout(field_index, field_row)

        self.playground = Playground(_("Test file name matching:"), parent=self)
        self.playground.set_description(
            description=_("Enter file names to test, one per line."),
            match_meaning=_("the file name matches"),
            skip_meaning=_("the file name does not match"),
        )
        self.ui.verticalLayout.insertWidget(self.ui.verticalLayout.count() - 1, self.playground)

        self.ui.local_cover_regex_edit.textChanged.connect(self._update_test_coverart_filter)
        self._mode_selector.currentIndexChanged.connect(self._on_mode_selected)
        self.playground.textChanged.connect(self._update_test_coverart_filter)

    @property
    def _current_mode(self) -> LocalCoverArtMode | None:
        if self._current_mode_id is None:
            return None
        return get_local_cover_art_mode(self._current_mode_id)

    def _stash_current_value(self):
        """Save the visible field into the current mode's in-memory value."""
        if self._current_mode_id is not None:
            self._mode_values[self._current_mode_id] = self.ui.local_cover_regex_edit.text()

    def _apply_mode(self, mode_id):
        """Show the value and labels for the given mode in the single field."""
        self._current_mode_id = mode_id
        mode = get_local_cover_art_mode(mode_id)
        if mode is None:
            return
        self.ui.local_cover_regex_label.setText(_(mode.description))
        self.ui.note.setText(_(mode.note))
        self.ui.local_cover_regex_edit.setPlaceholderText(mode.example)
        if mode.example:
            self.ui.local_cover_regex_edit.setToolTip(_("Example: %s") % mode.example)
        else:
            self.ui.local_cover_regex_edit.setToolTip("")
        self.ui.local_cover_regex_edit.setText(self._mode_values.get(mode_id, ""))
        self.playground.setVisible(mode.playground)
        try:
            self._doc_button.clicked.disconnect()
        except TypeError:
            pass  # No previous connection
        if mode.show_doc:
            tooltip = _(mode.doc_tooltip) if mode.doc_tooltip else _("Show documentation")
            self._doc_button.setToolTip(tooltip)
            self._doc_button.setAccessibleName(tooltip)
            self._doc_button.clicked.connect(lambda: mode.show_doc(self))
            self._doc_button.setVisible(True)
        else:
            self._doc_button.setVisible(False)
        self._update_test_coverart_filter()

    def _on_mode_selected(self, index):
        # Stash the outgoing mode's field before switching, so the switch is
        # lossless within the dialog.
        self._stash_current_value()
        mode_id = self._mode_selector.itemData(index)
        if mode_id is not None:
            self._apply_mode(mode_id)

    def load(self):
        modes = sorted(local_cover_art_modes(), key=lambda m: _(m.title).lower())
        # Load each mode's stored value up front so switching is lossless.
        self._mode_values = {mode.id: mode.get_value() for mode in modes}

        active_id = get_config().setting['local_cover_match_mode']
        if get_local_cover_art_mode(active_id) is None:
            active_id = REGEX_MODE_ID

        with QSignalBlocker(self._mode_selector):
            self._mode_selector.clear()
            for mode in modes:
                self._mode_selector.addItem(_(mode.title), mode.id)
            index = self._mode_selector.findData(active_id)
            if index >= 0:
                self._mode_selector.setCurrentIndex(index)
        # A single mode needs no selector; keep the UI clean.
        selector_visible = len(modes) > 1
        self._mode_selector.setVisible(selector_visible)
        self._mode_label.setVisible(selector_visible)

        self._apply_mode(active_id)

    def save(self):
        self._stash_current_value()
        for mode in local_cover_art_modes():
            if mode.id in self._mode_values:
                mode.set_value(self._mode_values[mode.id])
        if self._current_mode_id is not None:
            get_config().setting['local_cover_match_mode'] = self._current_mode_id

    def _update_test_coverart_filter(self):
        if not self.playground.isVisible():
            return
        mode = self._current_mode
        self.playground.clear_error()
        matcher = None
        if mode is not None and mode.make_matcher is not None:
            value = self.ui.local_cover_regex_edit.text()
            matcher = mode.make_matcher(value, self.playground.set_error)
        self.playground.update(matcher)


def _regex_playground_matcher(value, on_error):
    """Build a playground predicate for the regex mode from the field value."""
    if not value:
        return None
    try:
        pattern = re.compile(value, re.IGNORECASE)
    except re.error as e:
        on_error(_("Invalid regular expression: %s") % e)
        return None
    return lambda line: bool(pattern.search(line))


class CoverArtProviderLocal(CoverArtProvider):
    """Get cover art from local files"""

    NAME = "Local Files"
    TITLE = N_("Local Files")
    OPTIONS = ProviderOptionsLocal

    _types_split_re = re.compile('[^a-z0-9]', re.IGNORECASE)
    _known_types = frozenset(t['name'] for t in CAA_TYPES)
    _default_types = ('front',)

    def queue_images(self):
        config = get_config()
        # If the configured mode is not registered (e.g. the plugin that
        # provided it has been uninstalled or disabled), queue nothing rather
        # than silently applying a different mode's value.
        mode = get_local_cover_art_mode(config.setting['local_cover_match_mode'])
        if mode is not None:
            value = mode.get_value()
            if value:
                mode.queue_images(self, value)
        return CoverArtProvider.QueueState.FINISHED

    def get_types(self, string):
        found = {x.lower() for x in self._types_split_re.split(string) if x}
        return list(found.intersection(self._known_types))

    def find_local_images(self, current_dir, match_re):
        for root, _dirs, files in os.walk(current_dir):
            for filename in files:
                m = match_re.search(filename)
                if not m:
                    continue
                filepath = os.path.join(root, filename)
                if not os.path.exists(filepath):
                    continue
                try:
                    type_from_filename = self.get_types(m.group(1))
                except IndexError:
                    type_from_filename = []
                yield LocalFileCoverArtImage(
                    filepath,
                    types=type_from_filename or self._default_types,
                    support_types=True,
                    support_multi_types=True,
                )


def _queue_images_regex(provider, regex):
    """Queue cover art images whose file names match a regular expression."""
    match_re = re.compile(regex, re.IGNORECASE)
    dirs_done = set()
    for file in provider.album.iterfiles():
        current_dir = os.path.dirname(file.filename)
        if current_dir in dirs_done:
            continue
        dirs_done.add(current_dir)
        for image in provider.find_local_images(current_dir, match_re):
            provider.queue_put(image)


def _regex_get_value():
    return get_config().setting['local_cover_regex']


def _regex_set_value(value):
    get_config().setting['local_cover_regex'] = value


def register_builtin_local_cover_art_modes():
    """Register the local cover art matching modes provided by Picard core."""
    register_local_cover_art_mode(
        LocalCoverArtMode(
            id=REGEX_MODE_ID,
            title=N_("Regular expression"),
            description=N_("Local cover art files match the following regular expression:"),
            note=N_(
                "First group in the regular expression, if any, will be used as type, "
                "ie. cover-back-spine.jpg will be set as types Back + Spine. "
                "If no type is found, it will default to Front type."
            ),
            queue_images=_queue_images_regex,
            get_value=_regex_get_value,
            set_value=_regex_set_value,
            example=r'^(?:cover|folder)\.(?:jpe?g|png)$',
            playground=True,
            make_matcher=_regex_playground_matcher,
        )
    )
