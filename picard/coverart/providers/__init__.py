# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2014 Laurent Monin
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
from collections import defaultdict, namedtuple
import traceback

from picard import log, config
from picard.plugin import ExtensionPoint
from picard.ui.options import OptionsPage, register_options_page


_cover_art_providers = ExtensionPoint(label='cover_art_providers')


class ProviderOptions(OptionsPage):

    """ Template class for provider's options

        It works like OptionsPage for the most (options, load, save)
        It will append the provider's options page as a child of the main
        cover art's options page.

        The property _options_ui must be set to a valid Qt Ui class
        containing the layout and widgets for defined provider's options.

        A specific provider class (inhereting from CoverArtProvider) has
        to set the subclassed ProviderOptions as OPTIONS property.
        Options will be registered at the same time as the provider.

        class MyProviderOptions(ProviderOptions):
            _options_ui = Ui_MyProviderOptions
            ....

        class MyProvider(CoverArtProvider):
            OPTIONS = ProviderOptionsMyProvider
            ....

    """

    PARENT = "cover"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = self._options_ui()
        self.ui.setupUi(self)


def register_cover_art_provider(provider):
    _cover_art_providers.register(provider.__module__, provider)
    if hasattr(provider, 'OPTIONS') and provider.OPTIONS:
        provider.OPTIONS.NAME = provider.name.lower().replace(' ', '_')
        provider.OPTIONS.TITLE = provider.title
        register_options_page(provider.OPTIONS)


# named tuples used by cover_art_providers()
ProviderTuple = namedtuple('ProviderTuple', 'name title enabled cls')
PInfoTuple = namedtuple('PInfoTuple', 'position enabled')
POrderTuple = namedtuple('OrderTuple', 'name position enabled')


def cover_art_providers():
    def from_ca_providers_option():
        """Iterate through ca_providers option and yield name, position and enabled"""
        for pos, (name, enabled) in enumerate(config.setting['ca_providers']):
            yield POrderTuple(name=name, position=pos, enabled=enabled)

    # build a defaultdict with provider name as key, and PInfoTuple as value
    order = defaultdict(lambda: PInfoTuple(position=666, enabled=False))
    for o in from_ca_providers_option():
        order[o.name] = PInfoTuple(position=o.position, enabled=o.enabled)

    # use previously built dict to order providers, according to current ca_providers
    # (yet) unknown providers are placed at the end, disabled
    ordered_providers = sorted(_cover_art_providers, key=lambda p: order[p.name].position)

    def label(p):
        checked = 'x' if order[p.name].enabled else ' '
        return "%s [%s]" % (p.name, checked)

    log.debug("CA Providers order: %s", ' > '.join([label(p) for p in ordered_providers]))

    for p in ordered_providers:
        yield ProviderTuple(name=p.name, title=p.title, enabled=order[p.name].enabled, cls=p)


class CoverArtProviderMetaClass(type):
    """Provide default properties name & title for CoverArtProvider
    It is recommended to use those in place of NAME and TITLE that might not be defined
    """
    @property
    def name(cls):
        return getattr(cls, 'NAME', cls.__name__)

    @property
    def title(cls):
        return getattr(cls, 'TITLE', cls.name)


class CoverArtProvider(metaclass=CoverArtProviderMetaClass):
    """Subclasses of this class need to reimplement at least `queue_images()`.
       `__init__()` does not have to do anything.
       `queue_images()` will be called if `enabled()` returns `True`.
       `queue_images()` must return `FINISHED` when it finished to queue
       potential cover art downloads (using `queue_put(<CoverArtImage object>).
       If `queue_images()` delegates the job of queuing downloads to another
       method (asynchronous) it should return `WAIT` and the other method has to
       explicitly call `next_in_queue()`.
       If `FINISHED` is returned, `next_in_queue()` will be automatically called
       by CoverArt object.
    """

    # default state, internal use
    _STARTED = 0
    # returned by queue_images():
    # next_in_queue() will be automatically called
    FINISHED = 1
    # returned by queue_images():
    # next_in_queue() has to be called explicitly by provider
    WAIT = 2

    def __init__(self, coverart):
        self.coverart = coverart
        self.release = coverart.release
        self.metadata = coverart.metadata
        self.album = coverart.album

    def enabled(self):
        return not self.coverart.front_image_found

    def queue_images(self):
        # this method has to return CoverArtProvider.FINISHED or
        # CoverArtProvider.WAIT
        raise NotImplementedError

    def error(self, msg):
        self.coverart.album.error_append(msg)

    def queue_put(self, what):
        self.coverart.queue_put(what)

    def next_in_queue(self):
        # must be called by provider if queue_images() returns WAIT
        self.coverart.next_in_queue()

    def match_url_relations(self, relation_types, func):
        """Execute `func` for each relation url matching type in
           `relation_types`
        """
        try:
            if 'relations' in self.release:
                for relation in self.release['relations']:
                    if relation['target-type'] == 'url':
                        if relation['type'] in relation_types:
                            func(relation['url']['resource'])
        except AttributeError:
            self.error(traceback.format_exc())


from picard.coverart.providers.local import CoverArtProviderLocal
from picard.coverart.providers.caa import CoverArtProviderCaa
from picard.coverart.providers.whitelist import CoverArtProviderWhitelist
from picard.coverart.providers.caa_release_group import CoverArtProviderCaaReleaseGroup

__providers = [
    CoverArtProviderLocal,
    CoverArtProviderCaa,
    CoverArtProviderWhitelist,
    CoverArtProviderCaaReleaseGroup,
]

for provider in __providers:
    register_cover_art_provider(provider)
