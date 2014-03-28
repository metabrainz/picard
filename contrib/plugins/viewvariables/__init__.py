# -*- coding: utf-8 -*-

PLUGIN_NAME = u'View script variables'
PLUGIN_AUTHOR = u'Sophist'
PLUGIN_DESCRIPTION = u'''Display a dialog box listing the metadata variables for the file'''
PLUGIN_VERSION = '0.2'
PLUGIN_API_VERSIONS = ['1.0']

from PyQt4 import QtGui, QtCore
try:
    from picard.util.tags import MEDIA_TAGS
except ImportError:
    from picard.file import File
    MEDIA_TAGS = File._default_preserved_tags

from picard.file import File
from picard.track import Track
from picard.ui.itemviews import BaseAction, register_file_action, register_track_action
from picard.plugins.viewvariables.ui_variables_dialog import Ui_VariablesDialog

class ViewVariables(BaseAction):
    NAME = 'View script variables'

    def callback(self, objs):
        obj = objs[0]
        files = self.tagger.get_files_from_objects(objs)
        if files:
            obj = files[0]
        dialog = ViewVariablesDialog(obj)
        dialog.exec_()

class ViewVariablesDialog(QtGui.QDialog):

    def __init__(self, obj, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.ui = Ui_VariablesDialog()
        self.ui.setupUi(self)
        self.ui.buttonBox.accepted.connect(self.accept)
        self.ui.buttonBox.rejected.connect(self.reject)
        metadata = obj.metadata
        if isinstance(obj,File):
            self.setWindowTitle(_("File: %s") % obj.base_filename)
        elif isinstance(obj,Track):
            tn = metadata['tracknumber']
            if len(tn) == 1:
                tn = u"0" + tn
            self.setWindowTitle(_("Track: %s %s ") % (tn, metadata['title']))
        else:
            self.setWindowTitle(_("Variables"))
        self._display_metadata(metadata)

    def _display_metadata(self, metadata):
        keys = metadata.keys()
        keys.sort(key=lambda x:
            '0' + x if x in MEDIA_TAGS else
            '1' + x if x.startswith('~') else
            '2' + x
            )
        media = hidden = album = False
        table = self.ui.metadata_table
        key_example, value_example = self.get_table_items(table, 0)
        self.key_flags = key_example.flags()
        self.value_flags = value_example.flags()
        table.setRowCount(len(keys)+3)
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
            key_item.setFlags(self.key_flags)
            table.setItem(i, 0, key_item)
        if not value_item:
            value_item = QtGui.QTableWidgetItem()
            value_item.setFlags(self.value_flags)
            table.setItem(i, 1, value_item)
        return key_item, value_item

vv = ViewVariables()
register_file_action(vv)
register_track_action(vv)
