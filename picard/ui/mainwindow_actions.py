# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2008, 2011-2012, 2014 Lukáš Lalinský
# Copyright (C) 2007 Nikolai Prokoschenko
# Copyright (C) 2008 Gary van der Merwe
# Copyright (C) 2008 Robert Kaye
# Copyright (C) 2008 Will
# Copyright (C) 2008-2010, 2015, 2018-2023 Philipp Wolfer
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2009 David Hilton
# Copyright (C) 2011-2012 Chad Wilson
# Copyright (C) 2011-2013, 2015-2017 Wieland Hoffmann
# Copyright (C) 2011-2014 Michael Wiencek
# Copyright (C) 2013-2014, 2017 Sophist-UK
# Copyright (C) 2013-2023 Laurent Monin
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
# Copyright (C) 2018, 2021-2023 Bob Swift
# Copyright (C) 2019 Timur Enikeev
# Copyright (C) 2020-2021 Gabriel Ferreira
# Copyright (C) 2021 Petit Minion
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


from functools import partial

from PyQt6 import QtGui

from picard.browser import addrelease
from picard.config import get_config
from picard.const.sys import IS_MACOS
from picard.i18n import gettext as _
from picard.util import icontheme


_actions_functions = dict()


def action_add(action_name):
    def decorator(fn):
        _actions_functions[action_name] = fn
        return fn
    return decorator


def create_actions(parent):
    for action_name, action in _actions_functions.items():
        yield (action_name, action(parent))


@action_add('options_action')
def _create_options_action(parent):
    action = QtGui.QAction(icontheme.lookup('preferences-desktop'), _("&Options…"), parent)
    action.setMenuRole(QtGui.QAction.MenuRole.PreferencesRole)
    action.triggered.connect(parent.show_options)
    return action


@action_add('show_script_editor_action')
def _create_show_script_editor_action(parent):
    action = QtGui.QAction(_("Open &file naming script editor…"))
    action.setShortcut(QtGui.QKeySequence(_("Ctrl+Shift+S")))
    action.triggered.connect(parent.open_file_naming_script_editor)
    return action


@action_add('cut_action')
def _create_cut_action(parent):
    action = QtGui.QAction(icontheme.lookup('edit-cut', icontheme.ICON_SIZE_MENU), _("&Cut"), parent)
    action.setShortcut(QtGui.QKeySequence.StandardKey.Cut)
    action.setEnabled(False)
    action.triggered.connect(parent.cut)
    return action


@action_add('paste_action')
def _create_paste_action(parent):
    action = QtGui.QAction(icontheme.lookup('edit-paste', icontheme.ICON_SIZE_MENU), _("&Paste"), parent)
    action.setShortcut(QtGui.QKeySequence.StandardKey.Paste)
    action.setEnabled(False)
    action.triggered.connect(parent.paste)
    return action


@action_add('help_action')
def _create_help_action(parent):
    action = QtGui.QAction(_("&Help…"), parent)
    action.setShortcut(QtGui.QKeySequence.StandardKey.HelpContents)
    action.triggered.connect(parent.show_help)
    return action


@action_add('about_action')
def _create_about_action(parent):
    action = QtGui.QAction(_("&About…"), parent)
    action.setMenuRole(QtGui.QAction.MenuRole.AboutRole)
    action.triggered.connect(parent.show_about)
    return action


@action_add('donate_action')
def _create_donate_action(parent):
    action = QtGui.QAction(_("&Donate…"), parent)
    action.triggered.connect(parent.open_donation_page)
    return action


@action_add('report_bug_action')
def _create_report_bug_action(parent):
    action = QtGui.QAction(_("&Report a Bug…"), parent)
    action.triggered.connect(parent.open_bug_report)
    return action


@action_add('support_forum_action')
def _create_support_forum_action(parent):
    action = QtGui.QAction(_("&Support Forum…"), parent)
    action.triggered.connect(parent.open_support_forum)
    return action


@action_add('add_files_action')
def _create_add_files_action(parent):
    action = QtGui.QAction(icontheme.lookup('document-open'), _("&Add Files…"), parent)
    action.setStatusTip(_("Add files to the tagger"))
    # TR: Keyboard shortcut for "Add Files…"
    action.setShortcut(QtGui.QKeySequence.StandardKey.Open)
    action.triggered.connect(parent.add_files)
    return action


@action_add('add_directory_action')
def _create_add_directory_action(parent):
    action = QtGui.QAction(icontheme.lookup('folder'), _("Add Fold&er…"), parent)
    action.setStatusTip(_("Add a folder to the tagger"))
    # TR: Keyboard shortcut for "Add Directory…"
    action.setShortcut(QtGui.QKeySequence(_("Ctrl+E")))
    action.triggered.connect(parent.add_directory)
    return action


@action_add('close_window_action')
def _create_close_window_action(parent):
    if parent.show_close_window:
        action = QtGui.QAction(_("Close Window"), parent)
        action.setShortcut(QtGui.QKeySequence(_("Ctrl+W")))
        action.triggered.connect(parent.close_active_window)
    else:
        action = None
    return action


@action_add('save_action')
def _create_save_action(parent):
    action = QtGui.QAction(icontheme.lookup('document-save'), _("&Save"), parent)
    action.setStatusTip(_("Save selected files"))
    # TR: Keyboard shortcut for "Save"
    action.setShortcut(QtGui.QKeySequence.StandardKey.Save)
    action.setEnabled(False)
    action.triggered.connect(parent.save)
    return action


@action_add('submit_acoustid_action')
def _create_submit_acoustid_action(parent):
    action = QtGui.QAction(icontheme.lookup('acoustid-fingerprinter'), _("S&ubmit AcoustIDs"), parent)
    action.setStatusTip(_("Submit acoustic fingerprints"))
    action.setEnabled(False)
    action.triggered.connect(parent._on_submit_acoustid)
    return action


@action_add('exit_action')
def _create_exit_action(parent):
    action = QtGui.QAction(_("E&xit"), parent)
    action.setMenuRole(QtGui.QAction.MenuRole.QuitRole)
    # TR: Keyboard shortcut for "Exit"
    action.setShortcut(QtGui.QKeySequence(_("Ctrl+Q")))
    action.triggered.connect(parent.close)
    return action


@action_add('remove_action')
def _create_remove_action(parent):
    action = QtGui.QAction(icontheme.lookup('list-remove'), _("&Remove"), parent)
    action.setStatusTip(_("Remove selected files/albums"))
    action.setEnabled(False)
    action.triggered.connect(parent.remove)
    return action


@action_add('browser_lookup_action')
def _create_browser_lookup_action(parent):
    action = QtGui.QAction(icontheme.lookup('lookup-musicbrainz'), _("Lookup in &Browser"), parent)
    action.setStatusTip(_("Lookup selected item on MusicBrainz website"))
    action.setEnabled(False)
    # TR: Keyboard shortcut for "Lookup in Browser"
    action.setShortcut(QtGui.QKeySequence(_("Ctrl+Shift+L")))
    action.triggered.connect(parent.browser_lookup)
    return action


@action_add('submit_cluster_action')
def _create_submit_cluster_action(parent):
    if addrelease.is_available():
        action = QtGui.QAction(_("Submit cluster as release…"), parent)
        action.setStatusTip(_("Submit cluster as a new release to MusicBrainz"))
        action.setEnabled(False)
        action.triggered.connect(parent.submit_cluster)
    else:
        action = None
    return action


@action_add('submit_file_as_recording_action')
def _create_submit_file_as_recording_action(parent):
    if addrelease.is_available():
        action = QtGui.QAction(_("Submit file as standalone recording…"), parent)
        action.setStatusTip(_("Submit file as a new recording to MusicBrainz"))
        action.setEnabled(False)
        action.triggered.connect(parent.submit_file)
    else:
        action = None
    return action


@action_add('submit_file_as_release_action')
def _create_submit_file_as_release_action(parent):
    if addrelease.is_available():
        action = QtGui.QAction(_("Submit file as release…"), parent)
        action.setStatusTip(_("Submit file as a new release to MusicBrainz"))
        action.setEnabled(False)
        action.triggered.connect(partial(parent.submit_file, as_release=True))
    else:
        action = None
    return action


@action_add('similar_items_search_action')
def _create_similar_items_search_action(parent):
    action = QtGui.QAction(icontheme.lookup('system-search'), _("Search for similar items…"), parent)
    action.setIconText(_("Similar items"))
    action.setStatusTip(_("View similar releases or recordings and optionally choose a different one"))
    action.setEnabled(False)
    action.setShortcut(QtGui.QKeySequence(_("Ctrl+T")))
    action.triggered.connect(parent.show_similar_items_search)
    return action


@action_add('album_search_action')
def _create_album_search_action(parent):
    action = QtGui.QAction(icontheme.lookup('system-search'), _("Search for similar albums…"), parent)
    action.setStatusTip(_("View similar releases and optionally choose a different release"))
    action.setEnabled(False)
    action.setShortcut(QtGui.QKeySequence(_("Ctrl+T")))
    action.triggered.connect(parent.show_more_albums)
    return action


@action_add('track_search_action')
def _create_track_search_action(parent):
    action = QtGui.QAction(icontheme.lookup('system-search'), _("Search for similar tracks…"), parent)
    action.setStatusTip(_("View similar tracks and optionally choose a different release"))
    action.setEnabled(False)
    action.setShortcut(QtGui.QKeySequence(_("Ctrl+T")))
    action.triggered.connect(parent.show_more_tracks)
    return action


@action_add('album_other_versions_action')
def _create_album_other_versions_action(parent):
    action = QtGui.QAction(_("Show &other album versions…"), parent)
    action.setShortcut(QtGui.QKeySequence(_("Ctrl+Shift+O")))
    action.triggered.connect(parent.show_album_other_versions)
    return action


@action_add('show_file_browser_action')
def _create_show_file_browser_action(parent):
    config = get_config()
    action = QtGui.QAction(_("File &Browser"), parent)
    action.setCheckable(True)
    if config.persist['view_file_browser']:
        action.setChecked(True)
    action.setShortcut(QtGui.QKeySequence(_("Ctrl+B")))
    action.triggered.connect(parent.show_file_browser)
    return action


@action_add('show_metadata_view_action')
def _create_show_metadata_view_action(parent):
    config = get_config()
    action = QtGui.QAction(_("&Metadata"), parent)
    action.setCheckable(True)
    if config.persist['view_metadata_view']:
        action.setChecked(True)
    action.setShortcut(QtGui.QKeySequence(_("Ctrl+Shift+M")))
    action.triggered.connect(parent.show_metadata_view)
    return action


@action_add('show_cover_art_action')
def _create_show_cover_art_action(parent):
    config = get_config()
    action = QtGui.QAction(_("&Cover Art"), parent)
    action.setCheckable(True)
    if config.persist['view_cover_art']:
        action.setChecked(True)
    action.setEnabled(config.persist['view_metadata_view'])
    action.triggered.connect(parent.show_cover_art)
    return action


@action_add('show_toolbar_action')
def _create_show_toolbar_action(parent):
    config = get_config()
    action = QtGui.QAction(_("&Actions"), parent)
    action.setCheckable(True)
    if config.persist['view_toolbar']:
        action.setChecked(True)
    action.triggered.connect(parent.show_toolbar)
    return action


@action_add('search_action')
def _create_search_action(parent):
    action = QtGui.QAction(icontheme.lookup('system-search'), _("Search"), parent)
    action.setEnabled(False)
    action.triggered.connect(parent.search)
    return action


@action_add('cd_lookup_action')
def _create_cd_lookup_action(parent):
    action = QtGui.QAction(icontheme.lookup('media-optical'), _("Lookup &CD…"), parent)
    action.setStatusTip(_("Lookup the details of the CD in your drive"))
    # TR: Keyboard shortcut for "Lookup CD"
    action.setShortcut(QtGui.QKeySequence(_("Ctrl+K")))
    action.triggered.connect(parent.tagger.lookup_cd)
    return action


@action_add('analyze_action')
def _create_analyze_action(parent):
    action = QtGui.QAction(icontheme.lookup('picard-analyze'), _("&Scan"), parent)
    action.setStatusTip(_("Use AcoustID audio fingerprint to identify the files by the actual music, even if they have no metadata"))
    action.setEnabled(False)
    action.setToolTip(_("Identify the file using its AcoustID audio fingerprint"))
    # TR: Keyboard shortcut for "Analyze"
    action.setShortcut(QtGui.QKeySequence(_("Ctrl+Y")))
    action.triggered.connect(parent.analyze)
    return action


@action_add('generate_fingerprints_action')
def _create_generate_fingerprints_action(parent):
    action = QtGui.QAction(icontheme.lookup('fingerprint'), _("&Generate AcoustID Fingerprints"), parent)
    action.setIconText(_("Generate Fingerprints"))
    action.setStatusTip(_("Generate the AcoustID audio fingerprints for the selected files without doing a lookup"))
    action.setEnabled(False)
    action.setToolTip(_("Generate the AcoustID audio fingerprints for the selected files"))
    action.setShortcut(QtGui.QKeySequence(_("Ctrl+Shift+Y")))
    action.triggered.connect(parent.generate_fingerprints)
    return action


@action_add('cluster_action')
def _create_cluster_action(parent):
    action = QtGui.QAction(icontheme.lookup('picard-cluster'), _("Cl&uster"), parent)
    action.setStatusTip(_("Cluster files into album clusters"))
    action.setEnabled(False)
    # TR: Keyboard shortcut for "Cluster"
    action.setShortcut(QtGui.QKeySequence(_("Ctrl+U")))
    action.triggered.connect(parent.cluster)
    return action


@action_add('autotag_action')
def _create_autotag_action(parent):
    action = QtGui.QAction(icontheme.lookup('picard-auto-tag'), _("&Lookup"), parent)
    tip = _("Lookup selected items in MusicBrainz")
    action.setToolTip(tip)
    action.setStatusTip(tip)
    action.setEnabled(False)
    # TR: Keyboard shortcut for "Lookup"
    action.setShortcut(QtGui.QKeySequence(_("Ctrl+L")))
    action.triggered.connect(parent.autotag)
    return action


@action_add('view_info_action')
def _create_view_info_action(parent):
    action = QtGui.QAction(icontheme.lookup('picard-edit-tags'), _("&Info…"), parent)
    action.setEnabled(False)
    # TR: Keyboard shortcut for "Info"
    action.setShortcut(QtGui.QKeySequence(_("Ctrl+I")))
    action.triggered.connect(parent.view_info)
    return action


@action_add('refresh_action')
def _create_refresh_action(parent):
    action = QtGui.QAction(icontheme.lookup('view-refresh', icontheme.ICON_SIZE_MENU), _("&Refresh"), parent)
    action.setShortcut(QtGui.QKeySequence(_("Ctrl+R")))
    action.triggered.connect(parent.refresh)
    return action


@action_add('enable_renaming_action')
def _create_enable_renaming_action(parent):
    config = get_config()
    action = QtGui.QAction(_("&Rename Files"), parent)
    action.setCheckable(True)
    action.setChecked(config.setting['rename_files'])
    action.triggered.connect(parent.toggle_rename_files)
    return action


@action_add('enable_moving_action')
def _create_enable_moving_action(parent):
    config = get_config()
    action = QtGui.QAction(_("&Move Files"), parent)
    action.setCheckable(True)
    action.setChecked(config.setting['move_files'])
    action.triggered.connect(parent.toggle_move_files)
    return action


@action_add('enable_tag_saving_action')
def _create_enable_tag_saving_action(parent):
    config = get_config()
    action = QtGui.QAction(_("Save &Tags"), parent)
    action.setCheckable(True)
    action.setChecked(not config.setting['dont_write_tags'])
    action.triggered.connect(parent.toggle_tag_saving)
    return action


@action_add('tags_from_filenames_action')
def _create_tags_from_filenames_action(parent):
    action = QtGui.QAction(icontheme.lookup('picard-tags-from-filename'), _("Tags From &File Names…"), parent)
    action.setIconText(_("Parse File Names…"))
    action.setToolTip(_("Set tags based on the file names"))
    action.setShortcut(QtGui.QKeySequence(_("Ctrl+Shift+T")))
    action.setEnabled(False)
    action.triggered.connect(parent.open_tags_from_filenames)
    return action


@action_add('open_collection_in_browser_action')
def _create_open_collection_in_browser_action(parent):
    config = get_config()
    action = QtGui.QAction(_("&Open My Collections in Browser"), parent)
    action.setEnabled(config.setting['username'] != '')
    action.triggered.connect(parent.open_collection_in_browser)
    return action


@action_add('view_log_action')
def _create_view_log_action(parent):
    action = QtGui.QAction(_("View &Error/Debug Log"), parent)
    # TR: Keyboard shortcut for "View Error/Debug Log"
    action.setShortcut(QtGui.QKeySequence(_("Ctrl+G")))
    action.triggered.connect(parent.show_log)
    return action


@action_add('view_history_action')
def _create_view_history_action(parent):
    action = QtGui.QAction(_("View Activity &History"), parent)
    # TR: Keyboard shortcut for "View Activity History"
    # On macOS ⌘+H is a system shortcut to hide the window. Use ⌘+Shift+H instead.
    action.setShortcut(QtGui.QKeySequence(_("Ctrl+Shift+H") if IS_MACOS else _("Ctrl+H")))
    action.triggered.connect(parent.show_history)
    return action


@action_add('play_file_action')
def _create_play_file_action(parent):
    action = QtGui.QAction(icontheme.lookup('play-music'), _("Open in &Player"), parent)
    action.setStatusTip(_("Play the file in your default media player"))
    action.setEnabled(False)
    action.triggered.connect(parent.play_file)
    return action


@action_add('open_folder_action')
def _create_open_folder_action(parent):
    action = QtGui.QAction(icontheme.lookup('folder', icontheme.ICON_SIZE_MENU), _("Open Containing &Folder"), parent)
    action.setStatusTip(_("Open the containing folder in your file explorer"))
    action.setEnabled(False)
    action.triggered.connect(parent.open_folder)
    return action


@action_add('check_update_action')
def _create_check_update_action(parent):
    if parent.tagger.autoupdate_enabled:
        action = QtGui.QAction(_("&Check for Update…"), parent)
        action.setMenuRole(QtGui.QAction.MenuRole.ApplicationSpecificRole)
        action.triggered.connect(parent.do_update_check)
    else:
        action = None
    return action
