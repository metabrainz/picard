# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'options_matching.ui'
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
from PySide6.QtWidgets import (QApplication, QGridLayout, QGroupBox, QLabel,
    QSizePolicy, QSpacerItem, QSpinBox, QVBoxLayout,
    QWidget)

from picard.i18n import gettext as _

class Ui_MatchingOptionsPage(object):
    def setupUi(self, MatchingOptionsPage):
        if not MatchingOptionsPage.objectName():
            MatchingOptionsPage.setObjectName(u"MatchingOptionsPage")
        MatchingOptionsPage.resize(413, 612)
        self.vboxLayout = QVBoxLayout(MatchingOptionsPage)
        self.vboxLayout.setObjectName(u"vboxLayout")
        self.rename_files = QGroupBox(MatchingOptionsPage)
        self.rename_files.setObjectName(u"rename_files")
        self.gridLayout = QGridLayout(self.rename_files)
        self.gridLayout.setSpacing(2)
        self.gridLayout.setObjectName(u"gridLayout")
        self.label_6 = QLabel(self.rename_files)
        self.label_6.setObjectName(u"label_6")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_6.sizePolicy().hasHeightForWidth())
        self.label_6.setSizePolicy(sizePolicy)

        self.gridLayout.addWidget(self.label_6, 2, 0, 1, 1)

        self.track_matching_threshold = QSpinBox(self.rename_files)
        self.track_matching_threshold.setObjectName(u"track_matching_threshold")
        self.track_matching_threshold.setMaximum(100)

        self.gridLayout.addWidget(self.track_matching_threshold, 2, 1, 1, 1)

        self.cluster_lookup_threshold = QSpinBox(self.rename_files)
        self.cluster_lookup_threshold.setObjectName(u"cluster_lookup_threshold")
        self.cluster_lookup_threshold.setMaximum(100)

        self.gridLayout.addWidget(self.cluster_lookup_threshold, 1, 1, 1, 1)

        self.file_lookup_threshold = QSpinBox(self.rename_files)
        self.file_lookup_threshold.setObjectName(u"file_lookup_threshold")
        self.file_lookup_threshold.setMaximum(100)

        self.gridLayout.addWidget(self.file_lookup_threshold, 0, 1, 1, 1)

        self.label_4 = QLabel(self.rename_files)
        self.label_4.setObjectName(u"label_4")
        sizePolicy.setHeightForWidth(self.label_4.sizePolicy().hasHeightForWidth())
        self.label_4.setSizePolicy(sizePolicy)

        self.gridLayout.addWidget(self.label_4, 0, 0, 1, 1)

        self.label_5 = QLabel(self.rename_files)
        self.label_5.setObjectName(u"label_5")
        sizePolicy.setHeightForWidth(self.label_5.sizePolicy().hasHeightForWidth())
        self.label_5.setSizePolicy(sizePolicy)

        self.gridLayout.addWidget(self.label_5, 1, 0, 1, 1)


        self.vboxLayout.addWidget(self.rename_files)

        self.spacerItem = QSpacerItem(20, 41, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.vboxLayout.addItem(self.spacerItem)

#if QT_CONFIG(shortcut)
        self.label_6.setBuddy(self.file_lookup_threshold)
        self.label_4.setBuddy(self.file_lookup_threshold)
        self.label_5.setBuddy(self.file_lookup_threshold)
#endif // QT_CONFIG(shortcut)
        QWidget.setTabOrder(self.file_lookup_threshold, self.cluster_lookup_threshold)
        QWidget.setTabOrder(self.cluster_lookup_threshold, self.track_matching_threshold)

        self.retranslateUi(MatchingOptionsPage)

        QMetaObject.connectSlotsByName(MatchingOptionsPage)
    # setupUi

    def retranslateUi(self, MatchingOptionsPage):
        self.rename_files.setTitle(_(u"Thresholds"))
        self.label_6.setText(_(u"Minimal similarity for matching files to tracks:"))
        self.track_matching_threshold.setSuffix(_(u" %"))
        self.cluster_lookup_threshold.setSuffix(_(u" %"))
        self.file_lookup_threshold.setSuffix(_(u" %"))
        self.label_4.setText(_(u"Minimal similarity for file lookups:"))
        self.label_5.setText(_(u"Minimal similarity for cluster lookups:"))
        pass
    # retranslateUi

