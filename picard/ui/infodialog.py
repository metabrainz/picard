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
import traceback
from PyQt4 import QtGui, QtCore
from picard import log
from picard.util import format_time, encode_filename, bytes2human
from picard.ui.ui_infodialog import Ui_InfoDialog


class InfoDialog(QtGui.QDialog):

    def __init__(self, obj, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.obj = obj
        self.ui = Ui_InfoDialog()
        self.ui.setupUi(self)
        self.ui.buttonBox.accepted.connect(self.accept)
        self.ui.buttonBox.rejected.connect(self.reject)
        self.setWindowTitle(_("Info"))
        self._display_tabs()

    def _display_tabs(self):
        self._display_info_tab()
        self._display_artwork_tab()

    def _display_artwork_tab(self):
        tab = self.ui.artwork_tab
        images = self.obj.metadata.images
        if not images:
            self.tab_hide(tab)
            return

        for image in images:
            try:
                data = image.data
            except (OSError, IOError), e:
                log.error(traceback.format_exc())
                continue
            size = len(data)
            item = QtGui.QListWidgetItem()
            pixmap = QtGui.QPixmap()
            pixmap.loadFromData(data)
            icon = QtGui.QIcon(pixmap)
            item.setIcon(icon)
            s = "%s (%s)\n%d x %d" % (bytes2human.decimal(size),
                                      bytes2human.binary(size),
                                      pixmap.width(),
                                      pixmap.height())
            item.setText(s)
            self.ui.artwork_list.addItem(item)

    def tab_hide(self, widget):
        tab = self.ui.tabWidget
        index = tab.indexOf(widget)
        tab.removeTab(index)


class FileInfoDialog(InfoDialog):

    def __init__(self, file, parent=None):
        InfoDialog.__init__(self, file, parent)
        self.setWindowTitle(_("Info") + " - " + file.base_filename)

    def _display_info_tab(self):
        file = self.obj
        info = []
        info.append((_('Filename:'), file.filename))
        if '~format' in file.orig_metadata:
            info.append((_('Format:'), file.orig_metadata['~format']))
        try:
            size = os.path.getsize(encode_filename(file.filename))
            sizestr = "%s (%s)" % (bytes2human.decimal(size), bytes2human.binary(size))
            info.append((_('Size:'), sizestr))
        except:
            pass
        if file.orig_metadata.length:
            info.append((_('Length:'), format_time(file.orig_metadata.length)))
        if '~bitrate' in file.orig_metadata:
            info.append((_('Bitrate:'), '%s kbps' % file.orig_metadata['~bitrate']))
        if '~sample_rate' in file.orig_metadata:
            info.append((_('Sample rate:'), '%s Hz' % file.orig_metadata['~sample_rate']))
        if '~bits_per_sample' in file.orig_metadata:
            info.append((_('Bits per sample:'), str(file.orig_metadata['~bits_per_sample'])))
        if '~channels' in file.orig_metadata:
            ch = file.orig_metadata['~channels']
            if ch == 1:
                ch = _('Mono')
            elif ch == 2:
                ch = _('Stereo')
            else:
                ch = str(ch)
            info.append((_('Channels:'), ch))
        text = '<br/>'.join(map(lambda i: '<b>%s</b><br/>%s' %
                                (QtCore.Qt.escape(i[0]),
                                 QtCore.Qt.escape(i[1])), info))
        self.ui.info.setText(text)


class AlbumInfoDialog(InfoDialog):

    def __init__(self, album, parent=None):
        InfoDialog.__init__(self, album, parent)
        self.setWindowTitle(_("Album Info"))

    def _display_info_tab(self):
        tab = self.ui.info_tab
        album = self.obj
        tabWidget = self.ui.tabWidget
        tab_index = tabWidget.indexOf(tab)
        if album.errors:
            tabWidget.setTabText(tab_index, _("&Errors"))
            text = '<br />'.join(map(lambda s: '<font color="darkred">%s</font>' %
                                     '<br />'.join(unicode(QtCore.Qt.escape(s))
                                                   .replace('\t', ' ')
                                                   .replace(' ', '&nbsp;')
                                                   .splitlines()
                                                   ), album.errors)
                                 )
            self.ui.info.setText(text + '<hr />')
        else:
            tabWidget.setTabText(tab_index, _("&Info"))
            self.tab_hide(tab)
