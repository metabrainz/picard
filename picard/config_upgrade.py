# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2013-2014 Michael Wiencek
# Copyright (C) 2013-2016, 2018-2022 Laurent Monin
# Copyright (C) 2014, 2017 Lukáš Lalinský
# Copyright (C) 2014, 2018-2023 Philipp Wolfer
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


import re

from PyQt5 import QtWidgets

from picard import log
from picard.config import (
    BoolOption,
    IntOption,
    ListOption,
    Option,
    TextOption,
)
from picard.const import (
    DEFAULT_FILE_NAMING_FORMAT,
    DEFAULT_SCRIPT_NAME,
)
from picard.const.sys import IS_FROZEN
from picard.util import unique_numbered_title


# TO ADD AN UPGRADE HOOK:
# ----------------------
# add a function here, named after the version you want upgrade to
# ie. upgrade_to_v1_0_0_dev_1() for 1.0.0dev1
# register it in upgrade_config()
# and modify PICARD_VERSION to match it
#


def upgrade_to_v1_0_0_final_0(config, interactive=True, merge=True):
    """In version 1.0, the file naming formats for single and various artist releases were merged.
    """
    _s = config.setting

    def remove_va_file_naming_format(merge=True):
        if merge:
            _s['file_naming_format'] = (
                "$if($eq(%%compilation%%,1),\n$noop(Various Artist "
                "albums)\n%s,\n$noop(Single Artist Albums)\n%s)" % (
                    _s.value('va_file_naming_format', TextOption),
                    _s['file_naming_format']
                ))
        _s.remove('va_file_naming_format')
        _s.remove('use_va_format')

    if 'va_file_naming_format' in _s and 'use_va_format' in _s:

        if _s.value('use_va_format', BoolOption):
            remove_va_file_naming_format()
            if interactive:
                msgbox = QtWidgets.QMessageBox()
                msgbox.information(msgbox,
                    _("Various Artists file naming scheme removal"),
                    _("The separate file naming scheme for various artists "
                        "albums has been removed in this version of Picard.\n"
                        "Your file naming scheme has automatically been "
                        "merged with that of single artist albums."),
                    QtWidgets.QMessageBox.StandardButton.Ok)

        elif (_s.value('va_file_naming_format', TextOption)
              != r"$if2(%albumartist%,%artist%)/%album%/$if($gt(%totaldis"
                 "cs%,1),%discnumber%-,)$num(%tracknumber%,2) %artist% - "
                 "%title%"):
            if interactive:
                msgbox = QtWidgets.QMessageBox()
                msgbox.setWindowTitle(_("Various Artists file naming scheme removal"))
                msgbox.setText(_("The separate file naming scheme for various artists "
                    "albums has been removed in this version of Picard.\n"
                    "You currently do not use this option, but have a "
                    "separate file naming scheme defined.\n"
                    "Do you want to remove it or merge it with your file "
                    "naming scheme for single artist albums?"))
                msgbox.setIcon(QtWidgets.QMessageBox.Icon.Question)
                merge_button = msgbox.addButton(_("Merge"), QtWidgets.QMessageBox.ButtonRole.AcceptRole)
                msgbox.addButton(_("Remove"), QtWidgets.QMessageBox.ButtonRole.DestructiveRole)
                msgbox.exec_()
                merge = msgbox.clickedButton() == merge_button
            remove_va_file_naming_format(merge=merge)
        else:
            # default format, disabled
            remove_va_file_naming_format(merge=False)


def upgrade_to_v1_3_0_dev_1(config):
    """Option "windows_compatible_filenames" was renamed "windows_compatibility" (PICARD-110).
    """
    old_opt = 'windows_compatible_filenames'
    new_opt = 'windows_compatibility'
    rename_option(config, old_opt, new_opt, BoolOption, True)


def upgrade_to_v1_3_0_dev_2(config):
    """Option "preserved_tags" is now using comma instead of spaces as tag separator (PICARD-536)
    """
    _s = config.setting
    opt = 'preserved_tags'
    if opt in _s and isinstance(_s[opt], str):
        _s[opt] = re.sub(r"\s+", ",", _s[opt].strip())


def upgrade_to_v1_3_0_dev_3(config):
    """Options were made to support lists (solving PICARD-144 and others)
    """
    _s = config.setting
    option_separators = {
        'preferred_release_countries': '  ',
        'preferred_release_formats': '  ',
        'enabled_plugins': None,
        'caa_image_types': None,
        'metadata_box_sizes': None,
    }
    for (opt, sep) in option_separators.items():
        if opt in _s:
            try:
                _s[opt] = _s.raw_value(opt, qtype='QString').split(sep)
            except AttributeError:
                pass


def upgrade_to_v1_3_0_dev_4(config):
    """Option "release_type_scores" is now a list of tuples
    """
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


def upgrade_to_v1_4_0_dev_2(config):
    """Options "username" and "password" are removed and
    replaced with OAuth tokens
    """

    _s = config.setting
    opts = ['username', 'password']
    for opt in opts:
        _s.remove(opt)


def upgrade_to_v1_4_0_dev_3(config):
    """Cover art providers options were moved to a list of tuples"""
    _s = config.setting
    map_ca_provider = [
        ('ca_provider_use_amazon', 'Amazon'),
        ('ca_provider_use_caa', 'Cover Art Archive'),
        ('ca_provider_use_whitelist', 'Whitelist'),
        ('ca_provider_use_caa_release_group_fallback', 'CaaReleaseGroup')
    ]

    newopts = []
    for old, new in map_ca_provider:
        if old in _s:
            newopts.append((new, _s.value(old, BoolOption, True)))
    _s['ca_providers'] = newopts


OLD_DEFAULT_FILE_NAMING_FORMAT_v1_3 = "$if2(%albumartist%,%artist%)/" \
    "$if($ne(%albumartist%,),%album%/)" \
    "$if($gt(%totaldiscs%,1),%discnumber%-,)" \
    "$if($ne(%albumartist%,),$num(%tracknumber%,2) ,)" \
    "$if(%_multiartist%,%artist% - ,)" \
    "%title%"


def upgrade_to_v1_4_0_dev_4(config):
    """Adds trailing comma to default file names for scripts"""
    _s = config.setting
    if _s['file_naming_format'] == OLD_DEFAULT_FILE_NAMING_FORMAT_v1_3:
        _s['file_naming_format'] = DEFAULT_FILE_NAMING_FORMAT


def upgrade_to_v1_4_0_dev_5(config):
    """Using Picard.ini configuration file on all platforms"""
    # this is done in Config.__init__()


def upgrade_to_v1_4_0_dev_6(config):
    """Adds support for multiple and selective tagger scripts"""
    _s = config.setting
    old_enabled_option = 'enable_tagger_script'
    old_script_text_option = 'tagger_script'
    list_of_scripts = []
    if old_enabled_option in _s:
        _s['enable_tagger_scripts'] = _s.value(old_enabled_option, BoolOption, False)
    if old_script_text_option in _s:
        old_script_text = _s.value(old_script_text_option, TextOption, "")
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


def upgrade_to_v1_4_0_dev_7(config):
    """Option "save_only_front_images_to_tags" was renamed to "embed_only_one_front_image"."""
    old_opt = 'save_only_front_images_to_tags'
    new_opt = 'embed_only_one_front_image'
    rename_option(config, old_opt, new_opt, BoolOption, True)


def upgrade_to_v2_0_0_dev_3(config):
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


def upgrade_to_v2_1_0_dev_1(config):
    """Upgrade genre related options"""
    _s = config.setting
    if 'folksonomy_tags' in _s and _s['folksonomy_tags']:
        _s['use_genres'] = True
    rename_option(config, 'max_tags',      'max_genres',      IntOption,  5)
    rename_option(config, 'min_tag_usage', 'min_genre_usage', IntOption,  90)
    rename_option(config, 'ignore_tags',   'ignore_genres',   TextOption, '')
    rename_option(config, 'join_tags',     'join_genres',     TextOption, '')
    rename_option(config, 'only_my_tags',  'only_my_genres',  BoolOption, False)
    rename_option(config, 'artists_tags',  'artists_genres',  BoolOption, False)


def upgrade_to_v2_2_0_dev_3(config):
    """Option ignore_genres was replaced by option genres_filter"""
    _s = config.setting
    old_opt = 'ignore_genres'
    if old_opt in _s:
        if _s[old_opt]:
            new_opt = 'genres_filter'
            tags = ['-' + e.strip().lower() for e in _s[old_opt].split(',')]
            _s[new_opt] = '\n'.join(tags)
        _s.remove(old_opt)


OLD_DEFAULT_FILE_NAMING_FORMAT_v2_1 = "$if2(%albumartist%,%artist%)/" \
    "$if($ne(%albumartist%,),%album%/,)" \
    "$if($gt(%totaldiscs%,1),%discnumber%-,)" \
    "$if($ne(%albumartist%,),$num(%tracknumber%,2) ,)" \
    "$if(%_multiartist%,%artist% - ,)" \
    "%title%"


def upgrade_to_v2_2_0_dev_4(config):
    """Improved default file naming script"""
    _s = config.setting
    if _s['file_naming_format'] == OLD_DEFAULT_FILE_NAMING_FORMAT_v2_1:
        _s['file_naming_format'] = DEFAULT_FILE_NAMING_FORMAT


def upgrade_to_v2_4_0_beta_3(config):
    """Convert preserved tags to list"""
    _s = config.setting
    opt = 'preserved_tags'
    value = _s.raw_value(opt, qtype='QString')
    if not isinstance(value, list):
        _s[opt] = [t.strip() for t in value.split(',')]


def upgrade_to_v2_5_0_dev_1(config):
    """Rename whitelist cover art provider"""
    _s = config.setting
    _s['ca_providers'] = [
        ('UrlRelationships' if n == 'Whitelist' else n, s)
        for n, s in _s['ca_providers']
    ]


def upgrade_to_v2_5_0_dev_2(config):
    """Reset main view splitter states"""
    config.persist['splitter_state'] = b''
    config.persist['bottom_splitter_state'] = b''


def upgrade_to_v2_6_0_dev_1(config):
    """Unset fpcalc path in environments where auto detection is preferred."""
    if IS_FROZEN or config.setting['acoustid_fpcalc'].startswith('/snap/picard/'):
        config.setting['acoustid_fpcalc'] = ''


def upgrade_to_v2_6_0_beta_2(config):
    """Rename caa_image_type_as_filename and caa_save_single_front_image options"""
    rename_option(config, 'caa_image_type_as_filename', 'image_type_as_filename', BoolOption, False)
    rename_option(config, 'caa_save_single_front_image', 'save_only_one_front_image', BoolOption, False)


def upgrade_to_v2_6_0_beta_3(config):
    """Replace use_system_theme with ui_theme options"""
    from picard.ui.theme import UiTheme
    _s = config.setting
    TextOption('setting', 'ui_theme', str(UiTheme.DEFAULT))
    if _s['use_system_theme']:
        _s['ui_theme'] = str(UiTheme.SYSTEM)
    _s.remove('use_system_theme')


def upgrade_to_v2_7_0_dev_2(config):
    """Replace manually set persistent splitter settings with automated system.
    """
    def upgrade_persisted_splitter(new_persist_key, key_map):
        _p = config.persist
        splitter_dict = {}
        for (old_splitter_key, new_splitter_key) in key_map:
            if _p.__contains__(old_splitter_key):
                if _p[old_splitter_key] is not None:
                    splitter_dict[new_splitter_key] = bytearray(_p[old_splitter_key])
                _p.remove(old_splitter_key)
        Option('persist', new_persist_key, {})
        _p[new_persist_key] = splitter_dict

    # MainWindow splitters
    upgrade_persisted_splitter(
        new_persist_key='splitters_MainWindow',
        key_map=[
            ('bottom_splitter_state', 'main_window_bottom_splitter'),
            ('splitter_state', 'main_panel_splitter'),
        ]
    )

    # ScriptEditorDialog splitters
    upgrade_persisted_splitter(
        new_persist_key='splitters_ScriptEditorDialog',
        key_map=[
            ('script_editor_splitter_samples', 'splitter_between_editor_and_examples'),
            ('script_editor_splitter_samples_before_after', 'splitter_between_before_and_after'),
            ('script_editor_splitter_documentation', 'splitter_between_editor_and_documentation'),
        ]
    )

    # OptionsDialog splitters
    upgrade_persisted_splitter(
        new_persist_key='splitters_OptionsDialog',
        key_map=[
            ('options_splitter', 'dialog_splitter'),
            ('scripting_splitter', 'scripting_options_splitter'),
        ]
    )


def upgrade_to_v2_7_0_dev_3(config):
    """Save file naming scripts to dictionary.
    """
    from picard.script import get_file_naming_script_presets
    from picard.script.serializer import (
        FileNamingScript,
        ScriptImportError,
    )
    Option('setting', 'file_renaming_scripts', {})
    ListOption('setting', 'file_naming_scripts', [])
    TextOption('setting', 'file_naming_format', DEFAULT_FILE_NAMING_FORMAT)
    TextOption('setting', 'selected_file_naming_script_id', '')
    scripts = {}
    for item in config.setting['file_naming_scripts']:
        try:
            script_item = FileNamingScript().create_from_yaml(item, create_new_id=False)
            scripts[script_item['id']] = script_item.to_dict()
        except ScriptImportError:
            log.error("Error converting file naming script")
    script_list = set(scripts.keys()) | set(map(lambda item: item['id'], get_file_naming_script_presets()))
    if config.setting['selected_file_naming_script_id'] not in script_list:
        script_item = FileNamingScript(
            script=config.setting['file_naming_format'],
            title=_("Primary file naming script"),
            readonly=False,
            deletable=True,
        )
        scripts[script_item['id']] = script_item.to_dict()
        config.setting['selected_file_naming_script_id'] = script_item['id']
    config.setting['file_renaming_scripts'] = scripts
    config.setting.remove('file_naming_scripts')
    config.setting.remove('file_naming_format')


def upgrade_to_v2_7_0_dev_4(config):
    """Replace artist_script_exception with artist_script_exceptions"""
    _s = config.setting
    ListOption('setting', 'artist_script_exceptions', [])
    if _s['artist_script_exception']:
        _s['artist_script_exceptions'] = [_s['artist_script_exception']]
    _s.remove('artist_script_exception')
    ListOption('setting', 'artist_locales', ['en'])
    if _s['artist_locale']:
        _s['artist_locales'] = [_s['artist_locale']]
    _s.remove('artist_locale')


def upgrade_to_v2_7_0_dev_5(config):
    """Replace artist_script_exceptions with script_exceptions and remove artist_script_exception_weighting"""
    _s = config.setting
    ListOption('setting', 'script_exceptions', [])
    weighting = _s['artist_script_exception_weighting'] or 0
    artist_script_exceptions = _s['artist_script_exceptions'] or []
    _s['script_exceptions'] = [(script_exception, weighting) for script_exception in artist_script_exceptions]
    _s.remove('artist_script_exceptions')
    _s.remove('artist_script_exception_weighting')


def upgrade_to_v2_8_0_dev_2(config):
    """Remove AcousticBrainz settings from options"""
    toolbar_layout = config.setting['toolbar_layout']
    try:
        toolbar_layout.remove('extract_and_submit_acousticbrainz_features_action')
        config.setting['toolbar_layout'] = toolbar_layout
    except ValueError:
        pass


def upgrade_to_v2_9_0_alpha_2(config):
    """Add preset file naming scripts to editable user scripts disctionary"""
    from picard.script import get_file_naming_script_presets
    scripts = config.setting['file_renaming_scripts']
    for item in get_file_naming_script_presets():
        scripts[item['id']] = item.to_dict()
    config.setting['file_renaming_scripts'] = scripts


def rename_option(config, old_opt, new_opt, option_type, default):
    _s = config.setting
    if old_opt in _s:
        _s[new_opt] = _s.value(old_opt, option_type, default)
        _s.remove(old_opt)

        _p = config.profiles
        _s.init_profile_options()
        all_settings = _p['user_profile_settings']
        for profile in _p['user_profiles']:
            id = profile['id']
            if id in all_settings and old_opt in all_settings[id]:
                all_settings[id][new_opt] = all_settings[id][old_opt]
                all_settings[id].pop(old_opt)
        _p['user_profile_settings'] = all_settings


def upgrade_config(config):
    cfg = config
    cfg.register_upgrade_hook(upgrade_to_v1_0_0_final_0)
    cfg.register_upgrade_hook(upgrade_to_v1_3_0_dev_1)
    cfg.register_upgrade_hook(upgrade_to_v1_3_0_dev_2)
    cfg.register_upgrade_hook(upgrade_to_v1_3_0_dev_3)
    cfg.register_upgrade_hook(upgrade_to_v1_3_0_dev_4)
    cfg.register_upgrade_hook(upgrade_to_v1_4_0_dev_2)
    cfg.register_upgrade_hook(upgrade_to_v1_4_0_dev_3)
    cfg.register_upgrade_hook(upgrade_to_v1_4_0_dev_4)
    cfg.register_upgrade_hook(upgrade_to_v1_4_0_dev_5)
    cfg.register_upgrade_hook(upgrade_to_v1_4_0_dev_6)
    cfg.register_upgrade_hook(upgrade_to_v1_4_0_dev_7)
    cfg.register_upgrade_hook(upgrade_to_v2_0_0_dev_3)
    cfg.register_upgrade_hook(upgrade_to_v2_1_0_dev_1)
    cfg.register_upgrade_hook(upgrade_to_v2_2_0_dev_3)
    cfg.register_upgrade_hook(upgrade_to_v2_4_0_beta_3)
    cfg.register_upgrade_hook(upgrade_to_v2_5_0_dev_1)
    cfg.register_upgrade_hook(upgrade_to_v2_5_0_dev_2)
    cfg.register_upgrade_hook(upgrade_to_v2_6_0_dev_1)
    cfg.register_upgrade_hook(upgrade_to_v2_6_0_beta_2)
    cfg.register_upgrade_hook(upgrade_to_v2_6_0_beta_3)
    cfg.register_upgrade_hook(upgrade_to_v2_7_0_dev_2)
    cfg.register_upgrade_hook(upgrade_to_v2_7_0_dev_3)
    cfg.register_upgrade_hook(upgrade_to_v2_7_0_dev_4)
    cfg.register_upgrade_hook(upgrade_to_v2_7_0_dev_5)
    cfg.register_upgrade_hook(upgrade_to_v2_8_0_dev_2)
    cfg.register_upgrade_hook(upgrade_to_v2_9_0_alpha_2)
    cfg.run_upgrade_hooks(log.debug)
