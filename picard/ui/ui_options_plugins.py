# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python setup.py build_ui` to update it.

from PyQt5 import QtCore, QtWidgets

class Ui_PluginsOptionsPage(object):
    def setupUi(self, PluginsOptionsPage):
        PluginsOptionsPage.setObjectName("PluginsOptionsPage")
        PluginsOptionsPage.resize(513, 312)
        self.vboxlayout = QtWidgets.QVBoxLayout(PluginsOptionsPage)
        self.vboxlayout.setObjectName("vboxlayout")
        self.plugins_container = QtWidgets.QSplitter(PluginsOptionsPage)
        self.plugins_container.setEnabled(True)
        self.plugins_container.setOrientation(QtCore.Qt.Vertical)
        self.plugins_container.setHandleWidth(2)
        self.plugins_container.setObjectName("plugins_container")
        self.groupBox_2 = QtWidgets.QGroupBox(self.plugins_container)
        self.groupBox_2.setObjectName("groupBox_2")
        self.vboxlayout1 = QtWidgets.QVBoxLayout(self.groupBox_2)
        self.vboxlayout1.setSpacing(2)
        self.vboxlayout1.setObjectName("vboxlayout1")
        self.plugins = QtWidgets.QTreeWidget(self.groupBox_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.plugins.sizePolicy().hasHeightForWidth())
        self.plugins.setSizePolicy(sizePolicy)
        self.plugins.setAcceptDrops(True)
        self.plugins.setDragDropMode(QtWidgets.QAbstractItemView.DropOnly)
        self.plugins.setRootIsDecorated(False)
        self.plugins.setObjectName("plugins")
        self.vboxlayout1.addWidget(self.plugins)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.install_plugin = QtWidgets.QPushButton(self.groupBox_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.install_plugin.sizePolicy().hasHeightForWidth())
        self.install_plugin.setSizePolicy(sizePolicy)
        self.install_plugin.setObjectName("install_plugin")
        self.horizontalLayout.addWidget(self.install_plugin)
        self.folder_open = QtWidgets.QPushButton(self.groupBox_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.folder_open.sizePolicy().hasHeightForWidth())
        self.folder_open.setSizePolicy(sizePolicy)
        self.folder_open.setObjectName("folder_open")
        self.horizontalLayout.addWidget(self.folder_open)
        self.reload_list_of_plugins = QtWidgets.QPushButton(self.groupBox_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.reload_list_of_plugins.sizePolicy().hasHeightForWidth())
        self.reload_list_of_plugins.setSizePolicy(sizePolicy)
        self.reload_list_of_plugins.setObjectName("reload_list_of_plugins")
        self.horizontalLayout.addWidget(self.reload_list_of_plugins)
        self.vboxlayout1.addLayout(self.horizontalLayout)
        self.groupBox = QtWidgets.QGroupBox(self.plugins_container)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy)
        self.groupBox.setObjectName("groupBox")
        self.vboxlayout2 = QtWidgets.QVBoxLayout(self.groupBox)
        self.vboxlayout2.setSpacing(0)
        self.vboxlayout2.setObjectName("vboxlayout2")
        self.scrollArea = QtWidgets.QScrollArea(self.groupBox)
        self.scrollArea.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrollArea.sizePolicy().hasHeightForWidth())
        self.scrollArea.setSizePolicy(sizePolicy)
        self.scrollArea.setFrameShape(QtWidgets.QFrame.HLine)
        self.scrollArea.setFrameShadow(QtWidgets.QFrame.Plain)
        self.scrollArea.setLineWidth(0)
        self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 469, 76))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrollAreaWidgetContents.sizePolicy().hasHeightForWidth())
        self.scrollAreaWidgetContents.setSizePolicy(sizePolicy)
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.verticalLayout.setContentsMargins(0, 0, 6, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.details = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.details.sizePolicy().hasHeightForWidth())
        self.details.setSizePolicy(sizePolicy)
        self.details.setMinimumSize(QtCore.QSize(0, 0))
        self.details.setFrameShape(QtWidgets.QFrame.Box)
        self.details.setLineWidth(0)
        self.details.setText("")
        self.details.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.details.setWordWrap(True)
        self.details.setIndent(0)
        self.details.setOpenExternalLinks(True)
        self.details.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse|QtCore.Qt.TextSelectableByMouse)
        self.details.setObjectName("details")
        self.verticalLayout.addWidget(self.details)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.vboxlayout2.addWidget(self.scrollArea)
        self.vboxlayout.addWidget(self.plugins_container)

        self.retranslateUi(PluginsOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(PluginsOptionsPage)
        PluginsOptionsPage.setTabOrder(self.plugins, self.install_plugin)
        PluginsOptionsPage.setTabOrder(self.install_plugin, self.folder_open)
        PluginsOptionsPage.setTabOrder(self.folder_open, self.reload_list_of_plugins)
        PluginsOptionsPage.setTabOrder(self.reload_list_of_plugins, self.scrollArea)

    def retranslateUi(self, PluginsOptionsPage):
        _translate = QtCore.QCoreApplication.translate
        self.groupBox_2.setTitle(_("Plugins"))
        self.plugins.headerItem().setText(0, _("Name"))
        self.plugins.headerItem().setText(1, _("Version"))
        self.plugins.headerItem().setText(2, _("Status"))
        self.install_plugin.setText(_("Install plugin..."))
        self.folder_open.setText(_("Open plugin folder"))
        self.reload_list_of_plugins.setText(_("Reload List of Plugins"))
        self.groupBox.setTitle(_("Details"))

