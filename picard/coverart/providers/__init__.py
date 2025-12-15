# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2014-2015, 2018-2021, 2023-2024 Laurent Monin
# Copyright (C) 2015 Rahul Raturi
# Copyright (C) 2016 Ville Skyttä
# Copyright (C) 2016 Wieland Hoffmann
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2019-2021 Philipp Wolfer
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


from collections import (
    defaultdict,
    namedtuple,
)

from picard.config import get_config
from picard.coverart.providers.caa import CoverArtProviderCaa
from picard.coverart.providers.caa_release_group import (
    CoverArtProviderCaaReleaseGroup,
)
from picard.coverart.providers.local import CoverArtProviderLocal
from picard.coverart.providers.provider import (  # noqa: F401 # pylint: disable=unused-import
    CoverArtProvider,
    ProviderOptions,
)
from picard.coverart.providers.urlrels import CoverArtProviderUrlRelationships
from picard.extension_points.cover_art_providers import (
    ext_point_cover_art_providers,
    register_cover_art_provider,
)


# named tuples used by cover_art_providers()
ProviderTuple = namedtuple('ProviderTuple', 'name title enabled cls')
PInfoTuple = namedtuple('PInfoTuple', 'position enabled')


def cover_art_providers():
    config = get_config()

    # build a defaultdict with provider name as key, and PInfoTuple as value
    order = defaultdict(lambda: PInfoTuple(position=666, enabled=False))
    for position, (name, enabled) in enumerate(config.setting['ca_providers']):
        order[name] = PInfoTuple(position=position, enabled=enabled)

    # use previously built dict to order providers, according to current ca_providers
    # (yet) unknown providers are placed at the end, disabled
    for p in sorted(ext_point_cover_art_providers, key=lambda p: (order[p.name].position, p.name)):
        yield ProviderTuple(name=p.name, title=p.display_title(), enabled=order[p.name].enabled, cls=p)


__providers = [
    CoverArtProviderLocal,
    CoverArtProviderCaa,
    CoverArtProviderUrlRelationships,
    CoverArtProviderCaaReleaseGroup,
]

for provider in __providers:
    register_cover_art_provider(provider)
