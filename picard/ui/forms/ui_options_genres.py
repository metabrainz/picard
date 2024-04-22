# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'options_genres.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QGroupBox,
    QHBoxLayout, QLabel, QPlainTextEdit, QSizePolicy,
    QSpacerItem, QSpinBox, QVBoxLayout, QWidget)

from picard.i18n import gettext as _

class Ui_GenresOptionsPage(object):
    def setupUi(self, GenresOptionsPage):
        if not GenresOptionsPage.objectName():
            GenresOptionsPage.setObjectName(u"GenresOptionsPage")
        GenresOptionsPage.resize(590, 471)
        self.verticalLayout_2 = QVBoxLayout(GenresOptionsPage)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.use_genres = QGroupBox(GenresOptionsPage)
        self.use_genres.setObjectName(u"use_genres")
        self.use_genres.setFlat(False)
        self.use_genres.setCheckable(True)
        self.use_genres.setChecked(False)
        self.verticalLayout = QVBoxLayout(self.use_genres)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.only_my_genres = QCheckBox(self.use_genres)
        self.only_my_genres.setObjectName(u"only_my_genres")

        self.verticalLayout.addWidget(self.only_my_genres)

        self.artists_genres = QCheckBox(self.use_genres)
        self.artists_genres.setObjectName(u"artists_genres")

        self.verticalLayout.addWidget(self.artists_genres)

        self.folksonomy_tags = QCheckBox(self.use_genres)
        self.folksonomy_tags.setObjectName(u"folksonomy_tags")

        self.verticalLayout.addWidget(self.folksonomy_tags)

        self.hboxLayout = QHBoxLayout()
        self.hboxLayout.setSpacing(6)
        self.hboxLayout.setObjectName(u"hboxLayout")
        self.hboxLayout.setContentsMargins(0, 0, 0, 0)
        self.label_5 = QLabel(self.use_genres)
        self.label_5.setObjectName(u"label_5")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_5.sizePolicy().hasHeightForWidth())
        self.label_5.setSizePolicy(sizePolicy)

        self.hboxLayout.addWidget(self.label_5)

        self.min_genre_usage = QSpinBox(self.use_genres)
        self.min_genre_usage.setObjectName(u"min_genre_usage")
        self.min_genre_usage.setMaximum(100)

        self.hboxLayout.addWidget(self.min_genre_usage)


        self.verticalLayout.addLayout(self.hboxLayout)

        self.hboxLayout1 = QHBoxLayout()
        self.hboxLayout1.setSpacing(6)
        self.hboxLayout1.setObjectName(u"hboxLayout1")
        self.hboxLayout1.setContentsMargins(0, 0, 0, 0)
        self.label_6 = QLabel(self.use_genres)
        self.label_6.setObjectName(u"label_6")
        sizePolicy.setHeightForWidth(self.label_6.sizePolicy().hasHeightForWidth())
        self.label_6.setSizePolicy(sizePolicy)

        self.hboxLayout1.addWidget(self.label_6)

        self.max_genres = QSpinBox(self.use_genres)
        self.max_genres.setObjectName(u"max_genres")
        self.max_genres.setMaximum(100)

        self.hboxLayout1.addWidget(self.max_genres)


        self.verticalLayout.addLayout(self.hboxLayout1)

        self.hboxLayout2 = QHBoxLayout()
        self.hboxLayout2.setSpacing(6)
        self.hboxLayout2.setObjectName(u"hboxLayout2")
        self.hboxLayout2.setContentsMargins(0, 0, 0, 0)
        self.ignore_genres_4 = QLabel(self.use_genres)
        self.ignore_genres_4.setObjectName(u"ignore_genres_4")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(4)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.ignore_genres_4.sizePolicy().hasHeightForWidth())
        self.ignore_genres_4.setSizePolicy(sizePolicy1)

        self.hboxLayout2.addWidget(self.ignore_genres_4)

        self.join_genres = QComboBox(self.use_genres)
        self.join_genres.addItem("")
        self.join_genres.addItem("")
        self.join_genres.addItem("")
        self.join_genres.setObjectName(u"join_genres")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(1)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.join_genres.sizePolicy().hasHeightForWidth())
        self.join_genres.setSizePolicy(sizePolicy2)
        self.join_genres.setEditable(True)

        self.hboxLayout2.addWidget(self.join_genres)


        self.verticalLayout.addLayout(self.hboxLayout2)

        self.label_genres_filter = QLabel(self.use_genres)
        self.label_genres_filter.setObjectName(u"label_genres_filter")

        self.verticalLayout.addWidget(self.label_genres_filter)

        self.genres_filter = QPlainTextEdit(self.use_genres)
        self.genres_filter.setObjectName(u"genres_filter")

        self.verticalLayout.addWidget(self.genres_filter)

        self.label_test_genres_filter = QLabel(self.use_genres)
        self.label_test_genres_filter.setObjectName(u"label_test_genres_filter")

        self.verticalLayout.addWidget(self.label_test_genres_filter)

        self.test_genres_filter = QPlainTextEdit(self.use_genres)
        self.test_genres_filter.setObjectName(u"test_genres_filter")

        self.verticalLayout.addWidget(self.test_genres_filter)

        self.label_test_genres_filter_error = QLabel(self.use_genres)
        self.label_test_genres_filter_error.setObjectName(u"label_test_genres_filter_error")

        self.verticalLayout.addWidget(self.label_test_genres_filter_error)


        self.verticalLayout_2.addWidget(self.use_genres)

        self.spacerItem = QSpacerItem(181, 31, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.spacerItem)

#if QT_CONFIG(shortcut)
        self.label_5.setBuddy(self.min_genre_usage)
        self.label_6.setBuddy(self.min_genre_usage)
#endif // QT_CONFIG(shortcut)

        self.retranslateUi(GenresOptionsPage)

        QMetaObject.connectSlotsByName(GenresOptionsPage)
    # setupUi

    def retranslateUi(self, GenresOptionsPage):
        self.use_genres.setTitle(_(u"Use genres from MusicBrainz"))
        self.only_my_genres.setText(_(u"Use only my genres"))
        self.artists_genres.setText(_(u"Fall back on album's artists genres if no genres are found for the release or release group"))
        self.folksonomy_tags.setText(_(u"Use folksonomy tags as genre"))
        self.label_5.setText(_(u"Minimal genre usage:"))
        self.min_genre_usage.setSuffix(_(u" %"))
        self.label_6.setText(_(u"Maximum number of genres:"))
        self.ignore_genres_4.setText(_(u"Join multiple genres with:"))
        self.join_genres.setItemText(0, "")
        self.join_genres.setItemText(1, _(u" / "))
        self.join_genres.setItemText(2, _(u", "))

        self.label_genres_filter.setText(_(u"Genres or folksonomy tags to include or exclude, one per line:"))
        self.label_test_genres_filter.setText(_(u"Playground for genres or folksonomy tags filters (cleared on exit):"))
        self.label_test_genres_filter_error.setText("")
        pass
    # retranslateUi

