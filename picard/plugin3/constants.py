# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Philipp Wolfer
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

"""Plugin system constants shared between Picard and registry tools."""

# Trust levels that appear in registry JSON, ordered from highest to lowest trust level
REGISTRY_TRUST_LEVELS = ['official', 'trusted', 'community']

# Plugin categories
CATEGORIES = ['metadata', 'coverart', 'ui', 'scripting', 'formats', 'other']

# Default source locale for plugin translations
DEFAULT_SOURCE_LOCALE = 'en'

# Common SPDX licenses for plugins
LICENSES = {
    'GPL-2.0-or-later': 'https://www.gnu.org/licenses/gpl-2.0.html',
    'GPL-3.0-or-later': 'https://www.gnu.org/licenses/gpl-3.0.html',
    'MIT': 'https://opensource.org/license/MIT',
    'BSD-2-Clause': 'https://opensource.org/license/BSD-2-Clause',
    'BSD-3-Clause': 'https://opensource.org/license/BSD-3-Clause',
    'Apache-2.0': 'https://www.apache.org/licenses/LICENSE-2.0',
}
