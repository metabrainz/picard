# -*- coding: utf-8 -*-

PLUGIN_NAME = u"Add Cluster As Release"
PLUGIN_AUTHOR = u"Lukáš Lalinský"
PLUGIN_DESCRIPTION = ""
PLUGIN_VERSION = "0.2"
PLUGIN_API_VERSIONS = ["0.9.0", "0.10", "0.11", "0.12"]

# Hacked to popup an ugly dialog (to enable copy+pasting to non-IE browsers) for URLs longer than 2083
# characters to get around a Windows path limitation. Probably shouldn't be used on other platforms.

from PyQt4 import QtCore, QtGui, Qt
from picard.cluster import Cluster
from picard.util import webbrowser2, format_time
from picard.ui.itemviews import BaseAction, register_cluster_action
import sys


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

        # Chad Wilson: This is a windows-specific hack, and probably shouldn't be done on other systems. I'm lazy for now.
        # Carlin Mangar: I put in a condition for win32
        self.log.info(url)
        if (len(url) <= 2048) and sys.platform =="win32":
            webbrowser2.open(url)
        else:
            global w
            w = AddClusterViewUrl()
            w.addText(url)
            w.show()

class AddClusterViewUrl(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setWindowTitle(_("Add Cluster URL - Please copy and paste"))
        self.doc = QtGui.QTextDocument(self)
        self.textCursor = QtGui.QTextCursor(self.doc)
        font = QtGui.QFont()
        font.setFixedPitch(True)
        font.setPointSize(8)
        font.setWeight(QtGui.QFont.Normal)
        font.setFamily("")
        self.textFormat = QtGui.QTextCharFormat()
        self.textFormat.setFont(font)
        self.browser = QtGui.QTextBrowser(self)
        self.browser.setDocument(self.doc)
        vbox = QtGui.QHBoxLayout(self)
        vbox.addWidget(self.browser)     
    
    def addText(self, text):
        self.textCursor.insertText(text, self.textFormat)
        self.textCursor.insertBlock()

#w = AddClusterViewUrl()
register_cluster_action(AddClusterAsRelease())

