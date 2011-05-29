# -*- coding: utf-8 -*-

PLUGIN_NAME = u"Copy Cluster to Clipboard"
PLUGIN_AUTHOR = u"Michael Elsdörfer"
PLUGIN_DESCRIPTION = "Exports a cluster's tracks to the clipboard, so it can be copied into the tracklist field on MusicBrainz"
PLUGIN_VERSION = "0.1"
PLUGIN_API_VERSIONS = ["0.9.0", "0.10", "0.15"]


from PyQt4 import QtCore, QtGui
from picard.cluster import Cluster
from picard.util import format_time
from picard.ui.itemviews import BaseAction, register_cluster_action


class CopyClusterToClipboard(BaseAction):
    NAME = "Copy Cluster to Clipboard..."

    def callback(self, objs):
        if len(objs) != 1 or not isinstance(objs[0], Cluster):
            return
        cluster = objs[0]

        artists = set()
        for i, file in enumerate(cluster.files):
            artists.add(file.metadata["artist"])

        tracks = []
        for i, file in enumerate(cluster.files):
            try:
                i = int(file.metadata["tracknumber"])
            except:
                i += 1

            if len(artists) > 1:
                tracks.append((i, "%s. %s - %s (%s)" % (
                    i,
                    file.metadata["title"],
                    file.metadata["artist"],
                    format_time(file.metadata.length))))
            else:
                tracks.append((i, "%s. %s (%s)" % (
                    i,
                    file.metadata["title"],
                    format_time(file.metadata.length))))

        clipboard = QtGui.QApplication.clipboard()
        clipboard.setText("\n".join(map(lambda x: x[1], sorted(tracks))))


register_cluster_action(CopyClusterToClipboard())

