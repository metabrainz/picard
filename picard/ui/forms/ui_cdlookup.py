# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'cdlookup.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## Use `python setup.py build_ui` to update it.
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QHeaderView,
    QLabel, QPushButton, QSizePolicy, QSpacerItem,
    QStackedWidget, QToolButton, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget)

from picard.i18n import gettext as _

class Ui_CDLookupDialog(object):
    def setupUi(self, CDLookupDialog):
        if not CDLookupDialog.objectName():
            CDLookupDialog.setObjectName(u"CDLookupDialog")
        CDLookupDialog.resize(720, 320)
        self.vboxLayout = QVBoxLayout(CDLookupDialog)
        self.vboxLayout.setSpacing(6)
        self.vboxLayout.setObjectName(u"vboxLayout")
        self.vboxLayout.setContentsMargins(9, 9, 9, 9)
        self.results_view = QStackedWidget(CDLookupDialog)
        self.results_view.setObjectName(u"results_view")
        self.results_page = QWidget()
        self.results_page.setObjectName(u"results_page")
        self.verticalLayout_4 = QVBoxLayout(self.results_page)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel(self.results_page)
        self.label.setObjectName(u"label")

        self.verticalLayout_4.addWidget(self.label)

        self.release_list = QTreeWidget(self.results_page)
        __qtreewidgetitem = QTreeWidgetItem()
        __qtreewidgetitem.setText(0, u"1");
        self.release_list.setHeaderItem(__qtreewidgetitem)
        self.release_list.setObjectName(u"release_list")

        self.verticalLayout_4.addWidget(self.release_list)

        self.results_view.addWidget(self.results_page)
        self.no_results_page = QWidget()
        self.no_results_page.setObjectName(u"no_results_page")
        self.verticalLayout_3 = QVBoxLayout(self.no_results_page)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer_2)

        self.no_results_label = QLabel(self.no_results_page)
        self.no_results_label.setObjectName(u"no_results_label")
        self.no_results_label.setStyleSheet(u"margin-bottom: 9px;")

        self.verticalLayout_3.addWidget(self.no_results_label, 0, Qt.AlignHCenter)

        self.submit_button = QToolButton(self.no_results_page)
        self.submit_button.setObjectName(u"submit_button")
        self.submit_button.setStyleSheet(u"")
        icon = QIcon(QIcon.fromTheme(u"media-optical"))
        self.submit_button.setIcon(icon)
        self.submit_button.setIconSize(QSize(128, 128))
        self.submit_button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        self.verticalLayout_3.addWidget(self.submit_button, 0, Qt.AlignHCenter)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer)

        self.results_view.addWidget(self.no_results_page)

        self.vboxLayout.addWidget(self.results_view)

        self.hboxlayout = QHBoxLayout()
        self.hboxlayout.setSpacing(6)
        self.hboxlayout.setObjectName(u"hboxlayout")
        self.hboxlayout.setContentsMargins(0, 0, 0, 0)
        self.hspacer = QSpacerItem(111, 31, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hboxlayout.addItem(self.hspacer)

        self.ok_button = QPushButton(CDLookupDialog)
        self.ok_button.setObjectName(u"ok_button")
        self.ok_button.setEnabled(False)

        self.hboxlayout.addWidget(self.ok_button)

        self.lookup_button = QPushButton(CDLookupDialog)
        self.lookup_button.setObjectName(u"lookup_button")

        self.hboxlayout.addWidget(self.lookup_button)

        self.cancel_button = QPushButton(CDLookupDialog)
        self.cancel_button.setObjectName(u"cancel_button")

        self.hboxlayout.addWidget(self.cancel_button)


        self.vboxLayout.addLayout(self.hboxlayout)

        QWidget.setTabOrder(self.release_list, self.submit_button)
        QWidget.setTabOrder(self.submit_button, self.ok_button)
        QWidget.setTabOrder(self.ok_button, self.lookup_button)
        QWidget.setTabOrder(self.lookup_button, self.cancel_button)

        self.retranslateUi(CDLookupDialog)
        self.ok_button.clicked.connect(CDLookupDialog.accept)
        self.cancel_button.clicked.connect(CDLookupDialog.reject)

        self.results_view.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(CDLookupDialog)
    # setupUi

    def retranslateUi(self, CDLookupDialog):
        CDLookupDialog.setWindowTitle(_(u"CD Lookup"))
        self.label.setText(_(u"The following releases on MusicBrainz match the CD:"))
        self.no_results_label.setText(_(u"No matching releases found for this disc."))
        self.submit_button.setText(_(u"Submit disc ID"))
        self.ok_button.setText(_(u"&Load into Picard"))
        self.lookup_button.setText(_(u"&Submit disc ID"))
        self.cancel_button.setText(_(u"&Cancel"))
    # retranslateUi

