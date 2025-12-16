# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2014-2015, 2018-2019, 2021, 2024 Laurent Monin
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


from enum import Enum
import traceback
from typing import TYPE_CHECKING

from picard.util.display_title_base import HasDisplayTitle

from picard.ui.options import OptionsPage


if TYPE_CHECKING:
    from picard.coverart import CoverArt


class ProviderOptions(OptionsPage):
    """Template class for provider's options

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
        super().__init__(parent=parent)
        self.ui = self._options_ui()
        self.ui.setupUi(self)


class CoverArtProviderMetaClass(type):
    """Provide default properties name & title for CoverArtProvider
    It is recommended to use those in place of NAME and TITLE that might not be defined
    """

    @property
    def name(cls):
        return getattr(cls, 'NAME', cls.__name__)


class CoverArtProvider(HasDisplayTitle, metaclass=CoverArtProviderMetaClass):
    """Subclasses of this class need to reimplement at least `queue_images()`.
    `__init__()` does not have to do anything.
    `queue_images()` will be called if `enabled()` returns `True`.
    `queue_images()` must return `QueueState.FINISHED` when it finished to queue
    potential cover art downloads (using `queue_put(<CoverArtImage object>).
    If `queue_images()` delegates the job of queuing downloads to another
    method (asynchronous) it should return `QueueState.WAIT` and the other method has to
    explicitly call `next_in_queue()`.
    If `QueueState.FINISHED` is returned, `next_in_queue()` will be automatically called
    by CoverArt object.
    """

    class QueueState(Enum):
        # default state, internal use
        _STARTED = 0
        # returned by queue_images():
        # next_in_queue() will be automatically called
        FINISHED = 1
        # returned by queue_images():
        # next_in_queue() has to be called explicitly by provider
        WAIT = 2

    def __init__(self, coverart: 'CoverArt'):
        self.coverart = coverart
        self.release = coverart.release
        self.metadata = coverart.metadata
        self.album = coverart.album

    def enabled(self):
        return not self.coverart.front_image_found

    def queue_images(self) -> QueueState:
        # this method has to return CoverArtProvider.QueueState.FINISHED or
        # CoverArtProvider.QueueState.WAIT
        raise NotImplementedError

    def error(self, msg):
        self.coverart.album.error_append(msg)

    def queue_put(self, what):
        self.coverart.queue_put(what)

    def next_in_queue(self):
        # must be called by provider if queue_images() returns WAIT
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
