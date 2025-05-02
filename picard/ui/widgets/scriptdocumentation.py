# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021, 2025 Bob Swift
# Copyright (C) 2021-2022 Philipp Wolfer
# Copyright (C) 2021-2024 Laurent Monin
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


from PyQt6 import (
    QtCore,
    QtWidgets,
)

from picard.const import PICARD_URLS
from picard.i18n import gettext as _
from picard.script import script_function_documentation_all
from picard.util.tags import (
    ALL_TAGS,
    TagVar,
)

from picard.ui import FONT_FAMILY_MONOSPACE
from picard.ui.colors import interface_colors


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


class ScriptingDocumentationWidget(QtWidgets.QWidget):
    """Custom widget to display the scripting documentation.
    """
    def __init__(self, include_link=True, parent=None):
        """Custom widget to display the scripting documentation.

        Args:
            include_link (bool): Indicates whether the web link should be included
            parent (QWidget): Parent screen to check layoutDirection()
        """
        super().__init__(parent=parent)

        if self.layoutDirection() == QtCore.Qt.LayoutDirection.RightToLeft:
            text_direction = 'rtl'
        else:
            text_direction = 'ltr'

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

        funcdoc = script_function_documentation_all(
            fmt='html',
            postprocessor=process_html,
        )

        func_html = DOCUMENTATION_HTML_TEMPLATE % {
            'html': "<dl>%s</dl>" % funcdoc,
            'script_function_fg': interface_colors.get_qcolor('syntax_hl_func').name(),
            'monospace_font': FONT_FAMILY_MONOSPACE,
            'dir': text_direction,
            'inline_start': 'right' if text_direction == 'rtl' else 'left'
        }

        def process_tag(tag: TagVar):
            template = '<dt>%s</dt><dd>%s</dd>'
            tag_title = '%' + tag.script_name() + '%'
            tag_desc = tag.full_description_content()
            return template % (f'<a id="{tag.script_name()}"><code>{tag_title}</code></a>', tag_desc)

        tagdoc = ''
        for tag in sorted(ALL_TAGS, key=lambda x: x.script_name()):
            tagdoc += process_tag(tag)

        tag_html = DOCUMENTATION_HTML_TEMPLATE % {
            'html': "<dl>%s</dl>" % tagdoc,
            'script_function_fg': interface_colors.get_qcolor('syntax_hl_func').name(),
            'monospace_font': FONT_FAMILY_MONOSPACE,
            'dir': text_direction,
            'inline_start': 'right' if text_direction == 'rtl' else 'left'
        }

        # Scripting code is always left-to-right. Qt does not support the dir
        # attribute on inline tags, insert explicit left-right-marks instead.
        if text_direction == 'rtl':
            func_html = func_html.replace('<code>', '<code>&#8206;')
            tag_html = tag_html.replace('<code>', '<code>&#8206;')

        link = '<a href="' + PICARD_URLS['doc_scripting'] + '">' + _('Open Scripting Documentation in your browser') + '</a>'

        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName('docs_verticalLayout')

        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setContentsMargins(0, 0, 0, 0)

        self.func_page = QtWidgets.QWidget()
        self.func_page_layout = QtWidgets.QVBoxLayout()
        self.func_page_layout.setContentsMargins(0, 0, 0, 0)
        self.func_page.setLayout(self.func_page_layout)

        self.func_browser = QtWidgets.QTextBrowser()
        self.func_browser.setEnabled(True)
        self.func_browser.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.func_browser.setObjectName('func_browser')
        self.func_browser.setHtml(func_html)
        self.func_browser.show()
        self.func_page_layout.addWidget(self.func_browser)

        self.tags_page = QtWidgets.QWidget()
        self.tags_page_layout = QtWidgets.QVBoxLayout()
        self.tags_page_layout.setContentsMargins(0, 0, 0, 0)
        self.tags_page.setLayout(self.tags_page_layout)

        self.tags_browser = QtWidgets.QTextBrowser()
        self.tags_browser.setEnabled(True)
        self.tags_browser.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.tags_browser.setObjectName('tags_browser')
        self.tags_browser.setOpenExternalLinks(True)
        self.tags_browser.setHtml(tag_html)
        self.tags_browser.show()
        self.tags_page_layout.addWidget(self.tags_browser)

        self.tabs.addTab(self.func_page, _("Functions"))
        self.tabs.addTab(self.tags_page, _("Tags"))

        self.verticalLayout.addWidget(self.tabs)

        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setContentsMargins(-1, 0, -1, -1)
        self.horizontalLayout.setObjectName('docs_horizontalLayout')

        if include_link:
            self.scripting_doc_link = QtWidgets.QLabel()

            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)
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
