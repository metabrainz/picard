# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'widget_taglisteditor.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QHBoxLayout, QSizePolicy,
    QSpacerItem, QToolButton, QVBoxLayout, QWidget)

from picard.ui.widgets.editablelistview import UniqueEditableListView

from picard.i18n import gettext as _

class Ui_TagListEditor(object):
    def setupUi(self, TagListEditor):
        if not TagListEditor.objectName():
            TagListEditor.setObjectName(u"TagListEditor")
        TagListEditor.resize(400, 300)
        self.horizontalLayout = QHBoxLayout(TagListEditor)
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.tag_list_view = UniqueEditableListView(TagListEditor)
        self.tag_list_view.setObjectName(u"tag_list_view")
        self.tag_list_view.setDragDropMode(QAbstractItemView.InternalMove)
        self.tag_list_view.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.verticalLayout.addWidget(self.tag_list_view)

        self.edit_buttons = QWidget(TagListEditor)
        self.edit_buttons.setObjectName(u"edit_buttons")
        self.horizontalLayout_2 = QHBoxLayout(self.edit_buttons)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.tags_add_btn = QToolButton(self.edit_buttons)
        self.tags_add_btn.setObjectName(u"tags_add_btn")

        self.horizontalLayout_2.addWidget(self.tags_add_btn)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.sort_buttons = QWidget(self.edit_buttons)
        self.sort_buttons.setObjectName(u"sort_buttons")
        self.horizontalLayout_3 = QHBoxLayout(self.sort_buttons)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.tags_move_up_btn = QToolButton(self.sort_buttons)
        self.tags_move_up_btn.setObjectName(u"tags_move_up_btn")
        icon = QIcon()
        iconThemeName = u":/images/16x16/go-up.png"
        if QIcon.hasThemeIcon(iconThemeName):
            icon = QIcon.fromTheme(iconThemeName)
        else:
            icon.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)

        self.tags_move_up_btn.setIcon(icon)

        self.horizontalLayout_3.addWidget(self.tags_move_up_btn)

        self.tags_move_down_btn = QToolButton(self.sort_buttons)
        self.tags_move_down_btn.setObjectName(u"tags_move_down_btn")
        icon1 = QIcon()
        iconThemeName = u":/images/16x16/go-down.png"
        if QIcon.hasThemeIcon(iconThemeName):
            icon1 = QIcon.fromTheme(iconThemeName)
        else:
            icon1.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)

        self.tags_move_down_btn.setIcon(icon1)

        self.horizontalLayout_3.addWidget(self.tags_move_down_btn)


        self.horizontalLayout_2.addWidget(self.sort_buttons)

        self.tags_remove_btn = QToolButton(self.edit_buttons)
        self.tags_remove_btn.setObjectName(u"tags_remove_btn")

        self.horizontalLayout_2.addWidget(self.tags_remove_btn)


        self.verticalLayout.addWidget(self.edit_buttons)


        self.horizontalLayout.addLayout(self.verticalLayout)


        self.retranslateUi(TagListEditor)
        self.tags_add_btn.clicked.connect(self.tag_list_view.add_empty_row)
        self.tags_remove_btn.clicked.connect(self.tag_list_view.remove_selected_rows)
        self.tags_move_up_btn.clicked.connect(self.tag_list_view.move_selected_rows_up)
        self.tags_move_down_btn.clicked.connect(self.tag_list_view.move_selected_rows_down)

        QMetaObject.connectSlotsByName(TagListEditor)
    # setupUi

    def retranslateUi(self, TagListEditor):
        TagListEditor.setWindowTitle(_(u"Form"))
        self.tags_add_btn.setText(_(u"Add new tag"))
#if QT_CONFIG(tooltip)
        self.tags_move_up_btn.setToolTip(_(u"Move tag up"))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(accessibility)
        self.tags_move_up_btn.setAccessibleName(_(u"Move tag up"))
#endif // QT_CONFIG(accessibility)
        self.tags_move_up_btn.setText("")
#if QT_CONFIG(tooltip)
        self.tags_move_down_btn.setToolTip(_(u"Move tag down"))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(accessibility)
        self.tags_move_down_btn.setAccessibleName(_(u"Move tag down"))
#endif // QT_CONFIG(accessibility)
        self.tags_move_down_btn.setText("")
#if QT_CONFIG(tooltip)
        self.tags_remove_btn.setToolTip(_(u"Remove selected tags"))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(accessibility)
        self.tags_remove_btn.setAccessibleName(_(u"Remove selected tags"))
#endif // QT_CONFIG(accessibility)
        self.tags_remove_btn.setText(_(u"Remove tags"))
    # retranslateUi

