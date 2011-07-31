# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'options_lastfmplus.ui'
#
# Created: Thu Jul 23 10:55:17 2009
#      by: PyQt4 UI code generator 4.4.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_LastfmOptionsPage(object):
    def setupUi(self, LastfmOptionsPage):
        LastfmOptionsPage.setObjectName("LastfmOptionsPage")
        LastfmOptionsPage.resize(414, 493)
        self.horizontalLayout = QtGui.QHBoxLayout(LastfmOptionsPage)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.tabWidget = QtGui.QTabWidget(LastfmOptionsPage)
        self.tabWidget.setMinimumSize(QtCore.QSize(330, 475))
        self.tabWidget.setElideMode(QtCore.Qt.ElideNone)
        self.tabWidget.setUsesScrollButtons(False)
        self.tabWidget.setObjectName("tabWidget")
        self.tab_4 = QtGui.QWidget()
        self.tab_4.setObjectName("tab_4")
        self.gridLayout_3 = QtGui.QGridLayout(self.tab_4)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.groupBox_5 = QtGui.QGroupBox(self.tab_4)
        self.groupBox_5.setMinimumSize(QtCore.QSize(0, 0))
        self.groupBox_5.setBaseSize(QtCore.QSize(0, 0))
        self.groupBox_5.setObjectName("groupBox_5")
        self.gridLayout_2 = QtGui.QGridLayout(self.groupBox_5)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.label_10 = QtGui.QLabel(self.groupBox_5)
        self.label_10.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.label_10.setObjectName("label_10")
        self.gridLayout_2.addWidget(self.label_10, 0, 0, 1, 1)
        self.max_group_tags = QtGui.QSpinBox(self.groupBox_5)
        self.max_group_tags.setObjectName("max_group_tags")
        self.gridLayout_2.addWidget(self.max_group_tags, 0, 1, 1, 1)
        spacerItem = QtGui.QSpacerItem(20, 95, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout_2.addItem(spacerItem, 0, 2, 4, 1)
        self.label_12 = QtGui.QLabel(self.groupBox_5)
        self.label_12.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.label_12.setObjectName("label_12")
        self.gridLayout_2.addWidget(self.label_12, 0, 3, 1, 1)
        self.max_mood_tags = QtGui.QSpinBox(self.groupBox_5)
        self.max_mood_tags.setObjectName("max_mood_tags")
        self.gridLayout_2.addWidget(self.max_mood_tags, 0, 4, 1, 1)
        self.label_11 = QtGui.QLabel(self.groupBox_5)
        self.label_11.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.label_11.setObjectName("label_11")
        self.gridLayout_2.addWidget(self.label_11, 1, 0, 1, 1)
        self.max_minor_tags = QtGui.QSpinBox(self.groupBox_5)
        self.max_minor_tags.setObjectName("max_minor_tags")
        self.gridLayout_2.addWidget(self.max_minor_tags, 1, 1, 1, 1)
        self.label_14 = QtGui.QLabel(self.groupBox_5)
        self.label_14.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.label_14.setObjectName("label_14")
        self.gridLayout_2.addWidget(self.label_14, 1, 3, 1, 1)
        self.max_occasion_tags = QtGui.QSpinBox(self.groupBox_5)
        self.max_occasion_tags.setObjectName("max_occasion_tags")
        self.gridLayout_2.addWidget(self.max_occasion_tags, 1, 4, 1, 1)
        self.label_15 = QtGui.QLabel(self.groupBox_5)
        self.label_15.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.label_15.setObjectName("label_15")
        self.gridLayout_2.addWidget(self.label_15, 2, 3, 1, 1)
        self.max_category_tags = QtGui.QSpinBox(self.groupBox_5)
        self.max_category_tags.setObjectName("max_category_tags")
        self.gridLayout_2.addWidget(self.max_category_tags, 2, 4, 1, 1)
        self.app_major2minor_tag = QtGui.QCheckBox(self.groupBox_5)
        self.app_major2minor_tag.setObjectName("app_major2minor_tag")
        self.gridLayout_2.addWidget(self.app_major2minor_tag, 3, 0, 1, 2)
        self.label_26 = QtGui.QLabel(self.groupBox_5)
        self.label_26.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.label_26.setObjectName("label_26")
        self.gridLayout_2.addWidget(self.label_26, 3, 3, 1, 1)
        self.join_tags_sign = QtGui.QLineEdit(self.groupBox_5)
        self.join_tags_sign.setObjectName("join_tags_sign")
        self.gridLayout_2.addWidget(self.join_tags_sign, 3, 4, 1, 1)
        self.gridLayout_3.addWidget(self.groupBox_5, 0, 0, 1, 1)
        self.groupBox_4 = QtGui.QGroupBox(self.tab_4)
        self.groupBox_4.setObjectName("groupBox_4")
        self.gridLayout_6 = QtGui.QGridLayout(self.groupBox_4)
        self.gridLayout_6.setObjectName("gridLayout_6")
        self.use_country_tag = QtGui.QCheckBox(self.groupBox_4)
        self.use_country_tag.setObjectName("use_country_tag")
        self.gridLayout_6.addWidget(self.use_country_tag, 0, 0, 1, 1)
        self.use_city_tag = QtGui.QCheckBox(self.groupBox_4)
        self.use_city_tag.setTristate(False)
        self.use_city_tag.setObjectName("use_city_tag")
        self.gridLayout_6.addWidget(self.use_city_tag, 1, 0, 1, 1)
        self.use_year_tag = QtGui.QCheckBox(self.groupBox_4)
        self.use_year_tag.setObjectName("use_year_tag")
        self.gridLayout_6.addWidget(self.use_year_tag, 0, 1, 1, 1)
        self.use_decade_tag = QtGui.QCheckBox(self.groupBox_4)
        self.use_decade_tag.setObjectName("use_decade_tag")
        self.gridLayout_6.addWidget(self.use_decade_tag, 1, 1, 1, 1)
        self.gridLayout_3.addWidget(self.groupBox_4, 1, 0, 1, 1)
        self.groupBox_9 = QtGui.QGroupBox(self.tab_4)
        self.groupBox_9.setObjectName("groupBox_9")
        self.gridLayout_4 = QtGui.QGridLayout(self.groupBox_9)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.use_track_tags = QtGui.QCheckBox(self.groupBox_9)
        self.use_track_tags.setChecked(False)
        self.use_track_tags.setObjectName("use_track_tags")
        self.gridLayout_4.addWidget(self.use_track_tags, 0, 0, 1, 1)
        self.label_19 = QtGui.QLabel(self.groupBox_9)
        self.label_19.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.label_19.setObjectName("label_19")
        self.gridLayout_4.addWidget(self.label_19, 0, 2, 1, 1)
        self.min_tracktag_weight = QtGui.QSpinBox(self.groupBox_9)
        self.min_tracktag_weight.setObjectName("min_tracktag_weight")
        self.gridLayout_4.addWidget(self.min_tracktag_weight, 0, 3, 1, 1)
        self.label_20 = QtGui.QLabel(self.groupBox_9)
        self.label_20.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.label_20.setObjectName("label_20")
        self.gridLayout_4.addWidget(self.label_20, 1, 2, 1, 1)
        self.max_tracktag_drop = QtGui.QSpinBox(self.groupBox_9)
        self.max_tracktag_drop.setObjectName("max_tracktag_drop")
        self.gridLayout_4.addWidget(self.max_tracktag_drop, 1, 3, 1, 1)
        spacerItem1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout_4.addItem(spacerItem1, 0, 1, 2, 1)
        self.gridLayout_3.addWidget(self.groupBox_9, 2, 0, 1, 1)
        self.groupBox_10 = QtGui.QGroupBox(self.tab_4)
        self.groupBox_10.setObjectName("groupBox_10")
        self.gridLayout_5 = QtGui.QGridLayout(self.groupBox_10)
        self.gridLayout_5.setObjectName("gridLayout_5")
        spacerItem2 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout_5.addItem(spacerItem2, 0, 1, 3, 1)
        self.artist_tag_us_no = QtGui.QRadioButton(self.groupBox_10)
        self.artist_tag_us_no.setObjectName("artist_tag_us_no")
        self.gridLayout_5.addWidget(self.artist_tag_us_no, 0, 0, 1, 1)
        self.label_21 = QtGui.QLabel(self.groupBox_10)
        self.label_21.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.label_21.setObjectName("label_21")
        self.gridLayout_5.addWidget(self.label_21, 0, 2, 1, 1)
        self.artist_tags_weight = QtGui.QSpinBox(self.groupBox_10)
        self.artist_tags_weight.setObjectName("artist_tags_weight")
        self.gridLayout_5.addWidget(self.artist_tags_weight, 0, 3, 1, 1)
        self.artist_tag_us_ex = QtGui.QRadioButton(self.groupBox_10)
        self.artist_tag_us_ex.setObjectName("artist_tag_us_ex")
        self.gridLayout_5.addWidget(self.artist_tag_us_ex, 1, 0, 1, 1)
        self.label_22 = QtGui.QLabel(self.groupBox_10)
        self.label_22.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.label_22.setObjectName("label_22")
        self.gridLayout_5.addWidget(self.label_22, 1, 2, 1, 1)
        self.min_artisttag_weight = QtGui.QSpinBox(self.groupBox_10)
        self.min_artisttag_weight.setObjectName("min_artisttag_weight")
        self.gridLayout_5.addWidget(self.min_artisttag_weight, 1, 3, 1, 1)
        self.artist_tag_us_yes = QtGui.QRadioButton(self.groupBox_10)
        self.artist_tag_us_yes.setObjectName("artist_tag_us_yes")
        self.gridLayout_5.addWidget(self.artist_tag_us_yes, 2, 0, 1, 1)
        self.label_23 = QtGui.QLabel(self.groupBox_10)
        self.label_23.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.label_23.setObjectName("label_23")
        self.gridLayout_5.addWidget(self.label_23, 2, 2, 1, 1)
        self.max_artisttag_drop = QtGui.QSpinBox(self.groupBox_10)
        self.max_artisttag_drop.setObjectName("max_artisttag_drop")
        self.gridLayout_5.addWidget(self.max_artisttag_drop, 2, 3, 1, 1)
        self.gridLayout_3.addWidget(self.groupBox_10, 3, 0, 1, 1)
        self.tabWidget.addTab(self.tab_4, "")
        self.tab_3 = QtGui.QWidget()
        self.tab_3.setObjectName("tab_3")
        self.gridLayout_7 = QtGui.QGridLayout(self.tab_3)
        self.gridLayout_7.setObjectName("gridLayout_7")
        self.groupBox_3 = QtGui.QGroupBox(self.tab_3)
        self.groupBox_3.setObjectName("groupBox_3")
        self.gridLayout = QtGui.QGridLayout(self.groupBox_3)
        self.gridLayout.setObjectName("gridLayout")
        self.label = QtGui.QLabel(self.groupBox_3)
        self.label.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.genre_major = QtGui.QLineEdit(self.groupBox_3)
        self.genre_major.setObjectName("genre_major")
        self.gridLayout.addWidget(self.genre_major, 0, 1, 1, 1)
        self.label_2 = QtGui.QLabel(self.groupBox_3)
        self.label_2.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)
        self.genre_minor = QtGui.QLineEdit(self.groupBox_3)
        self.genre_minor.setObjectName("genre_minor")
        self.gridLayout.addWidget(self.genre_minor, 1, 1, 1, 1)
        self.label_3 = QtGui.QLabel(self.groupBox_3)
        self.label_3.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 2, 0, 1, 1)
        self.genre_mood = QtGui.QLineEdit(self.groupBox_3)
        self.genre_mood.setObjectName("genre_mood")
        self.gridLayout.addWidget(self.genre_mood, 2, 1, 1, 1)
        self.label_5 = QtGui.QLabel(self.groupBox_3)
        self.label_5.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label_5.setObjectName("label_5")
        self.gridLayout.addWidget(self.label_5, 3, 0, 1, 1)
        self.genre_year = QtGui.QLineEdit(self.groupBox_3)
        self.genre_year.setObjectName("genre_year")
        self.gridLayout.addWidget(self.genre_year, 3, 1, 1, 1)
        self.label_4 = QtGui.QLabel(self.groupBox_3)
        self.label_4.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 4, 0, 1, 1)
        self.genre_occasion = QtGui.QLineEdit(self.groupBox_3)
        self.genre_occasion.setObjectName("genre_occasion")
        self.gridLayout.addWidget(self.genre_occasion, 4, 1, 1, 1)
        self.label_6 = QtGui.QLabel(self.groupBox_3)
        self.label_6.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label_6.setObjectName("label_6")
        self.gridLayout.addWidget(self.label_6, 5, 0, 1, 1)
        self.genre_decade = QtGui.QLineEdit(self.groupBox_3)
        self.genre_decade.setObjectName("genre_decade")
        self.gridLayout.addWidget(self.genre_decade, 5, 1, 1, 1)
        self.label_7 = QtGui.QLabel(self.groupBox_3)
        self.label_7.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label_7.setObjectName("label_7")
        self.gridLayout.addWidget(self.label_7, 6, 0, 1, 1)
        self.genre_country = QtGui.QLineEdit(self.groupBox_3)
        self.genre_country.setObjectName("genre_country")
        self.gridLayout.addWidget(self.genre_country, 6, 1, 1, 1)
        self.label_9 = QtGui.QLabel(self.groupBox_3)
        self.label_9.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label_9.setObjectName("label_9")
        self.gridLayout.addWidget(self.label_9, 7, 0, 1, 1)
        self.genre_city = QtGui.QLineEdit(self.groupBox_3)
        self.genre_city.setObjectName("genre_city")
        self.gridLayout.addWidget(self.genre_city, 7, 1, 1, 1)
        self.label_8 = QtGui.QLabel(self.groupBox_3)
        self.label_8.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label_8.setObjectName("label_8")
        self.gridLayout.addWidget(self.label_8, 8, 0, 1, 1)
        self.genre_category = QtGui.QLineEdit(self.groupBox_3)
        self.genre_category.setObjectName("genre_category")
        self.gridLayout.addWidget(self.genre_category, 8, 1, 1, 1)
        self.gridLayout_7.addWidget(self.groupBox_3, 0, 0, 1, 2)
        self.groupBox_17 = QtGui.QGroupBox(self.tab_3)
        self.groupBox_17.setObjectName("groupBox_17")
        self.horizontalLayout_4 = QtGui.QHBoxLayout(self.groupBox_17)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.genre_translations = QtGui.QTextEdit(self.groupBox_17)
        self.genre_translations.setObjectName("genre_translations")
        self.horizontalLayout_4.addWidget(self.genre_translations)
        self.gridLayout_7.addWidget(self.groupBox_17, 1, 0, 1, 1)
        self.groupBox_2 = QtGui.QGroupBox(self.tab_3)
        self.groupBox_2.setObjectName("groupBox_2")
        self.verticalLayout = QtGui.QVBoxLayout(self.groupBox_2)
        self.verticalLayout.setObjectName("verticalLayout")
        self.filter_report = QtGui.QPushButton(self.groupBox_2)
        self.filter_report.setObjectName("filter_report")
        self.verticalLayout.addWidget(self.filter_report)
        self.check_word_lists = QtGui.QPushButton(self.groupBox_2)
        self.check_word_lists.setObjectName("check_word_lists")
        self.verticalLayout.addWidget(self.check_word_lists)
        self.check_translation_list = QtGui.QPushButton(self.groupBox_2)
        self.check_translation_list.setEnabled(False)
        self.check_translation_list.setObjectName("check_translation_list")
        self.verticalLayout.addWidget(self.check_translation_list)
        spacerItem3 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem3)
        self.load_default_lists = QtGui.QPushButton(self.groupBox_2)
        font = QtGui.QFont()
        font.setWeight(75)
        font.setBold(True)
        self.load_default_lists.setFont(font)
        self.load_default_lists.setObjectName("load_default_lists")
        self.verticalLayout.addWidget(self.load_default_lists)
        self.gridLayout_7.addWidget(self.groupBox_2, 1, 1, 1, 1)
        self.tabWidget.addTab(self.tab_3, "")
        self.horizontalLayout.addWidget(self.tabWidget)

        self.retranslateUi(LastfmOptionsPage)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(LastfmOptionsPage)
        LastfmOptionsPage.setTabOrder(self.max_group_tags, self.max_minor_tags)
        LastfmOptionsPage.setTabOrder(self.max_minor_tags, self.use_track_tags)
        LastfmOptionsPage.setTabOrder(self.use_track_tags, self.min_tracktag_weight)
        LastfmOptionsPage.setTabOrder(self.min_tracktag_weight, self.max_tracktag_drop)
        LastfmOptionsPage.setTabOrder(self.max_tracktag_drop, self.artist_tag_us_no)
        LastfmOptionsPage.setTabOrder(self.artist_tag_us_no, self.artist_tag_us_ex)
        LastfmOptionsPage.setTabOrder(self.artist_tag_us_ex, self.artist_tag_us_yes)
        LastfmOptionsPage.setTabOrder(self.artist_tag_us_yes, self.artist_tags_weight)
        LastfmOptionsPage.setTabOrder(self.artist_tags_weight, self.min_artisttag_weight)
        LastfmOptionsPage.setTabOrder(self.min_artisttag_weight, self.max_artisttag_drop)
        LastfmOptionsPage.setTabOrder(self.max_artisttag_drop, self.genre_major)
        LastfmOptionsPage.setTabOrder(self.genre_major, self.genre_minor)
        LastfmOptionsPage.setTabOrder(self.genre_minor, self.genre_mood)
        LastfmOptionsPage.setTabOrder(self.genre_mood, self.genre_year)
        LastfmOptionsPage.setTabOrder(self.genre_year, self.genre_occasion)
        LastfmOptionsPage.setTabOrder(self.genre_occasion, self.genre_decade)
        LastfmOptionsPage.setTabOrder(self.genre_decade, self.genre_country)
        LastfmOptionsPage.setTabOrder(self.genre_country, self.genre_category)
        LastfmOptionsPage.setTabOrder(self.genre_category, self.genre_translations)
        LastfmOptionsPage.setTabOrder(self.genre_translations, self.filter_report)
        LastfmOptionsPage.setTabOrder(self.filter_report, self.check_word_lists)
        LastfmOptionsPage.setTabOrder(self.check_word_lists, self.check_translation_list)
        LastfmOptionsPage.setTabOrder(self.check_translation_list, self.load_default_lists)

    def retranslateUi(self, LastfmOptionsPage):
        LastfmOptionsPage.setWindowTitle(QtGui.QApplication.translate("LastfmOptionsPage", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setWindowTitle(QtGui.QApplication.translate("LastfmOptionsPage", "LastfmOptionsPage", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_5.setTitle(QtGui.QApplication.translate("LastfmOptionsPage", "Max Tags Written   0=Disabled  1=One Tag  2+= Multiple Tags", None, QtGui.QApplication.UnicodeUTF8))
        self.label_10.setText(QtGui.QApplication.translate("LastfmOptionsPage", "Major Tags - Group", None, QtGui.QApplication.UnicodeUTF8))
        self.max_group_tags.setToolTip(QtGui.QApplication.translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">Max Grouping (Major Genres) Tags</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Tag Name:   %GROUPING%</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Top-level genres ex: <span style=\" font-style:italic;\">Classical, Rock, Soundtracks  </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Written to Grouping tag. Can also be appended to    </p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Genre tag if \'Append Major\' box (below) is checked.  </p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.label_12.setText(QtGui.QApplication.translate("LastfmOptionsPage", "Max Mood Tags", None, QtGui.QApplication.UnicodeUTF8))
        self.max_mood_tags.setToolTip(QtGui.QApplication.translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">Max Mood Tags   </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">ID3v2.4+ Only!    </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Tag:   %MOOD%    </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">How a track \'feels\'. ex:<span style=\" font-style:italic;\"> Happy, Introspective, Drunk</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Note: <span style=\" color:#dd3a3a;\">The TMOO frame is only standard in ID3v2.4 tags.    </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">For all other tags, Moods will be saved as a Comment.</p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.label_11.setText(QtGui.QApplication.translate("LastfmOptionsPage", "Minor Tags - Genre", None, QtGui.QApplication.UnicodeUTF8))
        self.max_minor_tags.setToolTip(QtGui.QApplication.translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">Max Genre Tags</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Tag:   %GENRE%</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">These are specific, detailed genres. ex:<span style=\" font-style:italic;\"> Baroque, Classic Rock, Delta Blues   </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Set this to 1 if using this tag for file naming, </p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">or if your player doesn\'t support multi-value tags</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"> </p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Consider setting this to 3+ if you use Genre</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">for searching in your music library.</p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.label_14.setText(QtGui.QApplication.translate("LastfmOptionsPage", "Max Occasion Tags", None, QtGui.QApplication.UnicodeUTF8))
        self.max_occasion_tags.setToolTip(QtGui.QApplication.translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">Max Occasion Tags   </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">Nonstandard!</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Tag:   %Comment:Songs-db_Occasion%    </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Good situations to play a track, ex: Driving<span style=\" font-style:italic;\">, Love, Party    </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Set to 2+ to increase this tag\'s usefulness.</p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.label_15.setText(QtGui.QApplication.translate("LastfmOptionsPage", "Max Category Tags", None, QtGui.QApplication.UnicodeUTF8))
        self.max_category_tags.setToolTip(QtGui.QApplication.translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">Max Category Tags   </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">Nonstandard!</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Tag:   %Comment:Songs-db_Custom2%    </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Another Top-level grouping tag.</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Contains tags like: <span style=\" font-style:italic;\">Female Vocalists, Singer-Songwriter</span></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.app_major2minor_tag.setToolTip(QtGui.QApplication.translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Append Major to Minor Tags       </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">This will prepend any Grouping tags   </p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">onto the Genre tag at tagging time. The effect is</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">that the Grouping Tag which is also the Major Genre</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Becomes the First Genre in the List of Minor Genres</p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.app_major2minor_tag.setText(QtGui.QApplication.translate("LastfmOptionsPage", "Prepend Major to Minor Tags", None, QtGui.QApplication.UnicodeUTF8))
        self.label_26.setText(QtGui.QApplication.translate("LastfmOptionsPage", "Join Tags With", None, QtGui.QApplication.UnicodeUTF8))
        self.join_tags_sign.setToolTip(QtGui.QApplication.translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">The Separator to use for <span style=\" font-weight:600;\">Multi-Value</span> tags</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">You may want to add a trailing space to</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">help with readability.</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">To use <span style=\" font-weight:600;\">Separate Tags</span> rather than a single</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">multi-value tag leave this field blank ie. no space at all.</p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.join_tags_sign.setText(QtGui.QApplication.translate("LastfmOptionsPage", ";", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_4.setTitle(QtGui.QApplication.translate("LastfmOptionsPage", "Enable (Selected) or Disable (Not Selected) other Tags", None, QtGui.QApplication.UnicodeUTF8))
        self.use_country_tag.setToolTip(QtGui.QApplication.translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Country   </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">Nonstandard!</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Tag:   %Comment:Songs-db_Custom2%</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">The country the artist or track is most </p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">associated with. Will retreive results using the Country</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">tag list on Tag Filter List Page</p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.use_country_tag.setText(QtGui.QApplication.translate("LastfmOptionsPage", "Country", None, QtGui.QApplication.UnicodeUTF8))
        self.use_city_tag.setToolTip(QtGui.QApplication.translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Country   </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">Nonstandard!</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Tag:   %Comment:Songs-db_Custom2%</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">The city or region the artist or track is most </p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">associated with. If Enabled will use the most popular</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">tag in the City list on Tag Filter Options page.  If </p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Country option has been selected as well the City tag</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">will be displayed second in the tag list.</p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.use_city_tag.setText(QtGui.QApplication.translate("LastfmOptionsPage", "City", None, QtGui.QApplication.UnicodeUTF8))
        self.use_year_tag.setToolTip(QtGui.QApplication.translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Original Year   </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">Nonstandard!</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Tag:   %ID3:TDOR% or </span><span style=\" font-weight:600;\">%ID3:TORY%</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">The year the song was created or most popular in. Quite often</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">this is the correct original release year of the track. The tag</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">written to is determined by the settings you have selected</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">in Picard Tag options. Ie. if ID3v2.3 is selected the original year tag</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">will be ID3:TORY rather than the default of ID3:TDOR</p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.use_year_tag.setText(QtGui.QApplication.translate("LastfmOptionsPage", "Original Year", None, QtGui.QApplication.UnicodeUTF8))
        self.use_decade_tag.setToolTip(QtGui.QApplication.translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Decade   </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">Nonstandard!</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Tag:   %Comment:Songs-db_Custom1%</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">The decade the song was created, ex: 1970s</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">This is based on the last fm tags first, if none found then </p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">the originalyear tag, and then the release date of the album.</p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.use_decade_tag.setText(QtGui.QApplication.translate("LastfmOptionsPage", "Decade", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_9.setTitle(QtGui.QApplication.translate("LastfmOptionsPage", "Track Based Tags: Tags based on Track Title and Artist", None, QtGui.QApplication.UnicodeUTF8))
        self.use_track_tags.setToolTip(QtGui.QApplication.translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Check this to use <span style=\" font-weight:600;\">Track-based tags. </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">These are tags relevant to the <span style=\" font-weight:600; font-style:italic;\">song</span></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.use_track_tags.setText(QtGui.QApplication.translate("LastfmOptionsPage", "Use Track Based Tags", None, QtGui.QApplication.UnicodeUTF8))
        self.label_19.setText(QtGui.QApplication.translate("LastfmOptionsPage", "Minimum Tag Weight", None, QtGui.QApplication.UnicodeUTF8))
        self.min_tracktag_weight.setToolTip(QtGui.QApplication.translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">The minimum weight track-based tag</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">to use, in terms of popularity</p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.min_tracktag_weight.setSuffix(QtGui.QApplication.translate("LastfmOptionsPage", " %", None, QtGui.QApplication.UnicodeUTF8))
        self.label_20.setText(QtGui.QApplication.translate("LastfmOptionsPage", "Maximum Inter-Tag Drop", None, QtGui.QApplication.UnicodeUTF8))
        self.max_tracktag_drop.setToolTip(QtGui.QApplication.translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">The maximum allowed drop in relevance</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">for the tag to still be a match</p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.max_tracktag_drop.setSuffix(QtGui.QApplication.translate("LastfmOptionsPage", " %", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_10.setTitle(QtGui.QApplication.translate("LastfmOptionsPage", "Artist Based Tags: Based on the Artist, not the Track Title.", None, QtGui.QApplication.UnicodeUTF8))
        self.artist_tag_us_no.setToolTip(QtGui.QApplication.translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Select this to Never use Artist based tags</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Be sure you have Use Track-Based Tags</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">checked, though.</p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.artist_tag_us_no.setText(QtGui.QApplication.translate("LastfmOptionsPage", "Don\'t use Artist Tags", None, QtGui.QApplication.UnicodeUTF8))
        self.label_21.setText(QtGui.QApplication.translate("LastfmOptionsPage", "Artist-Tags Weight", None, QtGui.QApplication.UnicodeUTF8))
        self.artist_tags_weight.setToolTip(QtGui.QApplication.translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">How strongly Artist-based tags</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">are considered for inclusion</p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.artist_tags_weight.setSuffix(QtGui.QApplication.translate("LastfmOptionsPage", " %", None, QtGui.QApplication.UnicodeUTF8))
        self.artist_tag_us_ex.setToolTip(QtGui.QApplication.translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Enabling this uses Artist-based tags only  </p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">if there aren\'t enough Track-based tags.   </p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Default: Enabled</span></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.artist_tag_us_ex.setText(QtGui.QApplication.translate("LastfmOptionsPage", "Extend Track-Tags", None, QtGui.QApplication.UnicodeUTF8))
        self.label_22.setText(QtGui.QApplication.translate("LastfmOptionsPage", "Minimum Tag Weight", None, QtGui.QApplication.UnicodeUTF8))
        self.min_artisttag_weight.setToolTip(QtGui.QApplication.translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">The minimum weight Artist-based tag    </p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">to use, in terms of popularity    </p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.min_artisttag_weight.setSuffix(QtGui.QApplication.translate("LastfmOptionsPage", " %", None, QtGui.QApplication.UnicodeUTF8))
        self.artist_tag_us_yes.setToolTip(QtGui.QApplication.translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Enable this to <span style=\" font-weight:600;\">Always</span> use Artist-based tags</p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.artist_tag_us_yes.setText(QtGui.QApplication.translate("LastfmOptionsPage", "Use Artist-Tags", None, QtGui.QApplication.UnicodeUTF8))
        self.label_23.setText(QtGui.QApplication.translate("LastfmOptionsPage", "Maximum Inter-Tag Drop", None, QtGui.QApplication.UnicodeUTF8))
        self.max_artisttag_drop.setToolTip(QtGui.QApplication.translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">The maximum allowed drop in relevance    </p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">for the tag to still be a match    </p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.max_artisttag_drop.setSuffix(QtGui.QApplication.translate("LastfmOptionsPage", " %", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_4), QtGui.QApplication.translate("LastfmOptionsPage", "General Options", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_3.setTitle(QtGui.QApplication.translate("LastfmOptionsPage", "Tag Lists", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("LastfmOptionsPage", "Grouping", None, QtGui.QApplication.UnicodeUTF8))
        self.genre_major.setToolTip(QtGui.QApplication.translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">Major Genres</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Top-level genres ex: <span style=\" font-style:italic;\">Classical, Rock, Soundtracks</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Written to Grouping tag. Can also be appended to</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Genre tag if enabled in General Options.</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Tag Name:   %GROUPING%   ID3 Frame:   TIT1</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Supported:   </span><span style=\" font-weight:600; color:#3852b0;\">Mp3, Ogg, Flac, Wma, AAC</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt; font-weight:600; color:#3852b0;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Compatibility                     Tag Mapping</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" vertical-align:super;\">______________________________________________________</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Foobar        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     CONTENT GROUP</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">iTunes        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     GROUPING</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">MediaMonkey        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     GROUPING</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">MP3Tag        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     CONTENTGROUP</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Winamp        </span><span style=\" font-size:7pt; font-weight:600; color:#707070;\">UNK</span><span style=\" font-size:7pt; font-weight:600;\">    ---</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">WMP        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     MUSIC CATEGORY DESCRIPTION</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:7pt; font-weight:600;\"></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("LastfmOptionsPage", "Genres", None, QtGui.QApplication.UnicodeUTF8))
        self.genre_minor.setToolTip(QtGui.QApplication.translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">Minor Genres</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">More specific genres. ex:<span style=\" font-style:italic;\"> Baroque, Classic Rock, Delta Blues</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Written to Genre tag.</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Tag Name:   %GENRE%    ID3 Frame:   TCON</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Supported:   </span><span style=\" font-weight:600; color:#3852b0;\">Mp3, Ogg, Flac, Wma, AAC, Ape, Wav</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt; font-weight:600; color:#3852b0;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Compatibility                     Tag Mapping</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" vertical-align:super;\">______________________________________________________</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Foobar        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     GENRE</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">iTunes        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     GENRE    </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">MediaMonkey        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     GENRE</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">MP3Tag        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     GENRE</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Winamp        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     GENRE</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">WMP        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     GENRE</span></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("LastfmOptionsPage", "Mood", None, QtGui.QApplication.UnicodeUTF8))
        self.genre_mood.setToolTip(QtGui.QApplication.translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">Mood   </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">ID3v2.4+ Only!</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">How a track \'feels\'. ex:<span style=\" font-style:italic;\"> Happy, Introspective, Drunk</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Note: The TMOO frame is only standard in ID3v2.4 tags.</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">For all other tags, Moods are saved as a Comment.</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Tag Name:   %MOOD%    ID3 Frame:   TMOO</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Supported:   </span><span style=\" font-weight:600; color:#3852b0;\">Mp3, Ogg, Flac, Wma, AAC</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt; font-weight:600; color:#3852b0;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Compatibility                     Tag Mapping</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" vertical-align:super;\">______________________________________________________</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Foobar         </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">NO</span><span style=\" font-size:7pt; font-weight:600;\">      ---</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">iTunes        </span><span style=\" font-size:7pt; font-weight:600; color:#707070;\">UNK</span><span style=\" font-size:7pt; font-weight:600;\">     ---</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">MediaMonkey        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     MOOD</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">MP3Tag        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     MOOD</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Winamp        </span><span style=\" font-size:7pt; font-weight:600; color:#707070;\">UNK</span><span style=\" font-size:7pt; font-weight:600;\">     ---</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">WMP        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     WM/MOOD</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:7pt; font-weight:600;\"></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.label_5.setText(QtGui.QApplication.translate("LastfmOptionsPage", "Years", None, QtGui.QApplication.UnicodeUTF8))
        self.genre_year.setToolTip(QtGui.QApplication.translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">Original Year </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">The year the track was first <span style=\" font-style:italic;\">recorded</span>.</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Note: This tag is often missing or wrong.</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">If Blank, the album release date is used.</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Tag Name:   %ORIGINALDATE%   </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">ID3 Frame: V2.3: TORY   v2.4: TDOR</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Supported:   </span><span style=\" font-weight:600; color:#3852b0;\">Mp3, Ogg, Flac, Wma, AAC</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt; font-weight:600; color:#3852b0;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Compatibility                     Tag Mapping</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" vertical-align:super;\">______________________________________________________</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Foobar        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">    ORIGINAL RELEASE DATE</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">iTunes        </span><span style=\" font-size:7pt; font-weight:600; color:#707070;\">UNK</span><span style=\" font-size:7pt; font-weight:600;\">    ---</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">MediaMonkey        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">    ORIGINAL DATE</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">MP3Tag        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">    ORIGYEAR</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Winamp        </span><span style=\" font-size:7pt; font-weight:600; color:#707070;\">UNK</span><span style=\" font-size:7pt; font-weight:600;\">    ---</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">WMP        </span><span style=\" font-size:7pt; font-weight:600; color:#707070;\">UNK</span><span style=\" font-size:7pt; font-weight:600;\">    ---</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:7pt; font-weight:600;\"></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("LastfmOptionsPage", "Occasion", None, QtGui.QApplication.UnicodeUTF8))
        self.genre_occasion.setToolTip(QtGui.QApplication.translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">Occasions   </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">Nonstandard!</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Good times to play the track, ex: Driving<span style=\" font-style:italic;\">, Love, Party</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Written to the Comment tag. Has very limited support.</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Tag Name:   %Comment:Songs-db_Occasion%</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">ID3 Frame:   COMM:Songs-db_Occasion</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Supported:   </span><span style=\" font-weight:600; color:#3852b0;\">Mp3, Ogg, Flac</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt; font-weight:600; color:#3852b0;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Compatibility                     Tag Mapping</span></p>\n"
"<p align=\"justify\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" vertical-align:super;\">______________________________________________________</span></p>\n"
"<p align=\"justify\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Foobar         </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">NO</span><span style=\" font-size:7pt; font-weight:600;\">     ---</span></p>\n"
"<p align=\"justify\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">iTunes         </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">NO</span><span style=\" font-size:7pt; font-weight:600;\">     ---</span></p>\n"
"<p align=\"justify\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">MediaMonkey        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     Custom tag</span></p>\n"
"<p align=\"justify\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">MP3Tag        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     Comment:Songs-db_Occasion</span></p>\n"
"<p align=\"justify\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Winamp         </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">NO</span><span style=\" font-size:7pt; font-weight:600;\">     ---</span></p>\n"
"<p align=\"justify\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">WMP       </span><span style=\" font-size:7pt; font-weight:600; color:#707070;\">UNK</span><span style=\" font-size:7pt; font-weight:600;\">     ---</span></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.label_6.setText(QtGui.QApplication.translate("LastfmOptionsPage", "Decades", None, QtGui.QApplication.UnicodeUTF8))
        self.genre_decade.setToolTip(QtGui.QApplication.translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">Decade   </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">Nonstandard!</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">The decade the song was created. Based on</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">originalyear, so will frequently be wrong.</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Unless your app can map Comment subvalues</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">this tag will show as part of any existing comment.</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Tag Name:   %Comment:Songs-db_Custom1%</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">ID3 Frame:   COMM:Songs-db_Custom1</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Supported:   </span><span style=\" font-weight:600; color:#3852b0;\">Mp3, Ogg, Flac</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt; font-weight:600; color:#3852b0;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Compatibility                     Tag Mapping</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" vertical-align:super;\">______________________________________________________</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Foobar         </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">NO</span><span style=\" font-size:7pt; font-weight:600;\">     ---</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">iTunes         </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">NO</span><span style=\" font-size:7pt; font-weight:600;\">     ---</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">MediaMonkey        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     Custom tag</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">MP3Tag        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     Comment:Songs-db_Custom1</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Winamp         </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">NO</span><span style=\" font-size:7pt; font-weight:600;\">     ---</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">WMP         </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">NO</span><span style=\" font-size:7pt; font-weight:600;\">     ---</span></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.label_7.setText(QtGui.QApplication.translate("LastfmOptionsPage", "Country", None, QtGui.QApplication.UnicodeUTF8))
        self.genre_country.setToolTip(QtGui.QApplication.translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">Country   </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">Nonstandard!</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Artist country/location info, ex: America, New York, NYC</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Allowing more tags will usually give more detailed info.</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Unless your app maps Comment subvalues</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">this tag will show as part of any existing comment.</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Tag Name:   %Comment:Songs-db_Custom3%</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">ID3 Frame:   COMM:Songs-db_Custom3</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Supported:   </span><span style=\" font-weight:600; color:#3852b0;\">Mp3, Ogg, Flac</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt; font-weight:600; color:#3852b0;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Compatibility                     Tag Mapping</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" vertical-align:super;\">______________________________________________________</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Foobar         </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">NO</span><span style=\" font-size:7pt; font-weight:600;\">     ---</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">iTunes         </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">NO</span><span style=\" font-size:7pt; font-weight:600;\">     ---</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">MediaMonkey        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     Custom tag</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">MP3Tag        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     Comment:Songs-db_Custom3</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Winamp         </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">NO</span><span style=\" font-size:7pt; font-weight:600;\">     ---</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">WMP         </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">NO</span><span style=\" font-size:7pt; font-weight:600;\">     ---</span></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.label_9.setText(QtGui.QApplication.translate("LastfmOptionsPage", "Cities", None, QtGui.QApplication.UnicodeUTF8))
        self.genre_city.setToolTip(QtGui.QApplication.translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">Country   </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">Nonstandard!</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Artist country/location info, ex: America, New York, NYC</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Allowing more tags will usually give more detailed info.</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Unless your app maps Comment subvalues</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">this tag will show as part of any existing comment.</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Tag Name:   %Comment:Songs-db_Custom3%</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">ID3 Frame:   COMM:Songs-db_Custom3</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Supported:   </span><span style=\" font-weight:600; color:#3852b0;\">Mp3, Ogg, Flac</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt; font-weight:600; color:#3852b0;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Compatibility                     Tag Mapping</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" vertical-align:super;\">______________________________________________________</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Foobar         </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">NO</span><span style=\" font-size:7pt; font-weight:600;\">     ---</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">iTunes         </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">NO</span><span style=\" font-size:7pt; font-weight:600;\">     ---</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">MediaMonkey        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     Custom tag</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">MP3Tag        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     Comment:Songs-db_Custom3</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Winamp         </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">NO</span><span style=\" font-size:7pt; font-weight:600;\">     ---</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">WMP         </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">NO</span><span style=\" font-size:7pt; font-weight:600;\">     ---</span></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.label_8.setText(QtGui.QApplication.translate("LastfmOptionsPage", "Category", None, QtGui.QApplication.UnicodeUTF8))
        self.genre_category.setToolTip(QtGui.QApplication.translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">Category   </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">Nonstandard!</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Another Top-level grouping tag.</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Returns terms like Female Vocalists, Singer-Songwriter</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Unless your app can map Comment subvalues</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">this tag will show as part of any existing comment.</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Tag Name:   %Comment:Songs-db_Custom2%</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">ID3 Frame:   COMM:Songs-db_Custom2</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Supported:   </span><span style=\" font-weight:600; color:#3852b0;\">Mp3, Ogg, Flac</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt; font-weight:600; color:#3852b0;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Compatibility                     Tag Mapping</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" vertical-align:super;\">______________________________________________________</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Foobar         </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">NO</span><span style=\" font-size:7pt; font-weight:600;\">     ---</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">iTunes         </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">NO</span><span style=\" font-size:7pt; font-weight:600;\">     ---</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">MediaMonkey        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     Custom tag</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">MP3Tag        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     Comment:Songs-db_Custom2</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Winamp         </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">NO</span><span style=\" font-size:7pt; font-weight:600;\">     ---</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">WMP         </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">NO</span><span style=\" font-size:7pt; font-weight:600;\">     ---</span></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_17.setTitle(QtGui.QApplication.translate("LastfmOptionsPage", "Tag Translations", None, QtGui.QApplication.UnicodeUTF8))
        self.genre_translations.setToolTip(QtGui.QApplication.translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">Tag Translations</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">This list lets you change how matches from the</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">tag lists are actually written into your tags.</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Typical Uses:</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-style:italic;\">- Standardize spellings,   ex: rock-n-roll , rock and roll , rock \'n roll  --&gt; rock &amp; roll</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-style:italic;\">- Clean formatting,          ex: lovesongs --&gt; love songs</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-style:italic;\">- Condense related tags, ex: heavy metal, hair metal, power metal  --&gt; metal</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Usage:   Old Name, New Name  </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">One Rule per line:</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600; color:#4659cf;\">Death Metal, Metal</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600; color:#4659cf;\">Sunshine-Pop, Pop</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600; color:#4659cf;\">Super-awesome-musics, Nice</span></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_2.setTitle(QtGui.QApplication.translate("LastfmOptionsPage", "Tools", None, QtGui.QApplication.UnicodeUTF8))
        self.filter_report.setToolTip(QtGui.QApplication.translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">Filter Report    </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Tells you how many tags and    </p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">translations you have in each list.    </p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.filter_report.setText(QtGui.QApplication.translate("LastfmOptionsPage", "Filter Report", None, QtGui.QApplication.UnicodeUTF8))
        self.check_word_lists.setToolTip(QtGui.QApplication.translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">Check Tag Lists</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Each tag may appear only <span style=\" font-weight:600;\">once</span> across all lists.    </p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">This scans all the lists for duplicated tags</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">so you can easily remove them.    </p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Run this whenever you add tags to a list!</span>    </p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.check_word_lists.setText(QtGui.QApplication.translate("LastfmOptionsPage", "Check Tag Lists", None, QtGui.QApplication.UnicodeUTF8))
        self.check_translation_list.setToolTip(QtGui.QApplication.translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:7pt;\">Not implemented yet.</span></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.check_translation_list.setText(QtGui.QApplication.translate("LastfmOptionsPage", "Translations", None, QtGui.QApplication.UnicodeUTF8))
        self.load_default_lists.setToolTip(QtGui.QApplication.translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:600; font-style:normal;\">\n"
"<p align=\"center\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" color:#dd3a3a;\">WARNING!</span></p>\n"
"<p align=\"center\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" color:#000000;\">This will overwrite all current</span></p>\n"
"<p align=\"center\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" color:#000000;\">Tag Lists and Translations!</span></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.load_default_lists.setText(QtGui.QApplication.translate("LastfmOptionsPage", "Load Defaults", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), QtGui.QApplication.translate("LastfmOptionsPage", "Tag Filter Lists", None, QtGui.QApplication.UnicodeUTF8))

