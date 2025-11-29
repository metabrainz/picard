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

import re


# Trust levels that appear in registry JSON
REGISTRY_TRUST_LEVELS = ['official', 'trusted', 'community']

# Plugin categories
CATEGORIES = ['metadata', 'coverart', 'ui', 'scripting', 'formats', 'other']

# Required MANIFEST.toml fields
REQUIRED_MANIFEST_FIELDS = ['uuid', 'name', 'version', 'description', 'api']

# String length constraints for MANIFEST.toml fields
MAX_NAME_LENGTH = 100
MAX_DESCRIPTION_LENGTH = 200
MAX_LONG_DESCRIPTION_LENGTH = 2000

# UUID v4 regex pattern (RFC 4122)
UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$', re.IGNORECASE)
