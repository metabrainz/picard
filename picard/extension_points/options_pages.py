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

    # Which options "Restore Defaults" resets (see PICARD-3525):
    #   * plugin pages -> every option registered in the 'plugin.<uuid>'
    #     section, so a single-page plugin resets correctly with no extra
    #     declaration;
    #   * core pages -> the OPTIONS keys, since scanning the shared 'setting'
    #     section would mean "reset every setting in Picard".
    if section.startswith('plugin.'):
        reset_names = {name for sect, name in Option.registry if sect == section}
    else:
        reset_names = set(options)

    # Register every OPTIONS entry for profile highlighting, then add any
    # remaining reset-only options (plugin section members not in OPTIONS).
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
        page_class.register_setting(opt_name, widgets)
    for opt_name in reset_names - set(options):
        page_class.register_setting(opt_name)
