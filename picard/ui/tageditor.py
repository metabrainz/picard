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
from picard.track import Track
from picard.metadata import Metadata
from picard.util import sanitize_date, format_time, encode_filename
from picard.ui.util import StandardButton
from picard.util.tags import tag_names, display_tag_name
from picard.ui.ui_tageditor import Ui_TagEditorDialog
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
            self.ui.value.selectAll()
            self.ui.value.setFocus(QtCore.Qt.OtherFocusReason)
        else:
            self.ui.name.lineEdit().selectAll()

    def accept(self):
        self.name = unicode(self.ui.name.currentText())
        self.value = self.ui.value.document().toPlainText()
        QtGui.QDialog.accept(self)


class TagEditor(QtGui.QDialog):

    def __init__(self, files, parent=None):
        QtGui.QDialog.__init__(self, parent)

        self.ui = Ui_TagEditorDialog()
        self.ui.setupUi(self)

        title = _("Details") + " - "
        total = len(files)
        if total == 1:
            title += files[0].base_filename
        else:
            title += ungettext("%d file", "%d files", total) % total
        self.setWindowTitle(title)

        self.ui.buttonbox.addButton(StandardButton(StandardButton.OK), QtGui.QDialogButtonBox.AcceptRole)
        self.ui.buttonbox.addButton(StandardButton(StandardButton.CANCEL), QtGui.QDialogButtonBox.RejectRole)
        self.connect(self.ui.buttonbox, QtCore.SIGNAL('accepted()'), self, QtCore.SLOT('accept()'))
        self.connect(self.ui.buttonbox, QtCore.SIGNAL('rejected()'), self, QtCore.SLOT('reject()'))

        self.connect(self.ui.tags_add, QtCore.SIGNAL('clicked()'), self.add_tag)
        self.connect(self.ui.tags_edit, QtCore.SIGNAL('clicked()'), self.edit_tag)
        self.connect(self.ui.tags_delete, QtCore.SIGNAL('clicked()'), self.delete_tag)
        self.connect(self.ui.tags, QtCore.SIGNAL("itemActivated (QTreeWidgetItem*, int)"), self.edit_tag)

        self.ui.tags.setSortingEnabled(True)
        self.ui.tags.sortByColumn(0, QtCore.Qt.AscendingOrder)
        
        if self.config.setting['enable_ratings']:
            self.ui.rating.setMaximum(self.config.setting['rating_steps'] - 1)
        else:
            self.ui.ratingLabel.hide()
            self.ui.rating.hide()

        self.changed = set()
        self.files = files
        self.load()
        self.load_info()

    def accept(self):
        self.save()
        QtGui.QDialog.accept(self)

    def load(self):
        all_tag_names = set()
        common_tags = None
        counts = dict()
        for file in self.files:
            tags = set()
            for name, values in file.metadata.rawitems():
                if not name.startswith("~"):
                    tags.add((name, tuple(sorted(values))))
                    all_tag_names.add(name)
                counts[name] = counts.get(name, 0) + 1
            if common_tags is None:
                common_tags = tags
            else:
                common_tags = common_tags.intersection(tags)

        common_tag_names = set([a for (a, b) in common_tags])
        different_tag_names = all_tag_names.difference(common_tag_names)

        total = len(self.files)
        for name in different_tag_names:
            item = QtGui.QTreeWidgetItem(self.ui.tags)
            item.setText(0, display_tag_name(name))
            item.setData(0, QtCore.Qt.UserRole, QtCore.QVariant(name))
            font = item.font(1)
            font.setItalic(True)
            item.setFont(1, font)
            missing = total - counts[name]
            if not missing:
                value = ungettext("(different across %d file)",
                                 "(different across %d files)", total) % total
            else:
                value = ungettext("(missing from %d file)",
                                 "(missing from %d files)", missing) % missing
            item.setText(1, value)

        for name, values in common_tags:
            for value in values:
                item = QtGui.QTreeWidgetItem(self.ui.tags)
                item.setText(0, display_tag_name(name))
                item.setData(0, QtCore.Qt.UserRole, QtCore.QVariant(name))
                item.setText(1, value)

        if len(self.files) == 1:
            if self.config.setting['enable_ratings']:
                ratings = self.files[0].metadata.getall('~rating')
                if len(ratings) > 0:
                    self.ui.rating.setRating(int(ratings[0]))
            for mime, data in self.files[0].metadata.images:
                item = QtGui.QListWidgetItem()
                pixmap = QtGui.QPixmap()
                pixmap.loadFromData(data)
                icon = QtGui.QIcon(pixmap)
                item.setIcon(icon)
                self.ui.artwork_list.addItem(item)

    def save(self):
        metadata = Metadata()
        for i in range(self.ui.tags.topLevelItemCount()):
            item = self.ui.tags.topLevelItem(i)
            name = unicode(item.data(0, QtCore.Qt.UserRole).toString())
            if name in self.changed:
                value = unicode(item.text(1))
                metadata.add(name, value)

        # Rate the different tracks    
        if self.config.setting['enable_ratings']:
            rating = self.ui.rating.getRating()
            metadata['~rating'] = unicode(rating)
            tracks = set([file.parent for file in self.files
                          if isinstance(file.parent, Track)])
            ratings = {}
            for track in tracks:
                ratings[('track', track.id)] = rating
                track.metadata['~rating'] = rating
            if self.config.setting['submit_ratings']:
                self.tagger.xmlws.submit_ratings(ratings, None)

        for file in self.files:
            for name in self.changed:
                try:
                    del file.metadata[name]
                except KeyError:
                    pass
            file.metadata.update(metadata)
            file.update()

    def add_tag(self):
        dialog = EditTagDialog('', None, self)
        if dialog.exec_():
            name = dialog.name
            value = dialog.value
            item = QtGui.QTreeWidgetItem(self.ui.tags)
            item.setText(0, display_tag_name(name))
            item.setData(0, QtCore.Qt.UserRole, QtCore.QVariant(name))
            item.setText(1, value)
            self.changed.add(name)

    def edit_tag(self, item=None, column=None):
        if item is None:
            items = self.ui.tags.selectedItems()
            if not items:
                return
            item = items[0]
        name = unicode(item.data(0, QtCore.Qt.UserRole).toString())
        value = item.text(1)
        dialog = EditTagDialog(name, value, self)
        if dialog.exec_():
            if value != dialog.value:
                name = dialog.name
                value = dialog.value
                item.setText(0, display_tag_name(name))
                item.setData(0, QtCore.Qt.UserRole, QtCore.QVariant(name))
                font = item.font(1)
                font.setItalic(False)
                item.setFont(1, font)
                item.setText(1, value)
                self.changed.add(name)

    def delete_tag(self):
        items = self.ui.tags.selectedItems()
        for item in items:
            name = unicode(item.data(0, QtCore.Qt.UserRole).toString())
            index = self.ui.tags.indexOfTopLevelItem(item)
            self.ui.tags.takeTopLevelItem(index)
            self.changed.add(name)

    def load_info(self):
        total = len(self.files)
        if total == 1:
            file = self.files[0]
            info = []
            info.append((_('Filename:'), file.filename))
            if '~format' in file.orig_metadata:
                info.append((_('Format:'), file.orig_metadata['~format']))
            try:
                size = os.path.getsize(encode_filename(file.filename))
                if size < 1024:
                    size = '%d B' % size
                elif size < 1024 * 1024:
                    size = '%0.1f kB' % (size / 1024.0)
                else:
                    size = '%0.1f MB' % (size / 1024.0 / 1024.0)
                info.append((_('Size:'), size))
            except:
                pass
            if file.orig_metadata.length:
                info.append((_('Length:'), format_time(file.orig_metadata.length)))
            if '~#bitrate' in file.orig_metadata:
                info.append((_('Bitrate:'), '%d kbps' % file.orig_metadata['~#bitrate']))
            if '~#sample_rate' in file.orig_metadata:
                info.append((_('Sample rate:'), '%d Hz' % file.orig_metadata['~#sample_rate']))
            if '~#bits_per_sample' in file.orig_metadata:
                info.append((_('Bits per sample:'), str(file.orig_metadata['~#bits_per_sample'])))
            if '~#channels' in file.orig_metadata:
                ch = file.orig_metadata['~#channels']
                if ch == 1: ch = _('Mono')
                elif ch == 2: ch = _('Stereo')
                else: ch = str(ch)
                info.append((_('Channels:'), ch))
            text = '<br/>'.join(map(lambda i: '<b>%s</b><br/>%s' % i, info))
            self.ui.info.setText(text)
        else:
            self.ui.info.setText(ungettext("%d file", "%d files", total) % total)
