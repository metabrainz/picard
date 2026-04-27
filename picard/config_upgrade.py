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

from contextlib import contextmanager
from inspect import (
    getmembers,
    isfunction,
)
import sys

from picard import PICARD_VERSION
from picard.config import (
    Config,
    ConfigValueType,
    Option,
)
from picard.version import (
    Version,
    VersionError,
)


# All upgrade functions have to start with following prefix
UPGRADE_FUNCTION_PREFIX = 'upgrade_to_v'

# Module that contains the upgrade hook functions
_HOOKS_MODULE = 'picard.config_upgrade_hooks'


# TO ADD AN UPGRADE HOOK:
# See config_upgrade_hooks.py


@contextmanager
def temp_option(option_type: type[Option], section: str, name: str, default: ConfigValueType):
    opt = option_type(section, name, default)
    yield opt
    opt.unregister()


def rename_option(
    config: Config,
    old_opt: str,
    new_opt: str,
    option_type: type[Option],
    default: ConfigValueType,
    reverse: bool = False,
):
    _s = config.setting
    if old_opt in _s:
        with temp_option(option_type, 'setting', old_opt, default) as opt:
            _s[new_opt] = _s.value(opt, default)
        if reverse:
            _s[new_opt] = not _s[new_opt]
        _s.remove(old_opt)

        _p = config.profiles
        _s.init_profile_options()
        all_settings = _p['user_profile_settings']
        for profile in _p['user_profiles']:
            id = profile['id']
            if id in all_settings and old_opt in all_settings[id]:
                all_settings[id][new_opt] = all_settings[id][old_opt]
                if reverse:
                    all_settings[id][new_opt] = not all_settings[id][new_opt]
                all_settings[id].pop(old_opt)
        _p['user_profile_settings'] = all_settings


class UpgradeHooksAutodetectError(Exception):
    pass


def autodetect_upgrade_hooks(module_name=None, prefix=UPGRADE_FUNCTION_PREFIX):
    """Detect upgrade hooks methods"""

    if module_name is None:
        import picard.config_upgrade_hooks  # noqa: F401

        module_name = _HOOKS_MODULE

    def is_upgrade_hook(f):
        """Check if passed function is an upgrade hook"""
        return isfunction(f) and f.__module__ == module_name and f.__name__.startswith(prefix)

    # Build a dict with version as key and function as value
    hooks = dict()
    for name, hook in getmembers(sys.modules[module_name], predicate=is_upgrade_hook):
        try:
            version = Version.from_string(name[len(prefix) :])
        except VersionError as e:
            raise UpgradeHooksAutodetectError("Failed to extract version from %s()" % hook.__name__) from e
        if version in hooks:
            raise UpgradeHooksAutodetectError(
                "Conflicting functions for version %s: %s vs %s" % (version, hooks[version], hook)
            )
        if version > PICARD_VERSION:
            raise UpgradeHooksAutodetectError(
                "Upgrade hook %s has version %s > Picard version %s" % (hook.__name__, version, PICARD_VERSION)
            )
        hooks[version] = hook

    return dict(sorted(hooks.items()))


def upgrade_config(config):
    """Execute detected upgrade hooks"""

    config.run_upgrade_hooks(autodetect_upgrade_hooks())
