# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2008, 2011-2014 Lukáš Lalinský
# Copyright (C) 2009, 2018-2024 Philipp Wolfer
# Copyright (C) 2012 Chad Wilson
# Copyright (C) 2012-2013 Michael Wiencek
# Copyright (C) 2013-2024 Laurent Monin
# Copyright (C) 2015 Ohm Patel
# Copyright (C) 2015 Sophist-UK
# Copyright (C) 2016 Suhas
# Copyright (C) 2016-2017 Wieland Hoffmann
# Copyright (C) 2016-2018 Sambhav Kothari
# Copyright (C) 2017 Ville Skyttä
# Copyright (C) 2018, 2021, 2023 Bob Swift
# Copyright (C) 2021 Gabriel Ferreira
# Copyright (C) 2022 skelly37
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


import sys

from picard.version import Version


PICARD_ORG_NAME = "MusicBrainz"
PICARD_APP_NAME = "Picard"
PICARD_DISPLAY_NAME = "MusicBrainz Picard"
PICARD_APP_ID = "org.musicbrainz.Picard"
PICARD_DESKTOP_NAME = PICARD_APP_ID + ".desktop"
PICARD_VERSION = Version(3, 0, 0, 'dev', 6)


# optional build version
# it should be in the form '<platform>_<YYMMDDHHMMSS>'
# ie. win32_20140415091256
PICARD_BUILD_VERSION_STR = ""


PICARD_VERSION_STR = str(PICARD_VERSION)
PICARD_VERSION_STR_SHORT = PICARD_VERSION.short_str()
if PICARD_BUILD_VERSION_STR:
    __version__ = "%s+%s" % (PICARD_VERSION_STR, PICARD_BUILD_VERSION_STR)
    PICARD_FANCY_VERSION_STR = "%s (%s)" % (PICARD_VERSION_STR_SHORT,
                                            PICARD_BUILD_VERSION_STR)
else:
    __version__ = PICARD_VERSION_STR_SHORT
    PICARD_FANCY_VERSION_STR = PICARD_VERSION_STR_SHORT

# Keep those ordered
api_versions = [
    "3.0",
]

api_versions_tuple = [Version.from_string(v) for v in api_versions]


def crash_handler(exc: Exception = None):
    """Implements minimal handling of an exception crashing the application.
    This function tries to log the exception to a log file and display
    a minimal crash dialog to the user.
    This function is supposed to be called from inside an except blog.
    """
    # Allow disabling the graphical crash handler for debugging and CI purposes.
    if set(sys.argv) & {'--no-crash-dialog', '-v', '--version', '-V', '--long-version', '-h', '--help'}:
        return

    # First try to get traceback information and write it to a log file
    # with minimum chance to fail.
    from tempfile import NamedTemporaryFile
    import traceback
    if exc:
        if sys.version_info < (3, 10):
            trace_list = traceback.format_exception(None, exc, exc.__traceback__)
        else:
            trace_list = traceback.format_exception(exc)  # pylint: disable=no-value-for-parameter
        trace = "".join(trace_list)
    else:
        trace = traceback.format_exc()
    logfile = None
    try:
        with NamedTemporaryFile(suffix='.log', prefix='picard-crash-', delete=False) as f:
            f.write(trace.encode(errors="replace"))
            logfile = f.name
    except:  # noqa: E722,F722 # pylint: disable=bare-except
        print("Failed writing log file {0}".format(logfile), file=sys.stderr)
        logfile = None

    # Display the crash information to the user as a dialog. This requires
    # importing Qt6 and has some potential to fail if things are broken.
    from PyQt6.QtCore import (
        QCoreApplication,
        Qt,
        QUrl,
    )
    from PyQt6.QtWidgets import (
        QApplication,
        QMessageBox,
    )
    app = QCoreApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    msgbox = QMessageBox()
    msgbox.setIcon(QMessageBox.Icon.Critical)
    msgbox.setWindowTitle("Picard terminated unexpectedly")
    msgbox.setTextFormat(Qt.TextFormat.RichText)
    msgbox.setText(
        'An unexpected error has caused Picard to crash. '
        'Please report this issue on the <a href="https://tickets.metabrainz.org/projects/PICARD">MusicBrainz bug tracker</a>.')
    if logfile:
        logfile_url = QUrl.fromLocalFile(logfile)
        msgbox.setInformativeText(
            'A logfile has been written to <a href="{0}">{1}</a>.'
            .format(logfile_url.url(), logfile))
    msgbox.setDetailedText(trace)
    msgbox.setStandardButtons(QMessageBox.StandardButton.Close)
    msgbox.setDefaultButton(QMessageBox.StandardButton.Close)
    msgbox.exec()
    app.quit()


def register_excepthook():
    def _global_exception_handler(exctype, value, traceback):
        from picard import crash_handler
        crash_handler(exc=value)
        sys.__excepthook__(exctype, value, traceback)

    sys.excepthook = _global_exception_handler
