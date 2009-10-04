# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/options_plugins.ui'
#
# Created: Sun Oct  4 14:04:42 2009
#      by: PyQt4 UI code generator 4.4.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_PluginsOptionsPage(object):
    def setupUi(self, PluginsOptionsPage):
        PluginsOptionsPage.setObjectName("PluginsOptionsPage")
        PluginsOptionsPage.resize(406, 297)
        self.vboxlayout = QtGui.QVBoxLayout(PluginsOptionsPage)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setObjectName("vboxlayout")
        self.splitter = QtGui.QSplitter(PluginsOptionsPage)
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.splitter.setObjectName("splitter")
        self.groupBox_2 = QtGui.QGroupBox(self.splitter)
        self.groupBox_2.setObjectName("groupBox_2")
        self.vboxlayout1 = QtGui.QVBoxLayout(self.groupBox_2)
        self.vboxlayout1.setSpacing(6)
        self.vboxlayout1.setMargin(9)
        self.vboxlayout1.setObjectName("vboxlayout1")
        self.plugins = QtGui.QTreeWidget(self.groupBox_2)
        self.plugins.setRootIsDecorated(False)
        self.plugins.setObjectName("plugins")
        self.vboxlayout1.addWidget(self.plugins)
        self.groupBox = QtGui.QGroupBox(self.splitter)
        self.groupBox.setObjectName("groupBox")
        self.vboxlayout2 = QtGui.QVBoxLayout(self.groupBox)
        self.vboxlayout2.setSpacing(6)
        self.vboxlayout2.setMargin(9)
        self.vboxlayout2.setObjectName("vboxlayout2")
        self.details = QtGui.QLabel(self.groupBox)
        self.details.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.details.setWordWrap(True)
        self.details.setOpenExternalLinks(True)
        self.details.setObjectName("details")
        self.vboxlayout2.addWidget(self.details)
        self.vboxlayout.addWidget(self.splitter)
        self.download_link = QtGui.QLabel(PluginsOptionsPage)
        self.download_link.setTextFormat(QtCore.Qt.RichText)
        self.download_link.setOpenExternalLinks(True)
        self.download_link.setObjectName("download_link")
        self.vboxlayout.addWidget(self.download_link)
        self.plugin_folder_link = QtGui.QLabel(PluginsOptionsPage)
        self.plugin_folder_link.setTextFormat(QtCore.Qt.RichText)
        self.plugin_folder_link.setOpenExternalLinks(True)
        self.plugin_folder_link.setObjectName("plugin_folder_link")
        self.vboxlayout.addWidget(self.plugin_folder_link)

        self.retranslateUi(PluginsOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(PluginsOptionsPage)

    def retranslateUi(self, PluginsOptionsPage):
        self.groupBox_2.setTitle(_("Plugins"))
        self.plugins.headerItem().setText(0, _("Name"))
        self.plugins.headerItem().setText(1, _("Author"))
        self.plugins.headerItem().setText(2, _("Version"))
        self.groupBox.setTitle(_("Details"))
        self.download_link.setText(QtGui.QApplication.translate("PluginsOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Sans Serif\'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><a href=\"http://musicbrainz.org/doc/PicardPlugins\"><span style=\" text-decoration: underline; color:#0000ff;\">Download plugins from MusicBrainz</span></a></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.plugin_folder_link.setText(_("Open local plugin folder"))

