# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2013-2014 Michael Wiencek
# Copyright (C) 2013-2016, 2018-2019 Laurent Monin
# Copyright (C) 2014, 2017 Lukáš Lalinský
# Copyright (C) 2014, 2018-2020 Philipp Wolfer
# Copyright (C) 2015 Ohm Patel
# Copyright (C) 2016 Suhas
# Copyright (C) 2016-2017 Sambhav Kothari
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
    TextOption,
)
from picard.const import (
    DEFAULT_FILE_NAMING_FORMAT,
    DEFAULT_NUMBERED_SCRIPT_NAME,
)
from picard.const.sys import IS_FROZEN


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
            _s["file_naming_format"] = (
                "$if($eq(%%compilation%%,1),\n$noop(Various Artist "
                "albums)\n%s,\n$noop(Single Artist Albums)\n%s)" % (
                    _s.value("va_file_naming_format", TextOption),
                    _s["file_naming_format"]
                ))
        _s.remove("va_file_naming_format")
        _s.remove("use_va_format")

    if "va_file_naming_format" in _s and "use_va_format" in _s:

        if _s.value("use_va_format", BoolOption):
            remove_va_file_naming_format()
            if interactive:
                msgbox = QtWidgets.QMessageBox()
                msgbox.information(msgbox,
                    _("Various Artists file naming scheme removal"),
                    _("The separate file naming scheme for various artists "
                        "albums has been removed in this version of Picard.\n"
                        "Your file naming scheme has automatically been "
                        "merged with that of single artist albums."),
                    QtWidgets.QMessageBox.Ok)

        elif (_s.value("va_file_naming_format", TextOption)
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
                msgbox.setIcon(QtWidgets.QMessageBox.Question)
                merge_button = msgbox.addButton(_('Merge'), QtWidgets.QMessageBox.AcceptRole)
                msgbox.addButton(_('Remove'), QtWidgets.QMessageBox.DestructiveRole)
                msgbox.exec_()
                merge = msgbox.clickedButton() == merge_button
            remove_va_file_naming_format(merge=merge)
        else:
            # default format, disabled
            remove_va_file_naming_format(merge=False)


def upgrade_to_v1_3_0_dev_1(config):
    """Option "windows_compatible_filenames" was renamed "windows_compatibility" (PICARD-110).
    """
    old_opt = "windows_compatible_filenames"
    new_opt = "windows_compatibility"
    rename_option(config, old_opt, new_opt, BoolOption, True)


def upgrade_to_v1_3_0_dev_2(config):
    """Option "preserved_tags" is now using comma instead of spaces as tag separator (PICARD-536)
    """
    _s = config.setting
    opt = "preserved_tags"
    if opt in _s and isinstance(_s[opt], str):
        _s[opt] = re.sub(r"\s+", ",", _s[opt].strip())


def upgrade_to_v1_3_0_dev_3(config):
    """Options were made to support lists (solving PICARD-144 and others)
    """
    _s = config.setting
    option_separators = {
        "preferred_release_countries": "  ",
        "preferred_release_formats": "  ",
        "enabled_plugins": None,
        "caa_image_types": None,
        "metadata_box_sizes": None,
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

    opt = "release_type_scores"
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
    opts = ["username", "password"]
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
    if _s["file_naming_format"] == OLD_DEFAULT_FILE_NAMING_FORMAT_v1_3:
        _s["file_naming_format"] = DEFAULT_FILE_NAMING_FORMAT


def upgrade_to_v1_4_0_dev_5(config):
    """Using Picard.ini configuration file on all platforms"""
    # this is done in Config.__init__()


def upgrade_to_v1_4_0_dev_6(config):
    """Adds support for multiple and selective tagger scripts"""
    _s = config.setting
    old_enabled_option = "enable_tagger_script"
    old_script_text_option = "tagger_script"
    list_of_scripts = []
    if old_enabled_option in _s:
        _s["enable_tagger_scripts"] = _s.value(old_enabled_option, BoolOption, False)
    if old_script_text_option in _s:
        old_script_text = _s.value(old_script_text_option, TextOption, "")
        if old_script_text:
            old_script = (0, _(DEFAULT_NUMBERED_SCRIPT_NAME) % 1, _s["enable_tagger_scripts"], old_script_text)
            list_of_scripts.append(old_script)
    _s["list_of_scripts"] = list_of_scripts
    _s.remove(old_enabled_option)
    _s.remove(old_script_text_option)


def upgrade_to_v1_4_0_dev_7(config):
    """Option "save_only_front_images_to_tags" was renamed to "embed_only_one_front_image"."""
    old_opt = "save_only_front_images_to_tags"
    new_opt = "embed_only_one_front_image"
    rename_option(config, old_opt, new_opt, BoolOption, True)


def upgrade_to_v2_0_0_dev_3(config):
    """Option "caa_image_size" value has different meaning."""
    _s = config.setting
    opt = "caa_image_size"
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
    if "folksonomy_tags" in _s and _s["folksonomy_tags"]:
        _s["use_genres"] = True
    rename_option(config, "max_tags",      "max_genres",      IntOption,  5)
    rename_option(config, "min_tag_usage", "min_genre_usage", IntOption,  90)
    rename_option(config, "ignore_tags",   "ignore_genres",   TextOption, "")
    rename_option(config, "join_tags",     "join_genres",     TextOption, "")
    rename_option(config, "only_my_tags",  "only_my_genres",  BoolOption, False)
    rename_option(config, "artists_tags",  "artists_genres",  BoolOption, False)


def upgrade_to_v2_2_0_dev_3(config):
    """Option ignore_genres was replaced by option genres_filter"""
    _s = config.setting
    old_opt = "ignore_genres"
    if old_opt in _s:
        if _s[old_opt]:
            new_opt = "genres_filter"
            tags = ["-" + e.strip().lower() for e in _s[old_opt].split(',')]
            _s[new_opt] = "\n".join(tags)
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
    if _s["file_naming_format"] == OLD_DEFAULT_FILE_NAMING_FORMAT_v2_1:
        _s["file_naming_format"] = DEFAULT_FILE_NAMING_FORMAT


def upgrade_to_v2_4_0_beta_3(config):
    """Convert preserved tags to list"""
    _s = config.setting
    opt = 'preserved_tags'
    _s[opt] = [t.strip() for t in _s.raw_value(opt, qtype='QString').split(',')]


def upgrade_to_v2_5_0_dev_1(config):
    """Rename whitelist cover art provider"""
    _s = config.setting
    _s['ca_providers'] = [
        ('UrlRelationships' if n == 'Whitelist' else n, s)
        for n, s in _s['ca_providers']
    ]


def upgrade_to_v2_5_0_dev_2(config):
    """Reset main view splitter states"""
    config.persist["splitter_state"] = b''
    config.persist["bottom_splitter_state"] = b''


def upgrade_to_v2_6_0_dev_1(config):
    """Unset fpcalc path in environments where auto detection is preferred."""
    if IS_FROZEN or config.setting['acoustid_fpcalc'].startswith('/snap/picard/'):
        config.setting['acoustid_fpcalc'] = ''


def rename_option(config, old_opt, new_opt, option_type, default):
    _s = config.setting
    if old_opt in _s:
        _s[new_opt] = _s.value(old_opt, option_type, default)
        _s.remove(old_opt)


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
    cfg.run_upgrade_hooks(log.debug)
