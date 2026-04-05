# -*- coding: utf-8 -*-
#
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

from __future__ import annotations

from dataclasses import dataclass
from functools import partial
import time

from PyQt6 import (
    QtCore,
    QtWidgets,
)

from picard.config import get_config
from picard.i18n import (
    N_,
    gettext as _,
)
from picard.util import get_url


@dataclass(frozen=True)
class TipDef:
    """Definition of a tutorial tip."""

    text: str
    widget_attr: str
    doc_path: str | None = None


TIPS: dict[str, TipDef] = {
    'overview': TipDef(
        text=N_(
            "Welcome to MusicBrainz Picard! Start by adding your music files: "
            "use 'Add Files' or 'Add Directory' from the toolbar or the File menu."
        ),
        widget_attr='toolbar',
        doc_path='/getting_started/screen_main.html',
    ),
    'add_files': TipDef(
        text=N_(
            "Your files are now in the left pane under 'Unmatched Files'. "
            "Next step: click 'Cluster' in the toolbar to group them by album, "
            "or select files and use 'Lookup' or 'Scan' to identify them."
        ),
        widget_attr='toolbar',
        doc_path='/usage/retrieve.html',
    ),
    'cluster': TipDef(
        text=N_(
            "Files have been grouped into clusters by album. "
            "Now select a cluster and click 'Lookup' in the toolbar to find "
            "the matching MusicBrainz release."
        ),
        widget_attr='toolbar',
        doc_path='/usage/retrieve_lookup.html',
    ),
    'lookup': TipDef(
        text=N_(
            "Picard is looking up your selection on MusicBrainz. "
            "Matched albums will appear in the right pane. "
            "You can then review the metadata before saving."
        ),
        widget_attr='toolbar',
        doc_path='/usage/retrieve_lookup.html',
    ),
    'scan': TipDef(
        text=N_(
            "Picard is generating audio fingerprints and looking up "
            "your files on AcoustID. Matched files will move to the "
            "right pane automatically."
        ),
        widget_attr='toolbar',
        doc_path='/usage/retrieve_scan.html',
    ),
    'album_loaded': TipDef(
        text=N_(
            "An album has been loaded in the right pane and files have been "
            "matched to tracks. The color indicates match quality: green means "
            "a good match. Review the results, then click 'Save' in the toolbar "
            "to write the new tags to your files."
        ),
        widget_attr='panel',
        doc_path='/usage/match.html',
    ),
    'metadata': TipDef(
        text=N_(
            "The metadata view shows tags for the selected item. "
            "'Original Value' is what's currently in your file, "
            "'New Value' is what Picard will write. "
            "Double-click a value to edit it. When you're happy with "
            "the tags, click 'Save' in the toolbar to write them."
        ),
        widget_attr='metadata_box',
        doc_path='/workflows/workflow_metadata.html',
    ),
    'cover_art': TipDef(
        text=N_(
            "Cover art for the selected item is shown here. "
            "You can drag and drop images, or right-click for more options."
        ),
        widget_attr='cover_art_box',
        doc_path='/usage/coverart.html',
    ),
    'save': TipDef(
        text=N_(
            "Saving writes the new metadata to your files. "
            "If renaming or moving is enabled in the options, "
            "files will also be renamed or moved accordingly."
        ),
        widget_attr='toolbar',
        doc_path='/usage/save.html',
    ),
    'drag_drop': TipDef(
        text=N_(
            "You can drag files between the left and right panes to "
            "manually match them to albums and tracks, or drag them "
            "back to unmatch. To add an album to the right pane, use "
            "'Lookup' on a cluster, search for it via 'Search', or "
            "paste a MusicBrainz URL."
        ),
        widget_attr='panel',
        doc_path='/usage/retrieve_manual.html',
    ),
}


class TutorialTip(QtWidgets.QDialog):
    """A non-modal dialog for tutorial tips, positioned near a target widget."""

    disabled = QtCore.pyqtSignal()

    def __init__(self, text: str, doc_url: str | None = None, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self.setWindowTitle(_("Picard Tutorial"))

        layout = QtWidgets.QVBoxLayout(self)

        header = QtWidgets.QHBoxLayout()
        icon_label = QtWidgets.QLabel()
        style = self.style()
        if style:
            icon_label.setPixmap(
                style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MessageBoxInformation).pixmap(32, 32)
            )
        icon_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        header.addWidget(icon_label, 0)
        text_label = QtWidgets.QLabel(text)
        text_label.setWordWrap(True)
        text_label.setOpenExternalLinks(True)
        header.addWidget(text_label, 1)
        layout.addLayout(header)

        if doc_url:
            link = QtWidgets.QLabel(
                '<a href="{url}">{text}</a>'.format(
                    url=doc_url,
                    text=_("Learn more…"),
                )
            )
            link.setToolTip(doc_url)
            link.setOpenExternalLinks(True)
            layout.addWidget(link)

        button_layout = QtWidgets.QHBoxLayout()
        disable_button = QtWidgets.QPushButton(_("Don't show tips again"))
        disable_button.clicked.connect(self._on_disable)
        button_layout.addWidget(disable_button)
        button_layout.addStretch()
        close_button = QtWidgets.QPushButton(_("Got it"))
        close_button.setDefault(True)
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)

    def _on_disable(self) -> None:
        self.disabled.emit()
        self.accept()

    def show_near_widget(self, widget: QtWidgets.QWidget) -> None:
        self.adjustSize()
        pos = widget.mapToGlobal(QtCore.QPoint(0, widget.height()))
        screen = widget.screen()
        if screen:
            screen_rect = screen.availableGeometry()
            if pos.x() + self.width() > screen_rect.right():
                pos.setX(screen_rect.right() - self.width())
            if pos.y() + self.height() > screen_rect.bottom():
                pos = widget.mapToGlobal(QtCore.QPoint(0, -self.height()))
        self.move(pos)
        self.show()


class TutorialManager:
    """Manages contextual tutorial tips shown once to new users."""

    MIN_DISPLAY_SECS = 3.0

    def __init__(self, window: QtWidgets.QMainWindow):
        self._window = window
        self._active_tip: TutorialTip | None = None
        self._tip_shown_at: float = 0
        self._pending_step: str | None = None
        self._pending_timer: QtCore.QTimer | None = None

    def should_show(self, step_id: str) -> bool:
        config = get_config()
        if config.persist['tutorial_disabled']:
            return False
        return step_id not in config.persist['tutorial_steps_shown']

    def mark_shown(self, step_id: str) -> None:
        config = get_config()
        shown = config.persist['tutorial_steps_shown']
        if step_id not in shown:
            shown.append(step_id)
            config.persist['tutorial_steps_shown'] = shown

    def disable(self) -> None:
        config = get_config()
        config.persist['tutorial_disabled'] = True

    def show(self, step_id: str) -> bool:
        """Show a tutorial tip by step ID. Returns True if shown."""
        if not self.should_show(step_id):
            return False
        # If a tip is active and hasn't been shown long enough, queue this one
        remaining_ms = self._tip_remaining_ms()
        if self._active_tip and remaining_ms > 0:
            self._queue_pending(step_id, remaining_ms)
            return True
        self._cancel_pending()
        self._show_now(step_id)
        return True

    def _tip_remaining_ms(self) -> int:
        elapsed = time.monotonic() - self._tip_shown_at
        return max(0, int((self.MIN_DISPLAY_SECS - elapsed) * 1000))

    def _queue_pending(self, step_id: str, delay_ms: int) -> None:
        self._cancel_pending()
        self._pending_step = step_id
        self._pending_timer = QtCore.QTimer(self._window)
        self._pending_timer.setSingleShot(True)
        self._pending_timer.timeout.connect(self._show_pending)
        self._pending_timer.start(delay_ms)

    def _cancel_pending(self) -> None:
        if self._pending_timer:
            self._pending_timer.stop()
            self._pending_timer = None
        self._pending_step = None

    def _show_pending(self) -> None:
        step_id = self._pending_step
        self._cancel_pending()
        if step_id and self.should_show(step_id):
            self._show_now(step_id)

    def _show_now(self, step_id: str) -> None:
        tip_def = TIPS[step_id]
        widget = getattr(self._window, tip_def.widget_attr)
        doc_url = get_url(tip_def.doc_path) if tip_def.doc_path else None
        self._close_active_tip()
        tip = TutorialTip(_(tip_def.text), doc_url=doc_url, parent=self._window)
        tip.finished.connect(partial(self.mark_shown, step_id))
        tip.finished.connect(partial(self._on_tip_closed, tip))
        tip.disabled.connect(self.disable)
        self._active_tip = tip
        self._tip_shown_at = time.monotonic()
        tip.show_near_widget(widget)

    def _close_active_tip(self) -> None:
        if self._active_tip:
            self._active_tip.close()
            self._active_tip = None

    def _on_tip_closed(self, tip: TutorialTip, _result: int | None = None) -> None:
        if self._active_tip is tip:
            self._active_tip = None
