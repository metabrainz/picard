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
import cgi
from PyQt4 import QtGui, QtCore
from picard.util import format_time, encode_filename, bytes2human
from picard.util.tags import MEDIA_TAGS
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
        self._display_metadata_tab()

    def _display_artwork_tab(self):
        tab = self.ui.artwork_tab
        images = self.obj.metadata.images
        if not images:
            self.tab_hide(tab)
            return

        for image in images:
            data = image["data"]
            type = image["type"].title()
            size = len(data)
            item = QtGui.QListWidgetItem()
            pixmap = QtGui.QPixmap()
            pixmap.loadFromData(data)
            icon = QtGui.QIcon(pixmap)
            item.setIcon(icon)
            s = "%s\n%s (%s)\n%d x %d" % (
                type,
                bytes2human.decimal(size),
                bytes2human.binary(size),
                pixmap.width(),
                pixmap.height()
            )
            item.setText(s)
            self.ui.artwork_list.addItem(item)

    def tab_hide(self, widget):
        tab = self.ui.tabWidget
        index = tab.indexOf(widget)
        tab.removeTab(index)

    def _display_metadata_tab(self):
        metadata = self.obj.metadata
        keys = metadata.keys()
        keys.sort(key=lambda x:
            '0' + x if x in MEDIA_TAGS else
            '1' + x if x.startswith('~') else
            '2' + x
            )
        media = hidden = album = False
        table = self.ui.metadata_table
        table.setRowCount(len(keys))
        i = 0
        for key in keys:
            if key in MEDIA_TAGS:
                if not media:
                    self.add_separator_row(table, i, _("File variables"))
                    i += 1
                    media = True
            elif key.startswith('~'):
                if not hidden:
                    self.add_separator_row(table, i, _("Hidden variables"))
                    i += 1
                    hidden = True
            else:
                if not album:
                    self.add_separator_row(table, i, _("Tag variables"))
                    i += 1
                    album = True

            key_item, value_item = self.get_table_items(table, i)
            i += 1
            key_item.setText(u"_" + key[1:] if key.startswith('~') else key)
            if key in metadata:
                value_item.setText(metadata[key])

    def add_separator_row(self, table, i, title):
        key_item, value_item = self.get_table_items(table, i)
        font = key_item.font()
        font.setBold(True)
        key_item.setFont(font)
        key_item.setText(title)

    def get_table_items(self, table, i):
        key_item = table.item(i, 0)
        value_item = table.item(i, 1)
        if not key_item:
            key_item = QtGui.QTableWidgetItem()
            table.setItem(i, 0, key_item)
        if not value_item:
            value_item = QtGui.QTableWidgetItem()
            table.setItem(i, 1, value_item)
        return key_item, value_item


class FileInfoDialog(InfoDialog):

    def __init__(self, file, parent=None):
        InfoDialog.__init__(self, file, parent)
        self.setWindowTitle(_("File Info - %s") % file.base_filename)

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
                                (cgi.escape(i[0]),
                                 cgi.escape(i[1])), info))
        self.ui.info.setText(text)


class AlbumInfoDialog(InfoDialog):

    def __init__(self, album, parent=None):
        InfoDialog.__init__(self, album, parent)
        if 'album' in album.metadata:
            title = "%s - %s" % (album.metadata['albumartist'], album.metadata['album'])
        else:
            title = album.id
        print "title",title
        self.setWindowTitle(_("Album Info - %s") % title)

    def _display_info_tab(self):
        tab = self.ui.info_tab
        album = self.obj
        tabWidget = self.ui.tabWidget
        tab_index = tabWidget.indexOf(tab)
        if album.errors:
            tabWidget.setTabText(tab_index, _("&Errors"))
            text = '<br />'.join(map(lambda s: '<font color="darkred">%s</font>' %
                                     '<br />'.join(unicode(cgi.escape(s))
                                                   .replace('\t', ' ')
                                                   .replace(' ', '&nbsp;')
                                                   .splitlines()
                                                   ), album.errors)
                                 )
            self.ui.info.setText(text + '<hr />')
        else:
            tabWidget.setTabText(tab_index, _("&Info"))
            self.tab_hide(tab)
