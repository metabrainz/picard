# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2014-2015, 2018-2019 Laurent Monin
# Copyright (C) 2015 Rahul Raturi
# Copyright (C) 2016 Ville Skyttä
# Copyright (C) 2016 Wieland Hoffmann
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2019-2020 Philipp Wolfer
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

from picard import log
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
from picard.plugin import ExtensionPoint

from picard.ui.options import register_options_page


_cover_art_providers = ExtensionPoint(label='cover_art_providers')


def register_cover_art_provider(provider):
    _cover_art_providers.register(provider.__module__, provider)
    if hasattr(provider, 'OPTIONS') and provider.OPTIONS:
        provider.OPTIONS.NAME = provider.name.lower().replace(' ', '_')
        provider.OPTIONS.TITLE = provider.title
        register_options_page(provider.OPTIONS)


# named tuples used by cover_art_providers()
ProviderTuple = namedtuple('ProviderTuple', 'name title enabled cls')
PInfoTuple = namedtuple('PInfoTuple', 'position enabled')
POrderTuple = namedtuple('OrderTuple', 'name position enabled')


def cover_art_providers():
    def from_ca_providers_option():
        """Iterate through ca_providers option and yield name, position and enabled"""
        config = get_config()
        for pos, (name, enabled) in enumerate(config.setting['ca_providers']):
            yield POrderTuple(name=name, position=pos, enabled=enabled)

    # build a defaultdict with provider name as key, and PInfoTuple as value
    order = defaultdict(lambda: PInfoTuple(position=666, enabled=False))
    for o in from_ca_providers_option():
        order[o.name] = PInfoTuple(position=o.position, enabled=o.enabled)

    # use previously built dict to order providers, according to current ca_providers
    # (yet) unknown providers are placed at the end, disabled
    ordered_providers = sorted(_cover_art_providers, key=lambda p: order[p.name].position)

    def label(p):
        checked = 'x' if order[p.name].enabled else ' '
        return "%s [%s]" % (p.name, checked)

    log.debug("CA Providers order: %s", ' > '.join([label(p) for p in ordered_providers]))

    for p in ordered_providers:
        yield ProviderTuple(name=p.name, title=p.title, enabled=order[p.name].enabled, cls=p)


__providers = [
    CoverArtProviderLocal,
    CoverArtProviderCaa,
    CoverArtProviderUrlRelationships,
    CoverArtProviderCaaReleaseGroup,
]

for provider in __providers:
    register_cover_art_provider(provider)
