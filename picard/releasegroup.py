# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2012 Michael Wiencek
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

import traceback
from functools import partial
from PyQt4 import QtCore
from picard import config, log
from picard.metadata import Metadata
from picard.dataobj import DataObject
from picard.mbxml import media_formats_from_node, label_info_from_node


class ReleaseGroup(DataObject):

    def __init__(self, id):
        DataObject.__init__(self, id)
        self.metadata = Metadata()
        self.loaded = False
        self.versions = []
        self.loaded_albums = set()
        self.refcount = 0

    def load_versions(self, callback):
        kwargs = {"release-group": self.id, "limit": 100}
        self.tagger.xmlws.browse_releases(partial(self._request_finished, callback), **kwargs)

    def _parse_versions(self, document):
        del self.versions[:]
        data = []

        for node in document.metadata[0].release_list[0].release:
            labels, catnums = label_info_from_node(node.label_info_list[0])
            data.append({
                "id":      node.id,
                "date":    node.date[0].text if "date" in node.children else "",
                "country": node.country[0].text if "country" in node.children else "",
                "format":  media_formats_from_node(node.medium_list[0]),
                "labels":  ", ".join(set(labels)),
                "catnums": ", ".join(set(catnums)),
                "tracks":  " + ".join([m.track_list[0].count for m in node.medium_list[0].medium]),
            })
        data.sort(key=lambda x: x["date"])
        keys = ("date", "country", "labels", "catnums", "tracks", "format")

        for version in data:
            name = " / ".join(filter(None, (version[k] for k in keys))).replace("&", "&&")
            if name == version["tracks"]:
                name = "%s / %s" % (_('[no release info]'), name)

            self.versions.append({"id": version["id"], "name": name})

    def _request_finished(self, callback, document, http, error):
        try:
            if error:
                log.error("%r", unicode(http.errorString()))
            else:
                try:
                    self._parse_versions(document)
                except:
                    error = True
                    log.error(traceback.format_exc())
        finally:
            self.loaded = True
            callback()

    def remove_album(self, id):
        self.loaded_albums.discard(id)
        self.refcount -= 1
        if self.refcount == 0:
            del self.tagger.release_groups[self.id]
