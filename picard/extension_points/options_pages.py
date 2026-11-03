# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2007 Lukáš Lalinský
# Copyright (C) 2009 Nikolai Prokoschenko
# Copyright (C) 2009, 2019-2022, 2025-2026 Philipp Wolfer
# Copyright (C) 2013, 2015, 2018-2026 Laurent Monin
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


from picard import log
from picard.config import Option
from picard.plugin import ExtensionPoint

from picard.ui.options import OptionsPage


ext_point_options_pages = ExtensionPoint[type[OptionsPage]](label='options_pages')


def register_options_page(page_class: type[OptionsPage]) -> None:
    ext_point_options_pages.register(page_class.__module__, page_class)
    section = page_class.OPTION_SECTION
    options = page_class.OPTIONS

    # Which options "Restore Defaults" resets, driven by the optional 'restore'
    # key on OPTIONS entries (see PICARD-3525):
    #   * any entry with restore=True -> reset ONLY the restore=True options;
    #   * otherwise -> the automatic default (plugin pages: every option in the
    #     'plugin.<uuid>' section; core pages: the OPTIONS keys) MINUS any
    #     option marked restore=False.
    if any(info.get('restore') is True for info in options.values()):
        reset_names = {name for name, info in options.items() if info.get('restore') is True}
    else:
        excluded = {name for name, info in options.items() if info.get('restore') is False}
        if section.startswith('plugin.'):
            candidates = {name for sect, name in Option.registry if sect == section}
        else:
            candidates = set(options)
        reset_names = candidates - excluded

    # Register every OPTIONS entry for profile highlighting, marking those in
    # the reset set as restorable; then add any remaining reset-only options
    # (plugin section members not listed in OPTIONS).
    for opt_name, opt_info in options.items():
        widgets = opt_info.get('widgets')
        if widgets:
            opt = Option.get(section, opt_name)
            if opt and not opt.in_profile:
                log.warning(
                    "Option '%s' has highlight widgets on page '%s' but in_profile=False; widgets ignored",
                    opt_name,
                    page_class.NAME,
                )
                widgets = None
        page_class.register_setting(opt_name, widgets, restorable=opt_name in reset_names)
    for opt_name in reset_names - set(options):
        page_class.register_setting(opt_name)
