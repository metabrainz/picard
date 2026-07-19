# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2013-2014 Michael Wiencek
# Copyright (C) 2013-2016, 2018-2026 Laurent Monin
# Copyright (C) 2014, 2017 Lukáš Lalinský
# Copyright (C) 2014, 2018-2026 Philipp Wolfer
# Copyright (C) 2015 Ohm Patel
# Copyright (C) 2016 Suhas
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2021 Gabriel Ferreira
# Copyright (C) 2021, 2023 Bob Swift
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


"""Config upgrade hook functions.

Config upgrade hook functions.

All hooks are registered via @upgrade_settings or @upgrade_config decorators.
See the comment block below for instructions on adding new hooks.
"""

import os
import re

from PyQt6 import QtWidgets

from picard import log
from picard.config import (
    BoolOption,
    IntOption,
    ListOption,
    TextOption,
)
from picard.config_upgrade import (
    get_option_value,
    remove_option,
    rename_option,
    temp_option,
    upgrade_config,
    upgrade_option_value,
    upgrade_settings,
    write_option,
)
from picard.const.defaults import (
    DEFAULT_FILE_NAMING_FORMAT,
    DEFAULT_REPLACEMENT,
    DEFAULT_SCRIPT_NAME,
)
from picard.const.sys import IS_FROZEN
from picard.i18n import (
    gettext as _,
    gettext_constants,
)
from picard.options import StandardizeArtistNames
from picard.util import unique_numbered_title


# TO ADD AN UPGRADE HOOK:
# ----------------------
#
# Use one of two decorators:
#
#   @upgrade_settings('x.y.z')  — for settings transforms (renames, value changes)
#   @upgrade_config('x.y.z')    — for non-settings operations (persist, UI state)
#
# @upgrade_settings functions receive a `settings` argument (dict or ConfigSection).
# They automatically run on base config + all profile overrides + imported profiles.
#
# @upgrade_config functions receive the full `config` object. They do NOT run on
# profiles or imported data. Only use for persist, allKeys(), interactive dialogs.
#
# Multiple functions can share the same version. All decorator types share a
# single registry: execution order follows source file order regardless of type.
# This lets you control sequencing when a settings change and a config change
# at the same version depend on each other.
#
# Function names are descriptive (no version encoding). The version is in the
# decorator argument only.
#
# Describe changes using a docstring — it is logged when the hook is executed.
#
# After adding a hook:
# 1. Update `PICARD_VERSION` to match the new hook version.
# 2. Add a corresponding test in test/test_config_upgrade_hooks.py, named
#    `test_` + the hook function name (e.g. `test_my_rename`).
#    The `test_all_hooks_have_tests` test will fail if a test is missing.
#
#
# COMMON PATTERNS:
# ---------------
#
# Rename an option (works on both dict and ConfigSection):
#   rename_option(settings, 'old_name', 'new_name', BoolOption, False)
#
# Rename with reversed boolean:
#   rename_option(settings, 'old_name', 'new_name', BoolOption, False, reverse=True)
#
# Value transform:
#   upgrade_option_value(settings, 'name', lambda v: v.lower())
#
# Read old option, write new option, remove old (type change / one→many):
#   value = get_option(settings, 'old_name', BoolOption, False)
#   write_option(settings, 'new_name', new_value)
#   remove_option(settings, 'old_name')
#
# Remove an obsolete option:
#   remove_option(settings, 'old_name')
#
# Read and remove a legacy option in @upgrade_config (QSettings deserialization):
#   with temp_option(TextOption, 'setting', 'old_name', '') as old_opt:
#       value = config.setting.value(old_opt)
#   config.setting.remove('old_name')


@upgrade_config('1.0.0final0')
def merge_va_file_naming(config, interactive=True, merge=True):
    """In version 1.0, the file naming formats for single and various artist releases were merged."""
    _s = config.setting

    def remove_va_file_naming_format(merge=True):
        if merge:
            with temp_option(TextOption, 'setting', 'va_file_naming_format', '') as old_opt:
                _s['file_naming_format'] = (
                    "$if($eq(%%compilation%%,1),\n$noop(Various Artist "
                    "albums)\n%s,\n$noop(Single Artist Albums)\n%s)"
                    % (
                        _s.value(old_opt),
                        _s['file_naming_format'],
                    )
                )
        _s.remove('va_file_naming_format')
        _s.remove('use_va_format')

    if 'va_file_naming_format' in _s and 'use_va_format' in _s:
        with temp_option(BoolOption, 'setting', 'use_va_format', False) as old_opt:
            old_value_use_va_format = _s.value(old_opt)
        with temp_option(TextOption, 'setting', 'va_file_naming_format', '') as old_opt:
            old_value_va_file_naming_format = _s.value(old_opt)

        if old_value_use_va_format:
            remove_va_file_naming_format()
            if interactive:
                msgbox = QtWidgets.QMessageBox()
                msgbox.information(
                    msgbox,
                    _("Various Artists file naming scheme removal"),
                    _(
                        "The separate file naming scheme for various artists "
                        "albums has been removed in this version of Picard.\n"
                        "Your file naming scheme has automatically been "
                        "merged with that of single artist albums."
                    ),
                    QtWidgets.QMessageBox.StandardButton.Ok,
                )

        elif (
            old_value_va_file_naming_format != r"$if2(%albumartist%,%artist%)/%album%/$if($gt(%totaldis"
            "cs%,1),%discnumber%-,)$num(%tracknumber%,2) %artist% - "
            "%title%"
        ):
            if interactive:
                msgbox = QtWidgets.QMessageBox()
                msgbox.setWindowTitle(_("Various Artists file naming scheme removal"))
                msgbox.setText(
                    _(
                        "The separate file naming scheme for various artists "
                        "albums has been removed in this version of Picard.\n"
                        "You currently do not use this option, but have a "
                        "separate file naming scheme defined.\n"
                        "Do you want to remove it or merge it with your file "
                        "naming scheme for single artist albums?"
                    )
                )
                msgbox.setIcon(QtWidgets.QMessageBox.Icon.Question)
                merge_button = msgbox.addButton(_("Merge"), QtWidgets.QMessageBox.ButtonRole.AcceptRole)
                msgbox.addButton(_("Remove"), QtWidgets.QMessageBox.ButtonRole.DestructiveRole)
                msgbox.exec()
                merge = msgbox.clickedButton() == merge_button
            remove_va_file_naming_format(merge=merge)
        else:
            # default format, disabled
            remove_va_file_naming_format(merge=False)


@upgrade_settings('1.3.0dev1')
def rename_windows_compatible_filenames(settings):
    """Option "windows_compatible_filenames" was renamed "windows_compatibility" (PICARD-110)."""
    rename_option(settings, 'windows_compatible_filenames', 'windows_compatibility', BoolOption, True)


@upgrade_config('1.3.0dev2')
def convert_preserved_tags_separator(config):
    """Option "preserved_tags" is now using comma instead of spaces as tag separator (PICARD-536)"""
    _s = config.setting
    opt = 'preserved_tags'
    if opt in _s and isinstance(_s[opt], str):
        _s[opt] = re.sub(r"\s+", ",", _s[opt].strip())


@upgrade_config('1.3.0dev3')
def convert_options_to_lists(config):
    """Options were made to support lists (solving PICARD-144 and others)"""
    _s = config.setting
    option_separators = {
        'preferred_release_countries': '  ',
        'preferred_release_formats': '  ',
        'enabled_plugins': None,
        'caa_image_types': None,
        'metadata_box_sizes': None,
    }
    for opt, sep in option_separators.items():
        if opt in _s:
            try:
                _s[opt] = _s.raw_value(opt, qtype='QString').split(sep)
            except AttributeError:
                pass


@upgrade_config('1.3.0dev4')
def convert_release_type_scores(config):
    """Option "release_type_scores" is now a list of tuples"""
    _s = config.setting

    def load_release_type_scores(setting):
        scores = []
        values = setting.split()
        for i in range(0, len(values), 2):
            try:
                score = float(values[i + 1])
            except IndexError:
                score = 0.0
            scores.append((values[i], score))
        return scores

    opt = 'release_type_scores'
    if opt in _s:
        try:
            _s[opt] = load_release_type_scores(_s.raw_value(opt, qtype='QString'))
        except AttributeError:
            pass


@upgrade_config('1.4.0dev2')
def remove_username_password(config):
    """Options "username" and "password" are removed and
    replaced with OAuth tokens
    """

    _s = config.setting
    opts = ['username', 'password']
    for opt in opts:
        _s.remove(opt)


@upgrade_config('1.4.0dev3')
def convert_ca_providers_to_tuples(config):
    """Cover art providers options were moved to a list of tuples"""
    _s = config.setting
    map_ca_provider = [
        ('ca_provider_use_amazon', 'Amazon'),
        ('ca_provider_use_caa', 'Cover Art Archive'),
        ('ca_provider_use_whitelist', 'Whitelist'),
        ('ca_provider_use_caa_release_group_fallback', 'CaaReleaseGroup'),
    ]

    newopts = []
    for old, new in map_ca_provider:
        if old in _s:
            with temp_option(BoolOption, 'setting', old, True) as old_opt:
                newopts.append((new, _s.value(old_opt)))
    _s['ca_providers'] = newopts


OLD_DEFAULT_FILE_NAMING_FORMAT_v1_3 = (
    "$if2(%albumartist%,%artist%)/"
    "$if($ne(%albumartist%,),%album%/)"
    "$if($gt(%totaldiscs%,1),%discnumber%-,)"
    "$if($ne(%albumartist%,),$num(%tracknumber%,2) ,)"
    "$if(%_multiartist%,%artist% - ,)"
    "%title%"
)


@upgrade_config('1.4.0dev4')
def update_default_file_naming_format_v1_3(config):
    """Adds trailing comma to default file names for scripts"""
    _s = config.setting
    if _s['file_naming_format'] == OLD_DEFAULT_FILE_NAMING_FORMAT_v1_3:
        _s['file_naming_format'] = DEFAULT_FILE_NAMING_FORMAT


@upgrade_config('1.4.0dev5')
def migrate_to_ini_config(config):
    """Using Picard.ini configuration file on all platforms"""
    # this is done in Config.__init__()


@upgrade_config('1.4.0dev6')
def convert_tagger_scripts_to_list(config):
    """Adds support for multiple and selective tagger scripts"""
    _s = config.setting
    old_enabled_option = 'enable_tagger_script'
    old_script_text_option = 'tagger_script'
    list_of_scripts = []
    if old_enabled_option in _s:
        with temp_option(BoolOption, 'setting', old_enabled_option, False) as old_opt:
            _s['enable_tagger_scripts'] = _s.value(old_opt)
    if old_script_text_option in _s:
        with temp_option(TextOption, 'setting', old_script_text_option, "") as old_opt:
            old_script_text = _s.value(old_opt)
        if old_script_text:
            old_script = (
                0,
                unique_numbered_title(gettext_constants(DEFAULT_SCRIPT_NAME), list_of_scripts),
                _s['enable_tagger_scripts'],
                old_script_text,
            )
            list_of_scripts.append(old_script)
    _s['list_of_scripts'] = list_of_scripts
    _s.remove(old_enabled_option)
    _s.remove(old_script_text_option)


@upgrade_settings('1.4.0dev7')
def rename_save_only_front_images_to_tags(settings):
    """Option "save_only_front_images_to_tags" was renamed to "embed_only_one_front_image"."""
    rename_option(settings, 'save_only_front_images_to_tags', 'embed_only_one_front_image', BoolOption, True)


@upgrade_config('2.0.0dev3')
def convert_caa_image_size(config):
    """Option "caa_image_size" value has different meaning."""
    _s = config.setting
    opt = 'caa_image_size'
    if opt in _s:
        # caa_image_size option was storing index of a combobox item as size
        # therefore it depends on items order and/or number, which is bad
        # To keep the option as is, values >= 250 are stored for thumbnails and -1 is
        # used for full size.
        _CAA_SIZE_COMPAT = {
            0: 250,
            1: 500,
            2: -1,
        }
        value = _s[opt]
        if value in _CAA_SIZE_COMPAT:
            _s[opt] = _CAA_SIZE_COMPAT[value]


@upgrade_settings('2.1.0dev1')
def upgrade_genre_options(settings):
    """Upgrade genre related options"""
    if 'folksonomy_tags' in settings:
        value = get_option_value(settings, 'folksonomy_tags', BoolOption, False)
        if value:
            write_option(settings, 'use_genres', True)
    rename_option(settings, 'max_tags', 'max_genres', IntOption, 5)
    rename_option(settings, 'min_tag_usage', 'min_genre_usage', IntOption, 90)
    rename_option(settings, 'ignore_tags', 'ignore_genres', TextOption, '')
    rename_option(settings, 'join_tags', 'join_genres', TextOption, '')
    rename_option(settings, 'only_my_tags', 'only_my_genres', BoolOption, False)
    rename_option(settings, 'artists_tags', 'artists_genres', BoolOption, False)


@upgrade_config('2.2.0dev3')
def convert_ignore_genres_to_filter(config):
    """Option ignore_genres was replaced by option genres_filter"""
    _s = config.setting
    old_opt = 'ignore_genres'
    if old_opt in _s:
        if _s[old_opt]:
            new_opt = 'genres_filter'
            tags = ['-' + e.strip().lower() for e in _s[old_opt].split(',')]
            _s[new_opt] = '\n'.join(tags)
        _s.remove(old_opt)


OLD_DEFAULT_FILE_NAMING_FORMAT_v2_1 = (
    "$if2(%albumartist%,%artist%)/"
    "$if($ne(%albumartist%,),%album%/,)"
    "$if($gt(%totaldiscs%,1),%discnumber%-,)"
    "$if($ne(%albumartist%,),$num(%tracknumber%,2) ,)"
    "$if(%_multiartist%,%artist% - ,)"
    "%title%"
)


@upgrade_config('2.2.0dev4')
def update_default_file_naming_format_v2_1(config):
    """Improved default file naming script"""
    _s = config.setting
    if _s['file_naming_format'] == OLD_DEFAULT_FILE_NAMING_FORMAT_v2_1:
        _s['file_naming_format'] = DEFAULT_FILE_NAMING_FORMAT


@upgrade_config('2.4.0beta3')
def convert_preserved_tags_to_list(config):
    """Convert preserved tags to list"""
    _s = config.setting
    opt = 'preserved_tags'
    value = _s.raw_value(opt, qtype='QString')
    if not isinstance(value, list):
        _s[opt] = [t.strip() for t in value.split(',')]


@upgrade_settings('2.5.0dev1')
def rename_whitelist_ca_provider(settings):
    """Rename whitelist cover art provider"""
    upgrade_option_value(
        settings,
        'ca_providers',
        lambda providers: [('UrlRelationships' if n == 'Whitelist' else n, s) for n, s in providers],
    )


@upgrade_config('2.5.0dev2')
def reset_main_splitter_states(config):
    """Reset main view splitter states"""
    config.persist['splitter_state'] = b''
    config.persist['bottom_splitter_state'] = b''


@upgrade_config('2.6.0dev1')
def clear_fpcalc_path(config):
    """Unset fpcalc path in environments where auto detection is preferred."""
    if IS_FROZEN or config.setting['acoustid_fpcalc'].startswith('/snap/picard/'):
        config.setting['acoustid_fpcalc'] = ''


@upgrade_settings('2.6.0beta2')
def rename_caa_image_options(settings):
    """Rename caa_image_type_as_filename and caa_save_single_front_image options"""
    rename_option(settings, 'caa_image_type_as_filename', 'image_type_as_filename', BoolOption, False)
    rename_option(settings, 'caa_save_single_front_image', 'save_only_one_front_image', BoolOption, False)


@upgrade_config('2.6.0beta3')
def convert_use_system_theme(config):
    """Replace use_system_theme with ui_theme options"""
    _s = config.setting
    with temp_option(BoolOption, 'setting', 'use_system_theme', False) as old_opt:
        if _s.value(old_opt):
            _s['ui_theme'] = 'system'
    _s.remove('use_system_theme')


@upgrade_config('2.7.0dev2')
def restructure_splitter_persist(config):
    """Replace manually set persistent splitter settings with automated system."""

    def upgrade_persisted_splitter(new_persist_key, key_map):
        _p = config.persist
        splitter_dict = {}
        for old_splitter_key, new_splitter_key in key_map:
            if old_splitter_key in _p:
                if v := _p.raw_value(old_splitter_key):
                    splitter_dict[new_splitter_key] = v
                _p.remove(old_splitter_key)
        _p[new_persist_key] = splitter_dict

    # MainWindow splitters
    upgrade_persisted_splitter(
        new_persist_key='splitters_MainWindow',
        key_map=[
            ('bottom_splitter_state', 'main_window_bottom_splitter'),
            ('splitter_state', 'main_panel_splitter'),
        ],
    )

    # ScriptEditorDialog splitters
    upgrade_persisted_splitter(
        new_persist_key='splitters_ScriptEditorDialog',
        key_map=[
            ('script_editor_splitter_samples', 'splitter_between_editor_and_examples'),
            ('script_editor_splitter_samples_before_after', 'splitter_between_before_and_after'),
            ('script_editor_splitter_documentation', 'splitter_between_editor_and_documentation'),
        ],
    )

    # OptionsDialog splitters
    upgrade_persisted_splitter(
        new_persist_key='splitters_OptionsDialog',
        key_map=[
            ('options_splitter', 'dialog_splitter'),
            ('scripting_splitter', 'scripting_options_splitter'),
        ],
    )


@upgrade_config('2.7.0dev3')
def convert_naming_scripts_to_dict(config):
    """Save file naming scripts to dictionary."""
    # Avoid init-order issue: config_upgrade runs during config init before full module graph is ready
    from picard.script import get_file_naming_script_presets
    from picard.script.serializer import (
        FileNamingScriptInfo,
        ScriptSerializerFromFileError,
    )

    scripts = {}
    for item in config.setting.raw_value('file_naming_scripts') or []:
        try:
            script_item = FileNamingScriptInfo().create_from_yaml(item, create_new_id=False)
            scripts[script_item['id']] = script_item.to_dict()
        except ScriptSerializerFromFileError:
            log.error("Error converting file naming script")
    script_list = set(scripts.keys()) | set(map(lambda item: item['id'], get_file_naming_script_presets()))
    if config.setting['selected_file_naming_script_id'] not in script_list:
        with temp_option(TextOption, 'setting', 'file_naming_format', '') as old_opt:
            script_item = FileNamingScriptInfo(
                script=config.setting.value(old_opt),
                title=_("Primary file naming script"),
                readonly=False,
                deletable=True,
            )
        scripts[script_item['id']] = script_item.to_dict()
        config.setting['selected_file_naming_script_id'] = script_item['id']
    config.setting['file_renaming_scripts'] = scripts
    config.setting.remove('file_naming_scripts')
    config.setting.remove('file_naming_format')


@upgrade_config('2.7.0dev4')
def convert_script_exception_to_list(config):
    """Replace artist_script_exception with artist_script_exceptions"""
    _s = config.setting
    with temp_option(TextOption, 'setting', 'artist_script_exception', '') as old_opt:
        if script := _s.value(old_opt):
            _s['artist_script_exceptions'] = [script]
    _s.remove('artist_script_exception')
    with temp_option(TextOption, 'setting', 'artist_locale', '') as old_opt:
        if locale := _s.value(old_opt):
            _s['artist_locales'] = [locale]
    _s.remove('artist_locale')


@upgrade_config('2.7.0dev5')
def convert_script_exceptions_with_weighting(config):
    """Replace artist_script_exceptions with script_exceptions and remove artist_script_exception_weighting"""
    _s = config.setting
    with temp_option(IntOption, 'setting', 'artist_script_exception_weighting', 0) as old_opt:
        weighting = _s.value(old_opt)
    if 'artist_script_exceptions' in _s:
        artist_script_exceptions = _s.raw_value('artist_script_exceptions') or []
    else:
        artist_script_exceptions = []
    _s['script_exceptions'] = [(script_exception, weighting) for script_exception in artist_script_exceptions]
    _s.remove('artist_script_exceptions')
    _s.remove('artist_script_exception_weighting')


@upgrade_settings('2.8.0dev2')
def remove_acousticbrainz_from_toolbar(settings):
    """Remove AcousticBrainz settings from options"""

    def _remove_action(toolbar_layout):
        toolbar_layout.remove('extract_and_submit_acousticbrainz_features_action')
        return toolbar_layout

    try:
        upgrade_option_value(settings, 'toolbar_layout', _remove_action)
    except ValueError:
        pass


@upgrade_config('2.9.0alpha2')
def add_preset_naming_scripts(config):
    """Add preset file naming scripts to editable user scripts dictionary"""
    # Avoid init-order issue: config_upgrade runs during config init before full module graph is ready
    from picard.script import get_file_naming_script_presets

    scripts = config.setting['file_renaming_scripts']
    for item in get_file_naming_script_presets():
        scripts[item['id']] = item.to_dict()
    config.setting['file_renaming_scripts'] = scripts


@upgrade_config('3.0.0dev1')
def clear_qt5_state(config):
    """Clear Qt5 state config"""
    # A lot of persisted data is serialized Qt5 data that is not compatible with Qt6.
    # Keep only the data that is still useful and definitely supported.
    keep_persist = (
        'current_browser_path',
        'current_directory',
        'mediaplayer_playback_rate',
        'mediaplayer_volume',
        'oauth_access_token_expires',
        'oauth_access_token',
        'oauth_refresh_token_scopes',
        'oauth_refresh_token',
        'oauth_username',
        'script_editor_show_documentation',
        'script_editor_tooltips',
        'script_editor_wordwrap',
        'show_changes_first',
        'show_hidden_files',
        'tags_from_filenames_format',
        'view_cover_art',
        'view_file_browser',
        'view_metadata_view',
        'view_toolbar',
    )

    # We need to make sure to load all keys in the config file, not just
    # those for which an initialized Option exists.
    for key in config.allKeys():
        if key.startswith('persist/') and key[8:] not in keep_persist:
            config.remove(key)


@upgrade_config('3.0.0dev2')
def reset_options_dialog_splitters(config):
    """Reset option dialog splitter states"""
    config.persist['splitters_OptionsDialog'] = b''


@upgrade_settings('3.0.0dev3')
def rename_toolbar_multiselect(settings):
    """Option "toolbar_multiselect" was renamed to "allow_multi_dirs_selection"."""
    rename_option(settings, 'toolbar_multiselect', 'allow_multi_dirs_selection', BoolOption, False)


@upgrade_config('3.0.0dev4')
def reset_locked_header_states(config):
    """Reset "file/album_view_header_state" if there were saved while locked."""
    if config.persist['album_view_header_locked']:
        config.persist.remove('album_view_header_state')
    if config.persist['file_view_header_locked']:
        config.persist.remove('file_view_header_state')


@upgrade_settings('3.0.0dev5')
def sanitize_replace_dir_separator(settings):
    """Ensure "replace_dir_separator" contains no directory separator"""

    def _sanitize(value):
        value = value.replace(os.sep, DEFAULT_REPLACEMENT)
        if os.altsep:
            value = value.replace(os.altsep, DEFAULT_REPLACEMENT)
        return value

    upgrade_option_value(settings, 'replace_dir_separator', _sanitize)


@upgrade_settings('3.0.0dev6')
def copy_standardize_instruments_to_vocals(settings):
    """New independent option "standardize_vocals" should use the value of the old shared option"""
    if 'standardize_instruments' in settings:
        value = get_option_value(settings, 'standardize_instruments', BoolOption, False)
        write_option(settings, 'standardize_vocals', value)


@upgrade_settings('3.0.0dev7')
def change_theme_system_to_default(settings):
    """Change theme option SYSTEM to DEFAULT"""
    # Avoid loading UI modules in headless/CLI contexts
    from picard.ui.theme import UiTheme

    def _fix_theme(value):
        return UiTheme.DEFAULT.value if value == "system" else value

    upgrade_option_value(settings, 'ui_theme', _fix_theme)


@upgrade_settings('3.0.0dev8')
def rename_dont_write_tags(settings):
    """Option "dont_write_tags" was renamed to "enable_tag_saving" (value is reversed)."""
    rename_option(settings, 'dont_write_tags', 'enable_tag_saving', BoolOption, False, reverse=True)


@upgrade_config('3.0.0dev9')
def remove_old_plugin_options(config):
    """Remove obsolete old plugin system options"""
    # Remove old plugin UI state options (unused)
    config.persist.remove('plugins_list_sort_order')
    config.persist.remove('plugins_list_sort_section')
    config.persist.remove('plugins_list_state')

    # Remove old plugin configuration (replaced by plugins3_enabled_plugins)
    config.setting.remove('enabled_plugins')


@upgrade_settings('3.0.0dev10')
def lowercase_cover_art_formats(settings):
    """Update cover art processing format options"""
    for setting_key in ('cover_tags_convert_to_format', 'cover_file_convert_to_format'):
        upgrade_option_value(
            settings,
            setting_key,
            lambda value: value.lower() if isinstance(value, str) else value,
        )


@upgrade_settings('3.0.0a2')
def fix_matchedtracks_in_scripts(settings):
    """Update $matchedtracks() usage in scripts"""

    matched_tracks_regex = re.compile(r'\$matchedtracks\([^)$]+\)')

    def fix_matchedtracks(script):
        return matched_tracks_regex.sub('$matchedtracks()', script)

    def fix_renaming_scripts(scripts):
        for script_item in scripts.values():
            script_item['script'] = fix_matchedtracks(script_item['script'])
        return scripts

    def fix_tagger_scripts(scripts):
        return [(pos, name, enabled, fix_matchedtracks(script)) for pos, name, enabled, script in scripts]

    upgrade_option_value(settings, 'file_renaming_scripts', fix_renaming_scripts)
    upgrade_option_value(settings, 'list_of_scripts', fix_tagger_scripts)


@upgrade_config('3.0.0a3')
def remove_persisted_column_config(config):
    """Remove persisted column configuration"""
    config.persist.remove('album_view_header_state')
    config.persist.remove('file_view_header_state')


@upgrade_settings('3.0.0b2')
def rename_artist_locales(settings):
    """Option "artist_locales" was renamed to "translation_locales"."""
    rename_option(settings, 'artist_locales', 'translation_locales', ListOption, ['en'])


@upgrade_settings('3.0.0b3')
def remove_similarity_thresholds(settings):
    """Replace absolute similarity thresholds with floor + margin.

    Old thresholds were tuned to a specific score distribution and are
    meaningless under the new tiered matching algorithm. Remove them so
    the new defaults (match_min_similarity, match_min_margin) take effect.
    """
    remove_option(settings, 'file_lookup_threshold')
    remove_option(settings, 'cluster_lookup_threshold')


@upgrade_settings('3.0.0b5')
def rename_selected_file_naming_script_id(settings):
    """Option "selected_file_naming_script_id" was renamed to "active_file_naming_script_id"."""
    rename_option(settings, 'selected_file_naming_script_id', 'active_file_naming_script_id', TextOption, '')


@upgrade_settings('3.0.0b5')
def add_quick_menu_items(settings):
    """Add rename_files, move_files, enable_tag_saving to quick_menu_items."""
    new_items = ['rename_files', 'move_files', 'enable_tag_saving']

    def _add_items(items):
        for item in reversed(new_items):
            if item not in items:
                items.insert(0, item)
        return items

    upgrade_option_value(settings, 'quick_menu_items', _add_items)


@upgrade_settings('3.0.0b6')
def convert_standardize_artists(settings):
    """Convert "standardize_artists" to "standardize_artist_names"."""
    if 'standardize_artists' not in settings:
        return
    value = get_option_value(settings, 'standardize_artists', BoolOption, False)
    write_option(
        settings,
        'standardize_artist_names',
        StandardizeArtistNames.ALL if value else StandardizeArtistNames.NONE,
    )
    remove_option(settings, 'standardize_artists')


@upgrade_settings('3.0.0b7')
def remove_rtd_updates_ask(settings):
    """Remove "rtd_updates_ask"."""
    remove_option(settings, 'rtd_updates_ask')


@upgrade_settings('3.0.0b8')
def convert_release_type_scores_to_lists(settings):
    """Convert release_type_scores to preferred/discouraged release type lists.

    Old format: release_type_scores = [('Album', 0.9), ('Single', 0.5), ('Compilation', 0.0)]
    New format:
      preferred_release_types = ['Album']        (score > 0.5, sorted by score desc)
      discouraged_release_types = ['Compilation'] (score < 0.5)
    """
    if 'release_type_scores' not in settings:
        return
    scores = get_option_value(settings, 'release_type_scores', ListOption, [])
    preferred = []
    discouraged = []
    for release_type, score in scores:
        if score < 0.5:
            discouraged.append(release_type)
        elif score > 0.5:
            preferred.append((release_type, score))
    # Sort preferred by score descending (highest priority first)
    preferred.sort(key=lambda x: x[1], reverse=True)
    write_option(settings, 'preferred_release_types', [t for t, _s in preferred])
    write_option(settings, 'discouraged_release_types', discouraged)
