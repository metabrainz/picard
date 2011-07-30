# -*- coding: utf-8 -*-

PLUGIN_NAME = u'No release'
PLUGIN_AUTHOR = u'Johannes Weißl'
PLUGIN_DESCRIPTION = '''Do not store specific release information in releases of unknown origin.'''
PLUGIN_VERSION = '0.1'
PLUGIN_API_VERSIONS = ['0.15']

from PyQt4 import QtCore, QtGui

from picard.album import Album
from picard.metadata import register_album_metadata_processor, register_track_metadata_processor
from picard.ui.options import register_options_page, OptionsPage
from picard.ui.itemviews import BaseAction, register_album_action
from picard.config import BoolOption, TextOption

class Ui_NoReleaseOptionsPage(object):
    def setupUi(self, NoReleaseOptionsPage):
        NoReleaseOptionsPage.setObjectName('NoReleaseOptionsPage')
        NoReleaseOptionsPage.resize(394, 300)
        self.verticalLayout = QtGui.QVBoxLayout(NoReleaseOptionsPage)
        self.verticalLayout.setObjectName('verticalLayout')
        self.groupBox = QtGui.QGroupBox(NoReleaseOptionsPage)
        self.groupBox.setObjectName('groupBox')
        self.vboxlayout = QtGui.QVBoxLayout(self.groupBox)
        self.vboxlayout.setObjectName('vboxlayout')
        self.norelease_enable = QtGui.QCheckBox(self.groupBox)
        self.norelease_enable.setObjectName('norelease_enable')
        self.vboxlayout.addWidget(self.norelease_enable)
        self.label = QtGui.QLabel(self.groupBox)
        self.label.setObjectName('label')
        self.vboxlayout.addWidget(self.label)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName('horizontalLayout')
        self.norelease_strip_tags = QtGui.QLineEdit(self.groupBox)
        self.norelease_strip_tags.setObjectName('norelease_strip_tags')
        self.horizontalLayout.addWidget(self.norelease_strip_tags)
        self.vboxlayout.addLayout(self.horizontalLayout)
        self.verticalLayout.addWidget(self.groupBox)
        spacerItem = QtGui.QSpacerItem(368, 187, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)

        self.retranslateUi(NoReleaseOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(NoReleaseOptionsPage)

    def retranslateUi(self, NoReleaseOptionsPage):
        self.groupBox.setTitle(QtGui.QApplication.translate('NoReleaseOptionsPage', 'No release', None, QtGui.QApplication.UnicodeUTF8))
        self.norelease_enable.setText(QtGui.QApplication.translate('NoReleaseOptionsPage', _('Enable plugin for all releases by default'), None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate('NoReleaseOptionsPage', _('Tags to strip (comma-separated)'), None, QtGui.QApplication.UnicodeUTF8))

def strip_release_specific_metadata(tagger, metadata):
    strip_tags = tagger.config.setting['norelease_strip_tags']
    strip_tags = [tag.strip() for tag in strip_tags.split(',')]
    for tag in strip_tags:
        if tag in metadata:
            del metadata[tag]

class NoReleaseAction(BaseAction):
    NAME = _('Remove specific release information...')
    def callback(self, objs):
        for album in objs:
            if isinstance(album, Album):
                strip_release_specific_metadata(self.tagger, album.metadata)
                for track in album.tracks:
                    strip_release_specific_metadata(self.tagger, track.metadata)
                    for file in track.linked_files:
                        track.update_file_metadata(file)
                album.update()

class NoReleaseOptionsPage(OptionsPage):
    NAME = 'norelease'
    TITLE = 'No release'
    PARENT = 'plugins'

    options = [
        BoolOption('setting', 'norelease_enable', False),
        TextOption('setting', 'norelease_strip_tags', 'asin,barcode,catalognumber,date,label,media,releasecountry,releasestatus'),
    ]

    def __init__(self, parent=None):
        super(NoReleaseOptionsPage, self).__init__(parent)
        self.ui = Ui_NoReleaseOptionsPage()
        self.ui.setupUi(self)

    def load(self):
        self.ui.norelease_strip_tags.setText(self.config.setting['norelease_strip_tags'])
        self.ui.norelease_enable.setChecked(self.config.setting['norelease_enable'])

    def save(self):
        self.config.setting['norelease_strip_tags'] = unicode(self.ui.norelease_strip_tags.text())
        self.config.setting['norelease_enable'] = self.ui.norelease_enable.isChecked()

def NoReleaseAlbumProcessor(tagger, metadata, release):
    if tagger.config.setting['norelease_enable']:
        strip_release_specific_metadata(tagger, metadata)

def NoReleaseTrackProcessor(tagger, metadata, track, release):
    if tagger.config.setting['norelease_enable']:
        strip_release_specific_metadata(tagger, metadata)

register_album_metadata_processor(NoReleaseAlbumProcessor)
register_track_metadata_processor(NoReleaseTrackProcessor)
register_album_action(NoReleaseAction())
register_options_page(NoReleaseOptionsPage)
