# -*- coding: utf-8 -*-

PLUGIN_NAME = u"Add Cluster As Release"
PLUGIN_AUTHOR = u"Lukáš Lalinský, Philip Jägenstedt"
PLUGIN_DESCRIPTION = "Adds a plugin context menu option to clusters to help you quickly add a release into the MusicBrainz\
 database via the website by pre-populating artists, track names and times."
PLUGIN_VERSION = "0.3"
PLUGIN_API_VERSIONS = ["1.0.0"]

from picard.cluster import Cluster
from picard.util import webbrowser2
from picard.ui.itemviews import BaseAction, register_cluster_action

import codecs
import os
import tempfile

HTML_HEAD = """<!doctype html>
<meta charset="UTF-8">
<title>Add Cluster As Release</title>
<form action="http://musicbrainz.org/release/add" method="post">
"""
HTML_INPUT = """<input type="hidden" name="%s" value="%s">
"""
HTML_TAIL = """<input type="submit" value="Add Release">
</form>
<script>document.forms[0].submit()</script>
"""
HTML_ATTR_ESCAPE = {
    "&": "&amp;",
    '"': "&quot;"
}

class AddClusterAsRelease(BaseAction):
    NAME = "Add Cluster As Release..."

    def callback(self, objs):
        if len(objs) != 1 or not isinstance(objs[0], Cluster):
            return
        cluster = objs[0]

        (fd, fp) = tempfile.mkstemp(suffix=".html")
        f = codecs.getwriter("utf-8")(os.fdopen(fd, "w"))

        def esc(s):
            return "".join(HTML_ATTR_ESCAPE.get(c, c) for c in s)
        # add a global (release-level) name-value
        def nv(n, v):
            f.write(HTML_INPUT % (esc(n), esc(v)))

        f.write(HTML_HEAD)

        nv("artist_credit.names.0.artist.name", cluster.metadata["albumartist"])
        nv("name", cluster.metadata["album"])

        for i, file in enumerate(cluster.files):
            try:
                i = int(file.metadata["tracknumber"]) - 1
            except:
                pass
            try:
                m = int(file.metadata["discnumber"]) - 1
            except:
                m = 0

            # add a track-level name-value
            def tnv(n, v):
                nv("mediums.%d.track.%d.%s" % (m, i, n), v)

            tnv("name", file.metadata["title"])
            if file.metadata["artist"] != cluster.metadata["albumartist"]:
                tnv("artist_credit.names.0.name", file.metadata["artist"])
            tnv("length", str(file.metadata.length))

        f.write(HTML_TAIL)
        f.close()
        webbrowser2.open("file://"+fp)

register_cluster_action(AddClusterAsRelease())
