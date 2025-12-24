# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021, 2025 Bob Swift
# Copyright (C) 2021-2022 Philipp Wolfer
# Copyright (C) 2021-2024, 2025 Laurent Monin
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.


from collections import namedtuple

from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard.const.tags import ALL_TAGS
from picard.extension_points.script_variables import ext_point_script_variables
from picard.i18n import gettext as _
from picard.script import script_function_documentation_all
from picard.tags.docs import (
    display_plugin_tag_full_description,
    display_tag_full_description,
)
from picard.util import get_url

from picard.ui import FONT_FAMILY_MONOSPACE
from picard.ui.colors import interface_colors


DocItem = namedtuple('DocItem', 'name desc plugin')

DOCUMENTATION_HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
<style>
dt {
    color: %(script_function_fg)s
}
dd {
    /* Qt does not support margin-inline-start, use margin-left/margin-right instead */
    margin-%(inline_start)s: 20px;
    margin-bottom: 50px;
}
code {
    font-family: %(monospace_font)s;
}
</style>
</head>
<body dir="%(dir)s">
    %(html)s
</body>
</html>
'''


def htmldoc(html, rtl):
    htmldoc = DOCUMENTATION_HTML_TEMPLATE % {
        'html': "<dl>%s</dl>" % html,
        'script_function_fg': interface_colors.get_qcolor('syntax_hl_func').name(),
        'monospace_font': FONT_FAMILY_MONOSPACE,
        'dir': 'rtl' if rtl else 'ltr',
        'inline_start': 'right' if rtl else 'left',
    }

    # Scripting code is always left-to-right. Qt does not support the dir
    # attribute on inline tags, insert explicit left-right-marks instead.
    if rtl:
        htmldoc = htmldoc.replace('<code>', '<code>&#8206;')

    return htmldoc


class HtmlBrowser(QtWidgets.QTextBrowser):
    def __init__(self, html, rtl, parent=None):
        super().__init__(parent=parent)

        self.setEnabled(True)
        self.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.setObjectName('func_browser')
        self.setOpenLinks(True)
        self.setOpenExternalLinks(True)
        self.setHtml(htmldoc(html, rtl))
        self.show()


class DocumentationPage(QtWidgets.QWidget):
    def __init__(self, rtl=False, parent=None):
        super().__init__(parent=parent)
        self.rtl = rtl
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        html = self.generate_html()
        self.browser = HtmlBrowser(html, self.rtl)
        layout.addWidget(self.browser)

    def generate_html(self):
        raise NotImplementedError


class FunctionsDocumentationPage(DocumentationPage):
    def generate_html(self):
        def process_html(html, function):
            if not html:
                html = ''
            template = '<dt>%s%s</dt><dd>%s</dd>'
            if function.module is not None and function.module != 'picard.script.functions':
                module = ' [' + function.module + ']'
            else:
                module = ''
            try:
                firstline, remaining = html.split("\n", 1)
                return template % (firstline, module, remaining)
            except ValueError:
                return template % ("<code>$%s()</code>" % function.name, module, html)

        return script_function_documentation_all(
            fmt='html',
            postprocessor=process_html,
        )


class TagsDocumentationPage(DocumentationPage):
    def generate_html(self):
        def process_tag(tag_name: str, tag_desc: str):
            tag_title = f'<a id="{tag_name}"><code>%{tag_name}%</code></a>'
            return f'<dt>{tag_title}</dt><dd>{tag_desc}</dd>'

        tags: list[DocItem] = []

        # Process system-defined tags and variables
        for tag_name in [tag.script_name() for tag in ALL_TAGS]:
            tags.append(
                DocItem(
                    name=tag_name,
                    desc=display_tag_full_description(tag_name),
                    plugin='',
                )
            )

        # Process plugin variables separately to allow plugin descriptions for duplicated variables.
        for tag_name, tag_desc, plugin in ext_point_script_variables:
            tags.append(
                DocItem(
                    name=tag_name,
                    desc=display_plugin_tag_full_description(tag_name, tag_desc),
                    plugin=plugin,
                )
            )

        html = ''
        # Sort tags alphabetically regardless of whether they are hidden, with system tags shown
        # before plugin tags having the same name.
        for tag in sorted(tags, key=lambda x: f"{x.name.lstrip('_')}:{x.plugin}"):
            html += process_tag(tag.name, tag.desc)

        return html


class ScriptingDocumentationWidget(QtWidgets.QWidget):
    """Custom widget to display the scripting documentation."""

    def __init__(self, include_link=True, parent=None):
        """Custom widget to display the scripting documentation.

        Args:
            include_link (bool): Indicates whether the web link should be included
            parent (QWidget): Parent screen to check layoutDirection()
        """
        super().__init__(parent=parent)

        self.found_item = 0
        self.found_items = 0

        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName('docs_verticalLayout')

        self.searchLayout = QtWidgets.QHBoxLayout()
        searchLabel = QtWidgets.QLabel(_("Find:"))
        self.searchLayout.addWidget(searchLabel)

        self.searchText = QtWidgets.QLineEdit()
        self.searchText.setClearButtonEnabled(True)
        self.searchText.setMaxLength(30)
        self.searchText.textEdited.connect(self._search_text_edited)
        self.searchLayout.addWidget(self.searchText)

        self.searchCount = QtWidgets.QLabel('')
        self.searchCount.setVisible(False)
        self.searchLayout.addWidget(self.searchCount)

        self.pb_prev = QtWidgets.QToolButton()
        self.pb_prev.setArrowType(QtCore.Qt.ArrowType.UpArrow)
        self.pb_prev.setToolTip(_('Find previous'))
        self.pb_prev.setDisabled(True)
        self.pb_prev.clicked.connect(self._find_prev)
        self.searchLayout.addWidget(self.pb_prev)

        self.pb_next = QtWidgets.QToolButton()
        self.pb_next.setArrowType(QtCore.Qt.ArrowType.DownArrow)
        self.pb_next.setToolTip(_('Find next'))
        self.pb_next.setDisabled(True)
        self.pb_next.clicked.connect(self._find_next)
        self.searchLayout.addWidget(self.pb_next)

        self.verticalLayout.addLayout(self.searchLayout)

        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setContentsMargins(0, 0, 0, 0)

        rtl = self.layoutDirection() == QtCore.Qt.LayoutDirection.RightToLeft
        func_page = FunctionsDocumentationPage(rtl=rtl)
        tags_page = TagsDocumentationPage(rtl=rtl)

        self.tabs.addTab(func_page, _("Functions"))
        self.tabs.addTab(tags_page, _("Tags"))
        self.tabs.currentChanged.connect(self._tab_changed)

        self.verticalLayout.addWidget(self.tabs)

        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setContentsMargins(-1, 0, -1, -1)
        self.horizontalLayout.setObjectName('docs_horizontalLayout')

        if include_link:
            link = (
                '<a href="'
                + get_url('doc_scripting')
                + '">'
                + _('Open Scripting Documentation in your browser')
                + '</a>'
            )
            self.scripting_doc_link = QtWidgets.QLabel()

            sizePolicy = QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred
            )
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(self.scripting_doc_link.sizePolicy().hasHeightForWidth())

            self.scripting_doc_link.setSizePolicy(sizePolicy)
            self.scripting_doc_link.setMinimumSize(QtCore.QSize(0, 20))
            self.scripting_doc_link.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.scripting_doc_link.setWordWrap(True)
            self.scripting_doc_link.setOpenExternalLinks(True)
            self.scripting_doc_link.setObjectName('docs_scripting_doc_link')
            self.scripting_doc_link.setText(link)
            self.scripting_doc_link.show()
            self.horizontalLayout.addWidget(self.scripting_doc_link)

        self.verticalLayout.addLayout(self.horizontalLayout)
        self.show()

    def _show_count(self):
        if not self.searchText.text():
            self.searchCount.setVisible(False)
            return
        if self.found_items > 0:
            self.searchCount.setText(_("({item} of {total})").format(item=self.found_item, total=self.found_items))
        else:
            self.searchCount.setText(_("(not found)"))
        self.searchCount.setVisible(True)

    def _set_button_status(self):
        self.pb_prev.setDisabled(self.found_item < 2)
        self.pb_next.setDisabled(not self.found_item < self.found_items)

    def _find_next(self):
        tab: DocumentationPage = self.tabs.currentWidget()
        tab.browser.find(self.searchText.text())
        self.found_item += 1
        self._show_count()
        self._set_button_status()

    def _find_prev(self):
        tab: DocumentationPage = self.tabs.currentWidget()
        tab.browser.find(self.searchText.text(), QtGui.QTextDocument.FindFlag.FindBackward)
        self.found_item -= 1
        self._show_count()
        self._set_button_status()

    def _tab_changed(self):
        self.searchText.clear()
        for i in range(self.tabs.count()):
            self._clear_find(self.tabs.widget(i).browser)

    def _clear_find(self, browser: HtmlBrowser):
        cursor = browser.textCursor()
        cursor.setPosition(0)
        browser.setTextCursor(cursor)
        browser.find('')
        self.found_item = self.found_items = 0
        self._set_button_status()

    def _search_text_edited(self):
        tab: DocumentationPage = self.tabs.currentWidget()
        self._clear_find(tab.browser)
        while tab.browser.find(self.searchText.text()):
            self.found_items += 1
        if self.found_items > 1:
            item_count = self.found_items
            self._clear_find(tab.browser)
            self.found_items = item_count
            tab.browser.find(self.searchText.text())
        if self.found_items > 0:
            self.found_item = 1
            self._set_button_status()
        self._show_count()
