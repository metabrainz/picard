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
from picard.util import sanitize_date, format_time, encode_filename
from picard.ui.util import StandardButton
from picard.util.tags import tag_names, display_tag_name
from picard.ui.ui_edittagdialog import Ui_EditTagDialog

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
        self.ui.name.addItems(sorted(tag_names.keys()))
        if name:
            self.ui.name.setEditText(name)
        if value:
            self.ui.value.document().setPlainText(value)

    def accept(self):
        self.name = unicode(self.ui.name.currentText())
        self.value = self.ui.value.document().toPlainText()
        QtGui.QDialog.accept(self)

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
                item.setText(0, display_tag_name(name))
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
            item.setText(0, display_tag_name(name))
            item.setData(0, QtCore.Qt.UserRole, QtCore.QVariant(name))
            item.setText(1, value)

    def add_tag(self):
        dialog = EditTagDialog('', None, self)
        if dialog.exec_():
            name = dialog.name
            value = dialog.value
            item = QtGui.QTreeWidgetItem(self.ui.tags)
            item.setText(0, display_tag_name(name))
            item.setData(0, QtCore.Qt.UserRole, QtCore.QVariant(name))
            item.setText(1, value)

    def delete_tag(self):
        items = self.ui.tags.selectedItems()
        for item in items:
            index = self.ui.tags.indexOfTopLevelItem(item)
            self.ui.tags.takeTopLevelItem(index)
