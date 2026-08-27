# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2008, 2011-2012, 2014 Lukáš Lalinský
# Copyright (C) 2007 Nikolai Prokoschenko
# Copyright (C) 2008 Gary van der Merwe
# Copyright (C) 2008 Robert Kaye
# Copyright (C) 2008 Will
# Copyright (C) 2008-2010, 2015, 2018-2023, 2025-2026 Philipp Wolfer
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2009 David Hilton
# Copyright (C) 2011-2012 Chad Wilson
# Copyright (C) 2011-2013, 2015-2017 Wieland Hoffmann
# Copyright (C) 2011-2014 Michael Wiencek
# Copyright (C) 2013-2014, 2017 Sophist-UK
# Copyright (C) 2013-2026 Laurent Monin
# Copyright (C) 2015 Ohm Patel
# Copyright (C) 2015 samithaj
# Copyright (C) 2016 Rahul Raturi
# Copyright (C) 2016 Simon Legner
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2017 Antonio Larrosa
# Copyright (C) 2017 Frederik “Freso” S. Olesen
# Copyright (C) 2018 Kartik Ohri
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2018 virusMac
# Copyright (C) 2018, 2021-2023, 2025 Bob Swift
# Copyright (C) 2019 Timur Enikeev
# Copyright (C) 2020-2021 Gabriel Ferreira
# Copyright (C) 2021 Petit Minion
# Copyright (C) 2025 João Sousa
# Copyright (C) 2025 Khoa Nguyen
# Copyright (C) 2026 metaisfacil
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


from functools import partial

from PyQt6 import (
    QtGui,
    QtWidgets,
)

from picard.browser import addrelease
from picard.config import get_config
from picard.const.sys import IS_MACOS
from picard.i18n import (
    N_,
    gettext as _,
)
from picard.util import icontheme

from picard.ui.enums import MainAction
from picard.ui.translatable_action import TranslatableAction


_actions_functions = {}


def add_action(action_name):
    def decorator(fn):
        _actions_functions[action_name] = fn
        return fn

    return decorator


def create_actions(parent):
    for action_name, action in _actions_functions.items():
        yield (action_name, action(parent))


def retranslate_actions(action_map):
    """Retranslate all TranslatableAction instances in the action map."""
    for action in action_map.values():
        if action is not None and hasattr(action, 'retranslateUi'):
            action.retranslateUi()


def _retranslate_action_property(action, prop_name, getter, setter):
    """Retranslate a single property of an action.

    On first call, saves the current (untranslated) value as the source.
    On every call, translates the source and applies it.
    """
    source_prop = f'_source_{prop_name}'
    source = action.property(source_prop)
    if source is None:
        # First call: capture the untranslated source string
        source = getter()
        if not source:
            return
        action.setProperty(source_prop, source)
    setter(_(source))


@add_action(MainAction.OPTIONS)
def _create_options_action(parent):
    action = TranslatableAction(icontheme.lookup('preferences-desktop'), N_("&Options…"), parent)
    action.setMenuRole(QtGui.QAction.MenuRole.PreferencesRole)
    action.triggered.connect(parent.show_options)
    return action


@add_action(MainAction.SHOW_SCRIPT_EDITOR)
def _create_show_script_editor_action(parent):
    action = TranslatableAction(N_("&Edit scripts…"))
    action.setShortcut(QtGui.QKeySequence(_("Ctrl+Shift+S")))
    action.triggered.connect(parent.open_file_naming_script_editor)
    return action


@add_action(MainAction.CUT)
def _create_cut_action(parent):
    action = TranslatableAction(icontheme.lookup('edit-cut', icontheme.ICON_SIZE_MENU), N_("&Cut"), parent)
    action.setShortcut(QtGui.QKeySequence.StandardKey.Cut)
    action.setEnabled(False)
    action.triggered.connect(parent.cut)
    return action


@add_action(MainAction.PASTE)
def _create_paste_action(parent):
    action = TranslatableAction(icontheme.lookup('edit-paste', icontheme.ICON_SIZE_MENU), N_("&Paste"), parent)
    action.setShortcut(QtGui.QKeySequence.StandardKey.Paste)
    action.setEnabled(False)
    action.triggered.connect(parent.paste)
    return action


@add_action(MainAction.HELP)
def _create_help_action(parent):
    action = TranslatableAction(N_("&Help…"), parent)
    action.setShortcut(QtGui.QKeySequence.StandardKey.HelpContents)
    action.triggered.connect(parent.show_help)
    return action


@add_action(MainAction.ABOUT)
def _create_about_action(parent):
    action = TranslatableAction(N_("&About…"), parent)
    action.setMenuRole(QtGui.QAction.MenuRole.AboutRole)
    action.triggered.connect(parent.show_about)
    return action


@add_action(MainAction.DONATE)
def _create_donate_action(parent):
    action = TranslatableAction(N_("&Donate…"), parent)
    action.triggered.connect(parent.open_donation_page)
    return action


@add_action(MainAction.REPORT_BUG)
def _create_report_bug_action(parent):
    action = TranslatableAction(N_("&Report a Bug…"), parent)
    action.triggered.connect(parent.open_bug_report)
    return action


@add_action(MainAction.SUPPORT_FORUM)
def _create_support_forum_action(parent):
    action = TranslatableAction(N_("&Support Forum…"), parent)
    action.triggered.connect(parent.open_support_forum)
    return action


@add_action(MainAction.ADD_FILES)
def _create_add_files_action(parent):
    action = TranslatableAction(icontheme.lookup('document-open'), N_("&Add Files…"), parent)
    action.setStatusTip(N_("Add files to the tagger"))
    # TR: Keyboard shortcut for "Add Files…"
    action.setShortcut(QtGui.QKeySequence.StandardKey.Open)
    action.triggered.connect(parent.add_files)
    return action


@add_action(MainAction.ADD_DIRECTORY)
def _create_add_directory_action(parent):
    action = TranslatableAction(icontheme.lookup('folder'), N_("Add Fold&er…"), parent)
    action.setStatusTip(N_("Add a folder to the tagger"))
    # TR: Keyboard shortcut for "Add Directory…"
    action.setShortcut(QtGui.QKeySequence(_("Ctrl+E")))
    action.triggered.connect(parent.add_directory)
    return action


@add_action(MainAction.CLOSE_WINDOW)
def _create_close_window_action(parent):
    if parent.show_close_window:
        action = TranslatableAction(N_("Close Window"), parent)
        action.setShortcut(QtGui.QKeySequence(_("Ctrl+W")))
        action.triggered.connect(parent.close_active_window)
    else:
        action = None
    return action


@add_action(MainAction.SAVE)
def _create_save_action(parent):
    action = TranslatableAction(icontheme.lookup('document-save'), N_("&Save"), parent)
    action.setStatusTip(N_("Save selected files"))
    # TR: Keyboard shortcut for "Save"
    action.setShortcut(QtGui.QKeySequence.StandardKey.Save)
    action.setEnabled(False)
    action.triggered.connect(parent.save)
    return action


@add_action(MainAction.TRASH)
def _create_trash_action(parent):
    icon = parent.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_TrashIcon)
    action = TranslatableAction(icon, N_("Move to &trash"), parent)
    action.setStatusTip(N_("Move files to trash"))
    action.setShortcut(QtGui.QKeySequence(_("Shift+Del")))
    action.setEnabled(False)
    action.triggered.connect(parent.trash_files)
    return action


@add_action(MainAction.SUBMIT_ACOUSTID)
def _create_submit_acoustid_action(parent):
    action = TranslatableAction(icontheme.lookup('acoustid-fingerprinter'), N_("S&ubmit AcoustIDs"), parent)
    action.setStatusTip(N_("Submit acoustic fingerprints"))
    action.setEnabled(False)
    action.triggered.connect(parent._on_submit_acoustid)
    return action


@add_action(MainAction.SUBMIT_ISRC)
def _create_submit_isrc_action(parent):
    action = TranslatableAction(icontheme.lookup('isrc-submit'), N_("Submit &ISRCs"), parent)
    action.setStatusTip(N_("Submit ISRCs to MusicBrainz"))
    action.setEnabled(False)
    action.triggered.connect(parent._on_submit_isrc)
    return action


@add_action(MainAction.EXIT)
def _create_exit_action(parent):
    action = TranslatableAction(N_("E&xit"), parent)
    action.setMenuRole(QtGui.QAction.MenuRole.QuitRole)
    # TR: Keyboard shortcut for "Exit"
    action.setShortcut(QtGui.QKeySequence(_("Ctrl+Q")))
    action.triggered.connect(parent.close)
    return action


@add_action(MainAction.REMOVE)
def _create_remove_action(parent):
    action = TranslatableAction(icontheme.lookup('list-remove'), N_("&Remove"), parent)
    action.setStatusTip(N_("Remove selected files/albums"))
    action.setEnabled(False)
    action.triggered.connect(parent.remove_selected_objects)
    return action


@add_action(MainAction.BROWSER_LOOKUP)
def _create_browser_lookup_action(parent):
    action = TranslatableAction(icontheme.lookup('lookup-musicbrainz'), N_("Lookup in &Browser"), parent)
    action.setStatusTip(N_("Lookup selected item on MusicBrainz website"))
    action.setEnabled(False)
    # TR: Keyboard shortcut for "Lookup in Browser"
    action.setShortcut(QtGui.QKeySequence(_("Ctrl+Shift+L")))
    action.triggered.connect(parent.browser_lookup)
    return action


@add_action(MainAction.LOOKUP_ISRC)
def _create_lookup_isrc_action(parent):
    action = TranslatableAction(N_("Lookup by &ISRC"), parent)
    action.setStatusTip(N_("Lookup selected item by ISRC"))
    action.setEnabled(False)
    action.triggered.connect(parent._on_lookup_isrc)
    return action


@add_action(MainAction.SUBMIT_CLUSTER)
def _create_submit_cluster_action(parent):
    if addrelease.is_available():
        action = TranslatableAction(N_("Submit cluster as release…"), parent)
        action.setStatusTip(N_("Submit cluster as a new release to MusicBrainz"))
        action.setEnabled(False)
        action.triggered.connect(parent.submit_cluster)
    else:
        action = None
    return action


@add_action(MainAction.SUBMIT_FILE_AS_RECORDING)
def _create_submit_file_as_recording_action(parent):
    if addrelease.is_available():
        action = TranslatableAction(N_("Submit file as standalone recording…"), parent)
        action.setStatusTip(N_("Submit file as a new recording to MusicBrainz"))
        action.setEnabled(False)
        action.triggered.connect(parent.submit_file)
    else:
        action = None
    return action


@add_action(MainAction.SUBMIT_FILE_AS_RELEASE)
def _create_submit_file_as_release_action(parent):
    if addrelease.is_available():
        action = TranslatableAction(N_("Submit file as release…"), parent)
        action.setStatusTip(N_("Submit file as a new release to MusicBrainz"))
        action.setEnabled(False)
        action.triggered.connect(partial(parent.submit_file, as_release=True))
    else:
        action = None
    return action


@add_action(MainAction.SIMILAR_ITEMS_SEARCH)
def _create_similar_items_search_action(parent):
    action = TranslatableAction(icontheme.lookup('system-search'), N_("Search for similar items…"), parent)
    action.setIconText(N_("Similar items"))
    action.setStatusTip(N_("View similar releases or recordings and optionally choose a different one"))
    action.setEnabled(False)
    action.setShortcut(QtGui.QKeySequence(_("Ctrl+T")))
    action.triggered.connect(parent.show_similar_items_search)
    return action


@add_action(MainAction.ALBUM_SEARCH)
def _create_album_search_action(parent):
    action = TranslatableAction(icontheme.lookup('system-search'), N_("Search for similar albums…"), parent)
    action.setStatusTip(N_("View similar releases and optionally choose a different release"))
    action.setEnabled(False)
    action.setShortcut(QtGui.QKeySequence(_("Ctrl+T")))
    action.triggered.connect(parent.show_more_albums)
    return action


@add_action(MainAction.TRACK_SEARCH)
def _create_track_search_action(parent):
    action = TranslatableAction(icontheme.lookup('system-search'), N_("Search for similar tracks…"), parent)
    action.setStatusTip(N_("View similar tracks and optionally choose a different release"))
    action.setEnabled(False)
    action.setShortcut(QtGui.QKeySequence(_("Ctrl+T")))
    action.triggered.connect(parent.show_more_tracks)
    return action


@add_action(MainAction.ALBUM_OTHER_VERSIONS)
def _create_album_other_versions_action(parent):
    action = TranslatableAction(N_("Show &other album versions…"), parent)
    action.setShortcut(QtGui.QKeySequence(_("Ctrl+Shift+O")))
    action.triggered.connect(parent.show_album_other_versions)
    return action


@add_action(MainAction.SHOW_FILE_BROWSER)
def _create_show_file_browser_action(parent):
    config = get_config()
    action = TranslatableAction(N_("File &Browser"), parent)
    action.setCheckable(True)
    if config.persist['view_file_browser']:
        action.setChecked(True)
    action.setShortcut(QtGui.QKeySequence(_("Ctrl+B")))
    action.triggered.connect(parent.show_file_browser)
    return action


@add_action(MainAction.SHOW_METADATA_VIEW)
def _create_show_metadata_view_action(parent):
    config = get_config()
    action = TranslatableAction(N_("&Metadata"), parent)
    action.setCheckable(True)
    if config.persist['view_metadata_view']:
        action.setChecked(True)
    action.setShortcut(QtGui.QKeySequence(_("Ctrl+Shift+M")))
    action.triggered.connect(parent.show_metadata_view)
    return action


@add_action(MainAction.SHOW_COVER_ART)
def _create_show_cover_art_action(parent):
    config = get_config()
    action = TranslatableAction(N_("&Cover Art"), parent)
    action.setCheckable(True)
    if config.persist['view_cover_art']:
        action.setChecked(True)
    action.setEnabled(config.persist['view_metadata_view'])
    action.triggered.connect(parent.show_cover_art)
    return action


@add_action(MainAction.SHOW_TOOLBAR)
def _create_show_toolbar_action(parent):
    config = get_config()
    action = TranslatableAction(N_("&Actions"), parent)
    action.setCheckable(True)
    if config.persist['view_toolbar']:
        action.setChecked(True)
    action.triggered.connect(parent.show_toolbar)
    return action


@add_action(MainAction.SHOW_FILTERBAR)
def _create_filter_bar_action(parent):
    config = get_config()
    action = TranslatableAction(N_("Filter Items"), parent)
    action.setStatusTip(N_("Toggle filtering of items based on specific tag values."))
    action.setCheckable(True)
    action.setShortcut(QtGui.QKeySequence(_("Ctrl+Shift+F")))
    if config.persist['view_filterbar']:
        action.setChecked(True)
    action.triggered.connect(parent.show_filter_bars)
    return action


@add_action(MainAction.SEARCH)
def _create_search_action(parent):
    action = TranslatableAction(icontheme.lookup('system-search'), N_("Search"), parent)
    action.setEnabled(False)
    action.triggered.connect(parent.search)
    return action


@add_action(MainAction.CD_LOOKUP)
def _create_cd_lookup_action(parent):
    action = TranslatableAction(icontheme.lookup('media-optical'), N_("Lookup &CD…"), parent)
    action.setStatusTip(N_("Lookup the details of the CD in your drive"))
    # TR: Keyboard shortcut for "Lookup CD"
    action.setShortcut(QtGui.QKeySequence(_("Ctrl+K")))
    action.triggered.connect(parent.lookup_cd)
    return action


@add_action(MainAction.DISCID_FROM_LOGFILE)
def _lookup_discid_from_logfile_action(parent):
    action = TranslatableAction(icontheme.lookup('file-disc'), N_("Lookup CD &log file…"), parent)
    action.setStatusTip(N_("Lookup release from a CD ripping log file"))
    action.setEnabled(True)
    action.triggered.connect(parent.tagger.lookup_discid_from_logfile)
    return action


@add_action(MainAction.DISCID_FROM_TAGS)
def _lookup_discid_from_tags_action(parent):
    action = TranslatableAction(icontheme.lookup('media-optical-disc-id'), N_("Lookup TOC &tag…"), parent)
    action.setStatusTip(N_("Lookup release via disc identifiers from track tags"))
    action.setEnabled(False)
    action.triggered.connect(parent.lookup_discid_from_tags)
    return action


@add_action(MainAction.ANALYZE)
def _create_analyze_action(parent):
    action = TranslatableAction(icontheme.lookup('picard-analyze'), N_("&Scan"), parent)
    action.setStatusTip(
        N_("Use AcoustID audio fingerprint to identify the files by the actual music, even if they have no metadata")
    )
    action.setEnabled(False)
    action.setToolTip(N_("Identify the file using its AcoustID audio fingerprint"))
    # TR: Keyboard shortcut for "Analyze"
    action.setShortcut(QtGui.QKeySequence(_("Ctrl+Y")))
    action.triggered.connect(parent.analyze)
    return action


@add_action(MainAction.GENERATE_FINGERPRINTS)
def _create_generate_fingerprints_action(parent):
    action = TranslatableAction(icontheme.lookup('fingerprint'), N_("&Generate AcoustID Fingerprints"), parent)
    action.setIconText(N_("Generate Fingerprints"))
    action.setStatusTip(N_("Generate the AcoustID audio fingerprints for the selected files without doing a lookup"))
    action.setEnabled(False)
    action.setToolTip(N_("Generate the AcoustID audio fingerprints for the selected files"))
    action.setShortcut(QtGui.QKeySequence(_("Ctrl+Shift+Y")))
    action.triggered.connect(parent.generate_fingerprints)
    return action


@add_action(MainAction.CLUSTER)
def _create_cluster_action(parent):
    action = TranslatableAction(icontheme.lookup('picard-cluster'), N_("Cl&uster"), parent)
    action.setStatusTip(N_("Cluster files into album clusters"))
    action.setEnabled(False)
    # TR: Keyboard shortcut for "Cluster"
    action.setShortcut(QtGui.QKeySequence(_("Ctrl+U")))
    action.triggered.connect(parent.cluster)
    return action


@add_action(MainAction.AUTOTAG)
def _create_autotag_action(parent):
    action = TranslatableAction(icontheme.lookup('picard-auto-tag'), N_("&Lookup"), parent)
    tip = N_("Lookup selected items in MusicBrainz")
    action.setToolTip(tip)
    action.setStatusTip(tip)
    action.setEnabled(False)
    # TR: Keyboard shortcut for "Lookup"
    action.setShortcut(QtGui.QKeySequence(_("Ctrl+L")))
    action.triggered.connect(parent.autotag)
    return action


@add_action(MainAction.VIEW_INFO)
def _create_view_info_action(parent):
    action = TranslatableAction(icontheme.lookup('picard-edit-tags'), N_("&Info…"), parent)
    action.setEnabled(False)
    # TR: Keyboard shortcut for "Info"
    action.setShortcut(QtGui.QKeySequence(_("Ctrl+I")))
    action.triggered.connect(parent.view_info)
    return action


@add_action(MainAction.REFRESH)
def _create_refresh_action(parent):
    action = TranslatableAction(icontheme.lookup('view-refresh', icontheme.ICON_SIZE_MENU), N_("&Refresh"), parent)
    action.setShortcut(QtGui.QKeySequence(_("Ctrl+R")))
    action.triggered.connect(parent.refresh)
    return action


@add_action(MainAction.TAGS_FROM_FILENAMES)
def _create_tags_from_filenames_action(parent):
    action = TranslatableAction(icontheme.lookup('picard-tags-from-filename'), N_("Tags From &File Names…"), parent)
    action.setIconText(N_("Parse File Names…"))
    action.setToolTip(N_("Set tags based on the file names"))
    action.setShortcut(QtGui.QKeySequence(_("Ctrl+Shift+T")))
    action.setEnabled(False)
    action.triggered.connect(parent.open_tags_from_filenames)
    return action


@add_action(MainAction.OPEN_COLLECTION_IN_BROWSER)
def _create_open_collection_in_browser_action(parent):
    action = TranslatableAction(N_("&Open My Collections in Browser"), parent)
    action.setEnabled(parent.tagger.webservice.oauth_manager.is_logged_in())
    action.triggered.connect(parent.open_collection_in_browser)
    return action


@add_action(MainAction.VIEW_LOG)
def _create_view_log_action(parent):
    action = TranslatableAction(N_("View &Error/Debug Log"), parent)
    # TR: Keyboard shortcut for "View Error/Debug Log"
    action.setShortcut(QtGui.QKeySequence(_("Ctrl+G")))
    action.triggered.connect(parent.show_log)
    return action


@add_action(MainAction.VIEW_HISTORY)
def _create_view_history_action(parent):
    action = TranslatableAction(N_("View Activity &History"), parent)
    # TR: Keyboard shortcut for "View Activity History"
    # On macOS ⌘+H is a system shortcut to hide the window. Use ⌘+Shift+H instead.
    action.setShortcut(QtGui.QKeySequence(_("Ctrl+Shift+H") if IS_MACOS else _("Ctrl+H")))
    action.triggered.connect(parent.show_history)
    return action


@add_action(MainAction.PLAY)
def _create_play_file_action(parent):
    action = TranslatableAction(icontheme.lookup('play'), N_("&Play"), parent)
    action.setStatusTip(N_("Play selected files"))
    action.setEnabled(False)
    action.setShortcut(QtGui.QKeySequence(_("Ctrl+Shift+P")))
    action.triggered.connect(parent.play)
    return action


@add_action(MainAction.PLAY_FILE_EXTERNAL)
def _create_play_file_external_action(parent):
    action = TranslatableAction(icontheme.lookup('play-music'), N_("Open in System &Media Player"), parent)
    action.setStatusTip(N_("Play the file in your default media player"))
    action.setEnabled(False)
    action.triggered.connect(parent.play_file_external)
    return action


@add_action(MainAction.OPEN_FOLDER)
def _create_open_folder_action(parent):
    action = TranslatableAction(
        icontheme.lookup('folder', icontheme.ICON_SIZE_MENU), N_("Open Containing &Folder"), parent
    )
    action.setStatusTip(N_("Open the containing folder in your file explorer"))
    action.setEnabled(False)
    action.triggered.connect(parent.open_folder)
    return action


@add_action(MainAction.CHECK_UPDATE)
def _create_check_update_action(parent):
    if parent.tagger.autoupdate_enabled:
        action = TranslatableAction(N_("&Check for Update…"), parent)
        action.setMenuRole(QtGui.QAction.MenuRole.ApplicationSpecificRole)
        action.triggered.connect(parent.do_update_check)
    else:
        action = None
    return action


@add_action(MainAction.SHOW_SETUP_WIZARD)
def _create_show_setup_wizard_action(parent):
    action = TranslatableAction(N_("Show Setup &Wizard…"), parent)
    action.setMenuRole(QtGui.QAction.MenuRole.ApplicationSpecificRole)
    action.triggered.connect(partial(parent.show_setup_wizard, True))
    return action


@add_action(MainAction.SAVE_SESSION_AS)
def _create_save_session_action(parent):
    action = TranslatableAction(icontheme.lookup('document-save'), N_("Save Session &As…"), parent)
    action.setStatusTip(N_("Save the current session to a new file"))
    action.triggered.connect(parent.save_session_as)
    return action


@add_action(MainAction.SAVE_SESSION)
def _create_quick_save_session_action(parent):
    action = TranslatableAction(icontheme.lookup('document-save'), N_("&Save Session"), parent)
    action.setStatusTip(N_("Save the current session to the last used file"))
    action.triggered.connect(parent.quick_save_session)
    return action


@add_action(MainAction.LOAD_SESSION)
def _create_load_session_action(parent):
    action = TranslatableAction(icontheme.lookup('document-open'), N_("&Load Session…"), parent)
    action.setStatusTip(N_("Load a session file"))
    action.triggered.connect(parent.load_session)
    return action


@add_action(MainAction.NEW_SESSION)
def _create_close_session_action(parent):
    action = TranslatableAction(N_("&New Session"), parent)
    action.setStatusTip(N_("Close the current session"))
    action.triggered.connect(parent.close_session)
    return action


@add_action(MainAction.CLEAR_RECENT_SESSIONS)
def _create_clear_recent_sessions_action(parent):
    action = TranslatableAction(N_("Clear Recent Sessions"), parent)
    action.setStatusTip(N_("Clear all recent session entries"))
    action.triggered.connect(parent.clear_recent_sessions)
    return action
