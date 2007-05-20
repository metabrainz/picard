# -*- coding: utf-8 -*-

PLUGIN_NAME = u"Add Cluster As Release"
PLUGIN_AUTHOR = u"Lukáš Lalinský"
PLUGIN_DESCRIPTION = ""


from PyQt4 import QtCore
from picard.cluster import Cluster
from picard.util import webbrowser2
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

        url = "http://musicbrainz.org/cdi/enter.html?tracks=%d" % len(cluster.files)
        if len(artists) > 1:
            url += "&hasmultipletrackartists=1&artistid=1"
        else:
            url += "&hasmultipletrackartists=0&artistid=2"
        url += "&artistedit=1&artistname=%s" % QtCore.QUrl.toPercentEncoding(cluster.metadata["artist"])
        url += "&releasename=%s" % QtCore.QUrl.toPercentEncoding(cluster.metadata["album"])
        for i, file in enumerate(cluster.files):
            url += "&track%d=%s" % (i, QtCore.QUrl.toPercentEncoding(file.metadata["title"]))
            url += "&tracklength%d=%s" % (i, QtCore.QUrl.toPercentEncoding(file.metadata["~length"]))
            if len(artists) > 1:
                url += "&tr%d_artistedit=1" % i
            url += "&tr%d_artistname=%s" % (i, QtCore.QUrl.toPercentEncoding(file.metadata["artist"]))
        webbrowser2.open(url)


register_cluster_action(AddClusterAsRelease())
