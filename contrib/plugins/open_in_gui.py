# -*- coding: utf-8 -*-

PLUGIN_NAME = u"Open files in the GUI environment"
PLUGIN_AUTHOR = u"Michael Elsdörfer"
PLUGIN_DESCRIPTION = ""
PLUGIN_VERSION = "0.1"
PLUGIN_API_VERSIONS = ["0.9.0", "0.10", "0.15"]


import subprocess, sys, os
from PyQt4 import QtCore, QtGui
from picard.file import File
from picard.track import Track
from picard.ui.itemviews import BaseAction, register_file_action


def startfile(path):
    """Start a file with its associated application. Like os.startfile(),
    but with fallbacks for non-Windows platforms.
    """
    try:
        os.startfile(path)
    except AttributeError:
        if sys.platform == 'darwin':
            subprocess.Popen(['open', path])
        else:
            try:
                subprocess.Popen(['xdg-open', path])
            except OSError:
                QtGui.QMessageBox.critical(None, _("Open Error"), _("Error while opening file:\n\n%s") % (e,))


class OpenFile(BaseAction):
    NAME = "Open file"

    def callback(self, objs):
        for obj in objs:
            if isinstance(obj, File):
                startfile(obj.filename)
                break
            elif isinstance(obj, Track):
                for linked in obj.linked_files:
                    startfile(linked.filename)
                    return


class OpenFolder(BaseAction):
    NAME = "Open folder"

    def callback(self, objs):
        folders = set()
        for obj in objs:
            if isinstance(obj, File):
                folders.add(os.path.dirname(obj.filename))
            elif isinstance(obj, Track):
                for linked in obj.linked_files:
                    folders.add(os.path.dirname(linked.filename))
        for folder in folders:
            startfile(folder)


register_file_action(OpenFile())
register_file_action(OpenFolder())
