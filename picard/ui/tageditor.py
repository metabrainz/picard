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
from PyQt4 import QtCore, QtGui
from picard.util import sanitize_date, format_time
from picard.ui.util import StandardButton
from picard.ui.ui_edittagdialog import Ui_EditTagDialog

_tag_names = {
    'album': N_('Album'),
    'artist': N_('Artist'),
    'title': N_('Title'),
    'date': N_('Date'),
    'tracknumber': N_('Track Number'),
    'totaltracks': N_('Total Tracks'),
    'discnumber': N_('Disc Number'),
    'totaldiscs': N_('Total Discs'),
    'albumartist_sortorder': N_('Album Artist Sort Order'),
    'artist_sortorder': N_('Artist Sort Order'),
    'title_sortorder': N_('Title Sort Order'),
    'album_sortorder': N_('Album Sort Order'),
    'asin': N_('ASIN'),
    'grouping': N_('Grouping'),
    'version': N_('Version'),
    'isrc': N_('ISRC'),
    'mood': N_('Mood'),
    'bpm': N_('BPM'),
    'copyright': N_('Copyright'),
    'composer': N_('Composer'),
    'conductor': N_('Conductor'),
    'ensemble': N_('Ensemble'),
    'lyricist': N_('Lyricist'),
    'arranger': N_('Arranger'),
    'producer': N_('Producer'),
    'engineer': N_('Engineer'),
    'subtitle': N_('Subtitle'),
    'remixer': N_('Remixer'),
    'musicbrainz_trackid': N_('MusicBrainz Track Id'),
    'musicbrainz_albumid': N_('MusicBrainz Release Id'),
    'musicbrainz_artistid': N_('MusicBrainz Artist Id'),
    'musicbrainz_albumartistid': N_('MusicBrainz Release Artist Id'),
    'musicbrainz_trmid': N_('MusicBrainz TRM Id'),
    'musicip_puid': N_('MusicIP PUID'),
    'website': N_('Website'),
    'compilation': N_('Compilation'),
    'comment:': N_('Comment'),
    'genre': N_('Genre'),
    'encodedby': N_('Encoded By'),
    'performer:': N_('Performer'),
    'releasetype': N_('Release Type'),
    'releasestatus': N_('Release Status'),
}

def _tag_name(name):
    if ':' in name:
        name, desc = name.split(':', 1)
        name = _(_tag_names.get(name + ':', '')) or name
        return '%s [%s]' % (_(name), desc)
    else:
        return _(_tag_names.get(name, '')) or name

class EditTagDialog(QtGui.QDialog):
    """Single tag editor."""

    def __init__(self, name, value, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.ui = Ui_EditTagDialog()
        self.ui.setupUi(self)
        self.ui.buttonbox.addButton(StandardButton(StandardButton.OK), QtGui.QDialogButtonBox.AcceptRole)
        self.ui.buttonbox.addButton(StandardButton(StandardButton.CANCEL), QtGui.QDialogButtonBox.RejectRole)
        self.connect(self.ui.buttonbox, QtCore.SIGNAL('accepted()'), self, QtCore.SLOT('accept()'))
        self.connect(self.ui.buttonbox, QtCore.SIGNAL('rejected()'), self, QtCore.SLOT('reject()'))
        self.connect(self.ui.name, QtCore.SIGNAL('currentIndexChanged(int)'), self.on_name_changed)
        items = []
        for itemname, label in _tag_names.iteritems():
            items.append((_(label), itemname))
        items.sort()
        index = -1
        i = 0
        for label, itemname in items:
            item = self.ui.name.addItem(label, QtCore.QVariant(itemname))
            if name == itemname or (itemname.endswith(':') and name.startswith(itemname)):
                index = i
            i += 1
        if ':' in name:
            self.ui.desc.setText(name.split(':', 1)[1])
        if index == -1 and name:
            self.ui.name.addItem(name, QtCore.QVariant(name))
            index = i
        if name:
            self.ui.name.setCurrentIndex(index)
        if value:
            self.ui.value.document().setPlainText(value)

    def accept(self):
        self.name = unicode(self.ui.name.itemData(self.ui.name.currentIndex()).toString())
        if self.name.endswith(':'):
            self.name += unicode(self.ui.desc.text())
        self.value = self.ui.value.document().toPlainText()
        QtGui.QDialog.accept(self)

    def on_name_changed(self, index):
        name = unicode(self.ui.name.itemData(index).toString())
        if name.endswith(':'):
            self.ui.desc.setEnabled(True)
        else:
            self.ui.desc.setEnabled(False)

class TagEditor(QtGui.QDialog):

    fields = [
        ("title", None),
        ("album", None),
        ("artist", None),
        ("tracknumber", None),
        ("totaltracks", None),
        ("discnumber", None),
        ("totaldiscs", None),
        ("date", sanitize_date),
        ("albumartist", None),
    ]

    def __init__(self, file, parent=None):
        QtGui.QDialog.__init__(self, parent)

        from picard.ui.ui_tageditor import Ui_TagEditorDialog
        self.ui = Ui_TagEditorDialog()
        self.ui.setupUi(self)
        self.setWindowTitle(_("Details - %s") % os.path.basename(file.filename))

        self.ui.buttonbox.addButton(StandardButton(StandardButton.OK), QtGui.QDialogButtonBox.AcceptRole)
        self.ui.buttonbox.addButton(StandardButton(StandardButton.CANCEL), QtGui.QDialogButtonBox.RejectRole)
        self.connect(self.ui.buttonbox, QtCore.SIGNAL('accepted()'), self, QtCore.SLOT('accept()'))
        self.connect(self.ui.buttonbox, QtCore.SIGNAL('rejected()'), self, QtCore.SLOT('reject()'))

        self.ui.tags.setHeaderLabels([_("Name"), _("Value")])
        self.connect(self.ui.tags, QtCore.SIGNAL("itemActivated (QTreeWidgetItem*, int)"), self.edit_tag)
        self.connect(self.ui.tags_add, QtCore.SIGNAL('clicked()'), self.add_tag)
        self.connect(self.ui.tags_delete, QtCore.SIGNAL('clicked()'), self.delete_tag)
        if hasattr(self.ui.tags, 'setSortingEnabled'): # Qt 4.2
            self.ui.tags.setSortingEnabled(True)
            self.ui.tags.sortByColumn(0, QtCore.Qt.AscendingOrder)
        self.file = file
        self.metadata = file.metadata
        self.__names = []
        self.load()
        self.load_info()

    def accept(self):
        self.save()
        QtGui.QDialog.accept(self)

    def load_info(self):
        info = []
        info.append((_('Filename:'), self.file.filename))
        if '~format' in self.file.orig_metadata:
            info.append((_('Format:'), self.file.orig_metadata['~format']))
        try:
            size = os.path.getsize(encode_filename(self.file.filename))
            if size < 1024:
                size = '%d B' % size
            elif size < 1024 * 1024:
                size = '%0.1f kB' % (size / 1024.0)
            else:
                size = '%0.1f MB' % (size / 1024.0 / 1024.0)
            info.append((_('Size:'), size))
        except:
            pass
        if '~#length' in self.file.orig_metadata:
            info.append((_('Length:'), format_time(self.file.orig_metadata['~#length'])))
        if '~#bitrate' in self.file.orig_metadata:
            info.append((_('Bitrate:'), '%d kbps' % self.file.orig_metadata['~#bitrate']))
        if '~#sample_rate' in self.file.orig_metadata:
            info.append((_('Sample rate:'), '%d Hz' % self.file.orig_metadata['~#sample_rate']))
        if '~#bits_per_sample' in self.file.orig_metadata:
            info.append((_('Bits per sample:'), str(self.file.orig_metadata['~#bits_per_sample'])))
        if '~#channels' in self.file.orig_metadata:
            ch = self.file.orig_metadata['~#channels']
            if ch == 1: ch = _('Mono')
            elif ch == 2: ch = _('Stereo')
            else: ch = str(ch)
            info.append((_('Channels:'), ch))
        text = '<br/>'.join(map(lambda i: '<b>%s</b><br/>%s' % i, info))
        self.ui.info.setText(text)

    def load(self):
        self.__names = []
        for name, convert in self.fields:
            text = self.metadata[name]
            getattr(self.ui, name).setText(text)
            self.__names.append(name)

        items = self.metadata.items()
        items = filter(lambda i: i[0] not in self.__names, items)
        for name, value in items:
            if not name.startswith("~"):
                item = QtGui.QTreeWidgetItem(self.ui.tags)
                item.setText(0, _tag_name(name))
                item.setData(0, QtCore.Qt.UserRole, QtCore.QVariant(name))
                item.setText(1, value)
                self.__names.append(name)

        if "~artwork" in self.metadata:
            pictures = self.metadata.getall("~artwork")
            for mime, data in pictures:
                item = QtGui.QListWidgetItem()
                pixmap = QtGui.QPixmap()
                pixmap.loadFromData(data)
                icon = QtGui.QIcon(pixmap)
                item.setIcon(icon)
                self.ui.artwork_list.addItem(item)

    def save(self):
        for name in self.__names:
            try: del self.metadata[name]
            except KeyError: pass

        for name, convert in self.fields:
            text = unicode(getattr(self.ui, name).text())
            if convert:
                text = convert(text)
            if text or name in self.metadata:
                self.metadata[name] = text

        for i in range(self.ui.tags.topLevelItemCount()):
            item = self.ui.tags.topLevelItem(i)
            name = unicode(item.data(0, QtCore.Qt.UserRole).toString())
            value = unicode(item.text(1))
            self.metadata.add(name, value)

        self.file.update()

    def edit_tag(self, item, column):
        name = unicode(item.data(0, QtCore.Qt.UserRole).toString())
        value = item.text(1)
        dialog = EditTagDialog(name, value, self)
        if dialog.exec_():
            name = dialog.name
            value = dialog.value
            item.setText(0, _tag_name(name))
            item.setData(0, QtCore.Qt.UserRole, QtCore.QVariant(name))
            item.setText(1, value)

    def add_tag(self):
        dialog = EditTagDialog('', None, self)
        if dialog.exec_():
            name = dialog.name
            value = dialog.value
            item = QtGui.QTreeWidgetItem(self.ui.tags)
            item.setText(0, _tag_name(name))
            item.setData(0, QtCore.Qt.UserRole, QtCore.QVariant(name))
            item.setText(1, value)

    def delete_tag(self):
        items = self.ui.tags.selectedItems()
        for item in items:
            index = self.ui.tags.indexOfTopLevelItem(item)
            self.ui.tags.takeTopLevelItem(index)
