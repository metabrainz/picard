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
from musicbrainz2.webservice import WebService

class CachedWebService(WebService):
    """This class provides a cached wrapper around ``WebService``."""

    def __init__(self, host='musicbrainz.org', port=80, pathPrefix='/ws',
			     username=None, password=None, realm='musicbrainz.org',
			     opener=None, cache_dir='.'):
        """Constructor."""
        WebService.__init__(self, host, port, pathPrefix, username, password,
                            realm, opener)
        self._cache_dir = cache_dir
        if not os.path.isdir(self._cache_dir):
            try:
                os.makedirs(self._cache_dir)
            except IOError:
                self._log.error('Couldn\'t create cache directory %s',
                                self._cache_dir)

    def get(self, entity, id_, include=(), filter={}, version='1'):
        """Query the web service."""
        url = self._makeUrl(entity, id_, include, filter, version)
        filename = self._make_cache_filename(url)
        if not os.path.isfile(filename):
            stream = WebService.get(self, entity, id_, include, filter, version)
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
            self._log.debug("(Cached) GET %s", url)
        return open(filename, 'rb')

    def get_from_url(self, url):
        filename = self._make_cache_filename(url)
        if not os.path.isfile(filename):
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
            self._log.debug("(Cached) GET %s", url)
        return open(filename, 'rb')

    def _make_cache_filename(self, url):
        filename = sha.new(url).hexdigest()
        m = re.search(r"\.([a-z]{2,3})(?:\?|$)", url)
        if m:
            filename += "." + m.group(1)
        return os.path.join(self._cache_dir, filename)
