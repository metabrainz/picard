# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'options_cover.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QSizePolicy, QSpacerItem, QToolButton, QVBoxLayout,
    QWidget)

from picard.i18n import gettext as _

class Ui_CoverOptionsPage(object):
    def setupUi(self, CoverOptionsPage):
        if not CoverOptionsPage.objectName():
            CoverOptionsPage.setObjectName(u"CoverOptionsPage")
        CoverOptionsPage.resize(632, 560)
        self.verticalLayout = QVBoxLayout(CoverOptionsPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.save_images_to_tags = QGroupBox(CoverOptionsPage)
        self.save_images_to_tags.setObjectName(u"save_images_to_tags")
        self.save_images_to_tags.setCheckable(True)
        self.save_images_to_tags.setChecked(False)
        self.vboxLayout = QVBoxLayout(self.save_images_to_tags)
        self.vboxLayout.setSpacing(2)
        self.vboxLayout.setObjectName(u"vboxLayout")
        self.vboxLayout.setContentsMargins(9, 9, 9, 9)
        self.cb_embed_front_only = QCheckBox(self.save_images_to_tags)
        self.cb_embed_front_only.setObjectName(u"cb_embed_front_only")

        self.vboxLayout.addWidget(self.cb_embed_front_only)


        self.verticalLayout.addWidget(self.save_images_to_tags)

        self.save_images_to_files = QGroupBox(CoverOptionsPage)
        self.save_images_to_files.setObjectName(u"save_images_to_files")
        self.save_images_to_files.setCheckable(True)
        self.save_images_to_files.setChecked(False)
        self.verticalLayout_2 = QVBoxLayout(self.save_images_to_files)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.label_use_filename = QLabel(self.save_images_to_files)
        self.label_use_filename.setObjectName(u"label_use_filename")

        self.verticalLayout_2.addWidget(self.label_use_filename)

        self.cover_image_filename = QLineEdit(self.save_images_to_files)
        self.cover_image_filename.setObjectName(u"cover_image_filename")

        self.verticalLayout_2.addWidget(self.cover_image_filename)

        self.save_images_overwrite = QCheckBox(self.save_images_to_files)
        self.save_images_overwrite.setObjectName(u"save_images_overwrite")

        self.verticalLayout_2.addWidget(self.save_images_overwrite)

        self.save_only_one_front_image = QCheckBox(self.save_images_to_files)
        self.save_only_one_front_image.setObjectName(u"save_only_one_front_image")

        self.verticalLayout_2.addWidget(self.save_only_one_front_image)

        self.image_type_as_filename = QCheckBox(self.save_images_to_files)
        self.image_type_as_filename.setObjectName(u"image_type_as_filename")

        self.verticalLayout_2.addWidget(self.image_type_as_filename)


        self.verticalLayout.addWidget(self.save_images_to_files)

        self.ca_providers_groupbox = QGroupBox(CoverOptionsPage)
        self.ca_providers_groupbox.setObjectName(u"ca_providers_groupbox")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.ca_providers_groupbox.sizePolicy().hasHeightForWidth())
        self.ca_providers_groupbox.setSizePolicy(sizePolicy)
        self.ca_providers_layout = QVBoxLayout(self.ca_providers_groupbox)
        self.ca_providers_layout.setObjectName(u"ca_providers_layout")
        self.ca_providers_list = QListWidget(self.ca_providers_groupbox)
        self.ca_providers_list.setObjectName(u"ca_providers_list")

        self.ca_providers_layout.addWidget(self.ca_providers_list)

        self.ca_layout = QHBoxLayout()
        self.ca_layout.setObjectName(u"ca_layout")
        self.move_label = QLabel(self.ca_providers_groupbox)
        self.move_label.setObjectName(u"move_label")

        self.ca_layout.addWidget(self.move_label)

        self.up_button = QToolButton(self.ca_providers_groupbox)
        self.up_button.setObjectName(u"up_button")
        self.up_button.setLayoutDirection(Qt.LeftToRight)
        icon = QIcon()
        iconThemeName = u":/images/16x16/go-up.png"
        if QIcon.hasThemeIcon(iconThemeName):
            icon = QIcon.fromTheme(iconThemeName)
        else:
            icon.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)

        self.up_button.setIcon(icon)
        self.up_button.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.up_button.setAutoRaise(False)

        self.ca_layout.addWidget(self.up_button)

        self.down_button = QToolButton(self.ca_providers_groupbox)
        self.down_button.setObjectName(u"down_button")
        icon1 = QIcon()
        iconThemeName = u":/images/16x16/go-down.png"
        if QIcon.hasThemeIcon(iconThemeName):
            icon1 = QIcon.fromTheme(iconThemeName)
        else:
            icon1.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)

        self.down_button.setIcon(icon1)
        self.down_button.setToolButtonStyle(Qt.ToolButtonIconOnly)

        self.ca_layout.addWidget(self.down_button)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.ca_layout.addItem(self.horizontalSpacer)


        self.ca_providers_layout.addLayout(self.ca_layout)


        self.verticalLayout.addWidget(self.ca_providers_groupbox, 0, Qt.AlignTop)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)


        self.retranslateUi(CoverOptionsPage)

        QMetaObject.connectSlotsByName(CoverOptionsPage)
    # setupUi

    def retranslateUi(self, CoverOptionsPage):
        self.save_images_to_tags.setTitle(_(u"Embed cover images into tags"))
        self.cb_embed_front_only.setText(_(u"Embed only a single front image"))
        self.save_images_to_files.setTitle(_(u"Save cover images as separate files"))
        self.label_use_filename.setText(_(u"Use the following file name for images:"))
        self.save_images_overwrite.setText(_(u"Overwrite the file if it already exists"))
        self.save_only_one_front_image.setText(_(u"Save only a single front image as separate file"))
        self.image_type_as_filename.setText(_(u"Always use the primary image type as the file name for non-front images"))
        self.ca_providers_groupbox.setTitle(_(u"Cover Art Providers"))
        self.move_label.setText(_(u"Reorder Priority:"))
#if QT_CONFIG(tooltip)
        self.up_button.setToolTip(_(u"Move selected item up"))
#endif // QT_CONFIG(tooltip)
        self.up_button.setText("")
#if QT_CONFIG(tooltip)
        self.down_button.setToolTip(_(u"Move selected item down"))
#endif // QT_CONFIG(tooltip)
        self.down_button.setText("")
        pass
    # retranslateUi

