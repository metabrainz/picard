# -*- coding: utf-8 -*-

PLUGIN_NAME = u"Add Cluster As Release"
PLUGIN_AUTHOR = u'Frederik "Freso" S. Olesen, Lukáš Lalinský, Philip Jägenstedt'
PLUGIN_DESCRIPTION = "Adds a plugin context menu option to clusters and single\
 files to help you quickly add them as releases or standalone recordings to\
 the MusicBrainz database via the website by pre-populating artists,\
 track names and times."
PLUGIN_VERSION = "0.5"
PLUGIN_API_VERSIONS = ["1.0.0"]

from picard.cluster import Cluster
from picard.file import File
from picard.util import webbrowser2
from picard.ui.itemviews import BaseAction, register_cluster_action, register_file_action

import codecs
import os
import tempfile

HTML_HEAD = """<!doctype html>
<meta charset="UTF-8">
<title>%s</title>
<form action="%s" method="post">
"""
HTML_INPUT = """<input type="hidden" name="%s" value="%s">
"""
HTML_TAIL = """<input type="submit" value="%s">
</form>
<script>document.forms[0].submit()</script>
"""
HTML_ATTR_ESCAPE = {
    "&": "&amp;",
    '"': "&quot;"
}


class AddObjectAsEntity(BaseAction):
    NAME = "Add Object As Entity..."
    objtype = None
    submit_url = 'http://musicbrainz.org/'

    def __init__(self):
        super(AddObjectAsEntity, self).__init__()
        self.form_values = {}

    def check_object(self, objs, objtype):
        """
        Checks if a given object array is valid (ie., has one item) and that
        its item is an object of the given type.

        Returns either False (if conditions are not met), or the object in the
        array.
        """
        if not isinstance(objs[0], objtype) or len(objs) != 1:
            return False
        else:
            return objs[0]

    def add_form_value(self, key, value):
        "Add global (e.g., release level) name-value pair."
        self.form_values[key] = value

    def set_form_values(self, objdata):
        return

    def generate_html_file(self, form_values):
        (fd, fp) = tempfile.mkstemp(suffix=".html")
        f = codecs.getwriter("utf-8")(os.fdopen(fd, "w"))

        def esc(s):
            return "".join(HTML_ATTR_ESCAPE.get(c, c) for c in s)
        # add a global (release-level) name-value

        def nv(n, v):
            f.write(HTML_INPUT % (esc(n), esc(v)))

        f.write(HTML_HEAD % (self.NAME, self.submit_url))

        for key in form_values:
            nv(key, form_values[key])

        f.write(HTML_TAIL % (self.NAME))
        f.close()
        return fp

    def open_html_file(self, fp):
        webbrowser2.open("file://" + fp)

    def callback(self, objs):
        objdata = self.check_object(objs, self.objtype)
        if objdata:
            self.set_form_values(objdata)
            html_file = self.generate_html_file(self.form_values)
            self.open_html_file(html_file)


class AddClusterAsRelease(AddObjectAsEntity):
    NAME = "Add Cluster As Release..."
    objtype = Cluster
    submit_url = 'http://musicbrainz.org/release/add'

    def set_form_values(self, cluster):
        nv = self.add_form_value

        nv("artist_credit.names.0.artist.name", cluster.metadata["albumartist"])
        nv("name", cluster.metadata["album"])

        discnumber_shift = -1
        for i, file in enumerate(cluster.files):
            try:
                i = int(file.metadata["tracknumber"]) - 1
            except:
                pass
            # As per https://musicbrainz.org/doc/Development/Release_Editor_Seeding#Tracklists_and_Mediums
            # the medium numbers ("m") must be starting with 0.
            # Maybe the existing tags don't have disc numbers in them or
            # they're starting with something smaller than or equal to 0, so try
            # to produce a sane disc number.
            try:
                m = int(file.metadata.get("discnumber", 1))
                if m <= 0:
                    # A disc number was smaller than or equal to 0 - all other
                    # disc numbers need to be changed to accommodate that.
                    discnumber_shift = max(discnumber_shift, 0 - m)
                m = m + discnumber_shift
            except Exception as e:
                # The most likely reason for an exception at this point is a
                # ValueError because the disc number in the tags was not a
                # number. Just log the exception and assume the medium number
                # is 0.
                file.log.info("Trying to get the disc number of %s caused the following error: %s; assuming 0",
                              file.filename, e)
                m = 0

            # add a track-level name-value
            def tnv(n, v):
                nv("mediums.%d.track.%d.%s" % (m, i, n), v)

            tnv("name", file.metadata["title"])
            if file.metadata["artist"] != cluster.metadata["albumartist"]:
                tnv("artist_credit.names.0.name", file.metadata["artist"])
            tnv("length", str(file.metadata.length))


class AddFileAsRecording(AddObjectAsEntity):
    NAME = "Add File As Standalone Recording..."
    objtype = File
    submit_url = 'http://musicbrainz.org/recording/create'

    def set_form_values(self, track):
        nv = self.add_form_value
        nv("edit-recording.name", track.metadata["title"])
        nv("edit-recording.artist_credit.names.0.artist.name", track.metadata["artist"])
        nv("edit-recording.length", track.metadata["~length"])


class AddFileAsRelease(AddObjectAsEntity):
    NAME = "Add File As Release..."
    objtype = File
    submit_url = 'http://musicbrainz.org/release/add'

    def set_form_values(self, track):
        nv = self.add_form_value

        # Main album attributes
        if track.metadata["albumartist"]:
            nv("artist_credit.names.0.artist.name", track.metadata["albumartist"])
        else:
            nv("artist_credit.names.0.artist.name", track.metadata["artist"])
        if track.metadata["album"]:
            nv("name", track.metadata["album"])
        else:
            nv("name", track.metadata["title"])

        # Tracklist
        nv("mediums.0.track.0.name", track.metadata["title"])
        nv("mediums.0.track.0.artist_credit.names.0.name", track.metadata["artist"])
        nv("mediums.0.track.0.length", str(track.metadata.length))


register_cluster_action(AddClusterAsRelease())
register_file_action(AddFileAsRecording())
register_file_action(AddFileAsRelease())
