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
from PyQt6.QtWidgets import QPushButton

from picard.config import get_config
from picard.coverart.image import LocalFileCoverArtImage
from picard.coverart.providers.provider import (
    CoverArtProvider,
    ProviderOptions,
)
from picard.coverart.utils import CAA_TYPES
from picard.i18n import (
    N_,
    gettext as _,
)
from picard.metadata import Metadata
from picard.options import (
    LOCAL_COVER_MODES,
    LocalCoverMatchMode,
)
from picard.util import wildcards_to_regex_pattern

from picard.ui.forms.ui_provider_options_local import Ui_LocalOptions
from picard.ui.options import PageOptionConfigs
from picard.ui.playground import Playground


class ProviderOptionsLocal(ProviderOptions):
    """
    Options for Local Files cover art provider.

    Each matching mode (see ``LocalCoverMatchMode`` / ``LOCAL_COVER_MODES``)
    stores its value in its own option, so switching modes is lossless and
    option profiles can override each value independently. Only the value for
    the currently active mode is shown in the single input field; the
    description and note labels adapt to the active mode.

    The active mode is stored in ``local_cover_match_mode`` and defaults to
    ``LocalCoverMatchMode.REGEX``, so existing configurations (and any config
    without the key) keep the previous regular-expression behavior.
    """

    NAME = "provider_local"
    HELP_URL = '/config/options_local_files.html'

    OPTIONS: ClassVar[PageOptionConfigs] = {
        'local_cover_regex': {'widgets': ['local_cover_regex_edit']},
        'local_cover_script': {'widgets': ['local_cover_regex_edit']},
        'local_cover_match_mode': {'widgets': ['local_cover_use_script']},
    }

    _options_ui = Ui_LocalOptions

    def __init__(self, parent=None):
        super().__init__(parent)

        # In-memory value for each mode, so switching modes in the dialog does
        # not discard the other mode's value before the page is saved.
        self._mode_values = dict.fromkeys(LocalCoverMatchMode, "")
        self._current_mode = LocalCoverMatchMode.REGEX

        self.playground = Playground(_("Test file name matching:"), parent=self)
        self.playground.set_description(
            description=_("Enter file names to test, one per line."),
            match_meaning=_("the file name matches"),
            skip_meaning=_("the file name does not match"),
        )
        self.ui.verticalLayout.insertWidget(self.ui.verticalLayout.count() - 1, self.playground)

        self._doc_button = QPushButton("?", self)
        self._doc_button.setToolTip(_("Show documentation"))
        self._doc_button.setFixedWidth(self._doc_button.fontMetrics().horizontalAdvance("?") * 3)
        self._doc_button.setVisible(False)
        self.ui.verticalLayout.insertWidget(self.ui.verticalLayout.count() - 1, self._doc_button)

        self.ui.local_cover_regex_edit.textChanged.connect(self._update_test_coverart_filter)
        self.ui.local_cover_use_script.toggled.connect(self._on_mode_toggled)
        self.playground.textChanged.connect(self._update_test_coverart_filter)

    @staticmethod
    def _mode_from_checkbox(checked):
        return LocalCoverMatchMode.SCRIPT if checked else LocalCoverMatchMode.REGEX

    def _apply_mode(self, mode):
        """Show the value and labels for the given mode in the single field."""
        self._current_mode = mode
        info = LOCAL_COVER_MODES[mode]
        self.ui.local_cover_regex_label.setText(_(info.description))
        self.ui.note.setText(_(info.note))
        # The example is a literal pattern; show it as placeholder (greyed hint
        # visible when the field is empty), and also as the field tooltip.
        self.ui.local_cover_regex_edit.setPlaceholderText(info.example)
        self.ui.local_cover_regex_edit.setToolTip(_("Example: %s") % info.example)
        self.ui.local_cover_regex_edit.setText(self._mode_values[mode])
        self.playground.setVisible(info.playground)
        # Show the documentation button if the mode provides a show_doc callable.
        try:
            self._doc_button.clicked.disconnect()
        except TypeError:
            pass  # No previous connection
        if info.show_doc:
            self._doc_button.clicked.connect(lambda: info.show_doc(self))
            self._doc_button.setVisible(True)
        else:
            self._doc_button.setVisible(False)
        self._update_test_coverart_filter()

    def _on_mode_toggled(self, checked):
        # Stash the current field into the outgoing mode before switching, so
        # the switch is lossless within the dialog.
        self._mode_values[self._current_mode] = self.ui.local_cover_regex_edit.text()
        self._apply_mode(self._mode_from_checkbox(checked))

    def load(self):
        config = get_config()
        for mode, info in LOCAL_COVER_MODES.items():
            self._mode_values[mode] = config.setting[info.setting]
        mode = config.setting['local_cover_match_mode']
        if mode not in LOCAL_COVER_MODES:
            mode = LocalCoverMatchMode.REGEX
        # Set the checkbox without triggering the lossless-swap handler, then
        # apply the mode explicitly.
        with QSignalBlocker(self.ui.local_cover_use_script):
            self.ui.local_cover_use_script.setChecked(mode == LocalCoverMatchMode.SCRIPT)
        self._apply_mode(mode)

    def save(self):
        config = get_config()
        # Capture the visible field into the active mode before persisting.
        self._mode_values[self._current_mode] = self.ui.local_cover_regex_edit.text()
        for mode, info in LOCAL_COVER_MODES.items():
            config.setting[info.setting] = self._mode_values[mode]
        config.setting['local_cover_match_mode'] = self._current_mode

    def _update_test_coverart_filter(self):
        if not self.playground.isVisible():
            return
        value = self.ui.local_cover_regex_edit.text()
        self.playground.clear_error()
        matcher = self._build_regex_matcher(value)
        check_line = (lambda line: bool(matcher.search(line))) if matcher is not None else None
        self.playground.update(check_line)

    def _build_regex_matcher(self, value):
        """Compile the field value as a regex for the playground.

        Returns a compiled pattern, or None if the value is empty or invalid
        (in which case an error message is shown on the playground).
        """
        if not value:
            return None
        try:
            return re.compile(value, re.IGNORECASE)
        except re.error as e:
            self.playground.set_error(_("Invalid regular expression: %s") % e)
            return None


class CoverArtProviderLocal(CoverArtProvider):
    """Get cover art from local files"""

    NAME = "Local Files"
    TITLE = N_("Local Files")
    OPTIONS = ProviderOptionsLocal

    _types_split_re = re.compile('[^a-z0-9]', re.IGNORECASE)
    _known_types = frozenset(t['name'] for t in CAA_TYPES)
    _default_types = ('front',)

    _queue_methods: ClassVar[dict[LocalCoverMatchMode, str]] = {
        LocalCoverMatchMode.REGEX: '_queue_images_regex',
        LocalCoverMatchMode.SCRIPT: '_queue_images_script',
    }

    def queue_images(self):
        config = get_config()
        mode = config.setting['local_cover_match_mode']
        value = config.setting[LOCAL_COVER_MODES[mode].setting]
        if value:
            getattr(self, self._queue_methods[mode])(value)
        return CoverArtProvider.QueueState.FINISHED

    def _queue_images_regex(self, regex):
        match_re = re.compile(regex, re.IGNORECASE)
        dirs_done = set()
        for file in self.album.iterfiles():
            current_dir = os.path.dirname(file.filename)
            if current_dir in dirs_done:
                continue
            dirs_done.add(current_dir)
            for image in self.find_local_images(current_dir, match_re):
                self.queue_put(image)

    def _queue_images_script(self, script):
        filepaths_done = set()
        walks_done = set()
        for file in self.album.iterfiles():
            current_dir = os.path.dirname(file.filename)
            expected_filename = self._eval_script(script, file.metadata)
            if not expected_filename:
                continue
            # Tracks of an album usually share metadata, so the evaluated
            # pattern is often identical across a directory. Walk each
            # (directory, pattern) pair only once.
            walk_key = (current_dir, expected_filename)
            if walk_key in walks_done:
                continue
            walks_done.add(walk_key)
            for image in self.find_local_images_by_script(current_dir, expected_filename, filepaths_done):
                self.queue_put(image)

    @staticmethod
    def _eval_script(script, metadata):
        """Evaluate a script and return its result for use as a file name pattern.

        Unlike script_to_filename(), the result is not sanitized as a file name:
        wildcard characters (``*``, ``?``, ``{``, ``}``, ``,``) are preserved so
        they can be interpreted by _pattern_to_re(). Only path separators in
        metadata values are replaced, to keep matching limited to file names.
        """
        from picard.script import ScriptParser

        new_metadata = Metadata()
        for name in metadata:
            new_metadata[name] = [str(v).replace(os.sep, '_') for v in metadata.getall(name)]
        script = script.replace('\t', '').replace('\n', '')
        result = ScriptParser().eval(script, new_metadata)
        return result.replace('\x00', '')

    @staticmethod
    def _pattern_to_re(pattern):
        """Compile a file name pattern to a regex.

        Reuses picard.util.wildcards_to_regex_pattern. The pattern is a file
        name produced by a user's script, so:

        - ``[`` and ``]`` are matched literally (``allow_char_class=False``):
          file names commonly contain brackets, e.g. "Album [2007].jpg", and
          users do not expect ``[...]`` to be a character class here.
        - ``{a,b,c}`` alternation is enabled (``allow_alternation=True``) so
          common cases like matching several extensions are easy, e.g.
          ``%album%.{jpg,png,gif}``.
        - ``*`` and ``?`` remain wildcards.

        The result is anchored to the full file name and matched
        case-insensitively.
        """
        regex = wildcards_to_regex_pattern(
            pattern,
            allow_char_class=False,
            allow_alternation=True,
            anchored=True,
        )
        return re.compile(regex, re.IGNORECASE)

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

    def find_local_images_by_script(self, current_dir, expected_filename, filepaths_done):
        match_re = self._pattern_to_re(expected_filename)
        for root, _dirs, files in os.walk(current_dir):
            for filename in files:
                if match_re.match(filename):
                    filepath = os.path.join(root, filename)
                    if filepath in filepaths_done:
                        continue
                    filepaths_done.add(filepath)
                    if os.path.exists(filepath):
                        types = self.get_types(filename) or self._default_types
                        yield LocalFileCoverArtImage(
                            filepath,
                            types=types,
                            support_types=True,
                            support_multi_types=True,
                        )
