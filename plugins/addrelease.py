# -*- coding: utf-8 -*-

PLUGIN_NAME = u"Add Cluster As Release"
PLUGIN_AUTHOR = u"Lukáš Lalinský"
PLUGIN_DESCRIPTION = ""
PLUGIN_VERSION = "0.1"
PLUGIN_API_VERSIONS = ["0.9.0"]


from PyQt4 import QtCore
from picard.cluster import Cluster
from picard.util import webbrowser2, format_time
from picard.ui.itemviews import BaseAction, register_cluster_action


class AddClusterAsRelease(BaseAction):
    NAME = "Add Cluster As Release..."

    def callback(self, objs):
        if len(objs) != 1 or not isinstance(objs[0], Cluster):
            return
        cluster = objs[0]

        artists = set()
        for i, file in enumerate(cluster.files):
            artists.add(file.metadata["artist"])

        url = "http://musicbrainz.org/cdi/enter.html"
        if len(artists) > 1:
            url += "?hasmultipletrackartists=1&artistid=1"
        else:
            url += "?hasmultipletrackartists=0&artistid=2"
        url += "&artistedit=1&artistname=%s" % QtCore.QUrl.toPercentEncoding(cluster.metadata["artist"])
        url += "&releasename=%s" % QtCore.QUrl.toPercentEncoding(cluster.metadata["album"])
        tracks = 0
        for i, file in enumerate(cluster.files):
            try:
                i = int(file.metadata["tracknumber"]) - 1
            except:
                pass
            tracks = max(tracks, i + 1)
            url += "&track%d=%s" % (i, QtCore.QUrl.toPercentEncoding(file.metadata["title"]))
            url += "&tracklength%d=%s" % (i, QtCore.QUrl.toPercentEncoding(format_time(file.metadata.length)))
            if len(artists) > 1:
                url += "&tr%d_artistedit=1" % i
            url += "&tr%d_artistname=%s" % (i, QtCore.QUrl.toPercentEncoding(file.metadata["artist"]))
        url += "&tracks=%d" % tracks
        webbrowser2.open(url)


register_cluster_action(AddClusterAsRelease())

