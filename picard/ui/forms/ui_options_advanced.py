# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'options_advanced.ui'
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
from PySide6.QtWidgets import (QAbstractSpinBox, QApplication, QCheckBox, QComboBox,
    QGridLayout, QGroupBox, QHBoxLayout, QLabel,
    QLayout, QLineEdit, QSizePolicy, QSpinBox,
    QVBoxLayout, QWidget)

from picard.ui.widgets.taglisteditor import TagListEditor

from picard.i18n import gettext as _

class Ui_AdvancedOptionsPage(object):
    def setupUi(self, AdvancedOptionsPage):
        if not AdvancedOptionsPage.objectName():
            AdvancedOptionsPage.setObjectName(u"AdvancedOptionsPage")
        AdvancedOptionsPage.resize(570, 455)
        self.vboxLayout = QVBoxLayout(AdvancedOptionsPage)
        self.vboxLayout.setObjectName(u"vboxLayout")
        self.groupBox = QGroupBox(AdvancedOptionsPage)
        self.groupBox.setObjectName(u"groupBox")
        self.gridLayout = QGridLayout(self.groupBox)
        self.gridLayout.setSpacing(2)
        self.gridLayout.setObjectName(u"gridLayout")
        self.label_ignore_regex = QLabel(self.groupBox)
        self.label_ignore_regex.setObjectName(u"label_ignore_regex")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_ignore_regex.sizePolicy().hasHeightForWidth())
        self.label_ignore_regex.setSizePolicy(sizePolicy)
        self.label_ignore_regex.setWordWrap(True)

        self.gridLayout.addWidget(self.label_ignore_regex, 1, 0, 1, 1)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label_query_limit = QLabel(self.groupBox)
        self.label_query_limit.setObjectName(u"label_query_limit")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label_query_limit.sizePolicy().hasHeightForWidth())
        self.label_query_limit.setSizePolicy(sizePolicy1)

        self.horizontalLayout_2.addWidget(self.label_query_limit)

        self.query_limit = QComboBox(self.groupBox)
        self.query_limit.addItem(u"25")
        self.query_limit.addItem(u"50")
        self.query_limit.addItem(u"75")
        self.query_limit.addItem(u"100")
        self.query_limit.setObjectName(u"query_limit")
        self.query_limit.setCurrentText(u"50")

        self.horizontalLayout_2.addWidget(self.query_limit)


        self.gridLayout.addLayout(self.horizontalLayout_2, 8, 0, 1, 1)

        self.regex_error = QLabel(self.groupBox)
        self.regex_error.setObjectName(u"regex_error")

        self.gridLayout.addWidget(self.regex_error, 3, 0, 1, 1)

        self.ignore_regex = QLineEdit(self.groupBox)
        self.ignore_regex.setObjectName(u"ignore_regex")

        self.gridLayout.addWidget(self.ignore_regex, 2, 0, 1, 1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.label_track_duration_diff = QLabel(self.groupBox)
        self.label_track_duration_diff.setObjectName(u"label_track_duration_diff")
        sizePolicy1.setHeightForWidth(self.label_track_duration_diff.sizePolicy().hasHeightForWidth())
        self.label_track_duration_diff.setSizePolicy(sizePolicy1)
        self.label_track_duration_diff.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.horizontalLayout.addWidget(self.label_track_duration_diff)

        self.ignore_track_duration_difference_under = QSpinBox(self.groupBox)
        self.ignore_track_duration_difference_under.setObjectName(u"ignore_track_duration_difference_under")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.ignore_track_duration_difference_under.sizePolicy().hasHeightForWidth())
        self.ignore_track_duration_difference_under.setSizePolicy(sizePolicy2)
        self.ignore_track_duration_difference_under.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        self.ignore_track_duration_difference_under.setAccelerated(True)
        self.ignore_track_duration_difference_under.setMinimum(1)
        self.ignore_track_duration_difference_under.setMaximum(7200)
        self.ignore_track_duration_difference_under.setValue(2)

        self.horizontalLayout.addWidget(self.ignore_track_duration_difference_under)


        self.gridLayout.addLayout(self.horizontalLayout, 6, 0, 2, 1)

        self.recursively_add_files = QCheckBox(self.groupBox)
        self.recursively_add_files.setObjectName(u"recursively_add_files")

        self.gridLayout.addWidget(self.recursively_add_files, 5, 0, 1, 1)

        self.ignore_hidden_files = QCheckBox(self.groupBox)
        self.ignore_hidden_files.setObjectName(u"ignore_hidden_files")

        self.gridLayout.addWidget(self.ignore_hidden_files, 4, 0, 1, 1)


        self.vboxLayout.addWidget(self.groupBox)

        self.groupBox_completeness = QGroupBox(AdvancedOptionsPage)
        self.groupBox_completeness.setObjectName(u"groupBox_completeness")
        self.gridLayout1 = QGridLayout(self.groupBox_completeness)
        self.gridLayout1.setObjectName(u"gridLayout1")
        self.completeness_ignore_videos = QCheckBox(self.groupBox_completeness)
        self.completeness_ignore_videos.setObjectName(u"completeness_ignore_videos")

        self.gridLayout1.addWidget(self.completeness_ignore_videos, 0, 0, 1, 1)

        self.completeness_ignore_data = QCheckBox(self.groupBox_completeness)
        self.completeness_ignore_data.setObjectName(u"completeness_ignore_data")
        self.completeness_ignore_data.setCheckable(True)

        self.gridLayout1.addWidget(self.completeness_ignore_data, 3, 0, 1, 1)

        self.completeness_ignore_pregap = QCheckBox(self.groupBox_completeness)
        self.completeness_ignore_pregap.setObjectName(u"completeness_ignore_pregap")

        self.gridLayout1.addWidget(self.completeness_ignore_pregap, 0, 1, 1, 1)

        self.completeness_ignore_silence = QCheckBox(self.groupBox_completeness)
        self.completeness_ignore_silence.setObjectName(u"completeness_ignore_silence")

        self.gridLayout1.addWidget(self.completeness_ignore_silence, 3, 1, 1, 1)


        self.vboxLayout.addWidget(self.groupBox_completeness)

        self.groupBox_ignore_tags = QGroupBox(AdvancedOptionsPage)
        self.groupBox_ignore_tags.setObjectName(u"groupBox_ignore_tags")
        self.verticalLayout = QVBoxLayout(self.groupBox_ignore_tags)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.compare_ignore_tags = TagListEditor(self.groupBox_ignore_tags)
        self.compare_ignore_tags.setObjectName(u"compare_ignore_tags")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.compare_ignore_tags.sizePolicy().hasHeightForWidth())
        self.compare_ignore_tags.setSizePolicy(sizePolicy3)

        self.verticalLayout.addWidget(self.compare_ignore_tags)


        self.vboxLayout.addWidget(self.groupBox_ignore_tags)

        QWidget.setTabOrder(self.ignore_regex, self.ignore_hidden_files)
        QWidget.setTabOrder(self.ignore_hidden_files, self.recursively_add_files)
        QWidget.setTabOrder(self.recursively_add_files, self.ignore_track_duration_difference_under)
        QWidget.setTabOrder(self.ignore_track_duration_difference_under, self.query_limit)
        QWidget.setTabOrder(self.query_limit, self.completeness_ignore_videos)
        QWidget.setTabOrder(self.completeness_ignore_videos, self.completeness_ignore_data)

        self.retranslateUi(AdvancedOptionsPage)

        self.query_limit.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(AdvancedOptionsPage)
    # setupUi

    def retranslateUi(self, AdvancedOptionsPage):
        self.groupBox.setTitle(_(u"Advanced options"))
        self.label_ignore_regex.setText(_(u"Ignore file paths matching the following regular expression:"))
        self.label_query_limit.setText(_(u"Maximum number of entities to return per MusicBrainz query"))

        self.regex_error.setText("")
        self.label_track_duration_diff.setText(_(u"Ignore track duration difference under this number of seconds"))
        self.ignore_track_duration_difference_under.setSuffix("")
        self.recursively_add_files.setText(_(u"Include sub-folders when adding files from folder"))
        self.ignore_hidden_files.setText(_(u"Ignore hidden files"))
        self.groupBox_completeness.setTitle(_(u"Ignore the following tracks when determining whether a release is complete"))
        self.completeness_ignore_videos.setText(_(u"Video tracks"))
        self.completeness_ignore_data.setText(_(u"Data tracks"))
        self.completeness_ignore_pregap.setText(_(u"Pregap tracks"))
        self.completeness_ignore_silence.setText(_(u"Silent tracks"))
        self.groupBox_ignore_tags.setTitle(_(u"Tags to ignore for comparison:"))
        pass
    # retranslateUi

