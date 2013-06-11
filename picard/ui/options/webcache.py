# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2006 Lukáš Lalinský
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

from picard import config
from picard.ui.options import OptionsPage, register_options_page
from picard.ui.ui_options_webcache import Ui_WebcacheOptionsPage


class WebcacheOptionsPage(OptionsPage):
    """Web-cache caches data from MusicBrainz and cover art downloads on your hard-drive, 
and enables the remote server to check whether the data has changed since it was last sent to you.  
Because MB and cover art servers do not provide an Expires or Cache-Control header,
when you request the same data again a request is still made to the server; 
it is only the bandwidth for sending the response or downloading cover art which is potentially saved.

We estimate that you will need a cache of between 1.5KB and 3KB per music file! 
If you set the cache too small, it is likely that the cache will fill up and wrap around before 
you can reuse the data, and the disk spaced used by for caching will be wasted.

Normally requests are still made to the server, and so this caching will not 
save you much elapsed time unless your internet connections is slow. 
However, if you have recently downloaded this data and want to reuse it anyway even if it has changed,
then enable Force Cache and the data will always be loaded from the cache if it is there even if
the data on the server has changed.
Otherwise, given the significant amount of disk space required and the limited performance benefits, 
we do not recommend this is enabled unless you have lots of disk space and a limited internet connection.
"""
    NAME = "webcache"
    TITLE = N_("Web Cache")
    PARENT = "advanced"
    SORT_ORDER = 20
    ACTIVE = True

    options = [
        config.BoolOption("setting", "webcache_use", False),
        config.IntOption("setting", "webcache_size_maximum", 250),
        config.BoolOption("setting", "webcache_force_cache", False),
    ]

    def __init__(self, parent=None):
        super(WebcacheOptionsPage, self).__init__(parent)
        self.ui = Ui_WebcacheOptionsPage()
        self.ui.setupUi(self)
        self.ui.webcache_enabled.clicked.connect(self.webcache_enable)
        self.ui.webcache_clear_cache.clicked.connect(self.clear_cache)

    def load(self):
        self.cache_actually_enabled = config.setting["webcache_use"]
        self.ui.webcache_enabled.setChecked(config.setting["webcache_use"])
        self.cache_actually_enabled = config.setting["webcache_use"]
        self.ui.webcache_max_size.setValue(config.setting["webcache_size_maximum"])
        self.ui.webcache_force_cache.setChecked(config.setting["webcache_force_cache"])
        self.display_cache_size(self.tagger.xmlws.cache_size())
        self.webcache_enable()

    def save(self):
        config.setting["webcache_use"] = self.ui.webcache_enabled.isChecked()
        config.setting["webcache_size_maximum"] = self.ui.webcache_max_size.value()
        config.setting["webcache_force_cache"] = self.ui.webcache_force_cache.isChecked()
        self.tagger.xmlws.set_cache()

    def display_cache_size(self,sizes):
        self.ui.webcache_current_sizes.setText(_(
            "You are currently using %dMB of a maximum of %dMB." 
            % sizes
            ))

    def webcache_enable(self):
        enabled = self.ui.webcache_enabled.isChecked()
        if self.cache_actually_enabled:
            self.ui.webcache_clear_cache.setEnabled(enabled)
        if enabled:
            self.display_cache_size(self.tagger.xmlws.cache_size())
        else:
            self.display_cache_size((0,0))
            self.ui.webcache_force_cache.setChecked(False)

    def clear_cache(self):
        self.tagger.xmlws.clear_cache()
        self.display_cache_size(self.tagger.xmlws.cache_size())


# TO-DO
# Clear cache button

register_options_page(WebcacheOptionsPage)
