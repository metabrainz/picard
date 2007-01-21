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

import os.path
import re
import sha
import time
from musicbrainz2.webservice import WebService
from stat import *

class CachedWebService(WebService):
    """This class provides a cached wrapper around ``WebService``."""

    def __init__(self, cachedir='.', force=False, **kwargs):
        """Constructor."""
        WebService.__init__(self, **kwargs)
        self.force = force
        self.cachedir = cachedir
        if not os.path.isdir(self.cachedir):
            try:
                os.makedirs(self.cachedir)
            except EnvironmentError:
                self._log.error("Couldn't create cache directory %s", self.cachedir)

    def get(self, entity, id_, include=(), filter={}, version='1'):
        """Query the web service."""
        url = self._makeUrl(entity, id_, include, filter, version)
        filename = self._make_cache_filename(url)
        if self.force or not os.path.isfile(filename):
            stream = WebService.get(self, entity, id_, include, filter, version)
            try:
                outfile = open(filename, 'wb')
            except EnvironmentError:
                self._log.error('Couldn\'t create cache file %s', filename)
                return stream
            else:
                outfile.write(stream.read())
                outfile.close()
                stream.close()
        else:
            self._log.debug(u"(Cached) GET %s", url)
        return open(filename, 'rb')

    def post(self, entity, id_, data, version='1'):
        url = self._makeUrl(entity, id_, version=version, type_=None)
        filename = self._make_cache_filename(url + data)
        if self.force or not os.path.isfile(filename):
            stream = WebService.post(self, entity, id_, data, version)
            try:
                outfile = open(filename, 'wb')
            except EnvironmentError:
                self._log.error('Couldn\'t create cache file %s', filename)
                return stream
            else:
                data = stream.read()
                if self._host == "ofa.musicdns.org":
                    data = data.replace("http://musicbrainz.org/ns/mmd/1/",
                                        "http://musicbrainz.org/ns/mmd-1.0#")
                outfile.write(data)
                outfile.close()
                stream.close()
        else:
            self._log.debug(u"(Cached) POST %s", url)
        return open(filename, 'rb')

    def get_from_url(self, url):
        filename = self._make_cache_filename(url)
        if self.force or not os.path.isfile(filename):
            self._log.debug(u"GET %s", url)
            stream = self._opener.open(url)
            try:
                outfile = open(filename, 'wb')
            except IOError:
                self._log.error('Couldn\'t create cache file %s', filename)
                return stream
            else:
                outfile.write(stream.read())
                outfile.close()
                stream.close()
        else:
            self._log.debug(u"(Cached) GET %s", url)
        return open(filename, 'rb')

    def _make_cache_filename(self, url):
        filename = sha.new(url).hexdigest()
        m = re.search(r"\.([a-z]{2,3})(?:\?|$)", url)
        if m:
            filename += "." + m.group(1)
        return os.path.join(self.cachedir, filename)

    @staticmethod
    def cleanup(cachedir):
        if not os.path.isdir(cachedir):
            # Nothing in the cache!
            return
        now = time.time()
        for filename in os.listdir(cachedir):
            filename = os.path.join(cachedir, filename)
            mtime = os.stat(filename)[ST_MTIME]
            if now - mtime > 60 * 60 * 24 * 10:
                os.unlink(filename)
