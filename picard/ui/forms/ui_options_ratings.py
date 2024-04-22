# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'options_ratings.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QGroupBox, QLabel,
    QLineEdit, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

from picard.i18n import gettext as _

class Ui_RatingsOptionsPage(object):
    def setupUi(self, RatingsOptionsPage):
        if not RatingsOptionsPage.objectName():
            RatingsOptionsPage.setObjectName(u"RatingsOptionsPage")
        RatingsOptionsPage.resize(397, 267)
        self.vboxLayout = QVBoxLayout(RatingsOptionsPage)
        self.vboxLayout.setObjectName(u"vboxLayout")
        self.enable_ratings = QGroupBox(RatingsOptionsPage)
        self.enable_ratings.setObjectName(u"enable_ratings")
        self.enable_ratings.setCheckable(True)
        self.enable_ratings.setChecked(True)
        self.vboxLayout1 = QVBoxLayout(self.enable_ratings)
        self.vboxLayout1.setObjectName(u"vboxLayout1")
        self.label = QLabel(self.enable_ratings)
        self.label.setObjectName(u"label")
        self.label.setWordWrap(True)

        self.vboxLayout1.addWidget(self.label)

        self.ignore_tags_2 = QLabel(self.enable_ratings)
        self.ignore_tags_2.setObjectName(u"ignore_tags_2")
        self.ignore_tags_2.setEnabled(True)
        self.ignore_tags_2.setWordWrap(True)

        self.vboxLayout1.addWidget(self.ignore_tags_2)

        self.rating_user_email = QLineEdit(self.enable_ratings)
        self.rating_user_email.setObjectName(u"rating_user_email")
        self.rating_user_email.setReadOnly(False)

        self.vboxLayout1.addWidget(self.rating_user_email)

        self.submit_ratings = QCheckBox(self.enable_ratings)
        self.submit_ratings.setObjectName(u"submit_ratings")

        self.vboxLayout1.addWidget(self.submit_ratings)


        self.vboxLayout.addWidget(self.enable_ratings)

        self.spacerItem = QSpacerItem(181, 31, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.vboxLayout.addItem(self.spacerItem)


        self.retranslateUi(RatingsOptionsPage)

        QMetaObject.connectSlotsByName(RatingsOptionsPage)
    # setupUi

    def retranslateUi(self, RatingsOptionsPage):
        self.enable_ratings.setTitle(_(u"Enable track ratings"))
        self.label.setText(_(u"Picard saves the ratings together with an e-mail address identifying the user who did the rating. That way different ratings for different users can be stored in the files. Please specify the e-mail you want to use to save your ratings."))
        self.ignore_tags_2.setText(_(u"E-mail:"))
        self.submit_ratings.setText(_(u"Submit ratings to MusicBrainz"))
        pass
    # retranslateUi

