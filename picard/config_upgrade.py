# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2013-2014 Laurent Monin
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


from PyQt4 import QtGui

import re
from picard import (log, config)


# TO ADD AN UPGRADE HOOK:
# ----------------------
# add a function here, named after the version you want upgrade to
# ie. upgrade_to_v1_0_0_dev_1() for 1.0.0dev1
# register it in upgrade_config()
# and modify PICARD_VERSION to match it
#

_s = config.setting

def upgrade_to_v1_0_0_final_0():
    """In version 1.0, the file naming formats for single and various artist releases were merged.
    """
    def remove_va_file_naming_format(merge=True):
        if merge:
            _s["file_naming_format"] = (
                "$if($eq(%%compilation%%,1),\n$noop(Various Artist "
                "albums)\n%s,\n$noop(Single Artist Albums)\n%s)" % (
                    _s["va_file_naming_format"],
                    _s["file_naming_format"]
                ))
        _s.remove("va_file_naming_format")
        _s.remove("use_va_format")

    if ("va_file_naming_format" in _s and "use_va_format" in _s):
        msgbox = QtGui.QMessageBox()

        if _s["use_va_format"].toBool():
            remove_va_file_naming_format()
            msgbox.information(msgbox,
                _("Various Artists file naming scheme removal"),
                _("The separate file naming scheme for various artists "
                    "albums has been removed in this version of Picard.\n"
                    "Your file naming scheme has automatically been "
                    "merged with that of single artist albums."),
                QtGui.QMessageBox.Ok)

        elif (_s["va_file_naming_format"] !=
                r"$if2(%albumartist%,%artist%)/%album%/$if($gt(%totaldis"
                "cs%,1),%discnumber%-,)$num(%tracknumber%,2) %artist% - "
                "%title%"):

            answer = msgbox.question(msgbox,
                _("Various Artists file naming scheme removal"),
                _("The separate file naming scheme for various artists "
                    "albums has been removed in this version of Picard.\n"
                    "You currently do not use this option, but have a "
                    "separate file naming scheme defined.\n"
                    "Do you want to remove it or merge it with your file "
                    "naming scheme for single artist albums?"),
                _("Merge"), _("Remove"))

            if answer:
                remove_va_file_naming_format(merge=False)
            else:
                remove_va_file_naming_format()
        else:
            # default format, disabled
            remove_va_file_naming_format(merge=False)


def upgrade_to_v1_3_0_dev_1():
    """Option "windows_compatible_filenames" was renamed "windows_compatibility" (PICARD-110).
    """
    old_opt = "windows_compatible_filenames"
    new_opt = "windows_compatibility"
    if old_opt in _s:
        _s[new_opt] = _s[old_opt]
        _s.remove(old_opt)


def upgrade_to_v1_3_0_dev_2():
    """Option "preserved_tags" is now using comma instead of spaces as tag separator (PICARD-536)
    """
    opt = "preserved_tags"
    if opt in _s:
        _s[opt] = re.sub(r"\s+", ",", _s[opt].strip())


def upgrade_to_v1_3_0_dev_3():
    """Options were made to support lists (solving PICARD-144 and others)
    """
    option_separators = {
        "preferred_release_countries": "  ",
        "preferred_release_formats": "  ",
        "enabled_plugins": None,
        "caa_image_types": None,
        "metadata_box_sizes": None,
    }
    for (opt, sep) in option_separators.iteritems():
        if opt in _s:
            _s[opt] = _s.raw_value(opt).split(sep)


def upgrade_config():
    cfg = config._config
    cfg.register_upgrade_hook(upgrade_to_v1_0_0_final_0)
    cfg.register_upgrade_hook(upgrade_to_v1_3_0_dev_1)
    cfg.register_upgrade_hook(upgrade_to_v1_3_0_dev_2)
    cfg.register_upgrade_hook(upgrade_to_v1_3_0_dev_3)
    cfg.run_upgrade_hooks(log.debug)
